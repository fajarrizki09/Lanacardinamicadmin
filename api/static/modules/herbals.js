"use strict";
// ─── HERBALS ──────────────────────────────────────────────────────────────────
// Layout: Form Add (atas) | Update Stok dengan selected badge (bawah-kiri)
//         Tabel klik untuk pilih (kanan)
const HERBAL_UNIT_OPTIONS = ['botol', 'pcs', 'box', 'saset', 'pack', 'strip', 'tablet', 'kapsul', 'dus'];
function herbalText(value, fallback = '') {
    const text = String(value ?? '').trim();
    return text || fallback;
}
function herbalNumber(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}
function herbalInput(id) {
    return document.getElementById(id);
}
function herbalSelect(id) {
    return document.getElementById(id);
}
function herbalErrorMessage(error, fallback = 'Terjadi kesalahan.') {
    return error instanceof Error ? error.message : fallback;
}
function herbalUnitSelectHtml(name, value = '', includeEmpty = false) {
    const options = (includeEmpty ? [''] : []).concat(HERBAL_UNIT_OPTIONS);
    return `<select name="${name}">${options.map(opt => {
        const label = opt || '- Tidak ada -';
        return `<option value="${escapeHtml(opt)}" ${opt === value ? 'selected' : ''}>${escapeHtml(label)}</option>`;
    }).join('')}</select>`;
}
function herbalPackageLabel(item) {
    if (!item.package_unit || Number(item.package_size || 1) <= 1)
        return '-';
    return `1 ${item.package_unit} = ${item.package_size} ${item.unit}`;
}
function renderHerbals(data) {
    window._herbalCatalog = (data || []).map((h) => ({
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
    window._herbalSaleItems = [];
    const outOfStock = data.filter((h) => h.stock <= 0).length;
    const lowStockHerb = data.filter((h) => h.stock > 0 && h.stock <= (h.min_stock || 5)).length;
    const goodStock = data.length - outOfStock - lowStockHerb;
    const html = `
        <!-- ── Stat Cards ── -->
        <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:18px;">
            <div class="stat-card" style="padding:14px; margin-bottom:0; border-left:3px solid var(--success);">
                <div class="stat-icon green" style="width:34px;height:34px;font-size:14px;"><i class="fas fa-leaf"></i></div>
                <div class="stat-details"><h4>Tersedia</h4><h2>${goodStock}</h2></div>
            </div>
            <div class="stat-card" style="padding:14px; margin-bottom:0; border-left:3px solid var(--warning);">
                <div class="stat-icon orange" style="width:34px;height:34px;font-size:14px;"><i class="fas fa-exclamation"></i></div>
                <div class="stat-details"><h4>Menipis</h4><h2 style="color:${lowStockHerb > 0 ? 'var(--warning)' : 'var(--text-main)'}">${lowStockHerb}</h2></div>
            </div>
            <div class="stat-card" style="padding:14px; margin-bottom:0; border-left:3px solid var(--danger);">
                <div class="stat-icon red" style="width:34px;height:34px;font-size:14px;"><i class="fas fa-times"></i></div>
                <div class="stat-details"><h4>Habis</h4><h2 style="color:${outOfStock > 0 ? 'var(--danger)' : 'var(--text-main)'}">${outOfStock}</h2></div>
            </div>
        </div>

        <!-- ── Main: Table kiri-besar | Forms kanan ── -->
        <div class="card stock-quick-add-card herbal">
            <div class="stock-quick-add-head">
                <div>
                    <h3><i class="fas fa-plus-circle"></i> Tambah Produk / Herbal Baru</h3>
                    <span>Form cepat agar admin tidak perlu scroll ke bawah.</span>
                </div>
                <button type="button" class="btn btn-primary" onclick="openHerbalSaleModal()" style="background:linear-gradient(135deg,#10b981,#059669); box-shadow:0 4px 12px rgba(16,185,129,0.3);">
                    <i class="fas fa-cash-register"></i> Jual Produk / Herbal
                </button>
                <button type="button" class="btn btn-secondary" onclick="openHerbalReturnModal()" style="width:auto;">
                    <i class="fas fa-undo"></i> Retur Penjualan
                </button>
            </div>
            <form action="/add_herbal" method="post" class="stock-quick-add-form">
                <div class="unit-help-note">
                    <strong>Satuan dasar</strong> = stok terkecil yang dihitung sistem. <strong>Satuan kemasan</strong> = bungkus besar. Contoh: dasar <b>botol</b>, kemasan <b>box</b>, isi <b>12</b> berarti 1 box = 12 botol.
                </div>
                <div class="form-group">
                    <label>Nama Produk / Herbal</label>
                    <input type="text" name="name" required placeholder="Nama produk">
                </div>
                <div class="form-group">
                    <label>Satuan Dasar</label>
                    ${herbalUnitSelectHtml('unit', 'botol')}
                </div>
                <div class="form-group">
                    <label>Satuan Kemasan</label>
                    ${herbalUnitSelectHtml('package_unit', '', true)}
                </div>
                <div class="form-group">
                    <label>Stok Awal</label>
                    <input type="number" name="stock" required placeholder="0" min="0">
                </div>
                <div class="form-group">
                    <label>Isi per Kemasan</label>
                    <input type="number" name="package_size" required value="1" min="1">
                </div>
                <div class="form-group">
                    <label>Harga Modal (Rp)</label>
                    <input type="number" name="cost_price" required placeholder="0" min="0">
                </div>
                <div class="form-group">
                    <label>Harga (Rp)</label>
                    <input type="number" name="price" required placeholder="100000" min="0">
                </div>
                <div class="form-group">
                    <label>Batas Aman</label>
                    <input type="number" name="min_stock" required placeholder="5" min="0">
                </div>
                <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Simpan</button>
            </form>
        </div>

        <div class="herbal-workspace">

            <!-- KIRI: Tabel Produk / Herbal (klik untuk pilih) -->
            <div class="card" style="padding:0; min-width:0;">
                <div class="card-header" style="padding:16px 20px 12px;">
                    <h3><i class="fas fa-mortar-pestle"></i> Katalog Produk / Herbal (${data.length} produk)</h3>
                    <span style="font-size:12px; color:var(--primary); font-weight:500;"><i class="fas fa-hand-pointer"></i> Klik baris untuk pilih</span>
                </div>
                <div class="herbal-table-wrap">
                    <table id="herbals-table" class="herbal-stock-table" style="width:100%; border-collapse:collapse; font-size:13px;">
                        <thead>
                            <tr style="background:#f8fafc;">
                                <th>Produk</th>
                                <th>Stok</th>
                                <th>Harga</th>
                                <th>Margin</th>
                                <th>Status</th>
                                <th>Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.length === 0
        ? `<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--text-muted);">Belum ada produk / herbal.</td></tr>`
        : data.map((h) => {
            const isEmpty = h.stock <= 0;
            const isLow = !isEmpty && h.stock <= (h.min_stock || 5);
            const stockColor = isEmpty ? 'var(--danger)' : isLow ? 'var(--warning)' : 'var(--success)';
            const rowBg = isEmpty ? '#fef2f2' : isLow ? '#fffbeb' : '';
            const statusBadge = isEmpty
                ? `<span style="background:#fee2e2;color:#dc2626;font-size:10px;font-weight:700;padding:3px 8px;border-radius:4px;">HABIS</span>`
                : isLow
                    ? `<span style="background:#fef3c7;color:#d97706;font-size:10px;font-weight:700;padding:3px 8px;border-radius:4px;">MENIPIS</span>`
                    : `<span style="background:#ecfdf5;color:#059669;font-size:10px;font-weight:700;padding:3px 8px;border-radius:4px;">OK</span>`;
            return `
                                    <tr data-id="${h.id}" data-name="${escapeHtml(h.name)}" data-stock="${h.stock}" data-price="${h.price}" data-unit="${escapeHtml(h.unit)}" data-package-unit="${escapeHtml(h.package_unit || '')}" data-package-size="${Number(h.package_size || 1)}"
                                        onclick="selectHerbal(this)"
                                        style="cursor:pointer; border-bottom:1px solid #f1f5f9; ${rowBg ? 'background:' + rowBg + ';' : ''} transition:background 0.15s;"
                                        onmouseover="if(!this.classList.contains('row-selected'))this.style.background='#f0f4ff'"
                                        onmouseout="if(!this.classList.contains('row-selected'))this.style.background='${rowBg}'">
                                        <td class="herbal-product-cell" style="padding:11px 16px;">
                                            <div class="herbal-product-name-wrap">
                                                <div style="width:32px;height:32px;border-radius:8px;background:#f0fdf4;display:flex;align-items:center;justify-content:center;color:#10b981;font-size:14px;flex-shrink:0;">
                                                    <i class="fas fa-leaf"></i>
                                                </div>
                                                <span class="herbal-product-name">
                                                    ${escapeHtml(h.name)}
                                                    <small>${escapeHtml(h.unit || '-')} · ${escapeHtml(herbalPackageLabel(h))}</small>
                                                </span>
                                            </div>
                                        </td>
                                        <td style="padding:11px 16px; text-align:center; font-size:16px; font-weight:700; color:${stockColor};">${escapeHtml(h.stock_display || h.stock)}</td>
                                        <td style="padding:11px 16px; text-align:right; font-weight:600; color:var(--success);">
                                            ${formatRupiah(h.price)}
                                            <small class="herbal-cell-muted">Modal ${formatRupiah(h.cost_price || 0)}</small>
                                        </td>
                                        <td style="padding:11px 16px; text-align:right; font-weight:600; color:${Number(h.margin || 0) >= 0 ? 'var(--primary)' : 'var(--danger)'};">${formatRupiah(h.margin || 0)}</td>
                                        <td style="padding:11px 16px; text-align:center;">${statusBadge}</td>
                                        <td style="padding:11px 16px; text-align:center;" onclick="event.stopPropagation()">
                                            <div style="display:flex; gap:6px; justify-content:center;">
                                                <button onclick="editHerbal(${h.id}, '${escapeHtml(h.name)}', '${escapeHtml(h.unit)}', ${h.price}, ${h.stock}, ${Number(h.cost_price || 0)}, '${escapeHtml(h.package_unit || '')}', ${Number(h.package_size || 1)}, ${Number(h.min_stock || 5)})" 
                                                        title="Edit Produk / Herbal"
                                                        style="background:transparent; border:none; color:var(--primary); cursor:pointer; font-size:14px; padding:4px; transition:color 0.2s;"
                                                        onmouseover="this.style.color='#4338ca'" onmouseout="this.style.color='var(--primary)'">
                                                    <i class="fas fa-edit"></i>
                                                </button>
                                                <button onclick="deleteHerbal(${h.id}, '${escapeHtml(h.name)}')" 
                                                        title="Hapus Produk / Herbal"
                                                        style="background:transparent; border:none; color:var(--danger); cursor:pointer; font-size:14px; padding:4px; transition:color 0.2s;"
                                                        onmouseover="this.style.color='#b91c1c'" onmouseout="this.style.color='var(--danger)'">
                                                    <i class="fas fa-trash-alt"></i>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>`;
        }).join('')}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- KANAN: Forms -->
            <div style="display:flex; flex-direction:column; gap:18px; width:320px; flex-shrink:0;">

                <!-- Form Koreksi Stok (klik baris untuk pilih) -->
                <div class="card" style="height:fit-content; border-top:3px solid #8b5cf6;">
                    <div class="card-header">
                        <h3><i class="fas fa-exchange-alt" style="color:#8b5cf6;"></i> Koreksi Stok Produk / Herbal</h3>
                    </div>
                    <div class="stock-workflow-note">
                        Gunakan untuk stok opname, barang rusak, hilang, sampel, atau koreksi input. Untuk transaksi berbayar gunakan tombol Jual Produk / Herbal.
                    </div>
                    <form action="/update_herbal" method="post" onsubmit="prepareHerbalStockSubmit(event)">
                        <input type="hidden" name="herbal_id" id="herbal-selected-id">
                        <input type="hidden" name="change" id="herbal-change-input" value="">
                        <div class="form-group">
                            <label>Produk / Herbal Terpilih</label>
                            <div id="herbal-selected-badge" style="padding:9px 12px;background:#f5f3ff;border:1px solid #c4b5fd;border-radius:8px;font-size:13px;color:#7c3aed;font-weight:500;min-height:38px;">
                                <i class="fas fa-arrow-left"></i> Klik baris produk/herbal di tabel
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Jenis Koreksi Stok</label>
                            <div class="stock-mode-picker" data-target="herbal">
                                <button type="button" class="active" data-mode="in" onclick="setHerbalStockMode('in')"><i class="fas fa-arrow-down"></i> Stok Bertambah</button>
                                <button type="button" data-mode="out" onclick="setHerbalStockMode('out')"><i class="fas fa-arrow-up"></i> Stok Berkurang</button>
                            </div>
                            <input type="hidden" id="herbal-stock-mode" value="in">
                        </div>
                        <div class="form-group">
                            <label>Jumlah</label>
                            <input type="number" required placeholder="Contoh: 5" id="herbal-change-amount" min="1" oninput="updateHerbalStockPreview()">
                            <div id="herbal-stock-preview" class="stock-preview">Pilih produk/herbal, jenis koreksi stok, dan jumlah.</div>
                        </div>
                        <div class="form-group">
                            <label>Satuan Transaksi</label>
                            <select name="multiplier" id="herbal-multiplier" onchange="updateHerbalStockPreview()">
                                <option value="1">Satuan dasar</option>
                            </select>
                            <small class="unit-field-hint">Pilih kemasan jika stok masuk/keluar berupa box, pack, dus, atau botol isi banyak.</small>
                        </div>
                        <div class="form-group">
                            <label>Alasan Koreksi</label>
                            <textarea name="reason" id="herbal-stock-reason" required minlength="5" rows="3" placeholder="Contoh: Stok opname, barang rusak, hilang, sampel"></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary" style="background:linear-gradient(135deg,#8b5cf6,#7c3aed); box-shadow:0 4px 12px rgba(139,92,246,0.35);"
                            onclick="if(!document.getElementById('herbal-selected-id').value){ showToast('Pilih produk/herbal di tabel terlebih dahulu!', 'warning'); return false; }">
                            <i class="fas fa-check"></i> Simpan Koreksi Stok
                        </button>
                    </form>
                </div>

                <!-- Form Registrasi Produk / Herbal Baru -->
                <div class="card" style="display:none; height:fit-content; border-top:3px solid #10b981;">
                    <div class="card-header">
                        <h3><i class="fas fa-plus-circle" style="color:#10b981;"></i> Registrasi Produk / Herbal</h3>
                    </div>
                    <form action="/add_herbal" method="post">
                        <div class="unit-help-note compact">
                            Dasar = stok terkecil. Kemasan = bungkus besar. Contoh: 1 box = 12 botol.
                        </div>
                        <div class="form-group">
                            <label>Nama Produk / Herbal</label>
                            <input type="text" name="name" required placeholder="Ketik nama produk...">
                        </div>
                        <div class="form-group">
                            <label>Satuan Dasar</label>
                            ${herbalUnitSelectHtml('unit', 'botol')}
                        </div>
                        <div class="form-group">
                            <label>Satuan Kemasan</label>
                            ${herbalUnitSelectHtml('package_unit', '', true)}
                        </div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                            <div class="form-group">
                                <label>Stok Awal</label>
                                <input type="number" name="stock" required placeholder="0" min="0">
                            </div>
                            <div class="form-group">
                                <label>Isi/Kemasan</label>
                                <input type="number" name="package_size" required value="1" min="1">
                            </div>
                            <div class="form-group">
                                <label>Modal (Rp)</label>
                                <input type="number" name="cost_price" required placeholder="0" min="0">
                            </div>
                            <div class="form-group">
                                <label>Harga (Rp)</label>
                                <input type="number" name="price" required placeholder="100000" min="0">
                            </div>
                            <div class="form-group">
                                <label>Batas Aman</label>
                                <input type="number" name="min_stock" required placeholder="5" min="0">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary" style="background:linear-gradient(135deg,#10b981,#059669); box-shadow:0 4px 12px rgba(16,185,129,0.35);">
                            <i class="fas fa-save"></i> Simpan Produk / Herbal Baru
                        </button>
                    </form>
                </div>
            </div>
        </div>
        <div class="card" style="margin-top:18px;padding:0;">
            <div class="card-header" style="padding:16px 20px 12px;">
                <h3><i class="fas fa-history"></i> Riwayat Koreksi</h3>
                <span style="font-size:12px;color:var(--text-muted);">Koreksi stok, retur, dan void invoice terakhir.</span>
            </div>
            <div id="correction-history-panel" style="padding:12px 20px 18px;color:var(--text-muted);font-size:13px;">
                Memuat riwayat koreksi...
            </div>
        </div>`;
    const displayArea = document.getElementById('display-area');
    if (displayArea)
        displayArea.innerHTML = html;
    loadCorrectionHistory();
}
// ── ROW SELECTION ─────────────────────────────────────────────────────────────
function selectHerbal(row) {
    // Deselect all
    document.querySelectorAll('#herbals-table tbody tr').forEach(r => {
        r.classList.remove('row-selected');
        r.style.background = r.dataset.rowbg || '';
    });
    // Select clicked
    row.classList.add('row-selected');
    row.style.background = '#ede9fe';
    // Fill form
    const id = row.dataset.id;
    const name = row.dataset.name;
    const stock = row.dataset.stock;
    const unit = row.dataset.unit || 'pcs';
    const packageUnit = row.dataset.packageUnit || '';
    const packageSize = Math.max(1, Number(row.dataset.packageSize || 1));
    const selectedId = herbalInput('herbal-selected-id');
    if (selectedId)
        selectedId.value = id || '';
    const multiplier = herbalSelect('herbal-multiplier');
    if (multiplier) {
        multiplier.innerHTML = `<option value="1">${escapeHtml(unit)}</option>`;
        if (packageUnit && packageUnit !== unit && packageSize > 1) {
            multiplier.innerHTML += `<option value="${packageSize}">${escapeHtml(packageUnit)} (1 = ${packageSize} ${escapeHtml(unit)})</option>`;
        }
    }
    const badge = document.getElementById('herbal-selected-badge');
    if (badge) {
        badge.innerHTML = `<i class="fas fa-leaf" style="color:#10b981;"></i> <strong>${name}</strong> <span style="color:#94a3b8;font-size:11px;">(stok: ${stock} ${unit})</span>`;
        badge.style.background = '#f0fdf4';
        badge.style.borderColor = '#6ee7b7';
        badge.style.color = '#059669';
    }
    // Focus change input
    updateHerbalStockPreview();
    const inp = document.getElementById('herbal-change-amount');
    if (inp)
        inp.focus();
}
// ── CRUD ACTIONS ─────────────────────────────────────────────────────────────
function setHerbalStockMode(mode) {
    const cleanMode = mode === 'out' ? 'out' : 'in';
    const input = herbalInput('herbal-stock-mode');
    if (input)
        input.value = cleanMode;
    document.querySelectorAll('.stock-mode-picker[data-target="herbal"] button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === cleanMode);
    });
    updateHerbalStockPreview();
}
function updateHerbalStockPreview() {
    const selected = herbalInput('herbal-selected-id')?.value;
    const amount = Math.max(0, Number(herbalInput('herbal-change-amount')?.value || 0));
    const multiplier = Math.max(1, Number(herbalSelect('herbal-multiplier')?.value || 1));
    const mode = herbalInput('herbal-stock-mode')?.value === 'out' ? 'out' : 'in';
    const preview = document.getElementById('herbal-stock-preview');
    if (!preview)
        return;
    const action = mode === 'out' ? 'berkurang (bukan penjualan)' : 'bertambah';
    const total = amount * multiplier;
    const selectedUnit = herbalSelect('herbal-multiplier')?.selectedOptions?.[0]?.textContent || 'item';
    preview.classList.toggle('danger', mode === 'out');
    preview.textContent = selected && amount > 0
        ? `Stok produk/herbal akan ${action}: ${amount} ${selectedUnit} = ${total} satuan dasar.`
        : 'Pilih produk/herbal, jenis koreksi stok, dan jumlah.';
}
function prepareHerbalStockSubmit(event) {
    const amount = Math.max(0, Number(herbalInput('herbal-change-amount')?.value || 0));
    const mode = herbalInput('herbal-stock-mode')?.value === 'out' ? 'out' : 'in';
    const reason = document.getElementById('herbal-stock-reason')?.value.trim() || '';
    const hidden = herbalInput('herbal-change-input');
    if (hidden)
        hidden.value = String(mode === 'out' ? -amount : amount);
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
function _herbalSaleOptions() {
    const items = window._herbalCatalog || [];
    if (!items.length)
        return '<option value="">Belum ada produk/herbal aktif</option>';
    let opts = '<option value="">- Pilih Produk / Herbal -</option>';
    items.forEach((h) => {
        opts += `<option value="${h.id}">${escapeHtml(h.name)} - stok ${h.stock} ${escapeHtml(h.unit)} - ${formatRupiah(h.price)}</option>`;
    });
    return opts;
}
function _selectedHerbalSaleItem() {
    const id = Number(herbalSelect('herbal-sale-select')?.value || 0);
    return (window._herbalCatalog || []).find((h) => h.id === id) || null;
}
function _herbalSaleUsedQty(herbalId) {
    return (window._herbalSaleItems || [])
        .filter((item) => item.herbal_id === herbalId)
        .reduce((sum, item) => sum + item.quantity, 0);
}
function openHerbalSaleModal() {
    window._herbalSaleItems = [];
    const html = `
        <div class="form-group">
            <label>Nama Pembeli <span style="color:#94a3b8;font-size:10px;text-transform:none;">(opsional)</span></label>
            <input type="text" id="herbal-sale-buyer" placeholder="Nama pembeli / umum">
        </div>
        <div class="form-group">
            <label>Pilih Produk / Herbal</label>
            <select id="herbal-sale-select" onchange="onHerbalSaleSelectChange()">${_herbalSaleOptions()}</select>
            <div id="herbal-sale-info" style="font-size:12px;color:var(--text-muted);margin-top:6px;">Pilih produk/herbal untuk melihat stok dan harga.</div>
        </div>
        <div style="display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;">
            <input type="number" id="herbal-sale-qty" min="1" placeholder="Jumlah" oninput="onHerbalSaleQtyInput()">
            <button type="button" class="btn btn-primary" onclick="addHerbalSaleItem()" style="padding:8px 12px;background:#10b981;"><i class="fas fa-plus"></i> Tambah</button>
        </div>
        <div id="herbal-sale-warning" style="display:none;margin-top:8px;color:#b91c1c;font-size:12px;font-weight:600;"></div>
        <div id="herbal-sale-list" style="margin-top:12px;"></div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding-top:10px;border-top:1px solid #e2e8f0;">
            <span style="color:var(--text-muted);font-size:13px;">Total penjualan</span>
            <strong id="herbal-sale-total">Rp0</strong>
        </div>
        <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:20px;">
            <button type="button" class="btn" onclick="closeModal()" style="background:#f1f5f9;color:#475569;">Batal</button>
            <button type="button" class="btn btn-primary" onclick="submitHerbalSale()" style="background:#10b981;"><i class="fas fa-save"></i> Simpan Penjualan</button>
        </div>
    `;
    openModal('Penjualan Produk / Herbal', html);
    syncHerbalSaleItems();
}
function onHerbalSaleSelectChange() {
    const herbal = _selectedHerbalSaleItem();
    const info = document.getElementById('herbal-sale-info');
    if (!info)
        return;
    if (!herbal) {
        info.textContent = 'Pilih produk/herbal untuk melihat stok dan harga.';
        return;
    }
    info.textContent = `${herbal.name} - stok ${herbal.stock} ${herbal.unit} - ${formatRupiah(herbal.price)}`;
    onHerbalSaleQtyInput();
}
function onHerbalSaleQtyInput() {
    const herbal = _selectedHerbalSaleItem();
    const qty = Number(herbalInput('herbal-sale-qty')?.value || 0);
    const warning = document.getElementById('herbal-sale-warning');
    if (!warning)
        return;
    warning.style.display = 'none';
    warning.textContent = '';
    if (!herbal || qty <= 0)
        return;
    const used = _herbalSaleUsedQty(herbal.id);
    if (used + qty > herbal.stock) {
        warning.textContent = `Stok ${herbal.name} tidak cukup. Tersedia ${herbal.stock}, sudah dipilih ${used}.`;
        warning.style.display = 'block';
    }
}
function addHerbalSaleItem() {
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
    const existing = (window._herbalSaleItems || []).find((item) => item.herbal_id === herbal.id);
    if (existing) {
        existing.quantity += qty;
    }
    else {
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
    if (qtyInput)
        qtyInput.value = '';
    syncHerbalSaleItems();
}
function removeHerbalSaleItem(herbalId) {
    window._herbalSaleItems = (window._herbalSaleItems || []).filter((item) => item.herbal_id !== herbalId);
    syncHerbalSaleItems();
}
function _herbalSaleTotal() {
    return (window._herbalSaleItems || []).reduce((sum, item) => sum + Number(item.price || 0) * Number(item.quantity || 0), 0);
}
function syncHerbalSaleItems() {
    const list = document.getElementById('herbal-sale-list');
    const items = window._herbalSaleItems || [];
    if (list) {
        if (!items.length) {
            list.innerHTML = '<div style="font-size:12px;color:var(--text-muted);padding:10px;background:#f8fafc;border-radius:6px;">Belum ada item penjualan.</div>';
        }
        else {
            list.innerHTML = items.map((item) => {
                const subtotal = Number(item.price || 0) * Number(item.quantity || 0);
                return `
                    <div style="display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;border:1px solid #e2e8f0;border-radius:6px;padding:8px;margin-top:6px;">
                        <div style="min-width:0;">
                            <div style="font-weight:700;font-size:13px;">${escapeHtml(item.name)}</div>
                            <div style="font-size:12px;color:var(--text-muted);">${item.quantity} ${escapeHtml(item.unit)} x ${formatRupiah(item.price)} = ${formatRupiah(subtotal)}</div>
                        </div>
                        <button type="button" onclick="removeHerbalSaleItem(${item.herbal_id})" title="Hapus item" style="border:none;background:#fee2e2;color:#b91c1c;border-radius:5px;padding:5px 7px;cursor:pointer;"><i class="fas fa-trash"></i></button>
                    </div>`;
            }).join('');
        }
    }
    const total = document.getElementById('herbal-sale-total');
    if (total)
        total.textContent = formatRupiah(_herbalSaleTotal());
    onHerbalSaleQtyInput();
}
function validateHerbalSaleStock() {
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
async function submitHerbalSale() {
    if (!validateHerbalSaleStock())
        return;
    const buyerName = herbalInput('herbal-sale-buyer')?.value.trim() || 'Umum';
    const lines = [`Pembeli: ${buyerName}`, ''];
    (window._herbalSaleItems || []).forEach((item) => {
        const subtotal = Number(item.price || 0) * Number(item.quantity || 0);
        lines.push(`- ${item.name} x${item.quantity} ${item.unit} = ${formatRupiah(subtotal)}`);
    });
    lines.push('', `Total: ${formatRupiah(_herbalSaleTotal())}`, 'Stok akan dikurangi setelah penjualan disimpan.');
    const ok = await showConfirm(lines.join('\n'), 'warning', {
        confirmText: 'Simpan Penjualan',
        cancelText: 'Batal',
        maxWidth: '460px'
    });
    if (!ok)
        return;
    const form = new FormData();
    form.append('buyer_name', buyerName === 'Umum' ? '' : buyerName);
    form.append('items', JSON.stringify((window._herbalSaleItems || []).map((item) => ({
        herbal_id: item.herbal_id,
        quantity: item.quantity
    }))));
    try {
        const response = await fetch('/herbals/sale', { method: 'POST', body: form });
        const data = await response.json();
        if (!response.ok || data.status !== 'success') {
            throw new Error(herbalText(data.detail || data.message, 'Gagal menyimpan penjualan produk/herbal.'));
        }
        closeModal();
        showToast(data.message, 'success');
        loadTab('herbals');
    }
    catch (error) {
        showToast(herbalErrorMessage(error), 'error');
    }
}
function _formatCorrectionDate(value) {
    if (!value)
        return '-';
    const text = String(value);
    const date = new Date(text);
    if (Number.isNaN(date.getTime()))
        return text;
    return date.toLocaleString('id-ID', { dateStyle: 'short', timeStyle: 'short' });
}
async function loadCorrectionHistory() {
    const panel = document.getElementById('correction-history-panel');
    if (!panel)
        return;
    try {
        const response = await fetch('/correction_logs?limit=20');
        const rows = await response.json();
        if (!response.ok)
            throw new Error(herbalText(Array.isArray(rows) ? '' : rows.detail, 'Gagal memuat riwayat koreksi.'));
        if (!Array.isArray(rows))
            throw new Error('Gagal memuat riwayat koreksi.');
        if (!rows.length) {
            panel.innerHTML = '<div style="padding:12px;background:#f8fafc;border-radius:6px;">Belum ada riwayat koreksi.</div>';
            return;
        }
        const labelMap = {
            stock_correction: 'Koreksi Stok',
            return: 'Retur',
            void_invoice: 'Void Invoice'
        };
        panel.innerHTML = `
            <div style="overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;font-size:12px;">
                    <thead>
                        <tr style="background:#f8fafc;">
                            <th style="text-align:left;padding:9px;">Tanggal</th>
                            <th style="text-align:left;padding:9px;">Tipe</th>
                            <th style="text-align:left;padding:9px;">Objek</th>
                            <th style="text-align:center;padding:9px;">Stok</th>
                            <th style="text-align:left;padding:9px;">Alasan</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows.map((row) => {
            const stockText = row.stock_before === null || row.stock_after === null
                ? '-'
                : `${row.stock_before} -> ${row.stock_after}`;
            const objectText = row.herbal_name || `${row.reference_type || '-'} #${row.reference_id || '-'}`;
            return `
                                <tr style="border-bottom:1px solid #eef2f7;">
                                    <td style="padding:9px;color:var(--text-muted);">${escapeHtml(_formatCorrectionDate(row.created_at))}</td>
                                    <td style="padding:9px;font-weight:700;">${escapeHtml(labelMap[row.action_type || ''] || row.action_type || '-')}</td>
                                    <td style="padding:9px;">${escapeHtml(objectText)}</td>
                                    <td style="padding:9px;text-align:center;">${escapeHtml(stockText)}</td>
                                    <td style="padding:9px;color:var(--text-muted);">${escapeHtml(row.reason || '-')}</td>
                                </tr>`;
        }).join('')}
                    </tbody>
                </table>
            </div>`;
    }
    catch (error) {
        panel.innerHTML = `<div style="padding:12px;background:#fef2f2;color:#b91c1c;border-radius:6px;">${escapeHtml(herbalErrorMessage(error))}</div>`;
    }
}
async function openHerbalReturnModal() {
    const html = `
        <div class="form-group">
            <label>Transaksi Penjualan</label>
            <select id="herbal-return-transaction">
                <option value="">Memuat transaksi...</option>
            </select>
            <div id="herbal-return-info" style="font-size:12px;color:var(--text-muted);margin-top:6px;">Pilih transaksi yang akan diretur.</div>
        </div>
        <div class="form-group">
            <label>Jumlah Retur</label>
            <input type="number" id="herbal-return-qty" min="1" required placeholder="Jumlah item">
        </div>
        <div class="form-group">
            <label>Alasan Retur</label>
            <textarea id="herbal-return-reason" rows="3" minlength="5" required placeholder="Contoh: Barang dikembalikan pelanggan"></textarea>
        </div>
        <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:20px;">
            <button type="button" class="btn" onclick="closeModal()" style="background:#f1f5f9;color:#475569;">Batal</button>
            <button type="button" class="btn btn-primary" onclick="submitHerbalReturn()" style="background:#f59e0b;"><i class="fas fa-undo"></i> Catat Retur</button>
        </div>
    `;
    openModal('Retur Penjualan Produk / Herbal', html);
    try {
        const response = await fetch('/herbals/transactions?page=1&page_size=50&transaction_type=sale');
        const payload = await response.json();
        if (!response.ok)
            throw new Error(payload.detail || 'Gagal memuat transaksi penjualan.');
        const select = herbalSelect('herbal-return-transaction');
        const rows = payload.data || [];
        if (!select)
            return;
        if (!rows.length) {
            select.innerHTML = '<option value="">Belum ada transaksi penjualan</option>';
            return;
        }
        select.innerHTML = '<option value="">- Pilih Transaksi -</option>' + rows.map((row) => {
            const label = `${_formatCorrectionDate(row.date)} - ${row.herbal_name} x${row.quantity} - ${formatRupiah(row.total_price)}`;
            return `<option value="${row.id}" data-qty="${row.quantity}" data-name="${escapeHtml(row.herbal_name)}">${escapeHtml(label)}</option>`;
        }).join('');
        select.onchange = () => {
            const option = select.options[select.selectedIndex];
            const info = document.getElementById('herbal-return-info');
            const qty = option?.dataset?.qty || '';
            if (info)
                info.textContent = qty ? `Maksimal retur awal: ${qty} item. Sistem tetap mengecek sisa retur di backend.` : 'Pilih transaksi yang akan diretur.';
        };
    }
    catch (error) {
        const select = herbalSelect('herbal-return-transaction');
        if (select)
            select.innerHTML = `<option value="">${escapeHtml(herbalErrorMessage(error))}</option>`;
    }
}
async function submitHerbalReturn() {
    const transactionId = herbalSelect('herbal-return-transaction')?.value;
    const quantity = Number(herbalInput('herbal-return-qty')?.value || 0);
    const reason = document.getElementById('herbal-return-reason')?.value.trim() || '';
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
    if (!ok)
        return;
    const form = new FormData();
    form.append('transaction_id', transactionId);
    form.append('quantity', String(quantity));
    form.append('reason', reason);
    try {
        const response = await fetch('/herbals/return', { method: 'POST', body: form });
        const data = await response.json();
        if (!response.ok || data.status !== 'success') {
            throw new Error(herbalText(data.detail || data.message, 'Gagal mencatat retur.'));
        }
        closeModal();
        showToast(data.message, 'success');
        loadTab('herbals');
    }
    catch (error) {
        showToast(herbalErrorMessage(error), 'error');
    }
}
function editHerbal(id, name, unit, price, stock, costPrice = 0, packageUnit = '', packageSize = 1, minStock = 5) {
    const html = `
        <form id="edit-herbal-form" onsubmit="submitEditHerbal(event)">
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
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="form-group">
                    <label>Satuan Kemasan</label>
                    ${herbalUnitSelectHtml('package_unit', packageUnit, true)}
                </div>
                <div class="form-group">
                    <label>Isi per Kemasan</label>
                    <input type="number" name="package_size" value="${Number(packageSize || 1)}" required min="1">
                </div>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
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
            <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
                <button type="button" class="btn" onclick="closeModal()" style="background:#f1f5f9;color:#475569;">Batal</button>
                <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Simpan</button>
            </div>
        </form>
    `;
    openModal('Edit Produk / Herbal', html);
}
async function submitEditHerbal(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    // Disable button during submit
    const btn = form.querySelector('button[type="submit"]');
    if (!btn)
        return;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
    btn.disabled = true;
    try {
        const response = await fetch('/edit_herbal', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.status === 'success') {
            closeModal();
            showToast(data.message, 'success');
            loadTab('herbals');
        }
        else {
            showToast(data.message || data.detail || 'Gagal menyimpan perubahan.', 'error');
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }
    catch (err) {
        showToast('Koneksi gagal saat menyimpan perubahan.', 'error');
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
async function deleteHerbal(id, name) {
    const decodedName = new DOMParser().parseFromString(name, 'text/html').documentElement.textContent;
    if (await showConfirm(`Apakah Anda yakin ingin menghapus produk/herbal "${decodedName}"?`)) {
        const formData = new FormData();
        formData.append('herbal_id', String(id));
        fetch('/delete_herbal', {
            method: 'POST',
            body: formData
        })
            .then(res => res.json())
            .then((data) => {
            if (data.status === 'success') {
                showToast(data.message, 'success');
                loadTab('herbals');
            }
            else {
                showToast(data.message || data.detail || 'Gagal menghapus produk/herbal.', 'error');
            }
        })
            .catch(() => showToast('Koneksi gagal saat menghapus produk/herbal.', 'error'));
    }
}
window.renderHerbals = renderHerbals;
window.selectHerbal = selectHerbal;
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
window.submitHerbalReturn = submitHerbalReturn;
window.editHerbal = editHerbal;
window.submitEditHerbal = submitEditHerbal;
window.deleteHerbal = deleteHerbal;
