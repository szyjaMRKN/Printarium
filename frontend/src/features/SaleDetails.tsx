import { useState } from 'react';
import type { FormEvent } from 'react';
import { Alert, Badge, Field, MoneyInput } from '../components/ui';
import { useMeta } from '../hooks/useMeta';
import { STATUS_BADGE, formatDate, formatMoney, optionLabel, todayIso } from '../utils/format';
import type { Sale } from '../types';

interface Props {
  sale: Sale;
  busy: boolean;
  onAddPayment: (payload: { payment_date: string; amount_gr: number; method: string; description: string | null }) => void;
  onDeletePayment: (paymentId: number) => void;
  onAddCorrection: (payload: {
    correction_date: string;
    correction_type: string;
    amount_gr?: number | null;
    new_value_gr?: number | null;
    refund_amount_gr: number;
    reason: string | null;
    description: string | null;
  }) => void;
}

const NEEDS_AMOUNT = ['zwrot_czesciowy', 'rabat_po_sprzedazy'];
const NEEDS_NEW_VALUE = ['korekta_wartosci'];

export function SaleDetails({ sale, busy, onAddPayment, onDeletePayment, onAddCorrection }: Props) {
  const { data: meta } = useMeta();
  const [tab, setTab] = useState<'przeglad' | 'platnosc' | 'korekta'>('przeglad');

  const [paymentAmountGr, setPaymentAmountGr] = useState(Math.max(sale.outstanding_gr, 0));
  const [paymentDate, setPaymentDate] = useState(todayIso());
  const [paymentMethod, setPaymentMethod] = useState(sale.payment_method ?? 'przelew');
  const [paymentDescription, setPaymentDescription] = useState('');

  const [correctionType, setCorrectionType] = useState('zwrot_czesciowy');
  const [correctionDate, setCorrectionDate] = useState(todayIso());
  const [correctionAmountGr, setCorrectionAmountGr] = useState(0);
  const [newValueGr, setNewValueGr] = useState(sale.accrued_revenue_gr);
  const [refundAmountGr, setRefundAmountGr] = useState(0);
  const [reason, setReason] = useState('');
  const [correctionDescription, setCorrectionDescription] = useState('');

  const submitPayment = (event: FormEvent) => {
    event.preventDefault();
    onAddPayment({
      payment_date: paymentDate,
      amount_gr: paymentAmountGr,
      method: paymentMethod,
      description: paymentDescription.trim() || null,
    });
  };

  const submitCorrection = (event: FormEvent) => {
    event.preventDefault();
    onAddCorrection({
      correction_date: correctionDate,
      correction_type: correctionType,
      amount_gr: NEEDS_AMOUNT.includes(correctionType) ? correctionAmountGr : null,
      new_value_gr: NEEDS_NEW_VALUE.includes(correctionType) ? newValueGr : null,
      refund_amount_gr: refundAmountGr,
      reason: reason.trim() || null,
      description: correctionDescription.trim() || null,
    });
  };

  return (
    <div className="stack">
      <div className="grid grid--stats">
        <div className="stat">
          <span className="stat__label">Wartość sprzedaży</span>
          <span className="stat__value">{formatMoney(sale.total_gr)}</span>
        </div>
        <div className="stat">
          <span className="stat__label">Przychód należny</span>
          <span className="stat__value">{formatMoney(sale.accrued_revenue_gr)}</span>
          <span className="stat__hint">korekty: {formatMoney(sale.corrections_total_gr)}</span>
        </div>
        <div className="stat">
          <span className="stat__label">Otrzymano</span>
          <span className="stat__value">{formatMoney(sale.paid_amount_gr)}</span>
          <span className="stat__hint">pozostało: {formatMoney(sale.outstanding_gr)}</span>
        </div>
        <div className="stat">
          <span className="stat__label">Status</span>
          <span className="stat__value">
            <Badge variant={STATUS_BADGE[sale.payment_status]}>
              {optionLabel(meta?.payment_status, sale.payment_status)}
            </Badge>
          </span>
          <span className="stat__hint">
            {sale.last_payment_date ? `ostatnia wpłata ${formatDate(sale.last_payment_date)}` : 'brak wpłat'}
          </span>
        </div>
      </div>

      <div className="tabs">
        <button type="button" className={tab === 'przeglad' ? 'tab is-active' : 'tab'} onClick={() => setTab('przeglad')}>
          Przegląd
        </button>
        <button
          type="button"
          className={tab === 'platnosc' ? 'tab is-active' : 'tab'}
          onClick={() => setTab('platnosc')}
          disabled={sale.is_cancelled}
        >
          Dodaj płatność
        </button>
        <button
          type="button"
          className={tab === 'korekta' ? 'tab is-active' : 'tab'}
          onClick={() => setTab('korekta')}
          disabled={sale.is_cancelled}
        >
          Dodaj korektę
        </button>
      </div>

      {tab === 'przeglad' ? (
        <div className="stack">
          <div>
            <h3>Pozycje</h3>
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>Nazwa</th>
                    <th>Wariant</th>
                    <th className="num">Ilość</th>
                    <th className="num">Cena</th>
                    <th className="num">Wartość</th>
                  </tr>
                </thead>
                <tbody>
                  {sale.items.map((item) => (
                    <tr key={item.id}>
                      <td data-label="Nazwa">{item.name}</td>
                      <td data-label="Wariant">{item.variant ?? '—'}</td>
                      <td data-label="Ilość" className="num">{item.quantity}</td>
                      <td data-label="Cena" className="num">{formatMoney(item.unit_price_gr)}</td>
                      <td data-label="Wartość" className="num">{formatMoney(item.line_total_gr)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h3>Płatności</h3>
            {sale.payments.length === 0 ? (
              <p className="muted small">Brak zarejestrowanych płatności.</p>
            ) : (
              <div className="table-wrap">
                <table className="data">
                  <thead>
                    <tr>
                      <th>Data</th>
                      <th className="num">Kwota</th>
                      <th>Metoda</th>
                      <th>Opis</th>
                      <th aria-label="Akcje" />
                    </tr>
                  </thead>
                  <tbody>
                    {sale.payments.map((payment) => (
                      <tr key={payment.id}>
                        <td data-label="Data">{formatDate(payment.payment_date)}</td>
                        <td data-label="Kwota" className={payment.amount_gr < 0 ? 'num negative' : 'num'}>
                          {formatMoney(payment.amount_gr)}
                        </td>
                        <td data-label="Metoda">{optionLabel(meta?.payment_method, payment.method)}</td>
                        <td data-label="Opis">{payment.description ?? '—'}</td>
                        <td data-label="">
                          <button
                            type="button"
                            className="btn btn--sm"
                            disabled={busy}
                            onClick={() => onDeletePayment(payment.id)}
                          >
                            Usuń
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div>
            <h3>Korekty</h3>
            {sale.corrections.length === 0 ? (
              <p className="muted small">Brak korekt — sprzedaż w wersji pierwotnej.</p>
            ) : (
              <div className="table-wrap">
                <table className="data">
                  <thead>
                    <tr>
                      <th>Data</th>
                      <th>Rodzaj</th>
                      <th className="num">Było</th>
                      <th className="num">Jest</th>
                      <th className="num">Kwota korekty</th>
                      <th>Powód</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sale.corrections.map((correction) => (
                      <tr key={correction.id}>
                        <td data-label="Data">{formatDate(correction.correction_date)}</td>
                        <td data-label="Rodzaj">{optionLabel(meta?.correction_type, correction.correction_type)}</td>
                        <td data-label="Było" className="num">{formatMoney(correction.previous_value_gr)}</td>
                        <td data-label="Jest" className="num">{formatMoney(correction.new_value_gr)}</td>
                        <td
                          data-label="Kwota korekty"
                          className={correction.amount_gr < 0 ? 'num negative' : 'num positive'}
                        >
                          {formatMoney(correction.amount_gr)}
                        </td>
                        <td data-label="Powód">{correction.reason ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {sale.notes ? (
            <div>
              <h3>Uwagi</h3>
              <p className="small">{sale.notes}</p>
            </div>
          ) : null}
        </div>
      ) : null}

      {tab === 'platnosc' ? (
        <form className="stack" onSubmit={submitPayment}>
          <div className="form-grid">
            <Field label="Kwota (zł)" htmlFor="pay_amount" hint="Ujemna kwota = zwrot pieniędzy">
              <MoneyInput id="pay_amount" valueGr={paymentAmountGr} onChangeGr={setPaymentAmountGr} allowNegative />
            </Field>
            <Field label="Data otrzymania" htmlFor="pay_date">
              <input
                id="pay_date"
                type="date"
                required
                value={paymentDate}
                onChange={(event) => setPaymentDate(event.target.value)}
              />
            </Field>
            <Field label="Metoda" htmlFor="pay_method">
              <select id="pay_method" value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)}>
                {meta?.payment_method.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Opis" htmlFor="pay_description">
              <input
                id="pay_description"
                value={paymentDescription}
                onChange={(event) => setPaymentDescription(event.target.value)}
              />
            </Field>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn--primary" disabled={busy || paymentAmountGr === 0}>
              Zapisz płatność
            </button>
          </div>
        </form>
      ) : null}

      {tab === 'korekta' ? (
        <form className="stack" onSubmit={submitCorrection}>
          <Alert variant="info">
            Korekta nie usuwa sprzedaży — zapisuje wartość poprzednią, nową i powód, a przychód należny jest
            przeliczany automatycznie.
          </Alert>
          <div className="form-grid">
            <Field label="Rodzaj korekty" htmlFor="correction_type">
              <select
                id="correction_type"
                value={correctionType}
                onChange={(event) => setCorrectionType(event.target.value)}
              >
                {meta?.correction_type.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Data korekty" htmlFor="correction_date">
              <input
                id="correction_date"
                type="date"
                required
                value={correctionDate}
                onChange={(event) => setCorrectionDate(event.target.value)}
              />
            </Field>
            {NEEDS_AMOUNT.includes(correctionType) ? (
              <Field label="Kwota korekty (zł)" htmlFor="correction_amount" hint="O tyle obniżymy przychód należny">
                <MoneyInput id="correction_amount" valueGr={correctionAmountGr} onChangeGr={setCorrectionAmountGr} />
              </Field>
            ) : null}
            {NEEDS_NEW_VALUE.includes(correctionType) ? (
              <Field label="Nowa wartość sprzedaży (zł)" htmlFor="correction_new_value">
                <MoneyInput id="correction_new_value" valueGr={newValueGr} onChangeGr={setNewValueGr} />
              </Field>
            ) : null}
            <Field
              label="Zwrot pieniędzy klientowi (zł)"
              htmlFor="refund_amount"
              hint={`Maksymalnie ${formatMoney(sale.paid_amount_gr)}`}
            >
              <MoneyInput id="refund_amount" valueGr={refundAmountGr} onChangeGr={setRefundAmountGr} />
            </Field>
            <Field label="Powód" htmlFor="correction_reason">
              <input id="correction_reason" value={reason} onChange={(event) => setReason(event.target.value)} />
            </Field>
          </div>
          <Field label="Opis" htmlFor="correction_description">
            <textarea
              id="correction_description"
              value={correctionDescription}
              onChange={(event) => setCorrectionDescription(event.target.value)}
            />
          </Field>
          <div className="form-actions">
            <button type="submit" className="btn btn--primary" disabled={busy}>
              Zapisz korektę
            </button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
