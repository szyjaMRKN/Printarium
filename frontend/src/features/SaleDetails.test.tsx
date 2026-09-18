import { describe, expect, it, vi } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SaleDetails } from './SaleDetails';
import { META_FIXTURE, renderWithProviders } from '../test/utils';
import type { Sale } from '../types';

vi.mock('../hooks/useMeta', () => ({
  useMeta: () => ({ data: META_FIXTURE, isLoading: false, error: null }),
}));

const SALE: Sale = {
  id: 1,
  document_number: 'SPR/2026/0001',
  sale_date: '2026-08-10',
  description: 'Formikarium x1',
  items_total_gr: 50000,
  discount_gr: 0,
  shipping_gr: 0,
  total_gr: 50000,
  corrections_total_gr: 0,
  accrued_revenue_gr: 50000,
  paid_amount_gr: 20000,
  outstanding_gr: 30000,
  payment_status: 'czesciowo_zaplacone',
  first_payment_date: '2026-08-12',
  last_payment_date: '2026-08-12',
  payment_method: 'przelew',
  sales_channel: 'allegro',
  customer_type: 'b2c',
  customer_name: 'Jan Nowak',
  customer_nip: null,
  customer_email: null,
  customer_phone: null,
  customer_address: null,
  notes: null,
  is_cancelled: false,
  created_at: '2026-08-10T10:00:00Z',
  updated_at: '2026-08-12T10:00:00Z',
  items: [
    {
      id: 1,
      product_id: null,
      position: 1,
      name: 'Formikarium',
      variant: null,
      quantity: 1,
      unit_price_gr: 50000,
      line_total_gr: 50000,
    },
  ],
  payments: [
    {
      id: 1,
      sale_id: 1,
      payment_date: '2026-08-12',
      amount_gr: 20000,
      method: 'przelew',
      description: null,
      correction_id: null,
      created_at: '2026-08-12T10:00:00Z',
    },
  ],
  corrections: [],
};

describe('Szczegóły sprzedaży', () => {
  it('pokazuje rozdzielony przychód należny i otrzymany', () => {
    renderWithProviders(
      <SaleDetails sale={SALE} busy={false} onAddPayment={vi.fn()} onDeletePayment={vi.fn()} onAddCorrection={vi.fn()} />,
    );

    expect(screen.getByText('Przychód należny')).toBeInTheDocument();
    expect(screen.getAllByText(/500,00\s?zł/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/200,00\s?zł/).length).toBeGreaterThan(0);
    expect(screen.getByText(/pozostało: .*300,00/)).toBeInTheDocument();
  });

  it('dodaje płatność z domyślną kwotą pozostałą do zapłaty', async () => {
    const onAddPayment = vi.fn();
    renderWithProviders(
      <SaleDetails sale={SALE} busy={false} onAddPayment={onAddPayment} onDeletePayment={vi.fn()} onAddCorrection={vi.fn()} />,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Dodaj płatność' }));
    fireEvent.change(screen.getByLabelText('Data otrzymania'), { target: { value: '2026-08-20' } });
    await userEvent.click(screen.getByRole('button', { name: 'Zapisz płatność' }));

    await waitFor(() => expect(onAddPayment).toHaveBeenCalled());
    expect(onAddPayment.mock.calls[0][0]).toMatchObject({
      amount_gr: 30000,
      payment_date: '2026-08-20',
      method: 'przelew',
    });
  });

  it('dodaje korektę zwrotu częściowego', async () => {
    const onAddCorrection = vi.fn();
    renderWithProviders(
      <SaleDetails sale={SALE} busy={false} onAddPayment={vi.fn()} onDeletePayment={vi.fn()} onAddCorrection={onAddCorrection} />,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Dodaj korektę' }));
    await userEvent.selectOptions(screen.getByLabelText('Rodzaj korekty'), 'zwrot_czesciowy');

    const amount = screen.getByLabelText('Kwota korekty (zł)');
    await userEvent.clear(amount);
    await userEvent.type(amount, '150');
    await userEvent.type(screen.getByLabelText('Powód'), 'Zwrot jednej sztuki');
    await userEvent.click(screen.getByRole('button', { name: 'Zapisz korektę' }));

    await waitFor(() => expect(onAddCorrection).toHaveBeenCalled());
    expect(onAddCorrection.mock.calls[0][0]).toMatchObject({
      correction_type: 'zwrot_czesciowy',
      amount_gr: 15000,
      reason: 'Zwrot jednej sztuki',
    });
  });
});
