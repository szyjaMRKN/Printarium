import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { reportsApi } from '../api/resources';
import { downloadFile } from '../api/client';
import { Alert, EmptyState, Field, Loading } from '../components/ui';
import { useMeta } from '../hooks/useMeta';
import { useToast } from '../hooks/useToast';
import { currentYear, formatDate, formatMoney, optionLabel } from '../utils/format';
import type { ReportColumn } from '../types';

function renderCell(value: unknown, column: ReportColumn, meta: ReturnType<typeof useMeta>['data']): string {
  if (column.type === 'money') return formatMoney(Number(value ?? 0));
  if (column.type === 'date') return formatDate(String(value ?? ''));
  if (column.type === 'int') return String(value ?? 0);
  if (value === null || value === undefined || value === '') return '—';
  const text = String(value);
  const dictionaries = [
    meta?.payment_status,
    meta?.payment_method,
    meta?.sales_channel,
    meta?.customer_type,
  ];
  for (const dictionary of dictionaries) {
    const match = dictionary?.find((option) => option.value === text);
    if (match) return match.label;
  }
  return text;
}

export function ReportsPage() {
  const { data: meta } = useMeta();
  const toast = useToast();
  const [reportKey, setReportKey] = useState('sprzedaz_miesieczna');
  const [year, setYear] = useState(currentYear());
  const [quarter, setQuarter] = useState<number | ''>('');
  const [month, setMonth] = useState<number | ''>('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const params = {
    year,
    quarter: quarter || undefined,
    month: month || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  };

  const report = useQuery({
    queryKey: ['report', reportKey, params],
    queryFn: () => reportsApi.get(reportKey, params),
  });

  const exportReport = async (format: 'csv' | 'xlsx' | 'pdf') => {
    try {
      await downloadFile(`/api/reports/${reportKey}/export`, { ...params, format });
    } catch (error) {
      toast.error(error);
    }
  };

  return (
    <>
      <div className="page__header">
        <div>
          <h1>Raporty</h1>
          <p>Zestawienia generowane przez serwer. Eksport do CSV, XLSX i PDF.</p>
        </div>
        <div className="btn-row">
          <button type="button" className="btn" onClick={() => void exportReport('csv')}>
            CSV
          </button>
          <button type="button" className="btn" onClick={() => void exportReport('xlsx')}>
            XLSX
          </button>
          <button type="button" className="btn" onClick={() => void exportReport('pdf')}>
            PDF
          </button>
        </div>
      </div>

      <section className="card">
        <div className="filters">
          <Field label="Raport" htmlFor="rp_key">
            <select id="rp_key" value={reportKey} onChange={(event) => setReportKey(event.target.value)}>
              {meta?.reports.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Rok" htmlFor="rp_year">
            <input id="rp_year" type="number" value={year} onChange={(event) => setYear(Number(event.target.value) || currentYear())} />
          </Field>
          <Field label="Kwartał" htmlFor="rp_quarter">
            <select id="rp_quarter" value={quarter} onChange={(event) => { setQuarter(event.target.value ? Number(event.target.value) : ''); setMonth(''); }}>
              <option value="">cały rok</option>
              <option value="1">I kwartał</option>
              <option value="2">II kwartał</option>
              <option value="3">III kwartał</option>
              <option value="4">IV kwartał</option>
            </select>
          </Field>
          <Field label="Miesiąc" htmlFor="rp_month">
            <select id="rp_month" value={month} onChange={(event) => { setMonth(event.target.value ? Number(event.target.value) : ''); setQuarter(''); }}>
              <option value="">wszystkie</option>
              {Array.from({ length: 12 }, (_, index) => index + 1).map((value) => (
                <option key={value} value={value}>
                  {String(value).padStart(2, '0')}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Data od" htmlFor="rp_from" hint="Nadpisuje rok/kwartał">
            <input id="rp_from" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          </Field>
          <Field label="Data do" htmlFor="rp_to">
            <input id="rp_to" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </Field>
        </div>
      </section>

      <section className="card card--flush">
        {report.isLoading ? (
          <Loading />
        ) : report.error ? (
          <Alert variant="danger">Nie udało się wygenerować raportu.</Alert>
        ) : report.data && report.data.rows.length === 0 ? (
          <EmptyState label="Brak danych dla wybranego raportu i okresu." />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <caption className="visually-hidden">{report.data?.title}</caption>
              <thead>
                <tr>
                  {report.data?.columns.map((column) => (
                    <th key={column.key} className={column.type === 'money' || column.type === 'int' ? 'num' : undefined}>
                      {column.title}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {report.data?.rows.map((row, index) => (
                  <tr key={index}>
                    {report.data?.columns.map((column) => (
                      <td
                        key={column.key}
                        data-label={column.title}
                        className={column.type === 'money' || column.type === 'int' ? 'num' : undefined}
                      >
                        {renderCell(row[column.key], column, meta)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {report.data && Object.keys(report.data.summary).length > 0 ? (
          <div className="pagination">
            {Object.entries(report.data.summary).map(([key, value]) => (
              <span key={key}>
                Razem — {optionLabel(report.data?.columns.map((c) => ({ value: c.key, label: c.title })), key)}:{' '}
                <strong>{formatMoney(value)}</strong>
              </span>
            ))}
          </div>
        ) : null}
      </section>
    </>
  );
}
