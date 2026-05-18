"use strict";
const SERVICE_CATEGORY_OPTIONS = [
    { value: 'therapy', label: 'Terapi' },
    { value: 'consultation', label: 'Konsultasi' },
    { value: 'package', label: 'Paket' },
    { value: 'general', label: 'Umum' },
];
window._serviceInventoryList = window._serviceInventoryList || [];
window._serviceUsageDrafts = window._serviceUsageDrafts || {};
window._serviceUnitPresets = window._serviceUnitPresets || ['sesi', 'titik', 'paket', 'layanan', 'area', 'menit', 'jam', 'kali', 'orang', 'item'];
window._serviceFilter = window._serviceFilter || 'active';
function serviceUnitPicker(inputId, value = 'sesi') {
    const currentValue = value || 'sesi';
    const selectedPreset = window._serviceUnitPresets.some(unit => unit.toLowerCase() === String(currentValue).toLowerCase());
    const presetOptions = window._serviceUnitPresets.map(unit => `<option value="${escapeHtml(unit)}" ${String(currentValue).toLowerCase() === unit ? 'selected' : ''}>${escapeHtml(unit)}</option>`).join('');
    return `
        <div class="service-unit-picker">
            <select aria-label="Pilih satuan cepat" onchange="setServiceUnitValue('${inputId}', this.value)">
                <option value="">Pilih satuan...</option>
                ${presetOptions}
                <option value="__custom" ${selectedPreset ? '' : 'selected'}>Satuan lainnya...</option>
            </select>
            <input type="text" id="${inputId}" class="service-unit-custom ${selectedPreset ? 'is-hidden' : ''}" name="unit_label" value="${escapeHtml(currentValue)}" required placeholder="Ketik satuan khusus">
        </div>
        <div class="field-helper">Pilih satuan cepat. Gunakan "Satuan lainnya" untuk satuan khusus.</div>
    `;
}
function setServiceUnitValue(inputId, value) {
    const input = document.getElementById(inputId);
    if (!input)
        return;
    if (value === '__custom') {
        input.classList.remove('is-hidden');
        input.value = '';
        input.focus();
        return;
    }
    if (value)
        input.value = value;
    input.classList.add('is-hidden');
}
function servicePricingTypeLabel(type) {
    return type === 'fixed' ? 'Harga tetap' : 'Per satuan';
}
function serviceCategoryLabel(category) {
    const value = String(category || 'general').trim().toLowerCase();
    return SERVICE_CATEGORY_OPTIONS.find(option => option.value === value)?.label || value.replace(/_/g, ' ') || 'Umum';
}
function servicePricingFields(prefix, service) {
    const pricingType = (service?.pricing_type === 'fixed' ? 'fixed' : 'per_unit');
    const category = service?.service_category || 'general';
    const fixedPrice = Number(service?.fixed_price || 0);
    const allowManualPrice = service?.allow_manual_price !== false;
    return `
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
            <div class="form-group">
                <label>Mode Harga</label>
                <select name="pricing_type" id="${prefix}-pricing-type" onchange="syncServicePricingMode('${prefix}')">
                    <option value="per_unit" ${pricingType === 'per_unit' ? 'selected' : ''}>Per satuan</option>
                    <option value="fixed" ${pricingType === 'fixed' ? 'selected' : ''}>Harga tetap / paket</option>
                </select>
                <div class="field-helper">Per satuan = qty × harga. Harga tetap = total paket.</div>
            </div>
            <div class="form-group">
                <label>Kategori Layanan</label>
                <select name="service_category">
                    ${SERVICE_CATEGORY_OPTIONS.map(option => `<option value="${escapeHtml(option.value)}" ${option.value === category ? 'selected' : ''}>${escapeHtml(option.label)}</option>`).join('')}
                </select>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
            <div class="form-group" id="${prefix}-price-per-unit-group">
                <label>Harga per Satuan</label>
                <input type="number" name="price_per_unit" id="${prefix}-price-per-unit" value="${Number(service?.price_per_unit || 0)}" min="0" step="1000">
            </div>
            <div class="form-group" id="${prefix}-fixed-price-group">
                <label>Harga Tetap / Paket</label>
                <input type="number" name="fixed_price" id="${prefix}-fixed-price" value="${fixedPrice}" min="0" step="1000">
            </div>
        </div>
        <label style="display:flex; gap:8px; align-items:flex-start; margin:2px 0 12px; font-size:12px; color:var(--text-muted);">
            <input type="checkbox" name="allow_manual_price" value="true" ${allowManualPrice ? 'checked' : ''} style="margin-top:2px;">
            <span>Izinkan operator mengubah harga manual saat input kunjungan.</span>
        </label>
    `;
}
function syncServicePricingMode(prefix) {
    const typeSelect = document.getElementById(`${prefix}-pricing-type`);
    const fixedGroup = document.getElementById(`${prefix}-fixed-price-group`);
    const perUnitGroup = document.getElementById(`${prefix}-price-per-unit-group`);
    const pricingType = typeSelect?.value === 'fixed' ? 'fixed' : 'per_unit';
    if (fixedGroup)
        fixedGroup.style.display = pricingType === 'fixed' ? '' : 'none';
    if (perUnitGroup)
        perUnitGroup.style.display = pricingType === 'fixed' ? 'none' : '';
}
async function ensureServiceInventoryLoaded(servicesData) {
    if (window._serviceInventoryLoaded)
        return;
    try {
        window._serviceInventoryList = await apiGetJson('/inventory');
    }
    catch (error) {
        window._serviceInventoryList = [];
    }
    finally {
        window._serviceInventoryLoaded = true;
        if (servicesData)
            renderServices(servicesData);
    }
}
function serviceInventoryOptions(selectedId) {
    const items = window._serviceInventoryList || [];
    if (!items.length)
        return '<option value="">Inventaris belum tersedia</option>';
    return '<option value="">- Pilih Inventaris -</option>' + items.map(item => `<option value="${item.id}" data-unit="${escapeHtml(item.unit || '')}" ${Number(selectedId) === Number(item.id) ? 'selected' : ''}>${escapeHtml(item.item_name)} (${item.quantity} ${escapeHtml(item.unit || '')})</option>`).join('');
}
function serviceUsageSummary(usage) {
    const items = Array.isArray(usage) ? usage : [];
    if (!items.length)
        return 'Belum ada pemakaian inventaris otomatis.';
    return items.map(item => `${escapeHtml(item.item_name || 'Inventaris')} ${item.quantity} ${escapeHtml(item.unit || '')}`).join(' - ');
}
function buildServiceUsageEditor(prefix, usage) {
    window._serviceUsageDrafts[prefix] = (Array.isArray(usage) ? usage : []).map(item => ({
        inventory_id: Number(item.inventory_id || 0),
        item_name: item.item_name || '',
        unit: item.unit || '',
        quantity: Number(item.quantity || 1)
    })).filter(item => item.inventory_id && item.quantity > 0);
    return `
        <div class="service-usage-editor">
            <div class="service-usage-head">
                <div>
                    <strong>Pemakaian Inventaris Otomatis</strong>
                    <span>Stok ini dipotong otomatis setiap kunjungan memakai layanan ini.</span>
                </div>
            </div>
            <input type="hidden" name="inventory_usage" id="${prefix}-inventory-usage-input" value="[]">
            <div class="service-usage-add">
                <select id="${prefix}-usage-inventory">${serviceInventoryOptions()}</select>
                <input type="number" id="${prefix}-usage-qty" min="1" placeholder="Jumlah">
                <button type="button" class="btn btn-secondary" onclick="addServiceUsageItem('${prefix}')"><i class="fas fa-plus"></i> Tambah</button>
            </div>
            <div id="${prefix}-usage-list" class="service-usage-list"></div>
        </div>
    `;
}
function renderServiceUsageList(prefix) {
    const list = document.getElementById(`${prefix}-usage-list`);
    if (!list)
        return;
    const items = window._serviceUsageDrafts[prefix] || [];
    if (!items.length) {
        list.innerHTML = '<div class="service-usage-empty">Belum ada inventaris otomatis untuk layanan ini.</div>';
        syncServiceUsageInput(prefix);
        return;
    }
    list.innerHTML = items.map((item, index) => `
        <div class="service-usage-row">
            <span><strong>${escapeHtml(item.item_name)}</strong><small>${item.quantity} ${escapeHtml(item.unit || '')} per kunjungan</small></span>
            <button type="button" onclick="removeServiceUsageItem('${prefix}', ${index})" title="Hapus item"><i class="fas fa-trash-alt"></i></button>
        </div>
    `).join('');
    syncServiceUsageInput(prefix);
}
function addServiceUsageItem(prefix) {
    const select = document.getElementById(`${prefix}-usage-inventory`);
    const qtyInput = document.getElementById(`${prefix}-usage-qty`);
    const inventoryId = Number(select?.value || 0);
    const quantity = Number(qtyInput?.value || 0);
    if (!inventoryId || quantity <= 0) {
        showToast('Pilih inventaris dan isi jumlah pemakaian.', 'warning');
        return;
    }
    const option = select?.options[select.selectedIndex];
    const itemName = option ? (option.textContent || '').replace(/\s*\([^)]*\)\s*$/, '') : 'Inventaris';
    const unit = option ? (option.dataset.unit || '') : '';
    const draft = window._serviceUsageDrafts[prefix] || [];
    const existing = draft.find(item => item.inventory_id === inventoryId);
    if (existing) {
        existing.quantity = quantity;
    }
    else {
        draft.push({ inventory_id: inventoryId, item_name: itemName, unit, quantity });
    }
    window._serviceUsageDrafts[prefix] = draft;
    if (qtyInput)
        qtyInput.value = '';
    renderServiceUsageList(prefix);
}
function removeServiceUsageItem(prefix, index) {
    const draft = window._serviceUsageDrafts[prefix] || [];
    draft.splice(index, 1);
    window._serviceUsageDrafts[prefix] = draft;
    renderServiceUsageList(prefix);
}
function syncServiceUsageInput(prefix) {
    const input = document.getElementById(`${prefix}-inventory-usage-input`);
    if (!input)
        return true;
    input.value = JSON.stringify((window._serviceUsageDrafts[prefix] || []).map(item => ({
        inventory_id: item.inventory_id,
        quantity: item.quantity
    })));
    return true;
}
function renderServices(data) {
    ensureServiceInventoryLoaded(data);
    window._serviceMap = {};
    data.forEach(service => { window._serviceMap[service.id] = service; });
    const currentFilter = window._serviceFilter || 'active';
    const activeCount = data.filter(service => service.is_active).length;
    const inactiveCount = data.length - activeCount;
    const visibleServices = data.filter(service => {
        if (currentFilter === 'inactive')
            return !service.is_active;
        if (currentFilter === 'all')
            return true;
        return !!service.is_active;
    });
    const filterButton = (filter, label, count) => `
        <button type="button" onclick="setServiceFilter('${filter}')"
            style="border:1px solid ${currentFilter === filter ? 'var(--primary)' : '#e5e7eb'};
                   background:${currentFilter === filter ? '#eef2ff' : '#fff'};
                   color:${currentFilter === filter ? 'var(--primary)' : 'var(--text-muted)'};
                   border-radius:999px; padding:5px 10px; font-size:12px; font-weight:700; cursor:pointer;">
            ${label} <span style="opacity:.72;">${count}</span>
        </button>
    `;
    const html = `
        <div class="grid-2">
            <div class="card" style="height:fit-content; border-top:3px solid var(--primary);">
                <div class="card-header">
                    <h3><i class="fas fa-plus-circle"></i> Tambah Layanan</h3>
                </div>
                <form action="/add_service" method="post" onsubmit="syncServiceUsageInput('add-service')">
                    <div class="form-group">
                        <label>Nama Layanan</label>
                        <input type="text" name="name" required placeholder="Contoh: Pijat Refleksi">
                    </div>
                    ${servicePricingFields('add-service')}
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                        <div class="form-group">
                            <label>Satuan</label>
                            ${serviceUnitPicker('add-service-unit', 'sesi')}
                        </div>
                        <div class="form-group">
                            <label>Jumlah Default</label>
                            <input type="number" name="default_quantity" value="1" min="1" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Template Catatan</label>
                        <textarea name="notes_template" class="service-notes-template" rows="4" placeholder="Keluhan; area terapi; respons pasien"></textarea>
                    </div>
                    ${buildServiceUsageEditor('add-service', [])}
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> Simpan Layanan
                    </button>
                </form>
            </div>

            <div class="card" style="padding:0;">
                <div class="card-header" style="padding:18px 20px 12px;">
                    <h3><i class="fas fa-spa"></i> Daftar Layanan
                        <span style="font-size:12px; font-weight:500; color:var(--text-muted); margin-left:6px;">${data.length} layanan</span>
                    </h3>
                    <div style="display:flex; gap:8px; font-size:12px;">
                        <span style="background:#ecfdf5; color:#059669; padding:4px 10px; border-radius:999px; font-weight:600; border:1px solid #a7f3d0;">
                            ${activeCount} Aktif
                        </span>
                        <span style="background:#f3f4f6; color:#6b7280; padding:4px 10px; border-radius:999px; font-weight:600; border:1px solid #e5e7eb;">
                            ${inactiveCount} Nonaktif
                        </span>
                    </div>
                </div>
                <div style="padding:0 20px 12px; display:flex; gap:8px; flex-wrap:wrap;">
                    ${filterButton('active', 'Aktif', activeCount)}
                    ${filterButton('inactive', 'Nonaktif', inactiveCount)}
                    ${filterButton('all', 'Semua', data.length)}
                </div>
                <div style="padding:14px; display:flex; flex-direction:column; gap:8px;">
                    ${visibleServices.length === 0 ? `
                        <div style="padding:50px; text-align:center; color:var(--text-muted);">
                            <i class="fas fa-spa" style="font-size:40px; opacity:0.15; display:block; margin-bottom:14px;"></i>
                            <p>${data.length === 0 ? 'Belum ada layanan.' : 'Tidak ada layanan pada filter ini.'}</p>
                        </div>
                    ` : visibleServices.map(service => serviceRow(service)).join('')}
                </div>
            </div>
        </div>
    `;
    const displayArea = document.getElementById('display-area');
    if (displayArea)
        displayArea.innerHTML = html;
    syncServicePricingMode('add-service');
    renderServiceUsageList('add-service');
}
function serviceRow(service) {
    const isActive = !!service.is_active;
    const pricingType = service.pricing_type === 'fixed' ? 'fixed' : 'per_unit';
    const priceLabel = pricingType === 'fixed'
        ? `Paket Rp ${Number(service.fixed_price || 0).toLocaleString('id-ID')}`
        : `${service.default_quantity} ${escapeHtml(service.unit_label || 'sesi')} - Rp ${Number(service.price_per_unit || 0).toLocaleString('id-ID')}`;
    return `
        <div style="display:flex; align-items:center; gap:12px; padding:13px 15px;
                    background:${isActive ? '#fafbff' : '#f9fafb'}; border-radius:12px;
                    border:1px solid ${isActive ? '#e0e7ff' : '#e5e7eb'};
                    opacity:${isActive ? 1 : 0.7};">
            <div style="width:44px; height:44px; border-radius:12px; background:#ecfdf5;
                        display:flex; align-items:center; justify-content:center;
                        font-size:18px; color:var(--primary); flex-shrink:0;">
                <i class="fas fa-hand-holding-medical"></i>
            </div>
            <div style="flex:1; min-width:0;">
                <div style="font-weight:700; font-size:14px;">${escapeHtml(service.name)}</div>
                <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                    ${priceLabel}
                </div>
                <div style="font-size:11px; color:var(--text-muted); margin-top:3px;">
                    ${escapeHtml(servicePricingTypeLabel(service.pricing_type))} · ${escapeHtml(serviceCategoryLabel(service.service_category))}${service.allow_manual_price === false ? ' · Harga terkunci' : ''}
                </div>
                <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">${escapeHtml(service.notes_template || '-')}</div>
                <div class="service-usage-summary"><i class="fas fa-box-open"></i> ${serviceUsageSummary(service.inventory_usage)}</div>
            </div>
            <span class="badge ${isActive ? 'badge-ok' : 'badge-low'}">
                ${isActive ? 'Aktif' : 'Nonaktif'}
            </span>
            <div style="display:flex; gap:6px; flex-shrink:0;">
                <button type="button" onclick="openEditServiceModal(${service.id}, this)" title="Edit Layanan"
                    style="width:32px; height:32px; border-radius:8px; border:1px solid #e0e7ff;
                           background:#f0f4ff; color:var(--primary); cursor:pointer;">
                    <i class="fas fa-pen"></i>
                </button>
                <button type="button" onclick="toggleService(${service.id}, this)"
                    class="activation-action mini ${isActive ? 'is-on' : 'is-off'}"
                    title="${isActive ? 'Klik untuk menonaktifkan layanan' : 'Klik untuk mengaktifkan layanan'}">
                    <i class="fas ${isActive ? 'fa-toggle-on' : 'fa-toggle-off'}"></i>
                    <span>
                        <strong>${isActive ? 'Aktif' : 'Nonaktif'}</strong>
                        <small>${isActive ? 'Matikan' : 'Aktifkan'}</small>
                    </span>
                </button>
                <button type="button" onclick="deleteService(${service.id})" title="Hapus Layanan"
                    style="width:32px; height:32px; border-radius:8px; border:1px solid #fecaca;
                           background:#fef2f2; color:var(--danger); cursor:pointer;">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </div>
        </div>
    `;
}
function openEditServiceModal(id, btn) {
    if (btn) {
        btn.disabled = true;
        btn.dataset.originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }
    window.requestAnimationFrame(() => {
        setTimeout(() => {
            try {
                renderEditServiceModal(id);
            }
            catch (error) {
                alert('Gagal membuka form edit layanan: ' + sanitizeAppErrorMessage(error));
            }
            finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = btn.dataset.originalHtml || '<i class="fas fa-pen"></i>';
                    delete btn.dataset.originalHtml;
                }
            }
        }, 0);
    });
}
function renderEditServiceModal(id) {
    const service = window._serviceMap?.[id];
    if (!service)
        return;
    if (typeof openModal !== 'function') {
        if (typeof initModals === 'function')
            initModals();
    }
    if (typeof openModal !== 'function') {
        throw new Error('Komponen modal belum siap.');
    }
    const html = `
        <form id="edit-service-form" onsubmit="submitEditService(event)">
            <input type="hidden" name="service_id" value="${service.id}">
            <input type="hidden" name="is_active" value="${service.is_active ? 'true' : 'false'}">
            <div class="form-group">
                <label>Nama Layanan</label>
                <input type="text" name="name" value="${escapeHtml(service.name)}" required>
            </div>
            ${servicePricingFields(`edit-service-${service.id}`, service)}
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="form-group">
                    <label>Satuan</label>
                    ${serviceUnitPicker(`edit-service-${service.id}-unit`, service.unit_label || 'sesi')}
                </div>
                <div class="form-group">
                    <label>Jumlah Default</label>
                    <input type="number" name="default_quantity" value="${service.default_quantity || 1}" min="1" required>
                </div>
            </div>
            <div class="form-group">
                <label>Template Catatan</label>
                <textarea name="notes_template" class="service-notes-template" rows="4">${escapeHtml(service.notes_template || '')}</textarea>
            </div>
            ${buildServiceUsageEditor(`edit-service-${service.id}`, service.inventory_usage)}
            <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
                <button type="button" class="btn" onclick="closeModal()" style="background:#f1f5f9;color:#475569;">Batal</button>
                <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Simpan</button>
            </div>
        </form>
    `;
    openModal('Edit Layanan', html);
    syncServicePricingMode(`edit-service-${service.id}`);
    renderServiceUsageList(`edit-service-${service.id}`);
}
async function submitEditService(event) {
    event.preventDefault();
    const formEl = event.target;
    if (!formEl)
        return;
    const serviceIdInput = formEl.querySelector('input[name="service_id"]');
    const serviceId = serviceIdInput?.value || '';
    syncServiceUsageInput(`edit-service-${serviceId}`);
    const btn = formEl.querySelector('button[type="submit"]');
    const originalText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
    }
    const form = new FormData(formEl);
    try {
        const data = await apiPostForm('/update_service', form);
        if (data.status === 'success') {
            closeModal();
            loadTab('services');
        }
        else {
            alert(window.LancarApi?.getErrorMessage(data, 'Gagal menyimpan layanan.') || 'Gagal menyimpan layanan.');
        }
    }
    catch (error) {
        alert('Gagal menyimpan layanan: ' + sanitizeAppErrorMessage(error));
    }
    finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
}
async function toggleService(id, btn) {
    btn.disabled = true;
    const service = window._serviceMap?.[id] || {};
    const form = new FormData();
    form.append('service_id', String(id));
    form.append('name', service.name || '');
    form.append('unit_label', service.unit_label || 'sesi');
    form.append('default_quantity', String(service.default_quantity || 1));
    form.append('price_per_unit', String(service.price_per_unit || 0));
    form.append('pricing_type', service.pricing_type || 'per_unit');
    form.append('service_category', service.service_category || 'general');
    form.append('fixed_price', String(service.fixed_price || 0));
    form.append('allow_manual_price', service.allow_manual_price === false ? 'false' : 'true');
    form.append('notes_template', service.notes_template || '');
    form.append('is_active', service.is_active ? 'false' : 'true');
    form.append('inventory_usage', JSON.stringify((service.inventory_usage || []).map(item => ({
        inventory_id: item.inventory_id,
        quantity: item.quantity
    }))));
    const data = await apiPostForm('/update_service', form);
    if (data.status === 'success') {
        loadTab('services');
    }
    else {
        btn.disabled = false;
        alert(window.LancarApi?.getErrorMessage(data, 'Gagal mengubah status layanan.') || 'Gagal mengubah status layanan.');
    }
}
async function deleteService(id) {
    const service = window._serviceMap?.[id];
    const name = service?.name || 'layanan ini';
    const ok = await showConfirm(`Hapus permanen layanan "${name}"?\n\nHapus hanya akan berhasil jika layanan belum pernah dipakai di kunjungan. Jika sudah punya riwayat, gunakan tombol Nonaktifkan agar riwayat tetap aman.`, 'error', { confirmText: 'Hapus', cancelText: 'Batal', maxWidth: '440px' });
    if (!ok)
        return;
    try {
        const form = new FormData();
        form.append('service_id', String(id));
        const data = await apiPostForm('/delete_service', form);
        if (data.status === 'success') {
            showToast(data.message || 'Layanan berhasil dihapus.', 'success');
            loadTab('services');
        }
        else {
            showToast(window.LancarApi?.getErrorMessage(data, 'Gagal menghapus layanan.') || 'Gagal menghapus layanan.', 'error');
        }
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal menghapus layanan.'), 'error');
    }
}
function setServiceFilter(filter) {
    window._serviceFilter = filter;
    renderServices(Object.values(window._serviceMap || {}));
}
window.renderServices = renderServices;
window.setServiceFilter = setServiceFilter;
window.setServiceUnitValue = setServiceUnitValue;
window.syncServicePricingMode = syncServicePricingMode;
window.addServiceUsageItem = addServiceUsageItem;
window.removeServiceUsageItem = removeServiceUsageItem;
window.syncServiceUsageInput = syncServiceUsageInput;
window.openEditServiceModal = openEditServiceModal;
window.submitEditService = submitEditService;
window.toggleService = toggleService;
window.deleteService = deleteService;
