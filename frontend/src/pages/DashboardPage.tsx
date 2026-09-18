import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { dashboardApi } from '../api/resources';
import { Alert, Badge, Loading, ProgressBar, Stat } from '../components/ui';
import { BarsChart, ChartCard, RankedBars, SERIES_COLORS, TrendChart } from '../components/charts';
import {
  LIMIT_STATUS_BADGE,
  LIMIT_STATUS_LABEL,
  formatDate,
  formatMoney,
  formatPercent,
  optionLabel,
} from '../utils/format';
import { useMeta } from '../hooks/useMeta';
import type { DashboardData, ThresholdCounter } from '../types';

function CounterAlert({ counter }: { counter: ThresholdCounter }) {
  if (!counter.message) return null;
  return (
    <Alert variant={counter.status === 'przekroczony' ? 'danger' : 'warning'} title={counter.label}>
      {counter.message} Aktualnie: {formatMoney(counter.value_gr)} z {formatMoney(counter.threshold_gr)} (
      {formatPercent(counter.usage_percent)}).
    </Alert>
  );
}

export function DashboardPage() {
  const { data: meta } = useMeta();
  const { data, isLoading, error } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.get,
  });

  if (isLoading) return <Loading />;
  if (error || !data) return <Alert variant="danger">Nie udało się pobrać danych pulpitu.</Alert>;

  const { limit, metrics, charts, counters } = data;
  const monthly = charts.monthly.map((row) => ({ ...row, label: row.label.slice(0, 3) }));
  const daily = charts.last_30_days.map((row) => ({ ...row, day: formatDate(row.day).slice(0, 5) }));

  return (
    <>
      <div className="page__header">
        <div>
          <h1>Pulpit</h1>
          <p>
            Dane na dzień {formatDate(data.today)} · {limit.label} {limit.year} ({formatDate(limit.date_from)} –{' '}
            {formatDate(limit.date_to)})
          </p>
        </div>
        <Link className="btn btn--primary" to="/sprzedaz?nowa=1">
          + Dodaj sprzedaż
        </Link>
      </div>

      <section className="limit-card">
        <div className="row spread">
          <span className="stat__label">Przychód należny — bieżący kwartał</span>
          <Badge variant={LIMIT_STATUS_BADGE[limit.status]}>{LIMIT_STATUS_LABEL[limit.status]}</Badge>
        </div>
        <div className="row spread" style={{ alignItems: 'baseline' }}>
          <span className="limit-card__value">
            {formatMoney(limit.accrued_revenue_gr)}
            <span className="muted" style={{ fontSize: 'var(--fs-lg)', fontWeight: 500 }}>
              {' '}
              / {formatMoney(limit.limit_gr)}
            </span>
          </span>
          <span className="limit-card__percent">{formatPercent(limit.usage_percent)}</span>
        </div>
        <ProgressBar percent={limit.usage_percent} status={limit.status} />
        <div className="row spread small muted">
          <span>
            Pozostało do limitu: <strong>{formatMoney(limit.remaining_gr)}</strong>
          </span>
          <span>Sprzedaży w kwartale: {limit.sales_count}</span>
        </div>

        {limit.status === 'przekroczony' && limit.message ? (
          <Alert variant="danger" title="Przekroczono limit">
            {limit.message}
            {limit.exceedance ? (
              <>
                <br />
                Limit został przekroczony {formatDate(limit.exceedance.exceeded_on)} sprzedażą{' '}
                <strong>{limit.exceedance.sale_document_number ?? `#${limit.exceedance.sale_id}`}</strong> o{' '}
                <strong>{formatMoney(limit.exceedance.exceeded_by_gr)}</strong>.
              </>
            ) : null}
          </Alert>
        ) : null}
        {limit.status === 'mocne_ostrzezenie' && limit.message ? (
          <Alert variant="warning">{limit.message}</Alert>
        ) : null}
        {limit.status === 'ostrzezenie' ? (
          <Alert variant="warning">
            Wykorzystano ponad 75% limitu kwartalnego. Kontroluj kolejne sprzedaże.
          </Alert>
        ) : null}
      </section>

      <CounterAlert counter={counters.cash_register} />
      <CounterAlert counter={counters.ksef} />

      <div className="grid grid--stats">
        <Stat label="Sprzedaż dzisiaj" value={formatMoney(metrics.accrued_today_gr)} hint={`${metrics.orders_today} zamówień`} />
        <Stat label="Przychód należny — miesiąc" value={formatMoney(metrics.accrued_month_gr)} hint={`${metrics.orders_month} zamówień`} />
        <Stat label="Przychód należny — kwartał" value={formatMoney(metrics.accrued_quarter_gr)} />
        <Stat label="Przychód należny — rok" value={formatMoney(metrics.accrued_year_gr)} />
        <Stat
          label="Otrzymane płatności — rok"
          value={formatMoney(metrics.received_year_gr)}
          hint={`w tym miesiącu ${formatMoney(metrics.received_month_gr)}`}
        />
        <Stat label="Niezapłacone należności" value={formatMoney(metrics.outstanding_gr)} hint="suma do zapłaty" />
        <Stat label="Koszty — rok" value={formatMoney(metrics.costs_year_gr)} hint={`w tym miesiącu ${formatMoney(metrics.costs_month_gr)}`} />
        <Stat
          label="Szacowany dochód — rok"
          value={formatMoney(metrics.income_year_gr)}
          hint="otrzymane płatności minus koszty"
        />
        <Stat label="Liczba zamówień — rok" value={String(metrics.orders_year)} />
        <Stat label="Średnia wartość zamówienia" value={formatMoney(metrics.average_order_year_gr)} hint="w tym roku" />
      </div>

      <div className="grid grid--2">
        <ChartCard title="Sprzedaż w ostatnich 30 dniach" legend={[
          { label: 'Przychód należny', color: SERIES_COLORS.accrued },
          { label: 'Przychód otrzymany', color: SERIES_COLORS.received },
        ]}>
          <TrendChart
            data={daily}
            xKey="day"
            series={[
              { key: 'accrued_gr', label: 'Przychód należny', color: SERIES_COLORS.accrued },
              { key: 'received_gr', label: 'Przychód otrzymany', color: SERIES_COLORS.received },
            ]}
          />
        </ChartCard>

        <ChartCard title="Sprzedaż miesięczna" subtitle={`rok ${data.year}`}>
          <BarsChart
            data={monthly}
            xKey="label"
            series={[{ key: 'accrued_gr', label: 'Przychód należny', color: SERIES_COLORS.accrued }]}
          />
        </ChartCard>

        <ChartCard
          title="Przychód należny a otrzymany"
          subtitle="ujęcie miesięczne"
          legend={[
            { label: 'Należny', color: SERIES_COLORS.accrued },
            { label: 'Otrzymany', color: SERIES_COLORS.received },
          ]}
        >
          <BarsChart
            data={monthly}
            xKey="label"
            series={[
              { key: 'accrued_gr', label: 'Przychód należny', color: SERIES_COLORS.accrued },
              { key: 'received_gr', label: 'Przychód otrzymany', color: SERIES_COLORS.received },
            ]}
          />
        </ChartCard>

        <ChartCard
          title="Koszty a przychód otrzymany"
          subtitle="ujęcie miesięczne"
          legend={[
            { label: 'Przychód otrzymany', color: SERIES_COLORS.received },
            { label: 'Koszty', color: SERIES_COLORS.costs },
          ]}
        >
          <BarsChart
            data={monthly}
            xKey="label"
            series={[
              { key: 'received_gr', label: 'Przychód otrzymany', color: SERIES_COLORS.received },
              { key: 'costs_gr', label: 'Koszty', color: SERIES_COLORS.costs },
            ]}
          />
        </ChartCard>

        <ChartCard title="Sprzedaż według kanału" subtitle={`rok ${data.year}`}>
          <RankedBars
            data={charts.by_channel.map((row) => ({
              ...row,
              channel: optionLabel(meta?.sales_channel, row.channel),
            }))}
            labelKey="channel"
            valueKey="accrued_gr"
          />
        </ChartCard>

        <ChartCard title="Sprzedaż według produktu" subtitle={`rok ${data.year} · 8 najlepszych`}>
          <RankedBars data={charts.by_product} labelKey="name" valueKey="value_gr" />
        </ChartCard>
      </div>
    </>
  );
}
