import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/resources';
import { downloadFile } from '../api/client';
import { Alert, Field, Loading, Stat } from '../components/ui';
import { useToast } from '../hooks/useToast';
import { currentYear, formatMoney } from '../utils/format';

export function PitPage() {
  const toast = useToast();
  const [year, setYear] = useState(currentYear());
  const { data, isLoading, error } = useQuery({
    queryKey: ['pit', year],
    queryFn: () => dashboardApi.pit(year),
  });

  if (isLoading) return <Loading />;
  if (error || !data) return <Alert variant="danger">Nie udało się pobrać podsumowania PIT.</Alert>;

  return (
    <>
      <div className="page__header">
        <div>
          <h1>Podsumowanie PIT</h1>
          <p>Przychód liczony kasowo (faktycznie otrzymane płatności) pomniejszony o koszty.</p>
        </div>
        <div className="row">
          <Field label="Rok" htmlFor="pit_year">
            <input id="pit_year" type="number" value={year} onChange={(event) => setYear(Number(event.target.value) || currentYear())} />
          </Field>
          <button
            type="button"
            className="btn"
            onClick={() =>
              void downloadFile('/api/reports/dochod/export', { format: 'xlsx', year }).catch((e) => toast.error(e))
            }
          >
            Eksport XLSX
          </button>
        </div>
      </div>

      <Alert variant="info" title="Informacja">
        {data.disclaimer}
      </Alert>

      <div className="grid grid--stats">
        <Stat label="Przychód otrzymany (rok)" value={formatMoney(data.yearly.received_gr)} />
        <Stat label="Koszty (rok)" value={formatMoney(data.yearly.costs_gr)} />
        <Stat label="Dochód (rok)" value={formatMoney(data.yearly.income_gr)} hint="przychód otrzymany minus koszty" />
        <Stat label="Przychód należny (rok)" value={formatMoney(data.yearly.accrued_gr)} hint="kontrola limitu, nie PIT" />
      </div>

      <section className="card card--flush">
        <div className="card__header" style={{ padding: 'var(--space-4) var(--space-4) 0' }}>
          <h2 className="card__title">Zestawienie miesięczne</h2>
        </div>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Miesiąc</th>
                <th className="num">Przychód otrzymany</th>
                <th className="num">Koszty</th>
                <th className="num">Dochód</th>
                <th className="num">Przychód należny</th>
              </tr>
            </thead>
            <tbody>
              {data.monthly.map((row) => (
                <tr key={row.label}>
                  <td data-label="Miesiąc">{row.label}</td>
                  <td data-label="Przychód otrzymany" className="num">{formatMoney(row.received_gr)}</td>
                  <td data-label="Koszty" className="num">{formatMoney(row.costs_gr)}</td>
                  <td data-label="Dochód" className={row.income_gr < 0 ? 'num negative' : 'num'}>
                    {formatMoney(row.income_gr)}
                  </td>
                  <td data-label="Przychód należny" className="num">{formatMoney(row.accrued_gr)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card card--flush">
        <div className="card__header" style={{ padding: 'var(--space-4) var(--space-4) 0' }}>
          <h2 className="card__title">Zestawienie kwartalne</h2>
        </div>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Kwartał</th>
                <th className="num">Przychód otrzymany</th>
                <th className="num">Koszty</th>
                <th className="num">Dochód</th>
                <th className="num">Przychód należny</th>
              </tr>
            </thead>
            <tbody>
              {data.quarterly.map((row) => (
                <tr key={row.label}>
                  <td data-label="Kwartał">{row.label}</td>
                  <td data-label="Przychód otrzymany" className="num">{formatMoney(row.received_gr)}</td>
                  <td data-label="Koszty" className="num">{formatMoney(row.costs_gr)}</td>
                  <td data-label="Dochód" className={row.income_gr < 0 ? 'num negative' : 'num'}>
                    {formatMoney(row.income_gr)}
                  </td>
                  <td data-label="Przychód należny" className="num">{formatMoney(row.accrued_gr)}</td>
                </tr>
              ))}
              <tr>
                <td data-label="Rok"><strong>Rok {data.year}</strong></td>
                <td data-label="Przychód otrzymany" className="num"><strong>{formatMoney(data.yearly.received_gr)}</strong></td>
                <td data-label="Koszty" className="num"><strong>{formatMoney(data.yearly.costs_gr)}</strong></td>
                <td data-label="Dochód" className="num"><strong>{formatMoney(data.yearly.income_gr)}</strong></td>
                <td data-label="Przychód należny" className="num"><strong>{formatMoney(data.yearly.accrued_gr)}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
