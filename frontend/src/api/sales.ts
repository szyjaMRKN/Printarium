import { api } from './client';
import type {
  DailyRegistryRow,
  Page,
  RegistryResponse,
  Sale,
  SaleInput,
  SaleListItem,
} from '../types';

export interface SaleQuery {
  date_from?: string;
  date_to?: string;
  day?: string;
  year?: number;
  quarter?: number;
  month?: number;
  product_id?: number;
  product?: string;
  sales_channel?: string;
  payment_method?: string;
  payment_status?: string;
  customer_type?: string;
  search?: string;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
}

export const salesApi = {
  list: (query: SaleQuery) => api.get<Page<SaleListItem>>('/api/sales', query as Record<string, unknown>),
  get: (id: number) => api.get<Sale>(`/api/sales/${id}`),
  create: (payload: SaleInput) => api.post<Sale>('/api/sales', payload),
  update: (id: number, payload: SaleInput) => api.put<Sale>(`/api/sales/${id}`, payload),
  remove: (id: number, reason?: string) =>
    api.delete<{ message: string }>(`/api/sales/${id}`, reason ? { reason } : undefined),
  restore: (id: number) => api.post<Sale>(`/api/sales/${id}/restore`),
  addPayment: (
    id: number,
    payload: { payment_date: string; amount_gr: number; method: string; description?: string | null },
  ) => api.post<Sale>(`/api/sales/${id}/payments`, payload),
  deletePayment: (paymentId: number) => api.delete<{ message: string }>(`/api/payments/${paymentId}`),
  addCorrection: (
    id: number,
    payload: {
      correction_date: string;
      correction_type: string;
      amount_gr?: number | null;
      new_value_gr?: number | null;
      refund_amount_gr?: number;
      refund_method?: string | null;
      reason?: string | null;
      description?: string | null;
    },
  ) => api.post<Sale>(`/api/sales/${id}/corrections`, payload),
  registry: (query: SaleQuery) =>
    api.get<RegistryResponse>('/api/registry', query as Record<string, unknown>),
  registryDaily: (query: SaleQuery) =>
    api.get<DailyRegistryRow[]>('/api/registry/daily', query as Record<string, unknown>),
};
