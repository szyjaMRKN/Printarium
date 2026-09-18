/** Typy odpowiadające schematom backendu. Wszystkie kwoty są w groszach. */

export type PaymentStatus =
  | 'niezaplacone'
  | 'czesciowo_zaplacone'
  | 'zaplacone'
  | 'anulowane'
  | 'zwrocone';

export type LimitStatus = 'normalny' | 'ostrzezenie' | 'mocne_ostrzezenie' | 'przekroczony';

export interface Option {
  value: string;
  label: string;
}

export interface User {
  id: number;
  login: string;
  email: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
  must_change_password: boolean;
}

export interface SessionInfo {
  user: User;
  csrf_token: string;
  expires_at: string;
}

export interface PageMeta {
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface Page<T> {
  items: T[];
  meta: PageMeta;
}

export interface SaleItem {
  id: number;
  product_id: number | null;
  position: number;
  name: string;
  variant: string | null;
  quantity: number;
  unit_price_gr: number;
  line_total_gr: number;
}

export interface Payment {
  id: number;
  sale_id: number;
  payment_date: string;
  amount_gr: number;
  method: string;
  description: string | null;
  correction_id: number | null;
  created_at: string;
}

export interface Correction {
  id: number;
  sale_id: number;
  correction_date: string;
  correction_type: string;
  previous_value_gr: number;
  new_value_gr: number;
  amount_gr: number;
  refund_amount_gr: number;
  reason: string | null;
  description: string | null;
  created_by_id: number | null;
  created_at: string;
}

export interface SaleListItem {
  id: number;
  document_number: string | null;
  sale_date: string;
  description: string | null;
  total_gr: number;
  corrections_total_gr: number;
  accrued_revenue_gr: number;
  paid_amount_gr: number;
  outstanding_gr: number;
  payment_status: PaymentStatus;
  payment_method: string | null;
  sales_channel: string | null;
  customer_type: string;
  customer_name: string | null;
  last_payment_date: string | null;
  is_cancelled: boolean;
}

export interface Sale extends SaleListItem {
  items_total_gr: number;
  discount_gr: number;
  shipping_gr: number;
  first_payment_date: string | null;
  customer_nip: string | null;
  customer_email: string | null;
  customer_phone: string | null;
  customer_address: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  items: SaleItem[];
  payments: Payment[];
  corrections: Correction[];
}

export interface SaleItemInput {
  product_id: number | null;
  name: string;
  variant: string | null;
  quantity: number;
  unit_price_gr: number;
}

export interface SaleInput {
  document_number: string | null;
  sale_date: string;
  description: string | null;
  items: SaleItemInput[];
  discount_gr: number;
  shipping_gr: number;
  payment_method: string | null;
  sales_channel: string | null;
  customer_type: string;
  customer_name: string | null;
  customer_nip: string | null;
  customer_email: string | null;
  customer_phone: string | null;
  customer_address: string | null;
  notes: string | null;
  initial_payment?: {
    amount_gr: number;
    payment_date: string;
    method: string;
    description?: string | null;
  } | null;
}

export interface RegistryRow {
  lp: number;
  sale_id: number;
  sale_date: string;
  document_number: string | null;
  description: string | null;
  total_gr: number;
  corrections_total_gr: number;
  accrued_revenue_gr: number;
  cumulative_gr: number;
  payment_status: PaymentStatus;
  paid_amount_gr: number;
}

export interface RegistryResponse {
  items: RegistryRow[];
  meta: PageMeta;
  summary: { accrued_revenue_gr: number };
}

export interface DailyRegistryRow {
  lp: number;
  day: string;
  sales_count: number;
  total_gr: number;
  cumulative_gr: number;
}

export interface Product {
  id: number;
  name: string;
  sku: string | null;
  model: string | null;
  category: string | null;
  price_gr: number;
  production_cost_gr: number;
  is_active: boolean;
  description: string | null;
  attributes: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface CostCategory {
  id: number;
  name: string;
  slug: string;
  is_active: boolean;
  sort_order: number;
}

export interface Cost {
  id: number;
  cost_date: string;
  name: string;
  category_id: number | null;
  category_name: string | null;
  vendor: string | null;
  invoice_number: string | null;
  amount_gr: number;
  payment_method: string | null;
  description: string | null;
  attachment_id: number | null;
  attachment_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  id: number;
  original_name: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export interface SalesDocument {
  id: number;
  document_type: string;
  number: string;
  sale_id: number | null;
  issue_date: string;
  sale_date: string;
  due_date: string | null;
  buyer_name: string;
  buyer_nip: string | null;
  buyer_address: string | null;
  buyer_email: string | null;
  customer_type: string;
  items_snapshot: Array<{
    name: string;
    quantity: number;
    unit: string;
    unit_price_gr: number;
    total_gr: number;
  }>;
  seller_snapshot: Record<string, string>;
  total_gr: number;
  payment_method: string | null;
  paid_note: string | null;
  notes: string | null;
  ksef_status: string;
  ksef_number: string | null;
  created_at: string;
}

export interface Exceedance {
  exceeded_on: string;
  sale_id: number;
  sale_document_number: string | null;
  exceeded_by_gr: number;
  cumulative_gr: number;
}

export interface QuarterLimit {
  year: number;
  quarter: number;
  label: string;
  date_from: string;
  date_to: string;
  accrued_revenue_gr: number;
  limit_gr: number;
  usage_percent: number;
  remaining_gr: number;
  status: LimitStatus;
  message: string | null;
  sales_count: number;
  exceedance: Exceedance | null;
}

export interface ThresholdCounter {
  label: string;
  period_label: string;
  value_gr: number;
  threshold_gr: number;
  usage_percent: number;
  status: LimitStatus;
  message: string | null;
}

export interface DashboardData {
  today: string;
  year: number;
  quarter: number;
  limit: QuarterLimit;
  metrics: {
    accrued_today_gr: number;
    accrued_month_gr: number;
    accrued_quarter_gr: number;
    accrued_year_gr: number;
    received_month_gr: number;
    received_quarter_gr: number;
    received_year_gr: number;
    outstanding_gr: number;
    costs_month_gr: number;
    costs_year_gr: number;
    income_year_gr: number;
    income_month_gr: number;
    orders_today: number;
    orders_month: number;
    orders_year: number;
    average_order_month_gr: number;
    average_order_year_gr: number;
  };
  charts: {
    last_30_days: Array<{ day: string; accrued_gr: number; received_gr: number }>;
    monthly: Array<{
      year: number;
      month: number;
      label: string;
      accrued_gr: number;
      received_gr: number;
      costs_gr: number;
      income_gr: number;
      sales_count: number;
    }>;
    by_channel: Array<{ channel: string; accrued_gr: number; sales_count: number }>;
    by_product: Array<{ product_id: number | null; name: string; value_gr: number; quantity: number }>;
    by_customer_type: Array<{ customer_type: string; accrued_gr: number; sales_count: number }>;
    costs_by_category: Array<{ category: string; amount_gr: number; count: number }>;
  };
  counters: {
    ksef: ThresholdCounter;
    cash_register: ThresholdCounter;
  };
}

export interface LimitsResponse {
  year: number;
  parameters: {
    minimum_wage_gr: number;
    limit_multiplier_permille: number;
    quarterly_limit_gr: number;
    quarterly_limit_override_gr: number | null;
  };
  quarters: QuarterLimit[];
  counters: { ksef: ThresholdCounter; cash_register: ThresholdCounter };
}

export interface ReportColumn {
  key: string;
  title: string;
  type: 'text' | 'money' | 'date' | 'int';
}

export interface ReportResponse {
  key: string;
  title: string;
  columns: ReportColumn[];
  rows: Array<Record<string, unknown>>;
  summary: Record<string, number>;
}

export interface PitPeriod {
  label: string;
  received_gr: number;
  costs_gr: number;
  income_gr: number;
  accrued_gr: number;
}

export interface PitSummary {
  year: number;
  disclaimer: string;
  monthly: PitPeriod[];
  quarterly: PitPeriod[];
  yearly: PitPeriod;
}

export interface BackupFile {
  filename: string;
  size_bytes: number;
  created_at: string;
  is_automatic: boolean;
}

export interface FiscalYear {
  year: number;
  minimum_wage_gr: number;
  limit_multiplier_permille: number;
  quarterly_limit_gr: number;
  quarterly_limit_override_gr: number | null;
  ksef_monthly_threshold_gr: number;
  cash_register_yearly_threshold_gr: number;
  note: string | null;
}

export type SettingsValues = Record<string, string | number | boolean | string[]>;

export interface AuditLogEntry {
  id: number;
  created_at: string;
  user_login: string | null;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  description: string | null;
  ip_address: string | null;
}

export interface MetaOptions {
  app: { name: string; version: string };
  payment_status: Option[];
  payment_method: Option[];
  sales_channel: Option[];
  customer_type: Option[];
  correction_type: Option[];
  document_type: Option[];
  ksef_status: Option[];
  user_role: Option[];
  reports: Option[];
}
