"use strict";
// ─── INVENTORY ────────────────────────────────────────────────────────────────
// Action-based workspace: table-first selection with focused modal workflows.
const INVENTORY_UNIT_OPTIONS = ['pcs', 'unit', 'ml', 'gr', 'botol', 'saset', 'box', 'pack', 'strip', 'tablet', 'kapsul', 'dus'];
let inventoryDelegationReady = false;
function inventoryItemType(value) {
    const normalized = String(value || 'consumable').trim().toLowerCase().replace(/[\s-]+/g, '_');
    return normalized === 'non_consumable' || normalized === 'nonconsumable' || normalized === 'asset' || normalized === 'reusable'
        ? 'non_consumable'
        : 'consumable';
}
function inventoryItemTypeLabel(value) {
    return inventoryItemType(value) === 'non_consumable' ? 'Non Consumable' : 'Consumable';
}
function inventoryStockBadge(label, iconClass, badgeClass) {
    return `<span class="badge ${badgeClass} inventory-badge">${iconClass ? `<i class="${iconClass}"></i>` : ''}${escapeHtml(label)}</span>`;
}
function goToInventoryPage(page) {
    window._inventoryPage = page;
    loadTab('inventory');
}
function inventoryItemTypeSelect(value = 'consumable') {
    const selected = inventoryItemType(value);
    return `
        <select name="item_type">
            <option value="consumable" ${selected === 'consumable' ? 'selected' : ''}>Consumable - habis terpakai</option>
            <option value="non_consumable" ${selected === 'non_consumable' ? 'selected' : ''}>Non-consumable - aset/peralatan</option>
        </select>
        <small class="unit-field-hint">Auto-deduct layanan hanya memotong item consumable.</small>
    `;
}
function inventoryText(value, fallback = '') {
    const text = String(value ?? '').trim();
    return text || fallback;
}
function inventoryNumber(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}
function inventoryPackageMeta(item) {
    const unit = inventoryText(item.unit, 'pcs');
    const packageUnit = inventoryText(item.package_unit ?? item.packageUnit);
    const packageSize = Math.max(1, inventoryNumber(item.package_size ?? item.packageSize, 1));
    return { unit, packageUnit, packageSize };
}
function unitSelectHtml(name, value = '', includeEmpty = false) {
    const options = (includeEmpty ? [''] : []).concat(INVENTORY_UNIT_OPTIONS);
    return `<select name="${name}">${options.map(opt => {
        const label = opt || '- Tidak ada -';
        return `<option value="${escapeHtml(opt)}" ${opt === value ? 'selected' : ''}>${escapeHtml(label)}</option>`;
    }).join('')}</select>`;
}
function packageLabel(item) {
    const { unit, packageUnit, packageSize } = inventoryPackageMeta(item);
    if (!packageUnit)
        return unit || '-';
    if (packageSize <= 1)
        return packageUnit;
    return `1 ${packageUnit} = ${packageSize} ${unit}`;
}
function inventoryStatus(item) {
    return Number(item.quantity || 0) <= Number(item.min_stock || 0) ? 'Kritis' : 'Aman';
}
function selectedInventory() {
    const selectedId = Number(window._selectedInventoryId || 0);
    return (window._inventoryCatalog || []).find(item => Number(item.id) === selectedId) || null;
}
function inventoryById(id) {
    const itemId = Number(id || 0);
    return (window._inventoryCatalog || []).find(item => Number(item.id) === itemId) || null;
}
function ensureInventoryEventDelegation() {
    if (inventoryDelegationReady)
        return;
    inventoryDelegationReady = true;
    document.addEventListener('click', (event) => {
        const actionElement = event.target?.closest('[data-inventory-action]');
        if (!actionElement)
            return;
        const action = actionElement.dataset.inventoryAction || '';
        if (!action)
            return;
        event.preventDefault();
        switch (action) {
            case 'open-add':
                openAddInventoryModal();
                break;
            case 'open-stock':
                openInventoryStockModal();
                break;
            case 'select-row':
                selectInventory(actionElement);
                break;
            case 'edit':
                editInventoryFromCache(actionElement.dataset.id || '');
                break;
            case 'delete':
                deleteInventoryFromCache(actionElement.dataset.id || '');
                break;
            case 'page':
                goToInventoryPage(Number(actionElement.dataset.page || 1));
                break;
            case 'close-modal':
                closeModal();
                break;
            case 'stock-mode':
                setInventoryStockMode(actionElement.dataset.mode || 'in');
                break;
        }
    });
    document.addEventListener('input', (event) => {
        const target = event.target;
        const action = target?.dataset?.inventoryAction || '';
        if (action === 'picker-filter')
            filterInventoryPicker();
        if (action === 'stock-preview')
            updateInventoryStockPreview();
    });
    document.addEventListener('change', (event) => {
        const target = event.target;
        const action = target?.dataset?.inventoryAction || '';
        if (action === 'picker-select')
            selectInventoryPickerItem();
        if (action === 'stock-preview')
            updateInventoryStockPreview();
    });
    document.addEventListener('submit', (event) => {
        const form = event.target;
        const action = form?.dataset?.inventoryFormAction || '';
        if (action === 'add')
            submitAddInventory(event);
        if (action === 'stock')
            submitInventoryStock(event);
        if (action === 'edit')
            submitEditInventory(event);
    });
}
function inventoryPickerOptions(items, selectedId) {
    if (!items.length)
        return '<option value="">Belum ada produk/peralatan tersedia.</option>';
    const prompt = selectedId ? '' : '<option value="" selected>Pilih peralatan</option>';
    return prompt + items.map(item => {
        const { unit } = inventoryPackageMeta(item);
        const selected = Number(item.id) === selectedId ? ' selected' : '';
        const label = `${item.item_name || item.name || '-'} | ${inventoryItemTypeLabel(item.item_type)} | ${inventoryStatus(item)} | stok ${Number(item.quantity || 0)} ${unit}`;
        return `<option value="${escapeHtml(item.id)}"${selected}>${escapeHtml(label)}</option>`;
    }).join('');
}
function inventoryPickerHtml(selectedId) {
    const items = window._inventoryCatalog || [];
    return `
        <div class="action-picker">
            <label for="inventory-correction-search">Cari Peralatan</label>
            <div class="action-picker-search">
                <i class="fas fa-search"></i>
                <input type="search" id="inventory-correction-search" autocomplete="off"
                    placeholder="Nama, jenis, stok, status, atau satuan"
                    data-inventory-action="picker-filter">
            </div>
            <select id="inventory-correction-select" class="action-picker-results" size="4"
                data-inventory-action="picker-select">
                ${inventoryPickerOptions(items, selectedId)}
            </select>
            <div id="inventory-correction-empty" class="action-picker-empty ${items.length ? 'hidden' : ''}">Belum ada produk/peralatan tersedia.</div>
            <div id="inventory-correction-info" class="selected-item-summary"></div>
        </div>`;
}
function updateInventorySelectionSummary() {
    const item = selectedInventory();
    const summary = document.getElementById('inventory-row-selection');
    if (!summary)
        return;
    if (!item) {
        summary.innerHTML = '<i class="fas fa-hand-pointer"></i> Pilih row untuk mengisi action secara otomatis, atau buka action dan cari peralatan.';
        summary.classList.remove('has-selection');
        return;
    }
    const { unit } = inventoryPackageMeta(item);
    summary.innerHTML = `<i class="fas fa-check-circle"></i> <strong>${escapeHtml(item.item_name || item.name || '-')}</strong><span>Stok ${Number(item.quantity || 0)} ${escapeHtml(unit)} &middot; ${escapeHtml(inventoryItemTypeLabel(item.item_type))} &middot; ${escapeHtml(inventoryStatus(item))}</span>`;
    summary.classList.add('has-selection');
}
function renderInventory(data) {
    ensureInventoryEventDelegation();
    window._inventoryCatalog = data || [];
    if (window._selectedInventoryId && !selectedInventory())
        window._selectedInventoryId = null;
    const criticalCount = data.filter(i => Number(i.quantity || 0) <= Number(i.min_stock || 0)).length;
    const safeCount = data.length - criticalCount;
    // Pagination
    const currentPage = window._inventoryPage || 1;
    const itemsPerPage = 10;
    const totalPages = Math.ceil(data.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedData = data.slice(startIndex, endIndex);
    const html = `
        <!-- ── Stat Cards ── -->
        <div class="inventory-stats-grid">
            <div class="stat-card border-success">
                <div class="stat-icon green"><i class="fas fa-check-circle"></i></div>
                <div class="stat-details"><h4>Stok Aman</h4><h2>${safeCount}</h2></div>
            </div>
            <div class="stat-card border-warning">
                <div class="stat-icon orange"><i class="fas fa-exclamation-triangle"></i></div>
                <div class="stat-details"><h4>Stok Kritis</h4><h2 style="color:${criticalCount > 0 ? 'var(--warning)' : 'var(--text-main)'}">${criticalCount}</h2></div>
            </div>
        </div>

        <div class="stock-action-bar">
            <button type="button" class="btn btn-primary" data-inventory-action="open-add">
                <i class="fas fa-plus"></i> Tambah Peralatan
            </button>
            <button type="button" class="btn btn-secondary btn-secondary-auto" data-inventory-action="open-stock">
                <i class="fas fa-sliders-h"></i> Koreksi / Update Stok
            </button>
        </div>
        <div id="inventory-row-selection" class="table-selection-summary" aria-live="polite"></div>

        <!-- ── Tabel Monitoring Stok (DI ATAS) ── -->
        <div class="card inventory-table-card">
            <div class="card-header">
                <h3><i class="fas fa-clipboard-list"></i> Monitoring Stok (${data.length} item)</h3>
                <span class="table-hint-text"><i class="fas fa-hand-pointer"></i> Klik baris untuk pilih</span>
            </div>
            <div class="inventory-table-wrapper">
                <table id="inventory-table" class="inventory-table">
                    <thead>
                        <tr>
                            <th class="text-left">Nama Peralatan</th>
                            <th class="text-center">Jenis</th>
                            <th class="text-center">Stok / Kemasan</th>
                            <th class="text-center">Batas</th>
                            <th class="text-center">Progress</th>
                            <th class="text-center">Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${paginatedData.length === 0
        ? `<tr><td colspan="6" class="table-empty-state">Inventori masih kosong.</td></tr>`
        : paginatedData.map(i => {
            const quantity = Number(i.quantity || 0);
            const minStock = Number(i.min_stock || 0);
            const itemType = inventoryItemType(i.item_type);
            const { unit, packageUnit, packageSize } = inventoryPackageMeta(i);
            const isLow = quantity <= minStock;
            const pct = minStock > 0 ? Math.min(100, Math.round(quantity / minStock * 100)) : 100;
            const barColor = isLow ? 'var(--danger)' : (pct < 150 ? 'var(--warning)' : 'var(--success)');
            const statusBadge = isLow
                ? inventoryStockBadge('Kritis', 'fas fa-exclamation-triangle', 'badge-low')
                : inventoryStockBadge('Aman', 'fas fa-check-circle', 'badge-ok');
            const typeBadge = inventoryStockBadge(inventoryItemTypeLabel(itemType), '', itemType === 'consumable' ? 'badge-ok' : 'badge-low');
            return `
                                <tr data-id="${i.id}" data-name="${escapeHtml(i.item_name)}" data-type="${itemType}" data-qty="${quantity}" data-min="${minStock}" data-unit="${escapeHtml(unit)}" data-package-unit="${escapeHtml(packageUnit)}" data-package-size="${packageSize}"
                                    data-inventory-action="select-row" class="${window._selectedInventoryId === Number(i.id) ? 'row-selected' : ''}">
                                    <td class="table-cell-name" title="${escapeHtml(i.item_name)}">${escapeHtml(i.item_name)}</td>
                                    <td class="table-cell-center">
                                        ${typeBadge}
                                    </td>
                                    <td class="table-cell-center">
                                        <span class="stock-display-main" style="color:${isLow ? 'var(--danger)' : 'var(--text-main)'}">${escapeHtml(i.stock_display || i.quantity)}</span>
                                        <span class="stock-display-sub" title="${escapeHtml(packageLabel(i))}">${escapeHtml(packageLabel(i))}</span>
                                    </td>
                                    <td class="table-cell-center text-app-muted">${minStock} ${escapeHtml(unit)}</td>
                                    <td class="table-cell-center">
                                        <div class="stock-progress-bar">
                                            <div class="stock-progress-fill" style="width:${Math.min(100, pct)}%;background:${barColor}"></div>
                                        </div>
                                    </td>
                                    <td class="table-cell-center">
                                        <div class="table-action-buttons">
                                            <button type="button" data-inventory-action="edit" data-id="${i.id}"
                                                    title="Edit Alat"
                                                    class="table-icon-btn edit">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                            <button type="button" data-inventory-action="delete" data-id="${i.id}"
                                                    title="Hapus Alat"
                                                    class="table-icon-btn delete">
                                                <i class="fas fa-trash-alt"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>`;
        }).join('')}
                    </tbody>
                </table>
            </div>
            ${totalPages > 1 ? `
            <div class="table-pagination">
                <span class="pagination-info">Halaman ${currentPage} dari ${totalPages}</span>
                <div class="pagination-buttons">
                    <button type="button" class="btn btn-secondary btn-secondary-auto" ${currentPage <= 1 ? 'disabled' : ''} data-inventory-action="page" data-page="${currentPage - 1}">
                        <i class="fas fa-chevron-left"></i> Sebelumnya
                    </button>
                    <button type="button" class="btn btn-secondary btn-secondary-auto" ${currentPage >= totalPages ? 'disabled' : ''} data-inventory-action="page" data-page="${currentPage + 1}">
                        Selanjutnya <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
            ` : ''}
        </div>

        `;
    const displayArea = document.getElementById('display-area');
    if (displayArea)
        displayArea.innerHTML = html;
    updateInventorySelectionSummary();
}
// ── ROW SELECTION ─────────────────────────────────────────────────────────────
function selectInventory(row) {
    // Deselect all
    document.querySelectorAll('#inventory-table tbody tr').forEach(r => {
        const rowEl = r;
        rowEl.classList.remove('row-selected');
        rowEl.style.background = '';
    });
    // Select clicked
    row.classList.add('row-selected');
    window._selectedInventoryId = Number(row.dataset.id || 0) || null;
    updateInventorySelectionSummary();
}
// ── CRUD ACTIONS ─────────────────────────────────────────────────────────────
async function submitInventoryActionForm(event, endpoint) {
    event.preventDefault();
    const form = event.target;
    const submit = form.querySelector('button[type="submit"]');
    const originalText = submit?.innerHTML || '';
    if (submit) {
        submit.disabled = true;
        submit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
    }
    try {
        const response = await fetch(endpoint, { method: 'POST', body: new FormData(form) });
        const data = await response.json();
        if (!response.ok || data.status !== 'success') {
            throw new Error(inventoryText(data.detail || data.message, 'Gagal menyimpan perubahan inventory.'));
        }
        closeModal();
        showToast(data.message || 'Perubahan inventory berhasil disimpan.', 'success');
        loadTab('inventory');
    }
    catch (error) {
        showToast(error instanceof Error ? error.message : 'Gagal menyimpan perubahan inventory.', 'error');
        if (submit) {
            submit.disabled = false;
            submit.innerHTML = originalText;
        }
    }
}
function openAddInventoryModal() {
    const html = `
        <form class="action-modal-form" data-inventory-form-action="add">
            <div class="unit-help-note compact">Form ini selalu membuat item baru. Auto-deduct layanan hanya berlaku untuk item consumable.</div>
            <div class="form-group">
                <label>Nama Peralatan</label>
                <input type="text" name="item_name" required placeholder="Alkohol, kapas">
            </div>
            <div class="form-group">
                <label>Jenis Item</label>
                ${inventoryItemTypeSelect('consumable')}
            </div>
            <div class="action-form-grid">
                <div class="form-group"><label>Satuan Dasar</label>${unitSelectHtml('unit', 'pcs')}</div>
                <div class="form-group"><label>Satuan Kemasan</label>${unitSelectHtml('package_unit', '', true)}</div>
                <div class="form-group"><label>Stok Awal</label><input type="number" name="initial_qty" required value="0" min="0"></div>
                <div class="form-group"><label>Batas Aman</label><input type="number" name="min_stock" required value="10" min="0"></div>
                <div class="form-group"><label>Isi per Kemasan</label><input type="number" name="package_size" required value="1" min="1"></div>
            </div>
            <div class="sale-modal-actions">
                <button type="button" class="btn btn-modal-cancel" data-inventory-action="close-modal">Batal</button>
                <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Simpan Peralatan</button>
            </div>
        </form>`;
    openModal('Tambah Peralatan', html);
}
async function submitAddInventory(event) {
    await submitInventoryActionForm(event, '/add_inventory');
}
function filterInventoryPicker() {
    const query = inventoryText(document.getElementById('inventory-correction-search')?.value).toLowerCase();
    const select = document.getElementById('inventory-correction-select');
    if (!select)
        return;
    const selectedId = Number(select.value || 0);
    const items = (window._inventoryCatalog || []).filter(item => {
        const { unit } = inventoryPackageMeta(item);
        const searchable = `${item.item_name || item.name || ''} ${inventoryItemTypeLabel(item.item_type)} ${Number(item.quantity || 0)} ${unit} ${inventoryStatus(item)}`.toLowerCase();
        return !query || searchable.includes(query);
    });
    select.innerHTML = inventoryPickerOptions(items, selectedId);
    const empty = document.getElementById('inventory-correction-empty');
    if (empty) {
        empty.textContent = items.length ? '' : 'Belum ada produk/peralatan tersedia.';
        empty.classList.toggle('hidden', items.length > 0);
    }
    selectInventoryPickerItem();
}
function selectInventoryPickerItem() {
    const select = document.getElementById('inventory-correction-select');
    const itemId = Number(select?.value || 0);
    const item = (window._inventoryCatalog || []).find(candidate => Number(candidate.id) === itemId) || null;
    const info = document.getElementById('inventory-correction-info');
    if (info) {
        const { unit } = item ? inventoryPackageMeta(item) : { unit: '' };
        info.innerHTML = item
            ? `<strong>${escapeHtml(item.item_name || item.name || '-')}</strong><span>Stok ${Number(item.quantity || 0)} ${escapeHtml(unit)} &middot; ${escapeHtml(inventoryItemTypeLabel(item.item_type))} &middot; ${escapeHtml(inventoryStatus(item))}</span>`
            : 'Pilih peralatan untuk melihat stok, satuan, jenis, dan status.';
        info.classList.toggle('has-selection', Boolean(item));
    }
    const selectedInput = document.getElementById('inv-selected-id');
    if (selectedInput)
        selectedInput.value = item ? String(item.id) : '';
    const multiplier = document.getElementById('inv-multiplier');
    if (multiplier) {
        multiplier.innerHTML = item ? `<option value="1">${escapeHtml(inventoryPackageMeta(item).unit)}</option>` : '<option value="1">Satuan dasar</option>';
        if (item) {
            const { unit, packageUnit, packageSize } = inventoryPackageMeta(item);
            if (packageUnit && packageUnit !== unit && packageSize > 1) {
                multiplier.innerHTML += `<option value="${packageSize}">${escapeHtml(packageUnit)} (1 = ${packageSize} ${escapeHtml(unit)})</option>`;
            }
        }
    }
    updateInventoryStockPreview();
}
function openInventoryStockModal() {
    const selectedId = Number(selectedInventory()?.id || 0) || null;
    const html = `
        <form class="action-modal-form" data-inventory-form-action="stock">
            ${inventoryPickerHtml(selectedId)}
            <input type="hidden" name="item_id" id="inv-selected-id">
            <input type="hidden" name="quantity_change" id="inv-change-input">
            <div class="form-group">
                <label>Jenis Pergerakan</label>
                <div class="stock-mode-picker" data-target="inventory">
                    <button type="button" class="active" data-mode="in" data-inventory-action="stock-mode"><i class="fas fa-arrow-down"></i> Tambah Stok</button>
                    <button type="button" data-mode="out" data-inventory-action="stock-mode"><i class="fas fa-arrow-up"></i> Koreksi Keluar</button>
                </div>
                <input type="hidden" id="inv-stock-mode" value="in">
                <small class="unit-field-hint">Gunakan koreksi keluar hanya untuk penyesuaian stok fisik di luar layanan normal.</small>
            </div>
            <div class="action-form-grid">
                <div class="form-group">
                    <label>Jumlah</label>
                    <input type="number" required id="inv-change-amount" min="1" placeholder="Contoh: 10" data-inventory-action="stock-preview">
                </div>
                <div class="form-group">
                    <label>Satuan Transaksi</label>
                    <select name="multiplier" id="inv-multiplier" data-inventory-action="stock-preview"><option value="1">Satuan dasar</option></select>
                </div>
            </div>
            <div class="form-group">
                <label>Catatan Koreksi</label>
                <textarea name="note" id="inv-stock-note" rows="2" placeholder="Contoh: Stok opname atau barang rusak"></textarea>
            </div>
            <div id="inv-stock-preview" class="stock-preview hidden"></div>
            <div class="sale-modal-actions">
                <button type="button" class="btn btn-modal-cancel" data-inventory-action="close-modal">Batal</button>
                <button type="submit" class="btn btn-primary"><i class="fas fa-check"></i> Terapkan Koreksi</button>
            </div>
        </form>`;
    openModal('Koreksi / Update Stok Peralatan', html);
    selectInventoryPickerItem();
}
async function submitInventoryStock(event) {
    prepareInventoryStockSubmit(event);
    if (event.defaultPrevented)
        return;
    event.preventDefault();
    const selectedId = document.getElementById('inv-selected-id');
    if (!selectedId?.value) {
        showToast('Pilih peralatan terlebih dahulu.', 'warning');
        return;
    }
    await submitInventoryActionForm(event, '/update_inventory');
}
function setInventoryStockMode(mode) {
    const cleanMode = mode === 'out' ? 'out' : 'in';
    const input = document.getElementById('inv-stock-mode');
    if (input)
        input.value = cleanMode;
    document.querySelectorAll('.stock-mode-picker[data-target="inventory"] button').forEach(btn => {
        const modeButton = btn;
        modeButton.classList.toggle('active', modeButton.dataset.mode === cleanMode);
    });
    updateInventoryStockPreview();
}
function updateInventoryStockPreview() {
    const selectedInput = document.getElementById('inv-selected-id');
    const amountInput = document.getElementById('inv-change-amount');
    const multiplierSelect = document.getElementById('inv-multiplier');
    const modeInput = document.getElementById('inv-stock-mode');
    const selected = selectedInput?.value;
    const amount = Math.max(0, Number(amountInput?.value || 0));
    const multiplier = Math.max(1, Number(multiplierSelect?.value || 1));
    const mode = modeInput?.value === 'out' ? 'out' : 'in';
    const preview = document.getElementById('inv-stock-preview');
    if (!preview)
        return;
    const total = amount * multiplier;
    const action = mode === 'out' ? 'keluar/terpakai' : 'masuk';
    const selectedUnit = multiplierSelect?.selectedOptions?.[0]?.textContent || 'satuan';
    preview.classList.toggle('danger', mode === 'out');
    if (selected && total > 0) {
        preview.textContent = `Stok akan ${action}: ${amount} ${selectedUnit} = ${total} satuan dasar.`;
        preview.classList.remove('hidden');
    }
    else {
        preview.textContent = 'Pilih item, jenis pergerakan, dan jumlah.';
        preview.classList.add('hidden');
    }
}
function prepareInventoryStockSubmit(event) {
    const amountInput = document.getElementById('inv-change-amount');
    const modeInput = document.getElementById('inv-stock-mode');
    const multiplierSelect = document.getElementById('inv-multiplier');
    const amount = Math.max(0, Number(amountInput?.value || 0));
    const mode = modeInput?.value === 'out' ? 'out' : 'in';
    const hidden = document.getElementById('inv-change-input');
    const note = document.getElementById('inv-stock-note');
    if (hidden)
        hidden.value = String(mode === 'out' ? -amount : amount);
    if (note && !note.value.trim())
        note.value = `${mode === 'out' ? 'Keluar' : 'Masuk'} ${amount} ${multiplierSelect?.selectedOptions?.[0]?.textContent || 'satuan'}`;
    if (amount <= 0) {
        event.preventDefault();
        showToast('Isi jumlah barang terlebih dahulu.', 'warning');
    }
}
function editInventory(id, name, qty, unit, minStock, packageUnit = '', packageSize = 1, itemType = 'consumable') {
    const html = `
        <form id="edit-inventory-form" data-inventory-form-action="edit">
            <input type="hidden" name="item_id" value="${id}">
            <div class="unit-help-note compact">
                <strong>Satuan dasar</strong> adalah stok terkecil. <strong>Satuan kemasan</strong> adalah bungkus besar. Contoh: dasar pcs, kemasan box, isi 100.
            </div>
            <div class="form-group">
                <label>Nama Alat</label>
                <input type="text" name="item_name" value="${escapeHtml(name)}" required>
            </div>
            <div class="form-group">
                <label>Jenis Item</label>
                ${inventoryItemTypeSelect(itemType)}
            </div>
            <div class="grid grid-cols-2 gap-2.5">
                <div class="form-group">
                    <label>Stok Saat Ini</label>
                    <input type="number" name="quantity" value="${qty}" required min="0">
                </div>
                <div class="form-group">
                    <label>Satuan Dasar</label>
                    ${unitSelectHtml('unit', unit)}
                </div>
            </div>
            <div class="grid grid-cols-2 gap-2.5">
                <div class="form-group">
                    <label>Satuan Kemasan</label>
                    ${unitSelectHtml('package_unit', packageUnit, true)}
                </div>
                <div class="form-group">
                    <label>Isi per Kemasan</label>
                    <input type="number" name="package_size" value="${Number(packageSize || 1)}" required min="1">
                </div>
            </div>
            <div class="form-group">
                <label>Batas Aman (Min Stok)</label>
                <input type="number" name="min_stock" value="${minStock}" required min="0">
            </div>
            <div class="sale-modal-actions">
                <button type="button" class="btn btn-modal-cancel" data-inventory-action="close-modal">Batal</button>
                <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Simpan</button>
            </div>
        </form>
    `;
    openModal('Edit Peralatan', html);
}
function editInventoryFromCache(id) {
    const item = inventoryById(id);
    if (!item) {
        showToast('Data inventori tidak ditemukan. Muat ulang data lalu coba lagi.', 'error');
        return;
    }
    const { unit, packageUnit, packageSize } = inventoryPackageMeta(item);
    editInventory(item.id, item.item_name || item.name || '', Number(item.quantity || 0), unit, Number(item.min_stock || 0), packageUnit, packageSize, inventoryItemType(item.item_type));
}
async function submitEditInventory(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const btn = form.querySelector('button[type="submit"]');
    if (!btn)
        return;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
    btn.disabled = true;
    try {
        const response = await fetch('/edit_inventory', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.status === 'success') {
            closeModal();
            showToast(data.message, 'success');
            loadTab('inventory');
        }
        else {
            showToast(data.message || data.detail || 'Gagal menyimpan perubahan.', 'error');
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }
    catch {
        showToast('Koneksi gagal saat menyimpan perubahan.', 'error');
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
async function deleteInventory(id, name) {
    const decodedName = new DOMParser().parseFromString(name, 'text/html').documentElement.textContent;
    if (await showConfirm(`Apakah Anda yakin ingin menghapus inventaris "${decodedName}"?`)) {
        const formData = new FormData();
        formData.append('item_id', String(id));
        fetch('/delete_inventory', {
            method: 'POST',
            body: formData
        })
            .then(res => res.json())
            .then(data => {
            if (data.status === 'success') {
                showToast(data.message, 'success');
                loadTab('inventory');
            }
            else {
                showToast(data.message || data.detail || 'Gagal menghapus inventaris.', 'error');
            }
        })
            .catch(() => showToast('Koneksi gagal saat menghapus inventaris.', 'error'));
    }
}
async function deleteInventoryFromCache(id) {
    const item = inventoryById(id);
    await deleteInventory(id, item?.item_name || item?.name || 'inventaris');
}
window.renderInventory = renderInventory;
window.goToInventoryPage = goToInventoryPage;
window.selectInventory = selectInventory;
window.setInventoryStockMode = setInventoryStockMode;
window.updateInventoryStockPreview = updateInventoryStockPreview;
window.prepareInventoryStockSubmit = prepareInventoryStockSubmit;
window.editInventory = editInventory;
window.submitEditInventory = submitEditInventory;
window.deleteInventory = deleteInventory;
window.openAddInventoryModal = openAddInventoryModal;
window.submitAddInventory = submitAddInventory;
window.openInventoryStockModal = openInventoryStockModal;
window.submitInventoryStock = submitInventoryStock;
window.filterInventoryPicker = filterInventoryPicker;
window.selectInventoryPickerItem = selectInventoryPickerItem;
