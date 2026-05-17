export type ID = number | string;

export type ApiResponse<T = unknown> = {
    status?: "success" | "error" | string;
    message?: string;
    detail?: unknown;
    data?: T;
};

export type ApiMessageResponse = ApiResponse & {
    status: "success" | "error" | string;
    message: string;
};

export type PaginatedResponse<T> = {
    page?: number;
    page_size?: number;
    total?: number;
    total_pages?: number;
    recordsTotal?: number;
    recordsFiltered?: number;
    draw?: number;
    data: T[];
};

export type ListResponse<T> = {
    items?: T[];
    data?: T[];
    message?: string;
};

export type Patient = {
    id: ID;
    name?: string;
    phone?: string;
    address?: string;
    gender?: string;
    birth_date?: string;
    created_at?: string;
    updated_at?: string;
};

export type Visit = {
    id: ID;
    patient_id?: ID;
    patient_name?: string;
    therapist_id?: ID;
    therapist_name?: string;
    visit_date?: string;
    service_id?: ID;
    service_name?: string;
    quantity?: number;
    total_price?: number;
    payment_status?: string;
    payment_method?: string;
    notes?: string;
};

export type HerbalTransaction = {
    id: ID;
    herbal_id?: ID;
    herbal_name?: string;
    visit_id?: ID | null;
    sale_group_id?: string | null;
    patient_id?: ID;
    patient_name?: string;
    item_id?: ID;
    item_name?: string;
    quantity?: number;
    unit?: string;
    price?: number;
    total_price?: number;
    date?: string | null;
    transaction_date?: string;
    transaction_type?: "sale" | "return" | "retur" | "stock_in" | "adjustment" | string;
    invoice_path?: string | null;
    invoice_status?: string;
    note?: string | null;
    payment_status?: string;
    payment_method?: string;
    amount_paid?: number | null;
    paid_at?: string | null;
};

export type InventoryItem = {
    id: ID;
    item_name?: string;
    name?: string;
    quantity?: number | string;
    stock_display?: string;
    unit?: string;
    package_unit?: string;
    package_size?: number | string;
    packageUnit?: string;
    packageSize?: number | string;
    min_stock?: number | string;
    last_updated?: string | null;
    is_active?: boolean;
};

export type HerbalItem = {
    id: ID;
    name?: string;
    stock?: number;
    stock_display?: string;
    cost_price?: number;
    price?: number;
    unit?: string;
    package_unit?: string;
    package_size?: number;
    min_stock?: number;
    margin?: number;
    last_updated?: string | null;
    is_active?: boolean;
};

export type DiscountRule = {
    id?: ID;
    name?: string;
    type?: "visit_count" | "voucher" | "manual" | "period" | string;
    discount_type?: "percent" | "fixed" | string;
    discount_value?: number;
    condition_value?: number | null;
    voucher_code?: string | null;
    start_date?: string | null;
    end_date?: string | null;
    is_active?: boolean;
    priority?: number;
    created_at?: string;
    usage_limit?: number | null;
    per_patient_limit?: number | null;
    usage_count?: number;
    target_patient_ids?: ID[];
    target_patient_names?: string[];
};

export type DashboardLowStockItem = {
    name?: string;
    quantity?: number;
    unit?: string;
    min_stock?: number;
};

export type DashboardRecentTransaction = {
    type?: "visit" | "herbal" | string;
    date?: string;
    title?: string;
    subtitle?: string;
    amount?: number;
};

export type DashboardSummary = {
    total_patients?: number;
    total_visits?: number;
    visits_today?: number;
    total_herbal_sales?: number;
    total_transactions?: number;
    total_income?: number;
    current_period_income?: number;
    gross_herbal_sales?: number;
    herbal_returns?: number;
    net_herbal_sales?: number;
    active_invoice_total?: number;
    low_stock_inventory?: number;
    out_of_stock_herbals?: number;
};

export type DashboardStats = DashboardSummary & {
    low_stock_items?: DashboardLowStockItem[];
    out_of_stock_items?: DashboardLowStockItem[];
    recent_transactions?: DashboardRecentTransaction[];
    discount_summary?: {
        active_count?: number;
        active_voucher_count?: number;
        active_visit_count?: number;
        active_items?: DiscountRule[];
        newest?: DiscountRule | null;
        previous?: DiscountRule | null;
    };
};

export type AnalyticsRevenueSummary = {
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

export type AnalyticsExpenseSummary = {
    operational_expense?: number;
    gross_profit?: number;
    net_profit?: number;
};

export type AnalyticsSummary = AnalyticsRevenueSummary & {
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
    top_therapists?: Array<{
        id?: ID;
        name?: string;
        visits?: number;
        income?: number;
        points?: number;
    }>;
    visit_frequency?: Record<"1" | "2-4" | "5+", number>;
    recent_visits?: AnalyticsRecentTransaction[];
    recent_transactions?: AnalyticsRecentTransaction[];
    correction_summary?: {
        stock_corrections?: number;
        herbal_returns?: number;
        void_invoices?: number;
    };
};

export type AnalyticsRecentTransaction = {
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

export type OwnerReportSummary = {
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
};

export type OwnerReportRow = {
    id?: ID;
    name?: string;
    phone?: string;
    visits?: number;
    revenue?: number;
    quantity?: number;
    last_visit?: string;
    segment?: string;
    segment_label?: string;
    days_since_last_visit?: number;
};

export type OwnerReportPayload = {
    period?: {
        type?: string;
        date_from?: string;
        date_to?: string;
        new_patient_source?: string;
    };
    summary?: OwnerReportSummary;
    top_services?: OwnerReportRow[];
    top_herbals?: OwnerReportRow[];
    top_loyal_patients?: OwnerReportRow[];
    patients_need_followup?: OwnerReportRow[];
};

export type SettingsPayload = {
    clinic_name?: string;
    clinic_tagline?: string;
    clinic_address?: string;
    clinic_phone?: string;
    clinic_email?: string;
    clinic_website?: string;
    clinic_logo_path?: string;
    invoice_footer?: string;
    admin_label?: string;
    invoice_prefix?: string;
    base_price?: number;
    price_per_point?: number;
    discount_percentage?: number;
    min_visits_for_discount?: number;
    backup_auto_enabled?: boolean;
    backup_interval?: string;
    backup_max_files?: number;
    last_backup_time?: string | null;
    last_backup_status?: string;
    free_visit_reasons?: string[];
    first_run_completed?: boolean;
    first_run_skipped?: boolean;
    admin_pin_set?: boolean;
    payment_gateway_enabled?: boolean;
    payment_gateway_default_provider?: "gateway_mock" | "midtrans" | "xendit" | "duitku" | string;
    payment_gateway_environment?: "sandbox" | "production" | string;
    midtrans_client_key?: string;
    midtrans_merchant_id?: string;
    duitku_merchant_code?: string;
};

export type Invoice = {
    id: ID;
    date?: string;
    name?: string;
    price?: number;
    path?: string;
    file_exists?: boolean;
    invoice_status?: string;
    void_reason?: string;
    payment_provider?: string;
    payment_method?: string;
    payment_status?: string;
    payment_reference?: string;
    payment_url?: string;
};

export type Service = {
    id: ID;
    name?: string;
    unit_label?: string;
    default_quantity?: number;
    price_per_unit?: number;
    notes_template?: string;
    is_active?: boolean;
    inventory_usage?: ServiceUsage[];
};

export type ServiceUsage = {
    inventory_id: number;
    item_name?: string;
    unit?: string;
    quantity: number;
};

export type Therapist = {
    id: ID;
    name?: string;
    gender?: string;
    specialization?: string;
    is_active?: boolean;
    can_handle_any_gender?: boolean;
};

export type CRMContact = {
    id: ID;
    patient_id?: ID;
    name?: string;
    phone?: string;
    segment?: string;
    segment_label?: string;
    last_visit?: string;
    days_since_last_visit?: number;
    followup_status?: string;
    followup_note?: string;
};
