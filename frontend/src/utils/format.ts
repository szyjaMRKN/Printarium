/** Formatowanie kwot (grosze), dat (DD.MM.RRRR) i etykiet. */

const PLN = new Intl.NumberFormat('pl-PL', {
  style: 'currency',
  currency: 'PLN',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const NUMBER = new Intl.NumberFormat('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** Grosze -> "10 813,50 zł" */
export function formatMoney(grosze: number | null | undefined): string {
  return PLN.format((grosze ?? 0) / 100);
}

/** Grosze -> "10 813,50" (bez symbolu waluty, np. do pól formularza) */
export function formatAmount(grosze: number | null | undefined): string {
  return NUMBER.format((grosze ?? 0) / 100);
}

/** "1 234,56" / "1234.56" -> 123456 groszy. Zwraca null przy błędnym wejściu. */
export function parseAmountToGrosze(input: string): number | null {
  const normalized = input.replace(/\s/g, '').replace(',', '.');
  if (normalized === '') return null;
  if (!/^-?\d*(\.\d{0,2})?$/.test(normalized)) return null;
  const value = Number(normalized);
  if (Number.isNaN(value)) return null;
  return Math.round(value * 100);
}

export function formatPercent(value: number, fractionDigits = 1): string {
  return `${value.toFixed(fractionDigits).replace('.', ',')}%`;
}

/** ISO (RRRR-MM-DD) -> DD.MM.RRRR */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const [year, month, day] = iso.slice(0, 10).split('-');
  if (!year || !month || !day) return iso;
  return `${day}.${month}.${year}`;
}

/** Znacznik techniczny (UTC) -> data i godzina w strefie Europe/Warsaw */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—';
  const withZone = /[Zz]|[+-]\d{2}:?\d{2}$/.test(value) ? value : `${value}Z`;
  const date = new Date(withZone);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('pl-PL', {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'Europe/Warsaw',
  }).format(date);
}

export function todayIso(): string {
  const now = new Date();
  const local = new Date(now.toLocaleString('en-US', { timeZone: 'Europe/Warsaw' }));
  const month = `${local.getMonth() + 1}`.padStart(2, '0');
  const day = `${local.getDate()}`.padStart(2, '0');
  return `${local.getFullYear()}-${month}-${day}`;
}

export function currentYear(): number {
  return Number(todayIso().slice(0, 4));
}

export function currentQuarter(): number {
  return Math.floor(Number(todayIso().slice(5, 7)) / 3.0001) + 1;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1).replace('.', ',')} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1).replace('.', ',')} MB`;
}

export const STATUS_BADGE: Record<string, string> = {
  zaplacone: 'badge--success',
  czesciowo_zaplacone: 'badge--warning',
  niezaplacone: 'badge--danger',
  anulowane: 'badge',
  zwrocone: 'badge--info',
};

export const LIMIT_STATUS_LABEL: Record<string, string> = {
  normalny: 'W normie',
  ostrzezenie: 'Ostrzeżenie',
  mocne_ostrzezenie: 'Uwaga — blisko limitu',
  przekroczony: 'Limit przekroczony',
};

export const LIMIT_STATUS_BADGE: Record<string, string> = {
  normalny: 'badge--success',
  ostrzezenie: 'badge--warning',
  mocne_ostrzezenie: 'badge--warning',
  przekroczony: 'badge--danger',
};

export const MONTHS_PL = [
  'styczeń',
  'luty',
  'marzec',
  'kwiecień',
  'maj',
  'czerwiec',
  'lipiec',
  'sierpień',
  'wrzesień',
  'październik',
  'listopad',
  'grudzień',
];

export function optionLabel(options: { value: string; label: string }[] | undefined, value: string | null): string {
  if (!value) return '—';
  return options?.find((option) => option.value === value)?.label ?? value;
}
