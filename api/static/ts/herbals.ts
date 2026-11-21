// ─── HERBALS ──────────────────────────────────────────────────────────────────
// Action-based workspace: table-first selection with focused modal workflows.

const HERBAL_UNIT_OPTIONS = ['botol', 'pcs', 'box', 'saset', 'pack', 'strip', 'tablet', 'kapsul', 'dus'];

type HerbalStockMode = 'in' | 'out';

type HerbalCatalogItem = {
    id: number;
    name: string;
    stock: number;
    stock_display?: string | number;
    price: number;
    cost_price: number;
    unit: string;
    package_unit: string;
    package_size: number;
    min_stock: number;
    margin?: number;
};

type HerbalSaleItem = {
    herbal_id: number;
    name: string;
    quantity: number;
    unit: string;
    price: number;
    stock: number;
};

type CorrectionLogRow = {
    created_at?: string | null;
    action_type?: string;
    herbal_name?: string;
    reference_type?: string;
    reference_id?: string | number;
    stock_before?: number | null;
    stock_after?: number | null;
    reason?: string | null;
};

type HerbalTransactionRow = {
    id: number | string;
    herbal_id?: number | string;
    date?: string | null;
    herbal_name?: string;
    quantity?: number;
    total_price?: number;
};

type HerbalTransactionPayload = {
    data?: HerbalTransactionRow[];
    detail?: string;
};

let herbalDelegationReady = false;

interface Window {
    _herbalCatalog?: HerbalCatalogItem[];
    _herbalSaleItems?: HerbalSaleItem[];
    _herbalReturnRows?: HerbalTransactionRow[];
    _selectedHerbalId?: number | null;
    renderHerbals?: (data: HerbalCatalogItem[]) => void;
    selectHerbal?: (row: HTMLTableRowElement) => void;
    goToHerbalPage?: (page: number) => void;
    setHerbalStockMode?: (mode: HerbalStockMode | string) => void;
    updateHerbalStockPreview?: () => void;
    prepareHerbalStockSubmit?: (event: SubmitEvent) => void;
    openAddHerbalModal?: () => void;
    submitAddHerbal?: (event: SubmitEvent) => Promise<void>;
    openHerbalStockModal?: () => void;
    submitHerbalStock?: (event: SubmitEvent) => Promise<void>;
    filterHerbalPicker?: (context: string) => void;
    selectHerbalPickerItem?: (context: string) => void;
    openHerbalSaleModal?: () => void;
    onHerbalSaleSelectChange?: () => void;
    onHerbalSaleQtyInput?: () => void;
    addHerbalSaleItem?: () => void;
    removeHerbalSaleItem?: (herbalId: number) => void;
    submitHerbalSale?: () => Promise<void>;
    openHerbalReturnModal?: () => Promise<void>;
    filterHerbalReturnPicker?: () => void;
    syncHerbalReturnInfo?: () => void;
    submitHerbalReturn?: () => Promise<void>;
    editHerbal?: (
        id: number | string,
        name: string,
        unit: string,
        price: number | string,
        stock: number | string,
        costPrice?: number | string,
        packageUnit?: string,
        packageSize?: number | string,
        minStock?: number | string
    ) => void;
    submitEditHerbal?: (event: SubmitEvent) => Promise<void>;
    deleteHerbal?: (id: number | string, name: string) => Promise<void>;
}

function herbalText(value: unknown, fallback = ''): string {
    const text = String(value ?? '').trim();
    return text || fallback;
}

function herbalNumber(value: unknown, fallback = 0): number {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function herbalInput(id: string): HTMLInputElement | null {
    return document.getElementById(id) as HTMLInputElement | null;
}

function herbalSelect(id: string): HTMLSelectElement | null {
    return document.getElementById(id) as HTMLSelectElement | null;
}

function herbalErrorMessage(error: unknown, fallback = 'Terjadi kesalahan.'): string {
    return error instanceof Error ? error.message : fallback;
}

function herbalUnitSelectHtml(name: string, value = '', includeEmpty = false): string {
    const options = (includeEmpty ? [''] : []).concat(HERBAL_UNIT_OPTIONS);
    return `<select name="${name}">${options.map(opt => {
        const label = opt || '- Tidak ada -';
        return `<option value="${escapeHtml(opt)}" ${opt === value ? 'selected' : ''}>${escapeHtml(label)}</option>`;
    }).join('')}</select>`;
}

function herbalPackageLabel(item: Pick<HerbalCatalogItem, 'package_unit' | 'package_size' | 'unit'>): string {
    if (!item.package_unit || Number(item.package_size || 1) <= 1) return '-';
    return `1 ${item.package_unit} = ${item.package_size} ${item.unit}`;
}

function herbalStatus(item: Pick<HerbalCatalogItem, 'stock' | 'min_stock'>): string {
    if (item.stock <= 0) return 'Habis';
    if (item.stock <= item.min_stock) return 'Menipis';
    return 'Tersedia';
}

function selectedHerbal(): HerbalCatalogItem | null {
    const selectedId = Number(window._selectedHerbalId || 0);
    return (window._herbalCatalog || []).find(item => item.id === selectedId) || null;
}

function herbalById(id: number | string): HerbalCatalogItem | null {
    const herbalId = Number(id || 0);
    return (window._herbalCatalog || []).find(item => item.id === herbalId) || null;
}

function ensureHerbalEventDelegation(): void {
    if (herbalDelegationReady) return;
    herbalDelegationReady = true;

    document.addEventListener('click', (event) => {
        const actionElement = (event.target as HTMLElement | null)?.closest<HTMLElement>('[data-herbal-action]');
        if (!actionElement) return;
        const action = actionElement.dataset.herbalAction || '';
        if (!action) return;
        event.preventDefault();

        switch (action) {
            case 'open-add':
                openAddHerbalModal();
                break;
            case 'open-sale':
                openHerbalSaleModal();
                break;
            case 'open-stock':
                openHerbalStockModal();
                break;
            case 'open-return':
                openHerbalReturnModal();
                break;
            case 'select-row':
                selectHerbal(actionElement as HTMLTableRowElement);
                break;
            case 'edit':
                editHerbalFromCache(actionElement.dataset.id || '');
                break;
            case 'delete':
                deleteHerbalFromCache(actionElement.dataset.id || '');
                break;
            case 'page':
                goToHerbalPage(Number(actionElement.dataset.page || 1));
                break;
            case 'close-modal':
                closeModal();
                break;
            case 'stock-mode':
                setHerbalStockMode(actionElement.dataset.mode || 'in');
                break;
            case 'sale-add':
                addHerbalSaleItem();
                break;
            case 'sale-submit':
                submitHerbalSale();
                break;
            case 'sale-remove':
                removeHerbalSaleItem(Number(actionElement.dataset.id || 0));
                break;
            case 'return-submit':
                submitHerbalReturn();
                break;
        }
    });

    document.addEventListener('input', (event) => {
        const target = event.target as HTMLInputElement | null;
        const action = target?.dataset?.herbalAction || '';
        if (!action) return;
        if (action === 'picker-filter') filterHerbalPicker(target.dataset.context || '');
        if (action === 'stock-preview') updateHerbalStockPreview();
        if (action === 'sale-qty') onHerbalSaleQtyInput();
        if (action === 'return-filter') filterHerbalReturnPicker();
    });

    document.addEventListener('change', (event) => {
        const target = event.target as HTMLElement | null;
        const action = target?.dataset?.herbalAction || '';
        if (!action) return;
        if (action === 'picker-select') selectHerbalPickerItem(target.dataset.context || '');
        if (action === 'stock-preview') updateHerbalStockPreview();
        if (action === 'return-sync') syncHerbalReturnInfo();
    });

    document.addEventListener('submit', (event) => {
        const form = event.target as HTMLFormElement | null;
        const action = form?.dataset?.herbalFormAction || '';
        if (!action) return;
        if (action === 'add') submitAddHerbal(event);
        if (action === 'stock') submitHerbalStock(event);
        if (action === 'edit') submitEditHerbal(event);
    });
}

function herbalPickerOptions(items: HerbalCatalogItem[], selectedId?: number | null): string {
    if (!items.length) return '<option value="">Belum ada produk/peralatan tersedia.</option>';
    const prompt = selectedId ? '' : '<option value="" selected>Pilih produk / herbal</option>';
    return prompt + items.map(item => {
        const selected = item.id === selectedId ? ' selected' : '';
        const label = `${item.name} | ${herbalStatus(item)} | stok ${item.stock} ${item.unit} | ${formatRupiah(item.price)}`;
        return `<option value="${item.id}"${selected}>${escapeHtml(label)}</option>`;
    }).join('');
}

function herbalPickerHtml(context: string, selectedId?: number | null): string {
    const items = window._herbalCatalog || [];
    return `
        <div class="action-picker" data-picker="${context}">
            <label for="${context}-search">Cari Produk / Herbal</label>
            <div class="action-picker-search">
                <i class="fas fa-search"></i>
                <input type="search" id="${context}-search" autocomplete="off"
                    placeholder="Nama, status, stok, satuan, atau harga"
                    data-herbal-action="picker-filter" data-context="${escapeHtml(context)}">
            </div>
            <select id="${context}-select" class="action-picker-results" size="4"
                data-herbal-action="picker-select" data-context="${escapeHtml(context)}">
                ${herbalPickerOptions(items, selectedId)}
            </select>
            <div id="${context}-empty" class="action-picker-empty ${items.length ? 'hidden' : ''}">Belum ada produk/peralatan tersedia.</div>
            <div id="${context}-info" class="selected-item-summary"></div>
        </div>`;
}

function updateHerbalSelectionSummary(): void {
    const item = selectedHerbal();
    const summary = document.getElementById('herbal-row-selection');
    if (!summary) return;
    if (!item) {
        summary.innerHTML = '<i class="fas fa-hand-pointer"></i> Pilih row untuk mengisi action secara otomatis, atau buka action dan cari produk.';
        summary.classList.remove('has-selection');
        return;
    }
    summary.innerHTML = `<i class="fas fa-check-circle"></i> <strong>${escapeHtml(item.name)}</strong><span>Stok ${item.stock} ${escapeHtml(item.unit)} &middot; ${formatRupiah(item.price)} &middot; ${escapeHtml(herbalStatus(item))}</span>`;
    summary.classList.add('has-selection');
}

function renderHerbals(data: HerbalCatalogItem[]): void {
    ensureHerbalEventDelegation();
    window._herbalCatalog = (data || []).map((h: HerbalCatalogItem) => ({
        id: Number(h.id),
        name: h.name || '',
        stock: Number(h.stock || 0),
        price: Number(h.price || 0),
        cost_price: Number(h.cost_price || 0),
        unit: h.unit || 'pcs',
        package_unit: h.package_unit || '',
        package_size: Number(h.package_size || 1),
        min_stock: Number(h.min_stock || 5)
    }));
    if (window._selectedHerbalId && !selectedHerbal()) window._selectedHerbalId = null;
    window._herbalSaleItems = [];
    const outOfStock = data.filter((h: HerbalCatalogItem) => h.stock <= 0).length;
    const lowStockHerb = data.filter((h: HerbalCatalogItem) => h.stock > 0 && h.stock <= (h.min_stock || 5)).length;
    const goodStock = data.length - outOfStock - lowStockHerb;

    // Pagination
    const currentPage = (window as any)._herbalPage || 1;
    const itemsPerPage = 10;
    const totalPages = Math.ceil(data.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedData = data.slice(startIndex, endIndex);

    const html = `
        <!-- ── Stat Cards ── -->
        <div class="herbal-stats-grid">
            <div class="stat-card border-success">
                <div class="stat-icon green"><i class="fas fa-leaf"></i></div>
                <div class="stat-details"><h4>Tersedia</h4><h2>${goodStock}</h2></div>
            </div>
            <div class="stat-card border-warning">
                <div class="stat-icon orange"><i class="fas fa-exclamation"></i></div>
                <div class="stat-details"><h4>Menipis</h4><h2 style="color:${lowStockHerb > 0 ? 'var(--warning)' : 'var(--text-main)'}">${lowStockHerb}</h2></div>
            </div>
            <div class="stat-card border-danger">
                <div class="stat-icon red"><i class="fas fa-times"></i></div>
                <div class="stat-details"><h4>Habis</h4><h2 style="color:${outOfStock > 0 ? 'var(--danger)' : 'var(--text-main)'}">${outOfStock}</h2></div>
            </div>
        </div>

        <!-- ── Action Buttons ── -->
        <div class="stock-action-bar">
            <button type="button" class="btn btn-primary" data-herbal-action="open-add">
                <i class="fas fa-plus"></i> Tambah Produk
            </button>
            <button type="button" class="btn btn-primary btn-herbal-sale" data-herbal-action="open-sale">
                <i class="fas fa-cash-register"></i> Jual Produk
            </button>
            <button type="button" class="btn btn-secondary btn-secondary-auto" data-herbal-action="open-stock">
                <i class="fas fa-sliders-h"></i> Koreksi Stok
            </button>
            <button type="button" class="btn btn-secondary btn-secondary-auto" data-herbal-action="open-return">
                <i class="fas fa-undo"></i> Retur
            </button>
        </div>
        <div id="herbal-row-selection" class="table-selection-summary" aria-live="polite"></div>

        <!-- ── Tabel Monitoring Produk/Herbal (DI ATAS) ── -->
        <div class="card herbal-table-card">
            <div class="card-header">
                <h3><i class="fas fa-mortar-pestle"></i> Monitoring Produk / Herbal (${data.length} produk)</h3>
                <span class="table-hint-text"><i class="fas fa-hand-pointer"></i> Klik baris untuk pilih</span>
            </div>
            <div class="herbal-table-wrapper">
                <table id="herbals-table" class="herbal-table">
                    <thead>
                        <tr>
                            <th class="text-left">Produk</th>
                            <th class="text-center">Stok / Kemasan</th>
                            <th class="text-right">Harga</th>
                            <th class="text-right">Margin</th>
                            <th class="text-center">Status</th>
                            <th class="text-center">Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${paginatedData.length === 0
            ? `<tr><td colspan="6" class="table-empty-state">Belum ada produk / herbal.</td></tr>`
            : paginatedData.map((h: HerbalCatalogItem) => {
                const isEmpty = h.stock <= 0;
                const isLow = !isEmpty && h.stock <= (h.min_stock || 5);
                const stockColor = isEmpty ? 'var(--danger)' : isLow ? 'var(--warning)' : 'var(--success)';
                const rowBg = isEmpty ? 'bg-red-50' : isLow ? 'bg-amber-50' : '';
                const statusBadge = isEmpty
                    ? `<span class="herbal-status-badge empty">HABIS</span>`
                    : isLow
                        ? `<span class="herbal-status-badge low">MENIPIS</span>`
                        : `<span class="herbal-status-badge ok">OK</span>`;
                return `
                                    <tr data-id="${h.id}" data-name="${escapeHtml(h.name)}" data-stock="${h.stock}" data-price="${h.price}" data-unit="${escapeHtml(h.unit)}" data-package-unit="${escapeHtml(h.package_unit || '')}" data-package-size="${Number(h.package_size || 1)}"
                                        data-herbal-action="select-row"
                                        class="${rowBg} ${window._selectedHerbalId === h.id ? 'row-selected' : ''}" data-rowbg="${rowBg}">
                                        <td class="table-cell-name" title="${escapeHtml(h.name)}">${escapeHtml(h.name)}</td>
                                        <td class="table-cell-center">
                                            <span class="stock-display-main" style="color:${stockColor}">${escapeHtml(h.stock_display || h.stock)}</span>
                                            <span class="stock-display-sub" title="${escapeHtml(herbalPackageLabel(h))}">${escapeHtml(herbalPackageLabel(h))}</span>
                                        </td>
                                        <td class="table-cell-right">
                                            <span class="price-display-main">${formatRupiah(h.price)}</span>
                                            <span class="price-display-sub">Modal ${formatRupiah(h.cost_price || 0)}</span>
                                        </td>
                                        <td class="table-cell-right font-semibold" style="color:${Number(h.margin || 0) >= 0 ? 'var(--primary)' : 'var(--danger)'}">${formatRupiah(h.margin || 0)}</td>
                                        <td class="table-cell-center">${statusBadge}</td>
                                        <td class="table-cell-center">
                                            <div class="table-action-buttons">
                                                <button type="button" data-herbal-action="edit" data-id="${h.id}"
                                                        title="Edit Produk / Herbal"
                                                        class="table-icon-btn edit">
                                                    <i class="fas fa-edit"></i>
                                                </button>
                                                <button type="button" data-herbal-action="delete" data-id="${h.id}"
                                                        title="Hapus Produk / Herbal"
                                                        class="table-icon-btn delete">
                                                    <i class="fas fa-trash-alt"></i>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>`;
            }).join('')
        }
                    </tbody>
                </table>
            </div>
            ${totalPages > 1 ? `
            <div class="table-pagination">
                <span class="pagination-info">Halaman ${currentPage} dari ${totalPages}</span>
                <div class="pagination-buttons">
                    <button type="button" class="btn btn-secondary btn-secondary-auto" ${currentPage <= 1 ? 'disabled' : ''} data-herbal-action="page" data-page="${currentPage - 1}">
                        <i class="fas fa-chevron-left"></i> Sebelumnya
                    </button>
                    <button type="button" class="btn btn-secondary btn-secondary-auto" ${currentPage >= totalPages ? 'disabled' : ''} data-herbal-action="page" data-page="${currentPage + 1}">
                        Selanjutnya <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
            ` : ''}
        </div>

        <div class="card correction-history-card">
            <div class="card-header">
                <h3><i class="fas fa-history"></i> Riwayat Koreksi</h3>
                <span>Koreksi stok, retur, dan void invoice terakhir.</span>
            </div>
            <div id="correction-history-panel" class="correction-history-panel">
                Memuat riwayat koreksi...
            </div>
        </div>`;

    const displayArea = document.getElementById('display-area');
    if (displayArea) displayArea.innerHTML = html;
    updateHerbalSelectionSummary();
    loadCorrectionHistory();
}

// ── ROW SELECTION ─────────────────────────────────────────────────────────────
function selectHerbal(row: HTMLTableRowElement): void {
    // Deselect all
    document.querySelectorAll<HTMLTableRowElement>('#herbals-table tbody tr').forEach(r => {
        r.classList.remove('row-selected');
        r.style.background = '';
    });
    // Select clicked
    row.classList.add('row-selected');

    window._selectedHerbalId = Number(row.dataset.id || 0) || null;
    updateHerbalSelectionSummary();
}

// ── CRUD ACTIONS ─────────────────────────────────────────────────────────────

async function submitHerbalActionForm(event: SubmitEvent, endpoint: string): Promise<void> {
    event.preventDefault();
    const form = event.target as HTMLFormElement;
    const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    const originalText = submit?.innerHTML || '';
    if (submit) {
        submit.disabled = true;
        submit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
    }
    try {
        const response = await fetch(endpoint, { method: 'POST', body: new FormData(form) });
        const data = await response.json() as ApiResponse;
        if (!response.ok || data.status !== 'success') {
            throw new Error(herbalText(data.detail || data.message, 'Gagal menyimpan perubahan produk/herbal.'));
        }
        closeModal();
        showToast(data.message || 'Perubahan produk/herbal berhasil disimpan.', 'success');
        loadTab('herbals');
    } catch (error) {
        showToast(herbalErrorMessage(error), 'error');
        if (submit) {
            submit.disabled = false;
            submit.innerHTML = originalText;
        }
    }
}

function openAddHerbalModal(): void {
    const html = `
        <form class="action-modal-form" data-herbal-form-action="add">
            <div class="unit-help-note compact">Form ini selalu membuat produk baru. Gunakan satuan dasar untuk stok terkecil.</div>
            <div class="form-group">
                <label>Nama Produk / Herbal</label>
                <input type="text" name="name" required placeholder="Nama produk">
            </div>
            <div class="action-form-grid">
                <div class="form-group"><label>Satuan Dasar</label>${herbalUnitSelectHtml('unit', 'botol')}</div>
                <div class="form-group"><label>Satuan Kemasan</label>${herbalUnitSelectHtml('package_unit', '', true)}</div>
                <div class="form-group"><label>Stok Awal</label><input type="number" name="stock" required value="0" min="0"></div>
                <div class="form-group"><label>Isi per Kemasan</label><input type="number" name="package_size" required value="1" min="1"></div>
                <div class="form-group"><label>Harga Modal (Rp)</label><input type="number" name="cost_price" required value="0" min="0"></div>
                <div class="form-group"><label>Harga Jual (Rp)</label><input type="number" name="price" required placeholder="0" min="0"></div>
                <div class="form-group"><label>Batas Aman</label><input type="number" name="min_stock" required value="5" min="0"></div>
            </div>
            <div class="sale-modal-actions">
                <button type="button" class="btn btn-modal-cancel" data-herbal-action="close-modal">Batal</button>
                <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Simpan Produk</button>
            </div>
        </form>`;
    openModal('Tambah Produk', html);
}

async function submitAddHerbal(event: SubmitEvent): Promise<void> {
    await submitHerbalActionForm(event, '/add_herbal');
}

function filterHerbalPicker(context: string): void {
    const query = herbalText(herbalInput(`${context}-search`)?.value).toLowerCase();
    const select = herbalSelect(`${context}-select`);
    if (!select) return;
    const selectedId = Number(select.value || 0);
    const items = (window._herbalCatalog || []).filter(item => {
        const searchable = `${item.name} ${item.unit} ${item.stock} ${herbalStatus(item)} ${item.price}`.toLowerCase();
        return !query || searchable.includes(query);
    });
    select.innerHTML = herbalPickerOptions(items, selectedId);
    const empty = document.getElementById(`${context}-empty`);
    if (empty) {
        empty.textContent = items.length ? '' : 'Belum ada produk/peralatan tersedia.';
        empty.classList.toggle('hidden', items.length > 0);
    }
    if (!items.some(item => item.id === selectedId)) {
        const hidden = herbalInput(context === 'herbal-correction' ? 'herbal-selected-id' : `${context}-selected-id`);
        if (hidden) hidden.value = '';
    }
    selectHerbalPickerItem(context);
}

function selectHerbalPickerItem(context: string): void {
    const select = herbalSelect(`${context}-select`);
    const itemId = Number(select?.value || 0);
    const item = (window._herbalCatalog || []).find(candidate => candidate.id === itemId) || null;
    const info = document.getElementById(`${context}-info`);
    if (info) {
        info.innerHTML = item
            ? `<strong>${escapeHtml(item.name)}</strong><span>Stok ${item.stock} ${escapeHtml(item.unit)} &middot; ${formatRupiah(item.price)} &middot; ${escapeHtml(herbalStatus(item))}</span>`
            : 'Pilih produk untuk melihat stok, satuan, harga, dan status.';
        info.classList.toggle('has-selection', Boolean(item));
    }
    if (context === 'herbal-correction') {
        const selectedId = herbalInput('herbal-selected-id');
        if (selectedId) selectedId.value = item ? String(item.id) : '';
        const multiplier = herbalSelect('herbal-multiplier');
        if (multiplier) {
            multiplier.innerHTML = item ? `<option value="1">${escapeHtml(item.unit)}</option>` : '<option value="1">Satuan dasar</option>';
            if (item && item.package_unit && item.package_unit !== item.unit && item.package_size > 1) {
                multiplier.innerHTML += `<option value="${item.package_size}">${escapeHtml(item.package_unit)} (1 = ${item.package_size} ${escapeHtml(item.unit)})</option>`;
            }
        }
        updateHerbalStockPreview();
    } else if (context === 'herbal-sale') {
        onHerbalSaleSelectChange();
    }
}

function openHerbalStockModal(): void {
    const selectedId = selectedHerbal()?.id || null;
    const html = `
        <form class="action-modal-form" data-herbal-form-action="stock">
            ${herbalPickerHtml('herbal-correction', selectedId)}
            <input type="hidden" name="herbal_id" id="herbal-selected-id">
            <input type="hidden" name="change" id="herbal-change-input">
            <div class="form-group">
                <label>Jenis Pergerakan</label>
                <div class="stock-mode-picker" data-target="herbal">
                    <button type="button" class="active" data-mode="in" data-herbal-action="stock-mode"><i class="fas fa-arrow-down"></i> Tambah Stok</button>
                    <button type="button" data-mode="out" data-herbal-action="stock-mode"><i class="fas fa-arrow-up"></i> Koreksi Keluar</button>
                </div>
                <input type="hidden" id="herbal-stock-mode" value="in">
                <small class="unit-field-hint">Koreksi keluar hanya untuk penyesuaian fisik, bukan penjualan.</small>
            </div>
            <div class="action-form-grid">
                <div class="form-group">
                    <label>Jumlah</label>
                    <input type="number" required id="herbal-change-amount" min="1" data-herbal-action="stock-preview" placeholder="Contoh: 10">
                </div>
                <div class="form-group">
                    <label>Satuan Transaksi</label>
                    <select name="multiplier" id="herbal-multiplier" data-herbal-action="stock-preview"><option value="1">Satuan dasar</option></select>
                </div>
            </div>
            <div class="form-group">
                <label>Alasan Koreksi</label>
                <textarea name="reason" id="herbal-stock-reason" required minlength="5" rows="3" placeholder="Contoh: Stok opname atau barang rusak"></textarea>
            </div>
            <div id="herbal-stock-preview" class="stock-preview hidden"></div>
            <div class="sale-modal-actions">
                <button type="button" class="btn btn-modal-cancel" data-herbal-action="close-modal">Batal</button>
                <button type="submit" class="btn btn-primary"><i class="fas fa-check"></i> Terapkan Koreksi</button>
            </div>
        </form>`;
    openModal('Koreksi Stok Produk', html);
    selectHerbalPickerItem('herbal-correction');
}

async function submitHerbalStock(event: SubmitEvent): Promise<void> {
    prepareHerbalStockSubmit(event);
    if (event.defaultPrevented) return;
    event.preventDefault();
    if (!herbalInput('herbal-selected-id')?.value) {
        showToast('Pilih produk/herbal terlebih dahulu.', 'warning');
        return;
    }
    await submitHerbalActionForm(event, '/update_herbal');
}

function setHerbalStockMode(mode: HerbalStockMode | string): void {
    const cleanMode = mode === 'out' ? 'out' : 'in';
    const input = herbalInput('herbal-stock-mode');
    if (input) input.value = cleanMode;
    document.querySelectorAll<HTMLButtonElement>('.stock-mode-picker[data-target="herbal"] button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === cleanMode);
    });
    updateHerbalStockPreview();
}

function updateHerbalStockPreview(): void {
    const selected = herbalInput('herbal-selected-id')?.value;
    const amount = Math.max(0, Number(herbalInput('herbal-change-amount')?.value || 0));
    const multiplier = Math.max(1, Number(herbalSelect('herbal-multiplier')?.value || 1));
    const mode: HerbalStockMode = herbalInput('herbal-stock-mode')?.value === 'out' ? 'out' : 'in';
    const preview = document.getElementById('herbal-stock-preview');
    if (!preview) return;

    const action = mode === 'out' ? 'berkurang (bukan penjualan)' : 'bertambah';
    const total = amount * multiplier;
    const selectedUnit = herbalSelect('herbal-multiplier')?.selectedOptions?.[0]?.textContent || 'item';
    
    if (selected && amount > 0) {
        preview.classList.remove('hidden');
        preview.classList.toggle('danger', mode === 'out');
        preview.textContent = `Stok produk/herbal akan ${action}: ${amount} ${selectedUnit} = ${total} satuan dasar.`;
    } else {
        preview.classList.add('hidden');
    }
}

function prepareHerbalStockSubmit(event: SubmitEvent): void {
    const amount = Math.max(0, Number(herbalInput('herbal-change-amount')?.value || 0));
    const mode: HerbalStockMode = herbalInput('herbal-stock-mode')?.value === 'out' ? 'out' : 'in';
    const reason = (document.getElementById('herbal-stock-reason') as HTMLTextAreaElement | null)?.value.trim() || '';
    const hidden = herbalInput('herbal-change-input');
    if (hidden) hidden.value = String(mode === 'out' ? -amount : amount);
    if (amount <= 0) {
        event.preventDefault();
        showToast('Isi jumlah produk/herbal terlebih dahulu.', 'warning');
        return;
    }
    if (reason.length < 5) {
        event.preventDefault();
        showToast('Alasan koreksi wajib diisi minimal 5 karakter.', 'warning');
    }
}

function _selectedHerbalSaleItem(): HerbalCatalogItem | null {
    const id = Number(herbalSelect('herbal-sale-select')?.value || 0);
    return (window._herbalCatalog || []).find((h: HerbalCatalogItem) => h.id === id) || null;
}

function _herbalSaleUsedQty(herbalId: number): number {
    return (window._herbalSaleItems || [])
        .filter((item: HerbalSaleItem) => item.herbal_id === herbalId)
        .reduce((sum: number, item: HerbalSaleItem) => sum + item.quantity, 0);
}

function openHerbalSaleModal(): void {
    window._herbalSaleItems = [];
    const selectedId = selectedHerbal()?.id || null;
    const html = `
        <div class="form-group">
            <label>Nama Pembeli <span class="text-slate-400 text-[10px] normal-case">(opsional)</span></label>
            <input type="text" id="herbal-sale-buyer" placeholder="Nama pembeli / umum">
        </div>
        ${herbalPickerHtml('herbal-sale', selectedId)}
        <div id="herbal-sale-info" class="unit-field-hint">Pilih produk/herbal untuk melihat stok dan harga.</div>
        <div class="grid grid-cols-[minmax(0,1fr)_auto] gap-2">
            <input type="number" id="herbal-sale-qty" min="1" placeholder="Jumlah" data-herbal-action="sale-qty">
            <button type="button" class="btn btn-primary px-3 py-2 bg-green-600" data-herbal-action="sale-add"><i class="fas fa-plus"></i> Tambah</button>
        </div>
        <div id="herbal-sale-warning" class="sale-warning hidden"></div>
        <div id="herbal-sale-list" class="mt-3"></div>
        <div class="sale-total-row">
            <span class="sale-total-label">Total penjualan</span>
            <strong id="herbal-sale-total">Rp0</strong>
        </div>
        <div class="sale-modal-actions">
            <button type="button" class="btn btn-modal-cancel" data-herbal-action="close-modal">Batal</button>
            <button type="button" class="btn btn-primary btn-modal-save" data-herbal-action="sale-submit"><i class="fas fa-save"></i> Simpan Penjualan</button>
        </div>
    `;
    openModal('Penjualan Produk / Herbal', html);
    selectHerbalPickerItem('herbal-sale');
    syncHerbalSaleItems();
}

function onHerbalSaleSelectChange(): void {
    const herbal = _selectedHerbalSaleItem();
    const info = document.getElementById('herbal-sale-info');
    if (!info) return;
    if (!herbal) {
        info.textContent = 'Pilih produk/herbal untuk melihat stok dan harga.';
        return;
    }
    info.textContent = `${herbal.name} - stok ${herbal.stock} ${herbal.unit} - ${formatRupiah(herbal.price)}`;
    onHerbalSaleQtyInput();
}

function onHerbalSaleQtyInput(): void {
    const herbal = _selectedHerbalSaleItem();
    const qty = Number(herbalInput('herbal-sale-qty')?.value || 0);
    const warning = document.getElementById('herbal-sale-warning');
    if (!warning) return;
    warning.classList.add('hidden');
    warning.textContent = '';
    if (!herbal || qty <= 0) return;
    const used = _herbalSaleUsedQty(herbal.id);
    if (used + qty > herbal.stock) {
        warning.textContent = `Stok ${herbal.name} tidak cukup. Tersedia ${herbal.stock}, sudah dipilih ${used}.`;
        warning.classList.remove('hidden');
    }
}

function addHerbalSaleItem(): void {
    const herbal = _selectedHerbalSaleItem();
    const qtyInput = herbalInput('herbal-sale-qty');
    const qty = Number(qtyInput?.value || 0);
    if (!herbal) {
        showToast('Pilih produk/herbal terlebih dahulu.', 'warning');
        return;
    }
    if (!Number.isInteger(qty) || qty <= 0) {
        showToast('Jumlah penjualan produk/herbal harus lebih dari 0.', 'warning');
        return;
    }
    const used = _herbalSaleUsedQty(herbal.id);
    if (used + qty > herbal.stock) {
        showToast('Stok produk/herbal tidak cukup. Silakan cek ulang penjualan.', 'error');
        return;
    }
    const existing = (window._herbalSaleItems || []).find((item: HerbalSaleItem) => item.herbal_id === herbal.id);
    if (existing) {
        existing.quantity += qty;
    } else {
        const saleItems = window._herbalSaleItems || [];
        saleItems.push({
            herbal_id: herbal.id,
            name: herbal.name,
            quantity: qty,
            unit: herbal.unit,
            price: herbal.price,
            stock: herbal.stock
        });
        window._herbalSaleItems = saleItems;
    }
    if (qtyInput) qtyInput.value = '';
    syncHerbalSaleItems();
}

function removeHerbalSaleItem(herbalId: number): void {
    window._herbalSaleItems = (window._herbalSaleItems || []).filter((item: HerbalSaleItem) => item.herbal_id !== herbalId);
    syncHerbalSaleItems();
}

function _herbalSaleTotal(): number {
    return (window._herbalSaleItems || []).reduce((sum: number, item: HerbalSaleItem) => sum + Number(item.price || 0) * Number(item.quantity || 0), 0);
}

function syncHerbalSaleItems(): void {
    const list = document.getElementById('herbal-sale-list');
    const items = window._herbalSaleItems || [];
    if (list) {
        if (!items.length) {
            list.innerHTML = '<div class="text-xs text-app-muted p-2.5 bg-slate-50 rounded-md">Belum ada item penjualan.</div>';
        } else {
            list.innerHTML = items.map((item: HerbalSaleItem) => {
                const subtotal = Number(item.price || 0) * Number(item.quantity || 0);
                return `
                    <div class="sale-item-grid">
                        <div class="min-w-0">
                            <div class="sale-item-name">${escapeHtml(item.name)}</div>
                            <div class="sale-item-details">${escapeHtml(item.quantity)} ${escapeHtml(item.unit)} x ${formatRupiah(item.price)} = ${formatRupiah(subtotal)}</div>
                        </div>
                        <button type="button" data-herbal-action="sale-remove" data-id="${Number(item.herbal_id || 0)}" title="Hapus item" class="border-0 bg-red-100 text-red-800 rounded px-[7px] py-[5px] cursor-pointer"><i class="fas fa-trash"></i></button>
                    </div>`;
            }).join('');
        }
    }
    const total = document.getElementById('herbal-sale-total');
    if (total) total.textContent = formatRupiah(_herbalSaleTotal());
    onHerbalSaleQtyInput();
}

function validateHerbalSaleStock(): boolean {
    const items = window._herbalSaleItems || [];
    if (!items.length) {
        showToast('Minimal pilih satu produk/herbal untuk dijual.', 'warning');
        return false;
    }
    for (const item of items) {
        if (item.quantity > item.stock) {
            showToast('Stok produk/herbal tidak cukup. Silakan cek ulang penjualan.', 'error');
            return false;
        }
    }
    return true;
}

async function submitHerbalSale(): Promise<void> {
    if (!validateHerbalSaleStock()) return;
    const buyerName = herbalInput('herbal-sale-buyer')?.value.trim() || 'Umum';
    const lines = [`Pembeli: ${buyerName}`, ''];
    (window._herbalSaleItems || []).forEach((item: HerbalSaleItem) => {
        const subtotal = Number(item.price || 0) * Number(item.quantity || 0);
        lines.push(`- ${item.name} x${item.quantity} ${item.unit} = ${formatRupiah(subtotal)}`);
    });
    lines.push('', `Total: ${formatRupiah(_herbalSaleTotal())}`, 'Stok akan dikurangi setelah penjualan disimpan.');

    const ok = await showConfirm(lines.join('\n'), 'warning', {
        confirmText: 'Simpan Penjualan',
        cancelText: 'Batal',
        maxWidth: '460px'
    });
    if (!ok) return;

    const form = new FormData();
    form.append('buyer_name', buyerName === 'Umum' ? '' : buyerName);
    form.append('items', JSON.stringify((window._herbalSaleItems || []).map((item: HerbalSaleItem) => ({
        herbal_id: item.herbal_id,
        quantity: item.quantity
    }))));

    try {
        const response = await fetch('/herbals/sale', { method: 'POST', body: form });
        const data = await response.json() as ApiResponse;
        if (!response.ok || data.status !== 'success') {
            throw new Error(herbalText(data.detail || data.message, 'Gagal menyimpan penjualan produk/herbal.'));
        }
        closeModal();
        showToast(data.message, 'success');
        loadTab('herbals');
    } catch (error) {
        showToast(herbalErrorMessage(error), 'error');
    }
}

function _formatCorrectionDate(value: unknown): string {
    if (!value) return '-';
    const text = String(value);
    const date = new Date(text);
    if (Number.isNaN(date.getTime())) return text;
    return date.toLocaleString('id-ID', { dateStyle: 'short', timeStyle: 'short' });
}

async function loadCorrectionHistory(): Promise<void> {
    const panel = document.getElementById('correction-history-panel');
    if (!panel) return;
    try {
        const response = await fetch('/correction_logs?limit=20');
        const rows = await response.json() as CorrectionLogRow[] | ApiResponse;
        if (!response.ok) throw new Error(herbalText(Array.isArray(rows) ? '' : rows.detail, 'Gagal memuat riwayat koreksi.'));
        if (!Array.isArray(rows)) throw new Error('Gagal memuat riwayat koreksi.');
        if (!rows.length) {
            panel.innerHTML = '<div class="p-3 bg-slate-50 rounded-md">Belum ada riwayat koreksi.</div>';
            return;
        }
        const labelMap = {
            stock_correction: 'Koreksi Stok',
            return: 'Retur',
            void_invoice: 'Void Invoice'
        } as Record<string, string>;
        panel.innerHTML = `
            <div class="overflow-x-auto">
                <table class="w-full border-collapse text-xs">
                    <thead>
                        <tr class="bg-slate-50">
                            <th class="text-left p-[9px]">Tanggal</th>
                            <th class="text-left p-[9px]">Tipe</th>
                            <th class="text-left p-[9px]">Objek</th>
                            <th class="text-center p-[9px]">Stok</th>
                            <th class="text-left p-[9px]">Alasan</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows.map((row: CorrectionLogRow) => {
                            const stockText = row.stock_before === null || row.stock_after === null
                                ? '-'
                                : `${row.stock_before} -> ${row.stock_after}`;
                            const objectText = row.herbal_name || `${row.reference_type || '-'} #${row.reference_id || '-'}`;
                            return `
                                <tr class="border-b border-slate-100">
                                    <td class="p-[9px] text-app-muted">${escapeHtml(_formatCorrectionDate(row.created_at))}</td>
                                    <td class="p-[9px] font-bold">${escapeHtml(labelMap[row.action_type || ''] || row.action_type || '-')}</td>
                                    <td class="p-[9px]">${escapeHtml(objectText)}</td>
                                    <td class="p-[9px] text-center">${escapeHtml(stockText)}</td>
                                    <td class="p-[9px] text-app-muted">${escapeHtml(row.reason || '-')}</td>
                                </tr>`;
                        }).join('')}
                    </tbody>
                </table>
            </div>`;
    } catch (error) {
        panel.innerHTML = `<div class="p-3 bg-red-50 text-red-800 rounded-md">${escapeHtml(herbalErrorMessage(error))}</div>`;
    }
}

async function openHerbalReturnModal(): Promise<void> {
    const initialSearch = selectedHerbal()?.name || '';
    const html = `
        <div class="action-picker">
            <label>Transaksi Penjualan</label>
            <div class="action-picker-search">
                <i class="fas fa-search"></i>
                <input type="search" id="herbal-return-search" value="${escapeHtml(initialSearch)}"
                    placeholder="Cari produk atau tanggal transaksi" data-herbal-action="return-filter">
            </div>
            <select id="herbal-return-transaction" class="action-picker-results" size="4" data-herbal-action="return-sync">
                <option value="">Memuat transaksi...</option>
            </select>
            <div id="herbal-return-info" class="unit-field-hint">Pilih transaksi yang akan diretur.</div>
        </div>
        <div class="form-group">
            <label>Jumlah Retur</label>
            <input type="number" id="herbal-return-qty" min="1" required placeholder="Jumlah item">
        </div>
        <div class="form-group">
            <label>Alasan Retur</label>
            <textarea id="herbal-return-reason" rows="3" minlength="5" required placeholder="Contoh: Barang dikembalikan pelanggan"></textarea>
        </div>
        <div class="sale-modal-actions">
            <button type="button" class="btn btn-modal-cancel" data-herbal-action="close-modal">Batal</button>
            <button type="button" class="btn btn-primary bg-amber-600" data-herbal-action="return-submit"><i class="fas fa-undo"></i> Catat Retur</button>
        </div>
    `;
    openModal('Retur Penjualan Produk / Herbal', html);
    try {
        const response = await fetch('/herbals/transactions?page=1&page_size=50&transaction_type=sale');
        const payload = await response.json() as HerbalTransactionPayload;
        if (!response.ok) throw new Error(payload.detail || 'Gagal memuat transaksi penjualan.');
        const select = herbalSelect('herbal-return-transaction');
        const rows = payload.data || [];
        window._herbalReturnRows = rows;
        if (!select) return;
        filterHerbalReturnPicker();
    } catch (error) {
        const select = herbalSelect('herbal-return-transaction');
        if (select) select.innerHTML = `<option value="">${escapeHtml(herbalErrorMessage(error))}</option>`;
    }
}

function filterHerbalReturnPicker(): void {
    const query = herbalText(herbalInput('herbal-return-search')?.value).toLowerCase();
    const select = herbalSelect('herbal-return-transaction');
    if (!select) return;
    const rows = (window._herbalReturnRows || []).filter(row => {
        const searchable = `${row.herbal_name || ''} ${_formatCorrectionDate(row.date)} ${row.quantity || ''} ${row.total_price || ''}`.toLowerCase();
        return !query || searchable.includes(query);
    });
    select.innerHTML = rows.length ? rows.map((row: HerbalTransactionRow) => {
        const label = `${_formatCorrectionDate(row.date)} - ${row.herbal_name} x${row.quantity} - ${formatRupiah(row.total_price)}`;
        return `<option value="${escapeHtml(row.id)}" data-herbal-id="${escapeHtml(row.herbal_id)}" data-qty="${escapeHtml(row.quantity)}" data-name="${escapeHtml(row.herbal_name)}">${escapeHtml(label)}</option>`;
    }).join('') : '<option value="">Belum ada transaksi/produk tersedia.</option>';
    syncHerbalReturnInfo();
}

function syncHerbalReturnInfo(): void {
    const select = herbalSelect('herbal-return-transaction');
    const option = select?.options[select.selectedIndex];
    const info = document.getElementById('herbal-return-info');
    const qty = option?.dataset?.qty || '';
    const productId = Number(option?.dataset?.herbalId || 0);
    const product = (window._herbalCatalog || []).find(item => item.id === productId);
    if (!info) return;
    if (!qty) {
        info.textContent = 'Belum ada transaksi/produk tersedia.';
        return;
    }
    const stockDetail = product
        ? ` Stok saat ini ${product.stock} ${product.unit} (${herbalStatus(product)}).`
        : '';
    info.textContent = `Maksimal retur awal: ${qty} item.${stockDetail} Sistem tetap mengecek sisa retur di backend.`;
}

async function submitHerbalReturn(): Promise<void> {
    const transactionId = herbalSelect('herbal-return-transaction')?.value;
    const quantity = Number(herbalInput('herbal-return-qty')?.value || 0);
    const reason = (document.getElementById('herbal-return-reason') as HTMLTextAreaElement | null)?.value.trim() || '';
    if (!transactionId) {
        showToast('Pilih transaksi penjualan yang akan diretur.', 'warning');
        return;
    }
    if (!Number.isInteger(quantity) || quantity <= 0) {
        showToast('Jumlah retur harus lebih dari 0.', 'warning');
        return;
    }
    if (reason.length < 5) {
        showToast('Alasan retur wajib diisi minimal 5 karakter.', 'warning');
        return;
    }
    const ok = await showConfirm('Catat retur ini dan kembalikan stok produk/herbal?', 'warning', {
        confirmText: 'Catat Retur',
        cancelText: 'Batal',
        maxWidth: '420px'
    });
    if (!ok) return;
    const form = new FormData();
    form.append('transaction_id', transactionId);
    form.append('quantity', String(quantity));
    form.append('reason', reason);
    try {
        const response = await fetch('/herbals/return', { method: 'POST', body: form });
        const data = await response.json() as ApiResponse;
        if (!response.ok || data.status !== 'success') {
            throw new Error(herbalText(data.detail || data.message, 'Gagal mencatat retur.'));
        }
        closeModal();
        showToast(data.message, 'success');
        loadTab('herbals');
    } catch (error) {
        showToast(herbalErrorMessage(error), 'error');
    }
}

function editHerbal(
    id: number | string,
    name: string,
    unit: string,
    price: number | string,
    stock: number | string,
    costPrice: number | string = 0,
    packageUnit = '',
    packageSize: number | string = 1,
    minStock: number | string = 5
): void {
    const html = `
        <form id="edit-herbal-form" data-herbal-form-action="edit">
            <input type="hidden" name="herbal_id" value="${id}">
            <div class="unit-help-note compact">
                <strong>Satuan dasar</strong> adalah stok terkecil. <strong>Satuan kemasan</strong> adalah bungkus besar. Contoh: dasar botol, kemasan box, isi 12.
            </div>
            <div class="form-group">
                <label>Nama Produk / Herbal</label>
                <input type="text" name="name" value="${escapeHtml(name)}" required>
            </div>
            <div class="form-group">
                <label>Satuan Dasar</label>
                ${herbalUnitSelectHtml('unit', unit)}
            </div>
            <div class="grid grid-cols-2 gap-2.5">
                <div class="form-group">
                    <label>Satuan Kemasan</label>
                    ${herbalUnitSelectHtml('package_unit', packageUnit, true)}
                </div>
                <div class="form-group">
                    <label>Isi per Kemasan</label>
                    <input type="number" name="package_size" value="${Number(packageSize || 1)}" required min="1">
                </div>
            </div>
            <div class="grid grid-cols-2 gap-2.5">
                <div class="form-group">
                    <label>Stok</label>
                    <input type="number" name="stock" value="${stock}" required min="0">
                </div>
                <div class="form-group">
                    <label>Modal (Rp)</label>
                    <input type="number" name="cost_price" value="${Number(costPrice || 0)}" required min="0">
                </div>
                <div class="form-group">
                    <label>Harga (Rp)</label>
                    <input type="number" name="price" value="${price}" required min="0">
                </div>
                <div class="form-group">
                    <label>Batas Aman</label>
                    <input type="number" name="min_stock" value="${Number(minStock || 5)}" required min="0">
                </div>
            </div>
            <div class="sale-modal-actions">
                <button type="button" class="btn btn-modal-cancel" data-herbal-action="close-modal">Batal</button>
                <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Simpan</button>
            </div>
        </form>
    `;
    openModal('Edit Produk / Herbal', html);
}

function editHerbalFromCache(id: number | string): void {
    const item = herbalById(id);
    if (!item) {
        showToast('Produk/herbal tidak ditemukan. Muat ulang data lalu coba lagi.', 'error');
        return;
    }
    editHerbal(
        item.id,
        item.name,
        item.unit,
        item.price,
        item.stock,
        item.cost_price,
        item.package_unit || '',
        item.package_size || 1,
        item.min_stock || 5
    );
}

async function submitEditHerbal(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    const form = event.target as HTMLFormElement;
    const formData = new FormData(form);

    // Disable button during submit
    const btn = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    if (!btn) return;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
    btn.disabled = true;

    try {
        const response = await fetch('/edit_herbal', {
            method: 'POST',
            body: formData
        });
        const data = await response.json() as ApiResponse;

        if (data.status === 'success') {
            closeModal();
            showToast(data.message, 'success');
            loadTab('herbals');
        } else {
            showToast(data.message || data.detail || 'Gagal menyimpan perubahan.', 'error');
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    } catch (err) {
        showToast('Koneksi gagal saat menyimpan perubahan.', 'error');
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function deleteHerbal(id: number | string, name: string): Promise<void> {
    const decodedName = new DOMParser().parseFromString(name, 'text/html').documentElement.textContent;
    if (await showConfirm(`Apakah Anda yakin ingin menghapus produk/herbal "${decodedName}"?`)) {
        const formData = new FormData();
        formData.append('herbal_id', String(id));

        fetch('/delete_herbal', {
            method: 'POST',
            body: formData
        })
            .then(res => res.json())
            .then((data: ApiResponse) => {
                if (data.status === 'success') {
                    showToast(data.message, 'success');
                    loadTab('herbals');
                } else {
                    showToast(data.message || data.detail || 'Gagal menghapus produk/herbal.', 'error');
                }
            })
            .catch(() => showToast('Koneksi gagal saat menghapus produk/herbal.', 'error'));
    }
}

async function deleteHerbalFromCache(id: number | string): Promise<void> {
    const item = herbalById(id);
    await deleteHerbal(id, item?.name || 'produk/herbal');
}

function goToHerbalPage(page: number): void {
    (window as any)._herbalPage = page;
    loadTab('herbals');
}

window.renderHerbals = renderHerbals;
window.selectHerbal = selectHerbal;
window.goToHerbalPage = goToHerbalPage;
window.setHerbalStockMode = setHerbalStockMode;
window.updateHerbalStockPreview = updateHerbalStockPreview;
window.prepareHerbalStockSubmit = prepareHerbalStockSubmit;
window.openHerbalSaleModal = openHerbalSaleModal;
window.onHerbalSaleSelectChange = onHerbalSaleSelectChange;
window.onHerbalSaleQtyInput = onHerbalSaleQtyInput;
window.addHerbalSaleItem = addHerbalSaleItem;
window.removeHerbalSaleItem = removeHerbalSaleItem;
window.submitHerbalSale = submitHerbalSale;
window.openHerbalReturnModal = openHerbalReturnModal;
window.filterHerbalReturnPicker = filterHerbalReturnPicker;
window.syncHerbalReturnInfo = syncHerbalReturnInfo;
window.submitHerbalReturn = submitHerbalReturn;
window.editHerbal = editHerbal;
window.submitEditHerbal = submitEditHerbal;
window.deleteHerbal = deleteHerbal;
window.openAddHerbalModal = openAddHerbalModal;
window.submitAddHerbal = submitAddHerbal;
window.openHerbalStockModal = openHerbalStockModal;
window.submitHerbalStock = submitHerbalStock;
window.filterHerbalPicker = filterHerbalPicker;
window.selectHerbalPickerItem = selectHerbalPickerItem;
