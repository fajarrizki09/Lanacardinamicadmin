// Central shared admin UI types.
// Keep this file dependency-free because tsconfig uses module: none and emits browser globals.

type EntityId = number | string;

type PaymentStatus =
    | 'paid'
    | 'unpaid'
    | 'partial'
    | 'pending'
    | 'failed'
    | 'expired'
    | 'void'
    | 'refunded'
    | string;

type PaymentMethod =
    | 'cash'
    | 'qris'
    | 'transfer'
    | 'debit'
    | 'ewallet'
    | 'virtual_account'
    | 'credit_card'
    | 'other'
    | 'free'
    | string;

type ServicePricingMode = 'per_unit' | 'fixed' | string;
type InventoryItemKind = 'consumable' | 'non_consumable' | string;
type ActivationFilter = 'active' | 'inactive' | 'all';

type AdminVisit = {
    id: EntityId;
    date?: string | Date;
    price?: number;
    original_price?: number;
    discount_amount?: number;
    final_price?: number;
    discount_applied?: boolean;
    point_count?: number;
    quantity?: number;
    therapist_id?: EntityId | null;
    service_id?: EntityId | null;
    service_name?: string;
    invoice_path?: string;
    invoice_status?: string;
    payment_status?: PaymentStatus;
    payment_method?: PaymentMethod;
    amount_paid?: number;
};

type AdminServiceModel = {
    id: EntityId;
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

type AdminInventoryModel = {
    id: EntityId;
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

type AdminHerbalModel = {
    id: EntityId;
    name?: string;
    unit?: string;
    price?: number;
    cost_price?: number;
    stock?: number;
    min_stock?: number;
    is_active?: boolean;
};

type AdminApiStatusResponse<T = unknown> = {
    status?: 'success' | 'error' | string;
    message?: string;
    detail?: unknown;
    data?: T;
};
