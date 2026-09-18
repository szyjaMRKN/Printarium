import { describe, expect, it, vi } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SaleForm } from './SaleForm';
import { META_FIXTURE, renderWithProviders } from '../test/utils';

vi.mock('../hooks/useMeta', () => ({
  useMeta: () => ({ data: META_FIXTURE, isLoading: false, error: null }),
}));

vi.mock('../api/resources', () => ({
  productsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 1,
          name: 'Formikarium L',
          sku: 'FRM-L',
          model: 'L',
          category: null,
          price_gr: 25000,
          production_cost_gr: 9000,
          is_active: true,
          description: null,
          attributes: null,
          created_at: '',
          updated_at: '',
        },
      ],
      meta: { total: 1, page: 1, per_page: 200, pages: 1 },
    }),
  },
  metaApi: { options: vi.fn() },
}));

describe('Formularz sprzedaży', () => {
  it('przelicza wartość całkowitą i wysyła kwoty w groszach', async () => {
    const onSubmit = vi.fn();
    renderWithProviders(<SaleForm submitting={false} onCancel={() => {}} onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText('Nazwa pozycji 1'), 'Formikarium');
    fireEvent.change(screen.getByLabelText('Ilość pozycji 1'), { target: { value: '2' } });

    const unitPrice = screen.getByLabelText('Cena jednostkowa pozycji 1');
    await userEvent.clear(unitPrice);
    await userEvent.type(unitPrice, '250');

    const shipping = screen.getByLabelText('Koszt wysyłki pobrany od klienta (zł)');
    await userEvent.clear(shipping);
    await userEvent.type(shipping, '19,99');

    await waitFor(() =>
      expect((screen.getByLabelText('Wartość całkowita') as HTMLInputElement).value.replace(/ /g, ' ')).toBe(
        '519,99 zł',
      ),
    );

    await userEvent.click(screen.getByRole('button', { name: 'Dodaj sprzedaż' }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    const payload = onSubmit.mock.calls[0][0];
    expect(payload.items[0]).toMatchObject({ name: 'Formikarium', quantity: 2, unit_price_gr: 25000 });
    expect(payload.shipping_gr).toBe(1999);
    expect(payload.discount_gr).toBe(0);
  });

  it('nie pozwala zapisać sprzedaży bez pozycji', async () => {
    const onSubmit = vi.fn();
    renderWithProviders(<SaleForm submitting={false} onCancel={() => {}} onSubmit={onSubmit} />);

    const form = screen.getByRole('button', { name: 'Dodaj sprzedaż' }).closest('form') as HTMLFormElement;
    form.noValidate = true;
    await userEvent.click(screen.getByRole('button', { name: 'Dodaj sprzedaż' }));

    expect(await screen.findByText('Dodaj co najmniej jedną pozycję sprzedaży.')).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('wypełnia pozycję danymi produktu z bazy', async () => {
    const onSubmit = vi.fn();
    renderWithProviders(<SaleForm submitting={false} onCancel={() => {}} onSubmit={onSubmit} />);

    await screen.findByRole('option', { name: 'Formikarium L' });
    await userEvent.selectOptions(screen.getByLabelText('Produkt z bazy'), '1');

    await waitFor(() => expect((screen.getByLabelText('Nazwa pozycji 1') as HTMLInputElement).value).toBe('Formikarium L'));
    await userEvent.click(screen.getByRole('button', { name: 'Dodaj sprzedaż' }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    expect(onSubmit.mock.calls[0][0].items[0]).toMatchObject({ product_id: 1, unit_price_gr: 25000 });
  });
});
