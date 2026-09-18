import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { DashboardPage } from './DashboardPage';
import { META_FIXTURE, renderWithProviders } from '../test/utils';
import type { DashboardData } from '../types';

vi.mock('../hooks/useMeta', () => ({
  useMeta: () => ({ data: META_FIXTURE, isLoading: false, error: null }),
}));

const dashboardMock = vi.fn();

vi.mock('../api/resources', () => ({
  dashboardApi: {
    get: () => dashboardMock(),
    limits: vi.fn(),
    pit: vi.fn(),
  },
  metaApi: { options: vi.fn() },
}));

function buildData(overrides: Partial<DashboardData['limit']> = {}): DashboardData {
  return {
    today: '2026-08-15',
    year: 2026,
    quarter: 3,
    limit: {
      year: 2026,
      quarter: 3,
      label: 'III kwartał',
      date_from: '2026-07-01',
      date_to: '2026-09-30',
      accrued_revenue_gr: 785000,
      limit_gr: 1081350,
      usage_percent: 72.59,
      remaining_gr: 296350,
      status: 'normalny',
      message: null,
      sales_count: 12,
      exceedance: null,
      ...overrides,
    },
    metrics: {
      accrued_today_gr: 25000,
      accrued_month_gr: 300000,
      accrued_quarter_gr: 785000,
      accrued_year_gr: 1200000,
      received_month_gr: 250000,
      received_quarter_gr: 700000,
      received_year_gr: 1100000,
      outstanding_gr: 85000,
      costs_month_gr: 40000,
      costs_year_gr: 300000,
      income_year_gr: 800000,
      income_month_gr: 210000,
      orders_today: 1,
      orders_month: 8,
      orders_year: 30,
      average_order_month_gr: 37500,
      average_order_year_gr: 40000,
    },
    charts: {
      last_30_days: [{ day: '2026-08-15', accrued_gr: 25000, received_gr: 25000 }],
      monthly: [
        {
          year: 2026,
          month: 8,
          label: 'sierpień',
          accrued_gr: 300000,
          received_gr: 250000,
          costs_gr: 40000,
          income_gr: 210000,
          sales_count: 8,
        },
      ],
      by_channel: [{ channel: 'allegro', accrued_gr: 500000, sales_count: 10 }],
      by_product: [{ product_id: 1, name: 'Formikarium', value_gr: 400000, quantity: 16 }],
      by_customer_type: [{ customer_type: 'b2c', accrued_gr: 900000, sales_count: 25 }],
      costs_by_category: [{ category: 'Materiały', amount_gr: 200000, count: 5 }],
    },
    counters: {
      ksef: {
        label: 'Sprzedaż udokumentowana fakturami (KSeF)',
        period_label: '08.2026',
        value_gr: 100000,
        threshold_gr: 1000000,
        usage_percent: 10,
        status: 'normalny',
        message: null,
      },
      cash_register: {
        label: 'Sprzedaż B2C (kasa fiskalna)',
        period_label: '2026',
        value_gr: 900000,
        threshold_gr: 2000000,
        usage_percent: 45,
        status: 'normalny',
        message: null,
      },
    },
  };
}

describe('Pulpit', () => {
  it('pokazuje wykorzystanie limitu kwartalnego', async () => {
    dashboardMock.mockResolvedValue(buildData());
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText('Przychód należny — bieżący kwartał')).toBeInTheDocument();
    expect(screen.getAllByText(/7\s?850,00\s?zł/).length).toBeGreaterThan(0);
    expect(screen.getByText(/10\s?813,50\s?zł/)).toBeInTheDocument();
    expect(screen.getByText('72,6%')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '73');
    expect(screen.getByText('W normie')).toBeInTheDocument();
  });

  it('ostrzega po przekroczeniu limitu i wskazuje sprzedaż', async () => {
    dashboardMock.mockResolvedValue(
      buildData({
        accrued_revenue_gr: 1100000,
        usage_percent: 101.72,
        remaining_gr: 0,
        status: 'przekroczony',
        message:
          'PRZEKROCZONO LIMIT DZIAŁALNOŚCI NIEREJESTROWANEJ. Sprawdź obowiązek rejestracji działalności w CEIDG. Termin na rejestrację wynosi co do zasady 7 dni od dnia przekroczenia limitu.',
        exceedance: {
          exceeded_on: '2026-08-15',
          sale_id: 7,
          sale_document_number: 'SPR/2026/0007',
          exceeded_by_gr: 18650,
          cumulative_gr: 1100000,
        },
      }),
    );
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText(/PRZEKROCZONO LIMIT DZIAŁALNOŚCI NIEREJESTROWANEJ/)).toBeInTheDocument();
    expect(screen.getByText(/CEIDG/)).toBeInTheDocument();
    expect(screen.getByText('SPR/2026/0007')).toBeInTheDocument();
    expect(screen.getByText('Limit przekroczony')).toBeInTheDocument();
  });

  it('pokazuje kluczowe wskaźniki finansowe', async () => {
    dashboardMock.mockResolvedValue(buildData());
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText('Niezapłacone należności')).toBeInTheDocument();
    expect(screen.getByText('Koszty — rok')).toBeInTheDocument();
    expect(screen.getByText('Szacowany dochód — rok')).toBeInTheDocument();
    expect(screen.getByText('Średnia wartość zamówienia')).toBeInTheDocument();
  });
});
