import type { ReactElement, ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { render } from '@testing-library/react';
import { ThemeProvider } from '../hooks/useTheme';
import { ToastProvider } from '../hooks/useToast';
import { AuthProvider } from '../hooks/useAuth';
import type { MetaOptions } from '../types';

export function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <ToastProvider>
            <AuthProvider>
              <MemoryRouter>{children}</MemoryRouter>
            </AuthProvider>
          </ToastProvider>
        </ThemeProvider>
      </QueryClientProvider>
    );
  };
}

export function renderWithProviders(ui: ReactElement) {
  return render(ui, { wrapper: createWrapper() });
}

export const META_FIXTURE: MetaOptions = {
  app: { name: 'Ewidencja', version: '0.1.0' },
  payment_status: [
    { value: 'niezaplacone', label: 'niezapłacone' },
    { value: 'czesciowo_zaplacone', label: 'częściowo zapłacone' },
    { value: 'zaplacone', label: 'zapłacone' },
    { value: 'anulowane', label: 'anulowane' },
    { value: 'zwrocone', label: 'zwrócone' },
  ],
  payment_method: [
    { value: 'przelew', label: 'przelew' },
    { value: 'blik', label: 'BLIK' },
    { value: 'gotowka', label: 'gotówka' },
  ],
  sales_channel: [
    { value: 'sklep_internetowy', label: 'sklep internetowy' },
    { value: 'allegro', label: 'Allegro' },
  ],
  customer_type: [
    { value: 'b2c', label: 'B2C' },
    { value: 'b2b', label: 'B2B' },
  ],
  correction_type: [
    { value: 'zwrot_calkowity', label: 'zwrot całkowity' },
    { value: 'zwrot_czesciowy', label: 'zwrot częściowy' },
    { value: 'rabat_po_sprzedazy', label: 'rabat po sprzedaży' },
    { value: 'anulowanie', label: 'anulowanie zamówienia' },
    { value: 'korekta_wartosci', label: 'korekta wartości' },
    { value: 'zwrot_pieniedzy', label: 'zwrot pieniędzy klientowi' },
  ],
  document_type: [
    { value: 'rachunek', label: 'rachunek' },
    { value: 'faktura_bez_vat', label: 'faktura bez VAT' },
  ],
  ksef_status: [
    { value: 'nie_dotyczy', label: 'nie dotyczy' },
    { value: 'poza_ksef', label: 'dokument poza KSeF' },
    { value: 'przeslany', label: 'przesłany do KSeF' },
  ],
  user_role: [
    { value: 'admin', label: 'administrator' },
    { value: 'ksiegowy', label: 'księgowość' },
  ],
  reports: [{ value: 'sprzedaz_miesieczna', label: 'Sprzedaż miesięczna' }],
};
