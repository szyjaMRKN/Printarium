import { useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { productsApi } from '../api/resources';
import { Alert, Field, MoneyInput } from '../components/ui';
import { useMeta } from '../hooks/useMeta';
import { formatMoney, todayIso } from '../utils/format';
import type { Sale, SaleInput, SaleItemInput } from '../types';

interface Props {
  sale?: Sale | null;
  submitting: boolean;
  onCancel: () => void;
  onSubmit: (payload: SaleInput) => void;
}

function emptyItem(): SaleItemInput {
  return { product_id: null, name: '', variant: null, quantity: 1, unit_price_gr: 0 };
}

export function SaleForm({ sale, submitting, onCancel, onSubmit }: Props) {
  const { data: meta } = useMeta();
  const { data: products } = useQuery({
    queryKey: ['products', 'active'],
    queryFn: () => productsApi.list({ only_active: true, per_page: 200 }),
  });

  const [documentNumber, setDocumentNumber] = useState(sale?.document_number ?? '');
  const [saleDate, setSaleDate] = useState(sale?.sale_date ?? todayIso());
  const [description, setDescription] = useState(sale?.description ?? '');
  const [items, setItems] = useState<SaleItemInput[]>(
    sale?.items.map((item) => ({
      product_id: item.product_id,
      name: item.name,
      variant: item.variant,
      quantity: item.quantity,
      unit_price_gr: item.unit_price_gr,
    })) ?? [emptyItem()],
  );
  const [discountGr, setDiscountGr] = useState(sale?.discount_gr ?? 0);
  const [shippingGr, setShippingGr] = useState(sale?.shipping_gr ?? 0);
  const [paymentMethod, setPaymentMethod] = useState(sale?.payment_method ?? 'przelew');
  const [salesChannel, setSalesChannel] = useState(sale?.sales_channel ?? 'sklep_internetowy');
  const [customerType, setCustomerType] = useState(sale?.customer_type ?? 'b2c');
  const [customerName, setCustomerName] = useState(sale?.customer_name ?? '');
  const [customerNip, setCustomerNip] = useState(sale?.customer_nip ?? '');
  const [customerEmail, setCustomerEmail] = useState(sale?.customer_email ?? '');
  const [customerPhone, setCustomerPhone] = useState(sale?.customer_phone ?? '');
  const [customerAddress, setCustomerAddress] = useState(sale?.customer_address ?? '');
  const [notes, setNotes] = useState(sale?.notes ?? '');
  const [withPayment, setWithPayment] = useState(false);
  const [paymentAmountGr, setPaymentAmountGr] = useState(0);
  const [paymentDate, setPaymentDate] = useState(todayIso());
  const [error, setError] = useState<string | null>(null);

  const itemsTotalGr = useMemo(
    () => items.reduce((sum, item) => sum + item.quantity * item.unit_price_gr, 0),
    [items],
  );
  const totalGr = itemsTotalGr - discountGr + shippingGr;

  const updateItem = (index: number, patch: Partial<SaleItemInput>) => {
    setItems((current) => current.map((item, position) => (position === index ? { ...item, ...patch } : item)));
  };

  const pickProduct = (index: number, productId: string) => {
    if (!productId) {
      updateItem(index, { product_id: null });
      return;
    }
    const product = products?.items.find((item) => item.id === Number(productId));
    if (!product) return;
    updateItem(index, {
      product_id: product.id,
      name: product.name,
      variant: product.model,
      unit_price_gr: product.price_gr,
    });
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    const cleaned = items.filter((item) => item.name.trim() !== '');
    if (cleaned.length === 0) {
      setError('Dodaj co najmniej jedną pozycję sprzedaży.');
      return;
    }
    if (cleaned.some((item) => item.quantity < 1)) {
      setError('Ilość każdej pozycji musi wynosić co najmniej 1.');
      return;
    }
    if (discountGr > itemsTotalGr) {
      setError('Rabat nie może być większy niż wartość produktów.');
      return;
    }
    if (withPayment && paymentAmountGr <= 0) {
      setError('Podaj kwotę otrzymanej płatności lub odznacz opcję.');
      return;
    }
    if (withPayment && paymentAmountGr > totalGr) {
      setError('Kwota płatności nie może przekraczać wartości sprzedaży.');
      return;
    }

    onSubmit({
      document_number: documentNumber.trim() || null,
      sale_date: saleDate,
      description: description.trim() || null,
      items: cleaned.map((item) => ({ ...item, variant: item.variant?.trim() || null })),
      discount_gr: discountGr,
      shipping_gr: shippingGr,
      payment_method: paymentMethod || null,
      sales_channel: salesChannel || null,
      customer_type: customerType,
      customer_name: customerName.trim() || null,
      customer_nip: customerNip.trim() || null,
      customer_email: customerEmail.trim() || null,
      customer_phone: customerPhone.trim() || null,
      customer_address: customerAddress.trim() || null,
      notes: notes.trim() || null,
      initial_payment:
        withPayment && !sale
          ? { amount_gr: paymentAmountGr, payment_date: paymentDate, method: paymentMethod || 'przelew' }
          : null,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="stack">
      {error ? <Alert variant="danger">{error}</Alert> : null}

      <div className="form-grid">
        <Field label="Data sprzedaży" htmlFor="sale_date" hint="Decyduje o kwartale limitu">
          <input
            id="sale_date"
            type="date"
            required
            value={saleDate}
            onChange={(event) => setSaleDate(event.target.value)}
          />
        </Field>
        <Field label="Numer dokumentu / zamówienia" htmlFor="document_number" hint="Puste = numer nadany automatycznie">
          <input
            id="document_number"
            value={documentNumber}
            onChange={(event) => setDocumentNumber(event.target.value)}
          />
        </Field>
        <Field label="Kanał sprzedaży" htmlFor="sales_channel">
          <select id="sales_channel" value={salesChannel} onChange={(event) => setSalesChannel(event.target.value)}>
            {meta?.sales_channel.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Metoda płatności" htmlFor="payment_method">
          <select id="payment_method" value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)}>
            {meta?.payment_method.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Typ klienta" htmlFor="customer_type">
          <select id="customer_type" value={customerType} onChange={(event) => setCustomerType(event.target.value)}>
            {meta?.customer_type.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Opis (opcjonalny)" htmlFor="description" hint="Puste = opis z pozycji">
          <input id="description" value={description} onChange={(event) => setDescription(event.target.value)} />
        </Field>
      </div>

      <div className="card card--flush">
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Produkt z bazy</th>
                <th>Nazwa</th>
                <th>Wariant / model</th>
                <th className="num">Ilość</th>
                <th className="num">Cena jedn. (zł)</th>
                <th className="num">Wartość</th>
                <th aria-label="Akcje" />
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={index}>
                  <td data-label="Produkt z bazy">
                    <select
                      value={item.product_id ?? ''}
                      onChange={(event) => pickProduct(index, event.target.value)}
                      aria-label="Produkt z bazy"
                    >
                      <option value="">— wpisz ręcznie —</option>
                      {products?.items.map((product) => (
                        <option key={product.id} value={product.id}>
                          {product.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td data-label="Nazwa">
                    <input
                      value={item.name}
                      onChange={(event) => updateItem(index, { name: event.target.value })}
                      aria-label={`Nazwa pozycji ${index + 1}`}
                      required
                    />
                  </td>
                  <td data-label="Wariant">
                    <input
                      value={item.variant ?? ''}
                      onChange={(event) => updateItem(index, { variant: event.target.value })}
                      aria-label={`Wariant pozycji ${index + 1}`}
                    />
                  </td>
                  <td data-label="Ilość" className="num">
                    <input
                      type="number"
                      min={1}
                      step={1}
                      value={item.quantity}
                      onChange={(event) => updateItem(index, { quantity: Number(event.target.value) || 1 })}
                      aria-label={`Ilość pozycji ${index + 1}`}
                    />
                  </td>
                  <td data-label="Cena jednostkowa" className="num">
                    <MoneyInput
                      valueGr={item.unit_price_gr}
                      onChangeGr={(value) => updateItem(index, { unit_price_gr: value })}
                      ariaLabel={`Cena jednostkowa pozycji ${index + 1}`}
                    />
                  </td>
                  <td data-label="Wartość" className="num">
                    {formatMoney(item.quantity * item.unit_price_gr)}
                  </td>
                  <td data-label="">
                    <button
                      type="button"
                      className="btn btn--sm"
                      onClick={() => setItems((current) => current.filter((_, position) => position !== index))}
                      disabled={items.length === 1}
                      aria-label={`Usuń pozycję ${index + 1}`}
                    >
                      Usuń
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="pagination">
          <button type="button" className="btn btn--sm" onClick={() => setItems((current) => [...current, emptyItem()])}>
            + Dodaj pozycję
          </button>
          <span>
            Wartość produktów: <strong>{formatMoney(itemsTotalGr)}</strong>
          </span>
        </div>
      </div>

      <div className="form-grid">
        <Field label="Rabat (zł)" htmlFor="discount">
          <MoneyInput id="discount" valueGr={discountGr} onChangeGr={setDiscountGr} />
        </Field>
        <Field label="Koszt wysyłki pobrany od klienta (zł)" htmlFor="shipping">
          <MoneyInput id="shipping" valueGr={shippingGr} onChangeGr={setShippingGr} />
        </Field>
        <Field label="Wartość całkowita" htmlFor="total">
          <input id="total" value={formatMoney(totalGr)} readOnly className="num" />
        </Field>
      </div>

      {!sale ? (
        <div className="card">
          <label className="checkbox">
            <input type="checkbox" checked={withPayment} onChange={(event) => setWithPayment(event.target.checked)} />
            Klient już zapłacił — dodaj płatność razem ze sprzedażą
          </label>
          {withPayment ? (
            <div className="form-grid" style={{ marginTop: 'var(--space-3)' }}>
              <Field label="Kwota otrzymana (zł)" htmlFor="payment_amount">
                <MoneyInput id="payment_amount" valueGr={paymentAmountGr} onChangeGr={setPaymentAmountGr} />
              </Field>
              <Field label="Data otrzymania płatności" htmlFor="payment_date">
                <input
                  id="payment_date"
                  type="date"
                  value={paymentDate}
                  onChange={(event) => setPaymentDate(event.target.value)}
                />
              </Field>
              <div className="field">
                <span className="field__label">&nbsp;</span>
                <button type="button" className="btn" onClick={() => setPaymentAmountGr(totalGr)}>
                  Wpisz pełną kwotę
                </button>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      <details>
        <summary style={{ cursor: 'pointer', marginBottom: 'var(--space-3)' }}>Dane klienta i uwagi</summary>
        <div className="form-grid">
          <Field label="Nazwa / imię i nazwisko" htmlFor="customer_name">
            <input id="customer_name" value={customerName} onChange={(event) => setCustomerName(event.target.value)} />
          </Field>
          <Field label="NIP" htmlFor="customer_nip">
            <input id="customer_nip" value={customerNip} onChange={(event) => setCustomerNip(event.target.value)} />
          </Field>
          <Field label="E-mail" htmlFor="customer_email">
            <input
              id="customer_email"
              type="email"
              value={customerEmail}
              onChange={(event) => setCustomerEmail(event.target.value)}
            />
          </Field>
          <Field label="Telefon" htmlFor="customer_phone">
            <input id="customer_phone" value={customerPhone} onChange={(event) => setCustomerPhone(event.target.value)} />
          </Field>
        </div>
        <div className="form-grid form-grid--wide" style={{ marginTop: 'var(--space-3)' }}>
          <Field label="Adres" htmlFor="customer_address">
            <textarea
              id="customer_address"
              value={customerAddress}
              onChange={(event) => setCustomerAddress(event.target.value)}
            />
          </Field>
          <Field label="Uwagi" htmlFor="notes">
            <textarea id="notes" value={notes} onChange={(event) => setNotes(event.target.value)} />
          </Field>
        </div>
      </details>

      <div className="form-actions">
        <button type="button" className="btn" onClick={onCancel}>
          Anuluj
        </button>
        <button type="submit" className="btn btn--primary" disabled={submitting}>
          {submitting ? 'Zapisywanie…' : sale ? 'Zapisz zmiany' : 'Dodaj sprzedaż'}
        </button>
      </div>
    </form>
  );
}
