import { useEffect, useState } from 'react';
import type { ChangeEvent, ReactNode } from 'react';
import { formatAmount, parseAmountToGrosze } from '../utils/format';

/** Pole formularza z etykietą, podpowiedzią i komunikatem błędu. */
export function Field({
  label,
  hint,
  error,
  htmlFor,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  htmlFor?: string;
  children: ReactNode;
}) {
  return (
    <div className="field">
      <label className="field__label" htmlFor={htmlFor}>
        {label}
      </label>
      {children}
      {hint && !error ? <span className="field__hint">{hint}</span> : null}
      {error ? <span className="field__error">{error}</span> : null}
    </div>
  );
}

/**
 * Pole kwoty w złotych — do API zawsze trafiają grosze.
 * W trakcie pisania trzymamy surowy tekst, a sformatowaną wartość pokazujemy
 * dopiero po opuszczeniu pola, żeby edycja nie "walczyła" z formatowaniem.
 */
export function MoneyInput({
  id,
  valueGr,
  onChangeGr,
  required,
  disabled,
  allowNegative = false,
  ariaLabel,
}: {
  id?: string;
  valueGr: number;
  onChangeGr: (value: number) => void;
  required?: boolean;
  disabled?: boolean;
  allowNegative?: boolean;
  ariaLabel?: string;
}) {
  const [text, setText] = useState(() => formatAmount(valueGr));
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    if (!focused) setText(formatAmount(valueGr));
  }, [valueGr, focused]);

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const raw = event.target.value;
    setText(raw);
    if (raw.trim() === '' || raw.trim() === '-') {
      onChangeGr(0);
      return;
    }
    const parsed = parseAmountToGrosze(raw);
    if (parsed === null) return;
    if (!allowNegative && parsed < 0) return;
    onChangeGr(parsed);
  };

  return (
    <input
      id={id}
      type="text"
      inputMode="decimal"
      className="num"
      value={text}
      onFocus={() => {
        setFocused(true);
        setText(valueGr === 0 ? '' : formatAmount(valueGr).replace(/\s/g, ''));
      }}
      onBlur={() => {
        setFocused(false);
        setText(formatAmount(valueGr));
      }}
      onChange={handleChange}
      required={required}
      disabled={disabled}
      aria-label={ariaLabel ?? (id ? undefined : 'Kwota w złotych')}
    />
  );
}

export function Modal({
  title,
  onClose,
  children,
  wide,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className={wide ? 'modal modal--wide' : 'modal'}>
        <div className="modal__header">
          <h2 className="modal__title">{title}</h2>
          <button type="button" className="btn btn--ghost btn--sm" onClick={onClose} aria-label="Zamknij">
            ✕
          </button>
        </div>
        <div className="modal__body">{children}</div>
      </div>
    </div>
  );
}

export function Pagination({
  page,
  pages,
  total,
  onChange,
}: {
  page: number;
  pages: number;
  total: number;
  onChange: (page: number) => void;
}) {
  return (
    <div className="pagination">
      <span>
        Pozycji: <strong>{total}</strong>
        {pages > 1 ? ` · strona ${page} z ${pages}` : null}
      </span>
      <div className="btn-row">
        <button type="button" className="btn btn--sm" disabled={page <= 1} onClick={() => onChange(page - 1)}>
          Poprzednia
        </button>
        <button
          type="button"
          className="btn btn--sm"
          disabled={pages === 0 || page >= pages}
          onClick={() => onChange(page + 1)}
        >
          Następna
        </button>
      </div>
    </div>
  );
}

export function Badge({ children, variant }: { children: ReactNode; variant?: string }) {
  return <span className={variant ? `badge ${variant}` : 'badge'}>{children}</span>;
}

export function Alert({
  variant = 'info',
  title,
  children,
}: {
  variant?: 'info' | 'warning' | 'danger' | 'success';
  title?: string;
  children: ReactNode;
}) {
  return (
    <div className={`alert alert--${variant}`} role={variant === 'danger' ? 'alert' : undefined}>
      <div>
        {title ? <strong>{title}</strong> : null}
        {children}
      </div>
    </div>
  );
}

export function Loading({ label = 'Wczytywanie danych…' }: { label?: string }) {
  return <div className="skeleton">{label}</div>;
}

export function EmptyState({ label }: { label: string }) {
  return <div className="table-empty">{label}</div>;
}

export function ProgressBar({ percent, status }: { percent: number; status: string }) {
  const width = Math.max(0, Math.min(percent, 100));
  return (
    <div
      className="progress"
      role="progressbar"
      aria-valuenow={Math.round(percent)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className="progress__bar" data-status={status} style={{ width: `${width}%` }} />
    </div>
  );
}

export function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
}) {
  return (
    <div className="stat">
      <span className="stat__label">{label}</span>
      <span className="stat__value">{value}</span>
      {hint ? <span className="stat__hint">{hint}</span> : null}
    </div>
  );
}
