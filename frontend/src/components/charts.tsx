/**
 * Wykresy pulpitu (Recharts).
 *
 * Zasady: jedna oś wartości, stałe przypisanie koloru do wielkości
 * (przychód należny = 1, przychód otrzymany = 2, koszty = 3), legenda przy
 * dwóch seriach i więcej, delikatna siatka, tooltip z kwotami w złotych.
 */

import type { ReactNode } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { formatMoney } from '../utils/format';

export const SERIES_COLORS = {
  accrued: 'var(--chart-1)',
  received: 'var(--chart-2)',
  costs: 'var(--chart-3)',
} as const;

const AXIS_STYLE = { fill: 'var(--chart-axis)', fontSize: 11 };
const AXIS_LINE = { stroke: 'var(--chart-grid)' };

function compactZl(value: number): string {
  const zl = value / 100;
  if (Math.abs(zl) >= 1000) return `${Math.round(zl / 1000)} tys.`;
  return `${Math.round(zl)}`;
}

interface TooltipPayloadItem {
  name?: string;
  value?: number | string;
  color?: string;
  dataKey?: string | number;
}

function MoneyTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string | number;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip__label">{label}</div>
      {payload.map((item) => (
        <div className="chart-tooltip__row" key={`${item.dataKey}`}>
          <span className="chart-legend__item">
            <span className="chart-legend__swatch" style={{ background: item.color }} />
            {item.name}
          </span>
          <strong>{formatMoney(Number(item.value ?? 0))}</strong>
        </div>
      ))}
    </div>
  );
}

export function ChartCard({
  title,
  subtitle,
  legend,
  children,
}: {
  title: string;
  subtitle?: string;
  legend?: Array<{ label: string; color: string }>;
  children: ReactNode;
}) {
  return (
    <section className="chart-card">
      <div className="chart-card__head">
        <h3 className="chart-card__title">{title}</h3>
        {subtitle ? <span className="chart-card__subtitle">{subtitle}</span> : null}
      </div>
      {legend && legend.length > 1 ? (
        <div className="chart-legend">
          {legend.map((item) => (
            <span className="chart-legend__item" key={item.label}>
              <span className="chart-legend__swatch" style={{ background: item.color }} />
              {item.label}
            </span>
          ))}
        </div>
      ) : null}
      {children}
    </section>
  );
}

export interface SeriesConfig {
  key: string;
  label: string;
  color: string;
}

/** Wykres liniowy — zmiana w czasie (np. ostatnie 30 dni). */
export function TrendChart({
  data,
  xKey,
  series,
  emptyLabel = 'Brak danych w tym okresie.',
}: {
  data: Array<Record<string, unknown>>;
  xKey: string;
  series: SeriesConfig[];
  emptyLabel?: string;
}) {
  const hasValues = data.some((row) => series.some((item) => Number(row[item.key] ?? 0) !== 0));
  if (!hasValues) return <div className="chart-empty">{emptyLabel}</div>;

  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
          <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
          <XAxis dataKey={xKey} tick={AXIS_STYLE} axisLine={AXIS_LINE} tickLine={false} minTickGap={24} />
          <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} width={52} tickFormatter={compactZl} />
          <Tooltip content={<MoneyTooltip />} cursor={{ stroke: 'var(--chart-axis)', strokeWidth: 1 }} />
          {series.map((item) => (
            <Line
              key={item.key}
              type="monotone"
              dataKey={item.key}
              name={item.label}
              stroke={item.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2, stroke: 'var(--chart-surface)' }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Wykres słupkowy — porównanie wielkości w okresach. */
export function BarsChart({
  data,
  xKey,
  series,
  emptyLabel = 'Brak danych w tym okresie.',
  height = 280,
}: {
  data: Array<Record<string, unknown>>;
  xKey: string;
  series: SeriesConfig[];
  emptyLabel?: string;
  height?: number;
}) {
  const hasValues = data.some((row) => series.some((item) => Number(row[item.key] ?? 0) !== 0));
  if (!hasValues) return <div className="chart-empty">{emptyLabel}</div>;

  return (
    <div className="chart-box" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }} barGap={2}>
          <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
          <XAxis dataKey={xKey} tick={AXIS_STYLE} axisLine={AXIS_LINE} tickLine={false} />
          <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} width={52} tickFormatter={compactZl} />
          <Tooltip content={<MoneyTooltip />} cursor={{ fill: 'var(--c-surface-2)' }} />
          {series.map((item) => (
            <Bar
              key={item.key}
              dataKey={item.key}
              name={item.label}
              fill={item.color}
              radius={[4, 4, 0, 0]}
              maxBarSize={38}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Poziome słupki dla podziału kategorialnego (kanały, produkty).
 * Jedna wielkość = jeden kolor; etykiety wartości są widoczne wprost,
 * więc identyfikacja nie opiera się wyłącznie na kolorze.
 */
export function RankedBars({
  data,
  labelKey,
  valueKey,
  emptyLabel = 'Brak danych w tym okresie.',
  color = 'var(--chart-1)',
}: {
  data: Array<Record<string, unknown>>;
  labelKey: string;
  valueKey: string;
  emptyLabel?: string;
  color?: string;
}) {
  const rows = data.filter((row) => Number(row[valueKey] ?? 0) > 0);
  if (rows.length === 0) return <div className="chart-empty">{emptyLabel}</div>;
  const max = Math.max(...rows.map((row) => Number(row[valueKey] ?? 0)));

  return (
    <div className="ranked-bars">
      {rows.map((row) => {
        const value = Number(row[valueKey] ?? 0);
        return (
          <div className="ranked-bars__row" key={String(row[labelKey])}>
            <span className="ranked-bars__label" title={String(row[labelKey])}>
              {String(row[labelKey])}
            </span>
            <span className="ranked-bars__track">
              <span
                className="ranked-bars__fill"
                style={{ width: `${Math.max((value / max) * 100, 2)}%`, background: color }}
              />
            </span>
            <span className="ranked-bars__value num">{formatMoney(value)}</span>
          </div>
        );
      })}
    </div>
  );
}

/** Pomocniczy wykres słupkowy z kolorem zależnym od statusu (limity kwartalne). */
export function QuarterLimitChart({
  data,
}: {
  data: Array<{ label: string; accrued_gr: number; limit_gr: number; status: string }>;
}) {
  const statusColor: Record<string, string> = {
    normalny: 'var(--c-success)',
    ostrzezenie: 'var(--c-warning)',
    mocne_ostrzezenie: '#e06c00',
    przekroczony: 'var(--c-danger)',
  };
  return (
    <div className="chart-box" style={{ height: 240 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
          <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
          <XAxis dataKey="label" tick={AXIS_STYLE} axisLine={AXIS_LINE} tickLine={false} />
          <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} width={52} tickFormatter={compactZl} />
          <Tooltip content={<MoneyTooltip />} cursor={{ fill: 'var(--c-surface-2)' }} />
          <Bar dataKey="accrued_gr" name="Przychód należny" radius={[4, 4, 0, 0]} maxBarSize={56}>
            {data.map((row) => (
              <Cell key={row.label} fill={statusColor[row.status] ?? 'var(--chart-1)'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
