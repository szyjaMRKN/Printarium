import { api } from './client';
import type {
  AuditLogEntry,
  Attachment,
  BackupFile,
  Cost,
  CostCategory,
  DashboardData,
  FiscalYear,
  LimitsResponse,
  MetaOptions,
  Page,
  PitSummary,
  Product,
  ReportResponse,
  SalesDocument,
  SettingsValues,
} from '../types';

export const metaApi = {
  options: () => api.get<MetaOptions>('/api/meta/options'),
};

export const dashboardApi = {
  get: () => api.get<DashboardData>('/api/dashboard'),
  limits: (year?: number) => api.get<LimitsResponse>('/api/limits', year ? { year } : undefined),
  pit: (year?: number) => api.get<PitSummary>('/api/pit', year ? { year } : undefined),
};

export interface ProductInput {
  name: string;
  sku: string | null;
  model: string | null;
  category: string | null;
  price_gr: number;
  production_cost_gr: number;
  is_active: boolean;
  description: string | null;
}

export const productsApi = {
  list: (params: { search?: string; only_active?: boolean; page?: number; per_page?: number }) =>
    api.get<Page<Product>>('/api/products', params as Record<string, unknown>),
  create: (payload: ProductInput) => api.post<Product>('/api/products', payload),
  update: (id: number, payload: ProductInput) => api.put<Product>(`/api/products/${id}`, payload),
  remove: (id: number) => api.delete<{ message: string }>(`/api/products/${id}`),
};

export interface CostInput {
  cost_date: string;
  name: string;
  category_id: number | null;
  vendor: string | null;
  invoice_number: string | null;
  amount_gr: number;
  payment_method: string | null;
  description: string | null;
  attachment_id: number | null;
}

export const costsApi = {
  list: (params: Record<string, unknown>) => api.get<Page<Cost>>('/api/costs', params),
  create: (payload: CostInput) => api.post<Cost>('/api/costs', payload),
  update: (id: number, payload: CostInput) => api.put<Cost>(`/api/costs/${id}`, payload),
  remove: (id: number) => api.delete<{ message: string }>(`/api/costs/${id}`),
  categories: () => api.get<CostCategory[]>('/api/cost-categories'),
  createCategory: (name: string) => api.post<CostCategory>('/api/cost-categories', { name }),
  updateCategory: (id: number, payload: { name?: string; is_active?: boolean }) =>
    api.put<CostCategory>(`/api/cost-categories/${id}`, payload),
  removeCategory: (id: number) => api.delete<{ message: string }>(`/api/cost-categories/${id}`),
  uploadAttachment: (file: File) => api.upload<Attachment>('/api/attachments', file),
};

export interface DocumentInput {
  document_type: string;
  sale_id: number | null;
  issue_date: string;
  sale_date: string | null;
  due_date: string | null;
  buyer_name: string;
  buyer_nip: string | null;
  buyer_address: string | null;
  buyer_email: string | null;
  customer_type: string;
  items: Array<{ name: string; quantity: number; unit_price_gr: number; unit: string }>;
  payment_method: string | null;
  paid_note: string | null;
  notes: string | null;
  ksef_status: string;
  ksef_number: string | null;
}

export const documentsApi = {
  list: (params: Record<string, unknown>) => api.get<Page<SalesDocument>>('/api/documents', params),
  create: (payload: DocumentInput) => api.post<SalesDocument>('/api/documents', payload),
  update: (
    id: number,
    payload: Partial<{ ksef_status: string; ksef_number: string | null; notes: string | null }>,
  ) => api.patch<SalesDocument>(`/api/documents/${id}`, payload),
  remove: (id: number) => api.delete<{ message: string }>(`/api/documents/${id}`),
};

export const reportsApi = {
  get: (key: string, params: Record<string, unknown>) => api.get<ReportResponse>(`/api/reports/${key}`, params),
};

export const settingsApi = {
  get: () => api.get<{ values: SettingsValues }>('/api/settings'),
  update: (values: SettingsValues) => api.put<{ values: SettingsValues }>('/api/settings', { values }),
  fiscalYears: () => api.get<FiscalYear[]>('/api/settings/fiscal-years'),
  updateFiscalYear: (year: number, payload: Partial<FiscalYear>) =>
    api.put<FiscalYear>(`/api/settings/fiscal-years/${year}`, payload),
};

export const backupsApi = {
  list: () => api.get<BackupFile[]>('/api/backups'),
  create: (note?: string) => api.post<BackupFile>('/api/backups', { note: note ?? null }),
  restore: (filename: string, confirmation: string) =>
    api.post<{ message: string; safety_backup: string }>('/api/backups/restore', {
      filename,
      confirm: true,
      confirmation,
    }),
  remove: (filename: string) => api.delete<{ message: string }>(`/api/backups/${filename}`),
};

export const auditApi = {
  list: (params: Record<string, unknown>) => api.get<Page<AuditLogEntry>>('/api/audit-logs', params),
};
