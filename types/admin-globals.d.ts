type ServiceInventoryItem = {
  id: number | string;
  item_name?: string;
  item_type?: "consumable" | "non_consumable" | string;
  quantity?: number;
  unit?: string;
};

type ServiceUsageItem = {
  inventory_id: number;
  item_name?: string;
  unit?: string;
  quantity: number;
};

type AdminService = {
  id?: number | string;
  name?: string;
  pricing_type?: "per_unit" | "fixed" | string;
  service_category?: string;
  fixed_price?: number;
  allow_manual_price?: boolean;
  unit_label?: string;
  default_quantity?: number;
  price_per_unit?: number;
  notes_template?: string;
  is_active?: boolean;
  inventory_usage?: ServiceUsageItem[];
};

type AdminTherapist = {
  id: number | string;
  name?: string;
  gender?: string;
  specialization?: string;
  is_active?: boolean;
  can_handle_any_gender?: boolean;
};

type DashboardStockItem = {
  name?: string;
  quantity?: number;
  unit?: string;
  min_stock?: number;
};

type DashboardRecentTransaction = {
  type?: string;
  title?: string;
  subtitle?: string;
  date?: string;
  amount?: number;
};

type DashboardDiscountRule = {
  id?: number | string;
  name?: string;
  type?: string;
  discount_type?: string;
  discount_value?: number;
  condition_value?: number | null;
  voucher_code?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_active?: boolean;
};

type DashboardStats = {
  total_patients?: number;
  total_visits?: number;
  total_transactions?: number;
  total_income?: number;
  total_herbal_sales?: number;
  low_stock_inventory?: number;
  out_of_stock_herbals?: number;
  low_stock_items?: DashboardStockItem[];
  out_of_stock_items?: DashboardStockItem[];
  recent_transactions?: DashboardRecentTransaction[];
  discount_summary?: {
    active_count?: number;
    active_voucher_count?: number;
    active_visit_count?: number;
    active_items?: DashboardDiscountRule[];
    newest?: DashboardDiscountRule | null;
    previous?: DashboardDiscountRule | null;
  };
};

type SunnahDate = {
  gDate: Date;
  hDay: string;
  hMonth: string;
};

type AnalyticsTopTherapist = {
  id?: number | string;
  name?: string;
  visits?: number;
  income?: number;
  points?: number;
};

type AnalyticsRecentTransaction = {
  date?: string;
  type?: "visit" | "herbal" | string;
  patient?: string;
  therapist?: string;
  price?: number;
  point_count?: number;
  transaction_type?: "sale" | "return" | "retur" | string;
  invoice_status?: string;
  payment_status?: string;
  payment_method?: string;
  amount_paid?: number | null;
};

type AnalyticsRevenueSummary = {
  total_income?: number;
  gross_visit_revenue?: number;
  void_visit_revenue?: number;
  net_visit_revenue?: number;
  gross_herbal_sales?: number;
  herbal_returns?: number;
  net_herbal_sales?: number;
  herbal_cogs?: number;
  gross_profit?: number;
  active_invoice_total?: number;
  void_invoice_total?: number;
  avg_income?: number;
  current_month_income?: number;
  income_growth_pct?: number;
};

type AnalyticsExpenseSummary = {
  operational_expense?: number;
  gross_profit?: number;
  net_profit?: number;
};

type AnalyticsSummary = AnalyticsRevenueSummary & {
  total_patients?: number;
  total_visits?: number;
  total_herbal_sales?: number;
  total_transactions?: number;
  active_invoice_count?: number;
  void_invoice_count?: number;
  current_month_visits?: number;
  current_month_herbal_sales?: number;
  current_month_transactions?: number;
  visits_growth_pct?: number;
  total_herbal_value?: number;
  low_stock_count?: number;
  male_count?: number;
  female_count?: number;
  monthly_labels?: string[];
  monthly_visits?: number[];
  monthly_income?: number[];
  top_therapists?: AnalyticsTopTherapist[];
  visit_frequency?: Record<"1" | "2-4" | "5+", number>;
  recent_visits?: AnalyticsRecentTransaction[];
  recent_transactions?: AnalyticsRecentTransaction[];
  correction_summary?: {
    stock_corrections?: number;
    herbal_returns?: number;
    void_invoices?: number;
  };
};

type AuditLogRow = {
  created_at?: string;
  action?: string;
  entity_type?: string;
  entity_id?: string | number;
  description?: string;
  metadata?: Record<string, unknown>;
  detail?: string;
};

type HelpSupport = {
  support_name?: string;
  support_whatsapp?: string;
  support_email?: string;
};

type HelpAppInfo = {
  support?: HelpSupport;
  app_version?: string;
  database_path?: string;
  backup_dir?: string;
  logs_dir?: string;
  exports_dir?: string;
  license?: {
    valid?: boolean;
    status?: string;
  };
  detail?: string;
};

type LicenseStatusPayload = {
  valid?: boolean;
  status?: string;
  verify_status?: string;
  clinic_id?: string;
  expired_at?: string;
  message?: string;
  detail?: string;
  license?: LicenseStatusPayload;
};

type OwnerReportRow = {
  id?: number | string;
  name?: string;
  phone?: string;
  visits?: number;
  revenue?: number;
  quantity?: number;
  category?: string;
  last_visit?: string;
  segment?: string;
  segment_label?: string;
  days_since_last_visit?: number;
};

type OwnerReportSummary = {
  total_revenue?: number;
  visit_revenue?: number;
  herbal_revenue?: number;
  total_visits?: number;
  unique_patients?: number;
  new_patients?: number;
  active_patients?: number;
  patients_need_followup?: number;
  dormant_patients?: number;
  total_whatsapp_followups?: number;
  total_whatsapp_confirmed?: number;
  followup_booked?: number;
  pending_revenue?: number;
  pending_visit_revenue?: number;
  pending_herbal_revenue?: number;
};

type OwnerReportPayload = {
  period?: {
    type?: string;
    date_from?: string;
    date_to?: string;
    new_patient_source?: string;
  };
  summary?: OwnerReportSummary;
  top_services?: OwnerReportRow[];
  top_service_categories?: OwnerReportRow[];
  top_herbals?: OwnerReportRow[];
  top_loyal_patients?: OwnerReportRow[];
  patients_need_followup?: OwnerReportRow[];
};

type InventoryItem = {
  id: number | string;
  item_name?: string;
  name?: string;
  item_type?: InventoryItemKind;
  quantity?: number | string;
  min_stock?: number | string;
  unit?: string;
  package_unit?: string;
  package_size?: number | string;
  packageUnit?: string;
  packageSize?: number | string;
  stock_display?: string;
};

type InvoiceItem = {
  id: number | string;
  date?: string;
  name?: string;
  price?: number;
  path?: string;
  file_exists?: boolean;
  invoice_status?: string;
  void_reason?: string;
  payment_provider?: string;
  payment_method?: PaymentMethod;
  payment_status?: PaymentStatus;
  payment_reference?: string;
  payment_url?: string;
};

type ConfirmOptions = {
  confirmText?: string;
  cancelText?: string;
  maxWidth?: string;
};

type ApiResponse<T = unknown> = {
  status?: "success" | "error" | string;
  message?: string;
  detail?: unknown;
  data?: T;
};

type Therapist = {
  id: number | string;
  name?: string;
  gender?: string;
  specialization?: string;
  is_active?: boolean;
  can_handle_any_gender?: boolean;
};

type Service = {
  id: number | string;
  name?: string;
  pricing_type?: ServicePricingMode;
  service_category?: string;
  fixed_price?: number;
  allow_manual_price?: boolean;
  unit_label?: string;
  default_quantity?: number;
  price_per_unit?: number;
  notes_template?: string;
  is_active?: boolean;
  inventory_usage?: ServiceUsageItem[];
};

interface Window {
  _serviceInventoryList?: ServiceInventoryItem[];
  _serviceInventoryLoaded?: boolean;
  _serviceUsageDrafts?: Record<string, ServiceUsageItem[]>;
  _serviceUnitPresets?: string[];
  _serviceFilter?: "active" | "inactive" | "all";
  _serviceMap?: Record<string | number, AdminService>;
  _therapistFilter?: "active" | "inactive" | "all";
  _therapistMap?: Record<string | number, AdminTherapist>;
  _appToken?: string;
  _initialLicense?: LicenseStatusPayload;
  _clinicName?: string;
  _ownerReportPeriod?: string;
  _ownerNewPatientSource?: string;
  _invoicesPage?: number;
  _invoicesPeriod?: string;
  _invoicesSearch?: string;
  _invoiceSearchTimer?: number;
  _invoiceSearchCursor?: number | null;
  _invoiceSearchRestoreFocus?: boolean;
  _analyticsPeriod?: string;
  _analyticsProfitData?: AnalyticsSummary;
  renderDashboard?: () => Promise<void>;
  renderTherapists?: (data: Therapist[]) => void;
  toggleTherapist?: (id: number | string, btn: HTMLButtonElement) => Promise<void>;
  deleteTherapist?: (id: number | string) => Promise<void>;
  setTherapistFilter?: (filter: "active" | "inactive" | "all") => void;
  renderServices?: (data: Service[]) => void;
  setServiceFilter?: (filter: "active" | "inactive" | "all") => void;
  setServiceUnitValue?: (inputId: string, value: string) => void;
  syncServicePricingMode?: (prefix: string) => void;
  addServiceUsageItem?: (prefix: string) => void;
  removeServiceUsageItem?: (prefix: string, index: number) => void;
  syncServiceUsageInput?: (prefix: string) => boolean;
  openEditServiceModal?: (id: number | string, btn?: HTMLButtonElement) => void;
  submitEditService?: (event: SubmitEvent) => Promise<void>;
  toggleService?: (id: number | string, btn: HTMLButtonElement) => Promise<void>;
  deleteService?: (id: number | string) => Promise<void>;
  renderAnalytics?: (data?: AnalyticsSummary) => void;
  updateProfitLossPreview?: () => void;
  renderOwnerReport?: () => Promise<void>;
  changeOwnerReportPeriod?: (value: string) => void;
  changeOwnerNewPatientSource?: (value: string) => void;
  exportOwnerReportExcel?: () => Promise<void>;
  renderInventory?: (data: InventoryItem[]) => void;
  selectInventory?: (row: HTMLTableRowElement) => void;
  setInventoryStockMode?: (mode: string) => void;
  updateInventoryStockPreview?: () => void;
  prepareInventoryStockSubmit?: (event: SubmitEvent) => void;
  editInventory?: (
    id: number | string,
    name: string,
    qty: number | string,
    unit: string,
    minStock: number | string,
    packageUnit?: string,
    packageSize?: number | string,
    itemType?: string
  ) => void;
  submitEditInventory?: (event: SubmitEvent) => Promise<void>;
  deleteInventory?: (id: number | string, name: string) => Promise<void>;
  requestAnimationFrame(callback: FrameRequestCallback): number;
}

declare function escapeHtml(value: unknown): string;
declare function formatRupiah(amount: unknown): string;
declare function sanitizeAppErrorMessage(value: unknown, fallback?: string): string;
declare function showToast(message: string, type?: "success" | "error" | "warning" | "info"): void;
declare function openModal(title: string, html: string): void;
declare function closeModal(): void;
declare function initModals(): void;
declare function loadTab(tabName: string): Promise<void> | void;
declare function openCRMFollowup(patientId: number): void;
declare function showConfirm(message: string, type?: string, options?: ConfirmOptions): Promise<boolean>;
