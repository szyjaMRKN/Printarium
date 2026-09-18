import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { salesApi } from '../api/sales';
import type { SaleQuery } from '../api/sales';
import { downloadFile } from '../api/client';
import { Alert, Badge, EmptyState, Field, Loading, Pagination } from '../components/ui';
import { useMeta } from '../hooks/useMeta';
import { useToast } from '../hooks/useToast';
import { STATUS_BADGE, currentQuarter, currentYear, formatDate, formatMoney, optionLabel } from '../utils/format';

export function RegistryPage() {
  const { data: meta } = useMeta();
  const toast = useToast();
  const [view, setView] = useState<'szczegolowa' | 'dzienna'>('szczegolowa');
  const [filters, setFilters] = useState<SaleQuery>({
    year: currentYear(),
    quarter: currentQuarter(),
    page: 1,
    per_page: 50,
  });

  const registry = useQuery({
    queryKey: ['registry', filters],
    queryFn: () => salesApi.registry(filters),
    enabled: view === 'szczegolowa',
  });

  const daily = useQuery({
    queryKey: ['registry-daily', filters],
    queryFn: () => salesApi.registryDaily(filters),
    enabled: view === 'dzienna',
  });

  const setFilter = (patch: Partial<SaleQuery>) => setFilters((current) => ({ ...current, ...patch, page: 1 }));

  const exportRegistry = async (format: 'csv' | 'xlsx' | 'pdf') => {
    try {
      await downloadFile('/api/reports/ewidencja_sprzedazy/export', {
        format,
        year: filters.year,
        quarter: filters.quarter,
        month: filters.month,
        date_from: filters.date_from,
        date_to: filters.date_to,
      });
    } catch (error) {
      toast.error(error);
    }
  };

  return (
    <>
      <div className="page__header">
        <div>
          <h1>Ewidencja sprzedaży</h1>
          <p>Uproszczona ewidencja z przychodem należnym narastająco w wybranym okresie.</p>
        </div>
        <div className="btn-row">
          <button type="button" className="btn" onClick={() => void exportRegistry('csv')}>
            Eksport CSV
          </button>
          <button type="button" className="btn" onClick={() => void exportRegistry('xlsx')}>
            Eksport XLSX
          </button>
          <button type="button" className="btn" onClick={() => void exportRegistry('pdf')}>
            Eksport PDF
          </button>
        </div>
      </div>

      <section className="card">
        <div className="filters">
          <Field label="Rok" htmlFor="r_year">
            <input id="r_year" type="number" min={2000} max={2100} value={filters.year ?? ''} onChange={(e) => setFilter({ year: e.target.value ? Number(e.target.value) : undefined })} />
          </Field>
          <Field label="Kwartał" htmlFor="r_quarter">
            <select id="r_quarter" value={filters.quarter ?? ''} onChange={(e) => setFilter({ quarter: e.target.value ? Number(e.target.value) : undefined, month: undefined })}>
              <option value="">wszystkie</option>
              <option value="1">I kwartał</option>
              <option value="2">II kwartał</option>
              <option value="3">III kwartał</option>
              <option value="4">IV kwartał</option>
            </select>
          </Field>
          <Field label="Miesiąc" htmlFor="r_month">
            <select id="r_month" value={filters.month ?? ''} onChange={(e) => setFilter({ month: e.target.value ? Number(e.target.value) : undefined, quarter: undefined })}>
              <option value="">wszystkie</option>
              {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => (
                <option key={month} value={month}>
                  {String(month).padStart(2, '0')}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Dzień" htmlFor="r_day">
            <input id="r_day" type="date" value={filters.day ?? ''} onChange={(e) => setFilter({ day: e.target.value || undefined })} />
          </Field>
          <Field label="Data od" htmlFor="r_from">
            <input id="r_from" type="date" value={filters.date_from ?? ''} onChange={(e) => setFilter({ date_from: e.target.value || undefined })} />
          </Field>
          <Field label="Data do" htmlFor="r_to">
            <input id="r_to" type="date" value={filters.date_to ?? ''} onChange={(e) => setFilter({ date_to: e.target.value || undefined })} />
          </Field>
          <Field label="Kanał" htmlFor="r_channel">
            <select id="r_channel" value={filters.sales_channel ?? ''} onChange={(e) => setFilter({ sales_channel: e.target.value || undefined })}>
              <option value="">wszystkie</option>
              {meta?.sales_channel.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Status płatności" htmlFor="r_status">
            <select id="r_status" value={filters.payment_status ?? ''} onChange={(e) => setFilter({ payment_status: e.target.value || undefined })}>
              <option value="">wszystkie</option>
              {meta?.payment_status.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
        </div>
      </section>

      <div className="tabs">
        <button type="button" className={view === 'szczegolowa' ? 'tab is-active' : 'tab'} onClick={() => setView('szczegolowa')}>
          Ewidencja szczegółowa
        </button>
        <button type="button" className={view === 'dzienna' ? 'tab is-active' : 'tab'} onClick={() => setView('dzienna')}>
          Ewidencja dzienna
        </button>
      </div>

      {view === 'szczegolowa' ? (
        <section className="card card--flush">
          {registry.isLoading ? (
            <Loading />
          ) : registry.error ? (
            <Alert variant="danger">Nie udało się pobrać ewidencji.</Alert>
          ) : registry.data && registry.data.items.length === 0 ? (
            <EmptyState label="Brak sprzedaży w wybranym okresie." />
          ) : (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>Lp.</th>
                    <th>Data</th>
                    <th>Numer sprzedaży</th>
                    <th>Opis</th>
                    <th className="num">Kwota sprzedaży</th>
                    <th className="num">Korekty</th>
                    <th className="num">Przychód należny</th>
                    <th className="num">Narastająco</th>
                    <th>Status płatności</th>
                    <th className="num">Kwota otrzymana</th>
                  </tr>
                </thead>
                <tbody>
                  {registry.data?.items.map((row) => (
                    <tr key={row.sale_id}>
                      <td data-label="Lp.">{row.lp}</td>
                      <td data-label="Data">{formatDate(row.sale_date)}</td>
                      <td data-label="Numer">{row.document_number ?? '—'}</td>
                      <td data-label="Opis">{row.description ?? '—'}</td>
                      <td data-label="Kwota sprzedaży" className="num">{formatMoney(row.total_gr)}</td>
                      <td data-label="Korekty" className={row.corrections_total_gr < 0 ? 'num negative' : 'num'}>
                        {row.corrections_total_gr === 0 ? '—' : formatMoney(row.corrections_total_gr)}
                      </td>
                      <td data-label="Przychód należny" className="num">{formatMoney(row.accrued_revenue_gr)}</td>
                      <td data-label="Narastająco" className="num">
                        <strong>{formatMoney(row.cumulative_gr)}</strong>
                      </td>
                      <td data-label="Status">
                        <Badge variant={STATUS_BADGE[row.payment_status]}>
                          {optionLabel(meta?.payment_status, row.payment_status)}
                        </Badge>
                      </td>
                      <td data-label="Kwota otrzymana" className="num">{formatMoney(row.paid_amount_gr)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {registry.data ? (
            <>
              <div className="pagination">
                <span>
                  Przychód należny w okresie: <strong>{formatMoney(registry.data.summary.accrued_revenue_gr)}</strong>
                </span>
              </div>
              <Pagination
                page={registry.data.meta.page}
                pages={registry.data.meta.pages}
                total={registry.data.meta.total}
                onChange={(page) => setFilters((current) => ({ ...current, page }))}
              />
            </>
          ) : null}
        </section>
      ) : (
        <section className="card card--flush">
          {daily.isLoading ? (
            <Loading />
          ) : daily.data && daily.data.length === 0 ? (
            <EmptyState label="Brak sprzedaży w wybranym okresie." />
          ) : (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>Lp.</th>
                    <th>Data</th>
                    <th className="num">Liczba sprzedaży</th>
                    <th className="num">Wartość sprzedaży</th>
                    <th className="num">Wartość narastająco</th>
                  </tr>
                </thead>
                <tbody>
                  {daily.data?.map((row) => (
                    <tr key={row.day}>
                      <td data-label="Lp.">{row.lp}</td>
                      <td data-label="Data">{formatDate(row.day)}</td>
                      <td data-label="Liczba sprzedaży" className="num">{row.sales_count}</td>
                      <td data-label="Wartość sprzedaży" className="num">{formatMoney(row.total_gr)}</td>
                      <td data-label="Narastająco" className="num">
                        <strong>{formatMoney(row.cumulative_gr)}</strong>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </>
  );
}
