import { describe, expect, it, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CostsPage } from './CostsPage';
import { META_FIXTURE, renderWithProviders } from '../test/utils';

vi.mock('../hooks/useMeta', () => ({
  useMeta: () => ({ data: META_FIXTURE, isLoading: false, error: null }),
}));

const createCost = vi.fn();

vi.mock('../api/resources', () => ({
  costsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 1,
          cost_date: '2026-08-02',
          name: 'Folia bąbelkowa',
          category_id: 1,
          category_name: 'Opakowania',
          vendor: 'Hurtownia',
          invoice_number: 'FV 1/2026',
          amount_gr: 12300,
          payment_method: 'przelew',
          description: null,
          attachment_id: null,
          attachment_name: null,
          created_at: '',
          updated_at: '',
        },
      ],
      meta: { total: 1, page: 1, per_page: 25, pages: 1 },
    }),
    create: (payload: unknown) => createCost(payload),
    update: vi.fn(),
    remove: vi.fn(),
    categories: vi.fn().mockResolvedValue([
      { id: 1, name: 'Opakowania', slug: 'opakowania', is_active: true, sort_order: 10 },
      { id: 2, name: 'Materiały', slug: 'materialy', is_active: true, sort_order: 20 },
    ]),
    createCategory: vi.fn(),
    updateCategory: vi.fn(),
    removeCategory: vi.fn(),
    uploadAttachment: vi.fn(),
  },
  metaApi: { options: vi.fn() },
}));

describe('Koszty', () => {
  it('pokazuje listę kosztów z kwotami', async () => {
    renderWithProviders(<CostsPage />);
    expect(await screen.findByText('Folia bąbelkowa')).toBeInTheDocument();
    expect(screen.getAllByText('Opakowania').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/123,00\s?zł/).length).toBeGreaterThan(0);
  });

  it('dodaje koszt z kwotą przeliczoną na grosze', async () => {
    createCost.mockResolvedValue({ id: 2 });
    renderWithProviders(<CostsPage />);

    await userEvent.click(screen.getByRole('button', { name: '+ Dodaj koszt' }));
    const dialog = await screen.findByRole('dialog');

    await userEvent.type(within(dialog).getByLabelText('Nazwa / rodzaj kosztu'), 'Beton szybkosprawny');
    const amount = within(dialog).getByLabelText('Kwota (zł)');
    await userEvent.clear(amount);
    await userEvent.type(amount, '89,90');
    await userEvent.selectOptions(within(dialog).getByLabelText('Kategoria'), '2');
    await userEvent.click(within(dialog).getByRole('button', { name: 'Zapisz koszt' }));

    await waitFor(() => expect(createCost).toHaveBeenCalled());
    expect(createCost.mock.calls[0][0]).toMatchObject({
      name: 'Beton szybkosprawny',
      amount_gr: 8990,
      category_id: 2,
    });
  });
});
