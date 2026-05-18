// ─── INVENTORY ────────────────────────────────────────────────────────────────
// Layout: Tabel klik-untuk-pilih (kiri besar) | Forms (kanan)

const INVENTORY_UNIT_OPTIONS = ['pcs', 'unit', 'ml', 'gr', 'botol', 'saset', 'box', 'pack', 'strip', 'tablet', 'kapsul', 'dus'];

type InventoryStockMode = "in" | "out";

type InventoryPackageMeta = {
    unit: string;
    packageUnit: string;
    packageSize: number;
};

function inventoryItemType(value: unknown): 'consumable' | 'non_consumable' {
    const normalized = String(value || 'consumable').trim().toLowerCase().replace(/[\s-]+/g, '_');
    return normalized === 'non_consumable' || normalized === 'nonconsumable' || normalized === 'asset' || normalized === 'reusable'
        ? 'non_consumable'
        : 'consumable';
}

function inventoryItemTypeLabel(value: unknown): string {
    return inventoryItemType(value) === 'non_consumable' ? 'Non-consumable' : 'Consumable';
}

function inventoryItemTypeSelect(value: unknown = 'consumable'): string {
    const selected = inventoryItemType(value);
    return `
        <select name="item_type">
            <option value="consumable" ${selected === 'consumable' ? 'selected' : ''}>Consumable - habis terpakai</option>
            <option value="non_consumable" ${selected === 'non_consumable' ? 'selected' : ''}>Non-consumable - aset/peralatan</option>
        </select>
        <small class="unit-field-hint">Auto-deduct layanan hanya memotong item consumable.</small>
    `;
}

function inventoryText(value: unknown, fallback = ''): string {
    const text = String(value ?? '').trim();
    return text || fallback;
}

function inventoryNumber(value: unknown, fallback = 0): number {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function inventoryPackageMeta(item: InventoryItem): InventoryPackageMeta {
    const unit = inventoryText(item.unit, 'pcs');
    const packageUnit = inventoryText(item.package_unit ?? item.packageUnit);
    const packageSize = Math.max(1, inventoryNumber(item.package_size ?? item.packageSize, 1));
    return { unit, packageUnit, packageSize };
}

function unitSelectHtml(name: string, value = '', includeEmpty = false): string {
    const options = (includeEmpty ? [''] : []).concat(INVENTORY_UNIT_OPTIONS);
    return `<select name="${name}">${options.map(opt => {
        const label = opt || '- Tidak ada -';
        return `<option value="${escapeHtml(opt)}" ${opt === value ? 'selected' : ''}>${escapeHtml(label)}</option>`;
    }).join('')}</select>`;
}

function packageLabel(item: InventoryItem): string {
    const { unit, packageUnit, packageSize } = inventoryPackageMeta(item);
    if (!packageUnit) return unit || '-';
    if (packageSize <= 1) return packageUnit;
    return `1 ${packageUnit} = ${packageSize} ${unit}`;
}

function renderInventory(data: InventoryItem[]): void {
    const criticalCount = data.filter(i => Number(i.quantity || 0) <= Number(i.min_stock || 0)).length;
    const safeCount = data.length - criticalCount;

    const html = `
        <!-- ── Stat Cards ── -->
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:18px;">
            <div class="stat-card" style="padding:16px; margin-bottom:0; border-left:3px solid var(--success);">
                <div class="stat-icon green" style="width:38px;height:38px;font-size:16px;"><i class="fas fa-check-circle"></i></div>
                <div class="stat-details"><h4>Stok Aman</h4><h2>${safeCount}</h2></div>
            </div>
            <div class="stat-card" style="padding:16px; margin-bottom:0; border-left:3px solid var(--warning);">
                <div class="stat-icon orange" style="width:38px;height:38px;font-size:16px;"><i class="fas fa-exclamation-triangle"></i></div>
                <div class="stat-details"><h4>Stok Kritis</h4><h2 style="color:${criticalCount > 0 ? 'var(--warning)' : 'var(--text-main)'}">${criticalCount}</h2></div>
            </div>
        </div>

        <!-- ── Main: Tabel kiri | Forms kanan ── -->
        <div class="card stock-quick-add-card inventory">
            <div class="stock-quick-add-head">
                <div>
                    <h3><i class="fas fa-plus-circle"></i> Tambah Peralatan Baru</h3>
                    <span>Form cepat agar admin tidak perlu scroll ke bawah.</span>
                </div>
            </div>
            <form action="/add_inventory" method="post" class="stock-quick-add-form inventory-add-form">
                <div class="unit-help-note">
                    <strong>Satuan dasar</strong> = stok terkecil yang dihitung sistem. <strong>Satuan kemasan</strong> = bungkus besar. Contoh: dasar <b>pcs</b>, kemasan <b>box</b>, isi <b>100</b> berarti 1 box = 100 pcs.
                </div>
                <div class="form-group inventory-item-name-field">
                    <label>Nama Alat</label>
                    <input type="text" name="item_name" required placeholder="Alkohol, kapas">
                </div>
                <div class="form-group inventory-item-type-field">
                    <label>Jenis Item</label>
                    ${inventoryItemTypeSelect('consumable')}
                </div>
                <div class="form-group inventory-base-unit-field">
                    <label>Satuan Dasar</label>
                    ${unitSelectHtml('unit', 'pcs')}
                </div>
                <div class="form-group inventory-package-unit-field">
                    <label>Satuan Kemasan</label>
                    ${unitSelectHtml('package_unit', '', true)}
                </div>
                <div class="form-group inventory-initial-stock-field">
                    <label>Stok Awal</label>
                    <input type="number" name="initial_qty" required placeholder="0" min="0">
                </div>
                <div class="form-group inventory-min-stock-field">
                    <label>Batas Aman</label>
                    <input type="number" name="min_stock" required placeholder="10" min="0">
                </div>
                <div class="form-group inventory-package-size-field">
                    <label>Isi per Kemasan</label>
                    <input type="number" name="package_size" required value="1" min="1">
                </div>
                <button type="submit" class="btn btn-primary inventory-save-btn"><i class="fas fa-save"></i> Simpan</button>
            </form>
        </div>

        <div style="display:flex; gap:18px; align-items:flex-start;">

            <!-- KIRI: Tabel (klik untuk pilih) -->
            <div class="card" style="padding:0; flex:1; min-width:0;">
                <div class="card-header" style="padding:16px 20px 12px;">
                    <h3><i class="fas fa-clipboard-list"></i> Monitoring Stok (${data.length} item)</h3>
                    <span style="font-size:12px; color:var(--primary); font-weight:500;"><i class="fas fa-hand-pointer"></i> Klik baris untuk pilih</span>
                </div>
                <div style="overflow-x:auto;">
                    <table id="inventory-table" style="width:100%; border-collapse:collapse; font-size:13px;">
                        <thead>
                            <tr style="background:#f8fafc;">
                                <th style="padding:11px 16px; text-align:left; font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.6px;">Nama Peralatan</th>
                                <th style="padding:11px 16px; text-align:center; font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.6px;">Jenis</th>
                                <th style="padding:11px 16px; text-align:center; font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.6px;">Stok Tersisa</th>
                                <th style="padding:11px 16px; text-align:center; font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.6px;">Kemasan</th>
                                <th style="padding:11px 16px; text-align:center; font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.6px;">Batas Aman</th>
                                <th style="padding:11px 16px; text-align:center; font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.6px;">Progress</th>
                                <th style="padding:11px 16px; text-align:center; font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.6px;">Status</th>
                                <th style="padding:11px 16px; text-align:center; font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.6px; width:70px;">Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.length === 0
            ? `<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--text-muted);">Inventori masih kosong.</td></tr>`
            : data.map(i => {
                const quantity = Number(i.quantity || 0);
                const minStock = Number(i.min_stock || 0);
                const itemType = inventoryItemType(i.item_type);
                const { unit, packageUnit, packageSize } = inventoryPackageMeta(i);
                const isLow = quantity <= minStock;
                const pct = minStock > 0 ? Math.min(100, Math.round(quantity / minStock * 100)) : 100;
                const barColor = isLow ? 'var(--danger)' : (pct < 150 ? 'var(--warning)' : 'var(--success)');
                const statusBadge = isLow
                    ? `<span class="badge badge-low"><i class="fas fa-exclamation-triangle"></i> Kritis</span>`
                    : `<span class="badge badge-ok"><i class="fas fa-check-circle"></i> Aman</span>`;
                return `
                                    <tr data-id="${i.id}" data-name="${escapeHtml(i.item_name)}" data-type="${itemType}" data-qty="${quantity}" data-min="${minStock}" data-unit="${escapeHtml(unit)}" data-package-unit="${escapeHtml(packageUnit)}" data-package-size="${packageSize}"
                                        onclick="selectInventory(this)"
                                        style="cursor:pointer; border-bottom:1px solid #f1f5f9; transition:background 0.15s;"
                                        onmouseover="if(!this.classList.contains('row-selected'))this.style.background='#f0f4ff'"
                                        onmouseout="if(!this.classList.contains('row-selected'))this.style.background=''">
                                        <td style="padding:11px 16px; font-weight:600;">${escapeHtml(i.item_name)}</td>
                                        <td style="padding:11px 16px; text-align:center;">
                                            <span class="badge ${itemType === 'consumable' ? 'badge-ok' : 'badge-low'}">${escapeHtml(inventoryItemTypeLabel(itemType))}</span>
                                        </td>
                                        <td style="padding:11px 16px; text-align:center;">
                                            <span style="font-size:16px; font-weight:700; color:${isLow ? 'var(--danger)' : 'var(--text-main)'};">${escapeHtml(i.stock_display || i.quantity)}</span>
                                        </td>
                                        <td style="padding:11px 16px; text-align:center; color:var(--text-muted);">${escapeHtml(packageLabel(i))}</td>
                                        <td style="padding:11px 16px; text-align:center; color:var(--text-muted);">${minStock} ${escapeHtml(unit)}</td>
                                        <td style="padding:11px 16px; text-align:center;">
                                            <div style="background:#f1f5f9;border-radius:999px;height:6px;width:72px;overflow:hidden;margin:0 auto;">
                                                <div style="height:100%;width:${Math.min(100, pct)}%;background:${barColor};border-radius:999px;transition:width 0.4s;"></div>
                                            </div>
                                            <div style="font-size:10px;color:var(--text-muted);margin-top:3px;">${pct}%</div>
                                        </td>
                                        <td style="padding:11px 16px; text-align:center;">${statusBadge}</td>
                                        <td style="padding:11px 16px; text-align:center;" onclick="event.stopPropagation()">
                                            <div style="display:flex; gap:6px; justify-content:center;">
                                                <button onclick="editInventory(${i.id}, '${escapeHtml(i.item_name)}', ${quantity}, '${escapeHtml(unit)}', ${minStock}, '${escapeHtml(packageUnit)}', ${packageSize}, '${itemType}')"
                                                        title="Edit Alat"
                                                        style="background:transparent; border:none; color:var(--primary); cursor:pointer; font-size:14px; padding:4px; transition:color 0.2s;"
                                                        onmouseover="this.style.color='#4338ca'" onmouseout="this.style.color='var(--primary)'">
                                                    <i class="fas fa-edit"></i>
                                                </button>
                                                <button onclick="deleteInventory(${i.id}, '${escapeHtml(i.item_name)}')"
                                                        title="Hapus Alat"
                                                        style="background:transparent; border:none; color:var(--danger); cursor:pointer; font-size:14px; padding:4px; transition:color 0.2s;"
                                                        onmouseover="this.style.color='#b91c1c'" onmouseout="this.style.color='var(--danger)'">
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
            </div>

            <!-- KANAN: Forms -->
            <div style="display:flex; flex-direction:column; gap:18px; width:320px; flex-shrink:0;">

                <!-- Form Sesuaikan Stok (klik baris untuk pilih) -->
                <div class="card" style="height:fit-content; border-top:3px solid var(--warning);">
                    <div class="card-header">
                        <h3><i class="fas fa-sliders-h" style="color:var(--warning);"></i> Koreksi Stok Manual</h3>
                    </div>
                    <div class="stock-workflow-note">
                        Stok alat untuk layanan otomatis berkurang saat kunjungan disimpan. Gunakan form ini untuk tambah stok baru atau koreksi manual di luar kunjungan, misalnya alat rusak, hilang, stok opname, atau salah input.
                    </div>
                    <form action="/update_inventory" method="post" onsubmit="prepareInventoryStockSubmit(event)">
                        <input type="hidden" name="item_id" id="inv-selected-id">
                        <input type="hidden" name="quantity_change" id="inv-change-input" value="">
                        <div class="form-group">
                            <label>Peralatan Terpilih</label>
                            <div id="inv-selected-badge" style="padding:9px 12px;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;font-size:13px;color:#d97706;font-weight:500;min-height:38px;">
                                <i class="fas fa-arrow-left"></i> Klik baris di tabel
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Jenis Pergerakan</label>
                            <div class="stock-mode-picker" data-target="inventory">
                                <button type="button" class="active" data-mode="in" onclick="setInventoryStockMode('in')"><i class="fas fa-arrow-down"></i> Tambah Stok</button>
                                <button type="button" data-mode="out" onclick="setInventoryStockMode('out')"><i class="fas fa-arrow-up"></i> Koreksi Keluar</button>
                            </div>
                            <input type="hidden" id="inv-stock-mode" value="in">
                            <small style="display:block;margin-top:7px;color:var(--text-muted);line-height:1.45;">
                                Koreksi Keluar bukan untuk transaksi layanan normal. Pakai hanya jika stok fisik perlu dikurangi manual.
                            </small>
                        </div>
                        <div class="form-group">
                            <label>Jumlah</label>
                            <input type="number" required placeholder="Contoh: 10" id="inv-change-amount" min="1" oninput="updateInventoryStockPreview()">
                        </div>
                        <div class="form-group">
                            <label>Satuan Transaksi</label>
                            <select name="multiplier" id="inv-multiplier" onchange="updateInventoryStockPreview()">
                                <option value="1">Satuan dasar</option>
                            </select>
                            <small class="unit-field-hint">Pilih kemasan jika stok masuk/keluar berupa box, pack, atau dus.</small>
                            <div id="inv-stock-preview" class="stock-preview">Pilih item, jenis pergerakan, dan jumlah.</div>
                        </div>
                        <input type="hidden" name="note" id="inv-stock-note" value="">
                        <button type="submit" class="btn btn-primary" style="background:linear-gradient(135deg,#f59e0b,#ef4444); box-shadow:0 4px 12px rgba(245,158,11,0.35);"
                            onclick="if(!document.getElementById('inv-selected-id').value){ showToast('Pilih peralatan di tabel terlebih dahulu!', 'warning'); return false; }">
                            <i class="fas fa-sync-alt"></i> Catat Pergerakan
                        </button>
                    </form>
                </div>

                <!-- Form Tambah Peralatan Baru -->
                <div class="card" style="display:none; height:fit-content; border-top:3px solid var(--info);">
                    <div class="card-header">
                        <h3><i class="fas fa-plus-circle" style="color:var(--info);"></i> Tambah Peralatan</h3>
                    </div>
                    <form action="/add_inventory" method="post">
                        <div class="unit-help-note compact">
                            Dasar = stok terkecil. Kemasan = bungkus besar. Contoh: 1 box = 100 pcs.
                        </div>
                        <div class="form-group">
                            <label>Nama Alat</label>
                            <input type="text" name="item_name" required placeholder="Contoh: Alkohol, kapas, sarung tangan...">
                        </div>
                        <div class="form-group">
                            <label>Jenis Item</label>
                            ${inventoryItemTypeSelect('consumable')}
                        </div>
                        <div class="form-group">
                            <label>Satuan Dasar</label>
                            ${unitSelectHtml('unit', 'pcs')}
                        </div>
                        <div class="form-group">
                            <label>Satuan Kemasan</label>
                            ${unitSelectHtml('package_unit', '', true)}
                        </div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                            <div class="form-group">
                                <label>Stok Awal</label>
                                <input type="number" name="initial_qty" required placeholder="0" min="0">
                            </div>
                            <div class="form-group">
                                <label>Batas Aman</label>
                                <input type="number" name="min_stock" required placeholder="10" min="0">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Isi per Kemasan</label>
                            <input type="number" name="package_size" required value="1" min="1">
                        </div>
                        <button type="submit" class="btn btn-primary" style="background:linear-gradient(135deg,#3b82f6,#6366f1); box-shadow:0 4px 12px rgba(59,130,246,0.35);">
                            <i class="fas fa-save"></i> Simpan Alat Baru
                        </button>
                    </form>
                </div>
            </div>
        </div>`;

    const displayArea = document.getElementById('display-area');
    if (displayArea) displayArea.innerHTML = html;
}

// ── ROW SELECTION ─────────────────────────────────────────────────────────────
function selectInventory(row: HTMLTableRowElement): void {
    // Deselect all
    document.querySelectorAll('#inventory-table tbody tr').forEach(r => {
        const rowEl = r as HTMLElement;
        rowEl.classList.remove('row-selected');
        rowEl.style.background = '';
    });
    // Select clicked
    row.classList.add('row-selected');
    row.style.background = '#fef3c7';

    // Fill form
    const id = row.dataset.id;
    const name = row.dataset.name;
    const qty = row.dataset.qty;
    const itemType = row.dataset.type || 'consumable';
    const unit = row.dataset.unit;
    const packageUnit = row.dataset.packageUnit || '';
    const packageSize = Math.max(1, Number(row.dataset.packageSize || 1));

    const selectedInput = document.getElementById('inv-selected-id') as HTMLInputElement | null;
    if (selectedInput) selectedInput.value = id || '';
    const multiplier = document.getElementById('inv-multiplier') as HTMLSelectElement | null;
    if (multiplier) {
        multiplier.innerHTML = `<option value="1">${escapeHtml(unit)}</option>`;
        if (packageUnit && packageUnit !== unit && packageSize > 1) {
            multiplier.innerHTML += `<option value="${packageSize}">${escapeHtml(packageUnit)} (1 = ${packageSize} ${escapeHtml(unit)})</option>`;
        }
    }
    const badge = document.getElementById('inv-selected-badge');
    if (badge) {
        badge.innerHTML = `<i class="fas fa-box-open" style="color:#f59e0b;"></i> <strong>${escapeHtml(name)}</strong> <span style="color:#94a3b8;font-size:11px;">(${escapeHtml(inventoryItemTypeLabel(itemType))}, stok: ${escapeHtml(qty)} ${escapeHtml(unit)})</span>`;
        badge.style.background = '#fffbeb';
        badge.style.borderColor = '#fcd34d';
        badge.style.color = '#92400e';
    }
    updateInventoryStockPreview();
    const inp = document.getElementById('inv-change-amount') as HTMLInputElement | null;
    if (inp) inp.focus();
}

// ── CRUD ACTIONS ─────────────────────────────────────────────────────────────

function setInventoryStockMode(mode: InventoryStockMode | string): void {
    const cleanMode = mode === 'out' ? 'out' : 'in';
    const input = document.getElementById('inv-stock-mode') as HTMLInputElement | null;
    if (input) input.value = cleanMode;
    document.querySelectorAll('.stock-mode-picker[data-target="inventory"] button').forEach(btn => {
        const modeButton = btn as HTMLButtonElement;
        modeButton.classList.toggle('active', modeButton.dataset.mode === cleanMode);
    });
    updateInventoryStockPreview();
}

function updateInventoryStockPreview(): void {
    const selectedInput = document.getElementById('inv-selected-id') as HTMLInputElement | null;
    const amountInput = document.getElementById('inv-change-amount') as HTMLInputElement | null;
    const multiplierSelect = document.getElementById('inv-multiplier') as HTMLSelectElement | null;
    const modeInput = document.getElementById('inv-stock-mode') as HTMLInputElement | null;
    const selected = selectedInput?.value;
    const amount = Math.max(0, Number(amountInput?.value || 0));
    const multiplier = Math.max(1, Number(multiplierSelect?.value || 1));
    const mode = modeInput?.value === 'out' ? 'out' : 'in';
    const preview = document.getElementById('inv-stock-preview');
    if (!preview) return;

    const total = amount * multiplier;
    const action = mode === 'out' ? 'keluar/terpakai' : 'masuk';
    const selectedUnit = multiplierSelect?.selectedOptions?.[0]?.textContent || 'satuan';
    preview.classList.toggle('danger', mode === 'out');
    preview.textContent = selected && total > 0
        ? `Stok akan ${action}: ${amount} ${selectedUnit} = ${total} satuan dasar.`
        : 'Pilih item, jenis pergerakan, dan jumlah.';
}

function prepareInventoryStockSubmit(event: SubmitEvent): void {
    const amountInput = document.getElementById('inv-change-amount') as HTMLInputElement | null;
    const modeInput = document.getElementById('inv-stock-mode') as HTMLInputElement | null;
    const multiplierSelect = document.getElementById('inv-multiplier') as HTMLSelectElement | null;
    const amount = Math.max(0, Number(amountInput?.value || 0));
    const mode = modeInput?.value === 'out' ? 'out' : 'in';
    const hidden = document.getElementById('inv-change-input') as HTMLInputElement | null;
    const note = document.getElementById('inv-stock-note') as HTMLInputElement | null;
    if (hidden) hidden.value = String(mode === 'out' ? -amount : amount);
    if (note) note.value = `${mode === 'out' ? 'Keluar' : 'Masuk'} ${amount} ${multiplierSelect?.selectedOptions?.[0]?.textContent || 'satuan'}`;
    if (amount <= 0) {
        event.preventDefault();
        showToast('Isi jumlah barang terlebih dahulu.', 'warning');
    }
}

function editInventory(
    id: number | string,
    name: string,
    qty: number | string,
    unit: string,
    minStock: number | string,
    packageUnit = '',
    packageSize: number | string = 1,
    itemType: string = 'consumable'
): void {
    const html = `
        <form id="edit-inventory-form" onsubmit="submitEditInventory(event)">
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
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="form-group">
                    <label>Stok Saat Ini</label>
                    <input type="number" name="quantity" value="${qty}" required min="0">
                </div>
                <div class="form-group">
                    <label>Satuan Dasar</label>
                    ${unitSelectHtml('unit', unit)}
                </div>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
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
            <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
                <button type="button" class="btn" onclick="closeModal()" style="background:#f1f5f9;color:#475569;">Batal</button>
                <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Simpan</button>
            </div>
        </form>
    `;
    openModal('Edit Peralatan', html);
}

async function submitEditInventory(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    const form = event.target as HTMLFormElement;
    const formData = new FormData(form);

    const btn = form.querySelector('button[type="submit"]') as HTMLButtonElement | null;
    if (!btn) return;
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
        } else {
            showToast(data.message || data.detail || 'Gagal menyimpan perubahan.', 'error');
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    } catch {
        showToast('Koneksi gagal saat menyimpan perubahan.', 'error');
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function deleteInventory(id: number | string, name: string): Promise<void> {
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
                } else {
                    showToast(data.message || data.detail || 'Gagal menghapus inventaris.', 'error');
                }
            })
            .catch(() => showToast('Koneksi gagal saat menghapus inventaris.', 'error'));
    }
}

window.renderInventory = renderInventory;
window.selectInventory = selectInventory;
window.setInventoryStockMode = setInventoryStockMode;
window.updateInventoryStockPreview = updateInventoryStockPreview;
window.prepareInventoryStockSubmit = prepareInventoryStockSubmit;
window.editInventory = editInventory;
window.submitEditInventory = submitEditInventory;
window.deleteInventory = deleteInventory;
