import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/resources';
import { Alert, Badge, Field, Loading, ProgressBar } from '../components/ui';
import { ChartCard, QuarterLimitChart } from '../components/charts';
import {
  LIMIT_STATUS_BADGE,
  LIMIT_STATUS_LABEL,
  currentYear,
  formatDate,
  formatMoney,
  formatPercent,
} from '../utils/format';

export function LimitsPage() {
  const [year, setYear] = useState(currentYear());
  const { data, isLoading, error } = useQuery({
    queryKey: ['limits', year],
    queryFn: () => dashboardApi.limits(year),
  });

  if (isLoading) return <Loading />;
  if (error || !data) return <Alert variant="danger">Nie udało się pobrać limitów.</Alert>;

  const multiplierPercent = data.parameters.limit_multiplier_permille / 10;

  return (
    <>
      <div className="page__header">
        <div>
          <h1>Limity działalności</h1>
          <p>
            Limit kwartalny liczony jako {formatPercent(multiplierPercent, 1)} minimalnego wynagrodzenia (
            {formatMoney(data.parameters.minimum_wage_gr)}) ={' '}
            <strong>{formatMoney(data.parameters.quarterly_limit_gr)}</strong>
            {data.parameters.quarterly_limit_override_gr ? ' (limit ustawiony ręcznie)' : ''}
          </p>
        </div>
        <Field label="Rok" htmlFor="limit_year">
          <input
            id="limit_year"
            type="number"
            min={2000}
            max={2100}
            value={year}
            onChange={(event) => setYear(Number(event.target.value) || currentYear())}
          />
        </Field>
      </div>

      {data.quarters
        .filter((quarter) => quarter.status === 'przekroczony' || quarter.status === 'mocne_ostrzezenie')
        .map((quarter) => (
          <Alert
            key={quarter.quarter}
            variant={quarter.status === 'przekroczony' ? 'danger' : 'warning'}
            title={`${quarter.label} ${quarter.year}`}
          >
            {quarter.message}
            {quarter.exceedance ? (
              <>
                <br />
                Przekroczenie nastąpiło {formatDate(quarter.exceedance.exceeded_on)} przy sprzedaży{' '}
                <strong>{quarter.exceedance.sale_document_number ?? `#${quarter.exceedance.sale_id}`}</strong>; kwota
                ponad limit: <strong>{formatMoney(quarter.exceedance.exceeded_by_gr)}</strong>.
              </>
            ) : null}
          </Alert>
        ))}

      <section className="card card--flush">
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Kwartał</th>
                <th>Okres</th>
                <th className="num">Przychód należny</th>
                <th className="num">Limit</th>
                <th>Wykorzystanie</th>
                <th className="num">Pozostało</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.quarters.map((quarter) => (
                <tr key={quarter.quarter}>
                  <td data-label="Kwartał">{quarter.label}</td>
                  <td data-label="Okres">
                    {formatDate(quarter.date_from)} – {formatDate(quarter.date_to)}
                  </td>
                  <td data-label="Przychód należny" className="num">{formatMoney(quarter.accrued_revenue_gr)}</td>
                  <td data-label="Limit" className="num">{formatMoney(quarter.limit_gr)}</td>
                  <td data-label="Wykorzystanie">
                    <div className="stack" style={{ gap: 'var(--space-1)' }}>
                      <span className="num small">{formatPercent(quarter.usage_percent)}</span>
                      <ProgressBar percent={quarter.usage_percent} status={quarter.status} />
                    </div>
                  </td>
                  <td data-label="Pozostało" className="num">{formatMoney(quarter.remaining_gr)}</td>
                  <td data-label="Status">
                    <Badge variant={LIMIT_STATUS_BADGE[quarter.status]}>{LIMIT_STATUS_LABEL[quarter.status]}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid grid--2">
        <ChartCard title="Przychód należny w kwartałach" subtitle={`rok ${data.year}`}>
          <QuarterLimitChart
            data={data.quarters.map((quarter) => ({
              label: `Q${quarter.quarter}`,
              accrued_gr: quarter.accrued_revenue_gr,
              limit_gr: quarter.limit_gr,
              status: quarter.status,
            }))}
          />
        </ChartCard>

        <section className="card">
          <h3>Liczniki pomocnicze</h3>
          <div className="stack">
            {[data.counters.cash_register, data.counters.ksef].map((counter) => (
              <div key={counter.label} className="stack" style={{ gap: 'var(--space-2)' }}>
                <div className="row spread">
                  <strong>{counter.label}</strong>
                  <span className="small muted">{counter.period_label}</span>
                </div>
                <ProgressBar percent={counter.usage_percent} status={counter.status} />
                <div className="row spread small muted">
                  <span>
                    {formatMoney(counter.value_gr)} z {formatMoney(counter.threshold_gr)}
                  </span>
                  <span>{formatPercent(counter.usage_percent)}</span>
                </div>
                {counter.message ? <Alert variant="warning">{counter.message}</Alert> : null}
              </div>
            ))}
            <p className="small muted">
              Progi są konfigurowalne w ustawieniach roku podatkowego. Aplikacja wyłącznie ostrzega — nie rozstrzyga
              o obowiązkach podatkowych.
            </p>
          </div>
        </section>
      </div>
    </>
  );
}
