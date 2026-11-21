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
let serviceDelegationReady = false;
function ensureServiceEventDelegation() {
    if (serviceDelegationReady)
        return;
    serviceDelegationReady = true;
    document.addEventListener('click', (event) => {
        const target = event.target;
        if (target?.classList.contains('service-modal-overlay')) {
            closeServiceModal();
            return;
        }
        const actionElement = target?.closest('[data-service-action]');
        if (!actionElement)
            return;
        const action = actionElement.dataset.serviceAction || '';
        if (!action)
            return;
        event.preventDefault();
        switch (action) {
            case 'filter':
                setServiceFilter((actionElement.dataset.filter || 'active'));
                break;
            case 'open-add':
                openServiceModal();
                break;
            case 'close-modal':
                closeServiceModal();
                break;
            case 'edit':
                openEditServiceModal(actionElement.dataset.serviceId || '');
                break;
            case 'toggle':
                toggleService(actionElement.dataset.serviceId || '', actionElement);
                break;
            case 'delete':
                deleteService(actionElement.dataset.serviceId || '');
                break;
            case 'usage-add':
                addServiceUsageItem(actionElement.dataset.prefix || '');
                break;
            case 'usage-remove':
                removeServiceUsageItem(actionElement.dataset.prefix || '', Number(actionElement.dataset.index || 0));
                break;
        }
    });
    document.addEventListener('change', (event) => {
        const target = event.target;
        const action = target?.dataset?.serviceAction || '';
        if (action === 'unit-select') {
            setServiceUnitValue(target.dataset.inputId || '', target.value);
        }
        if (action === 'pricing-mode') {
            syncServicePricingMode(target.dataset.prefix || '');
        }
    });
    document.addEventListener('submit', (event) => {
        const form = event.target;
        const action = form?.dataset?.serviceFormAction || '';
        if (action === 'add') {
            syncServiceUsageInput(form.dataset.prefix || 'add-service');
        }
        if (action === 'edit') {
            submitEditService(event);
        }
    });
}
function serviceUnitPicker(inputId, value = 'sesi') {
    const currentValue = value || 'sesi';
    const selectedPreset = window._serviceUnitPresets.some(unit => unit.toLowerCase() === String(currentValue).toLowerCase());
    const presetOptions = window._serviceUnitPresets.map(unit => `<option value="${escapeHtml(unit)}" ${String(currentValue).toLowerCase() === unit ? 'selected' : ''}>${escapeHtml(unit)}</option>`).join('');
    return `
        <div class="service-unit-picker">
            <select aria-label="Pilih satuan cepat" data-service-action="unit-select" data-input-id="${escapeHtml(inputId)}">
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
        <div class="service-form-grid">
            <div class="form-group">
                <label>Mode Harga</label>
                <select name="pricing_type" id="${prefix}-pricing-type" data-service-action="pricing-mode" data-prefix="${escapeHtml(prefix)}">
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
        <div class="service-form-grid">
            <div class="form-group" id="${prefix}-price-per-unit-group">
                <label>Harga per Satuan</label>
                <input type="number" name="price_per_unit" id="${prefix}-price-per-unit" value="${Number(service?.price_per_unit || 0)}" min="0" step="1000">
            </div>
            <div class="form-group" id="${prefix}-fixed-price-group">
                <label>Harga Tetap / Paket</label>
                <input type="number" name="fixed_price" id="${prefix}-fixed-price" value="${fixedPrice}" min="0" step="1000">
            </div>
        </div>
        <label class="service-manual-price-toggle">
            <input type="checkbox" name="allow_manual_price" value="true" ${allowManualPrice ? 'checked' : ''}>
            <span>
                <strong>Harga manual saat kunjungan</strong>
                <small>Operator boleh mengubah harga saat input kunjungan.</small>
            </span>
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
                <button type="button" class="btn btn-secondary" data-service-action="usage-add" data-prefix="${escapeHtml(prefix)}"><i class="fas fa-plus"></i> Tambah</button>
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
            <button type="button" data-service-action="usage-remove" data-prefix="${escapeHtml(prefix)}" data-index="${index}" title="Hapus item"><i class="fas fa-trash-alt"></i></button>
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
    ensureServiceEventDelegation();
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
        <button type="button" data-service-action="filter" data-filter="${filter}"
            class="service-filter-btn ${currentFilter === filter ? 'is-active' : ''}">
            ${label} <span>${count}</span>
        </button>
    `;
    const html = `
        <div class="services-page">
            <div class="service-header">
                <div class="service-header-left">
                    <h2><i class="fas fa-spa"></i> Daftar Layanan</h2>
                </div>
                <button type="button" data-service-action="open-add" class="service-add-btn">
                    <i class="fas fa-plus-circle"></i> Tambah Layanan
                </button>
            </div>

            <div class="service-filter-row">
                ${filterButton('active', 'Aktif', activeCount)}
                ${filterButton('inactive', 'Nonaktif', inactiveCount)}
                ${filterButton('all', 'Semua', data.length)}
            </div>

            ${visibleServices.length === 0 ? `
                <div class="service-empty-state">
                    <i class="fas fa-spa"></i>
                    <p>${data.length === 0 ? 'Belum ada layanan. Klik "Tambah Layanan" untuk memulai.' : 'Tidak ada layanan pada filter ini.'}</p>
                </div>
            ` : `
                <div class="service-card-grid">
                    ${visibleServices.map(service => serviceCard(service)).join('')}
                </div>
            `}
        </div>
    `;
    const displayArea = document.getElementById('display-area');
    if (displayArea)
        displayArea.innerHTML = html;
}
function serviceCard(service) {
    const isActive = !!service.is_active;
    const pricingType = service.pricing_type === 'fixed' ? 'fixed' : 'per_unit';
    const priceLabel = pricingType === 'fixed'
        ? `Rp ${Number(service.fixed_price || 0).toLocaleString('id-ID')}`
        : `Rp ${Number(service.price_per_unit || 0).toLocaleString('id-ID')} / ${escapeHtml(service.unit_label || 'sesi')}`;
    const category = serviceCategoryLabel(service.service_category);
    const usageItems = Array.isArray(service.inventory_usage) ? service.inventory_usage : [];
    const hasUsage = usageItems.length > 0;
    return `
        <div class="service-card ${isActive ? '' : 'inactive'}">
            <div class="service-card-header">
                <div class="service-card-title-group">
                    <div class="service-card-icon ${pricingType}">
                        <i class="fas ${pricingType === 'fixed' ? 'fa-box' : 'fa-hand-holding-medical'}"></i>
                    </div>
                    <h3 class="service-card-name">${escapeHtml(service.name)}</h3>
                </div>
                <span class="service-card-status-badge ${isActive ? 'active' : 'inactive'}">
                    ${isActive ? 'Aktif' : 'Nonaktif'}
                </span>
            </div>
            <div class="service-card-body">
                <div class="service-card-category">
                    <i class="fas fa-tag"></i> ${escapeHtml(category)}
                </div>
                <div class="service-card-price">${priceLabel}</div>
                <div class="service-card-meta">
                    ${escapeHtml(servicePricingTypeLabel(service.pricing_type))}
                    ${service.allow_manual_price === false ? ' · <span class="text-amber-600"><i class="fas fa-lock"></i> Harga terkunci</span>' : ''}
                </div>
                ${hasUsage ? `
                    <div class="service-card-usage">
                        <i class="fas fa-box-open"></i> ${usageItems.length} item inventaris
                    </div>
                ` : ''}
            </div>
            <div class="service-card-footer">
                <button type="button" data-service-action="edit" data-service-id="${escapeHtml(service.id)}"
                    class="service-card-action edit" title="Edit">
                    <i class="fas fa-pen"></i><span>Edit</span>
                </button>
                <button type="button" data-service-action="toggle" data-service-id="${escapeHtml(service.id)}"
                    class="service-card-action toggle ${isActive ? 'active' : 'inactive'}"
                    title="${isActive ? 'Nonaktifkan' : 'Aktifkan'}">
                    <i class="fas ${isActive ? 'fa-toggle-on' : 'fa-toggle-off'}"></i><span>${isActive ? 'Nonaktifkan' : 'Aktifkan'}</span>
                </button>
                <button type="button" data-service-action="delete" data-service-id="${escapeHtml(service.id)}"
                    class="service-card-action delete" title="Hapus">
                    <i class="fas fa-trash-alt"></i><span>Hapus</span>
                </button>
            </div>
        </div>
    `;
}
function openServiceModal() {
    ensureServiceEventDelegation();
    const modalHtml = `
        <div class="service-modal-overlay">
            <div class="service-modal-content">
                <div class="service-modal-header">
                    <h3><i class="fas fa-plus-circle"></i> Tambah Layanan</h3>
                    <button type="button" data-service-action="close-modal" class="service-modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <form action="/add_service" method="post" data-service-form-action="add" data-prefix="add-service">
                    <div class="form-group">
                        <label>Nama Layanan</label>
                        <input type="text" name="name" required placeholder="Contoh: Pijat Refleksi">
                    </div>
                    ${servicePricingFields('add-service')}
                    <div class="service-form-grid">
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
                    <div class="service-modal-actions">
                        <button type="button" class="btn btn-secondary" data-service-action="close-modal">Batal</button>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Simpan Layanan
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    setTimeout(() => {
        syncServicePricingMode('add-service');
        renderServiceUsageList('add-service');
    }, 0);
}
function closeServiceModal() {
    const modal = document.querySelector('.service-modal-overlay');
    if (modal)
        modal.remove();
}
function openEditServiceModal(id) {
    const service = window._serviceMap?.[id];
    if (!service)
        return;
    const modalHtml = `
        <div class="service-modal-overlay">
            <div class="service-modal-content">
                <div class="service-modal-header">
                    <h3><i class="fas fa-pen"></i> Edit Layanan</h3>
                    <button type="button" data-service-action="close-modal" class="service-modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <form id="edit-service-form" data-service-form-action="edit">
                    <input type="hidden" name="service_id" value="${service.id}">
                    <input type="hidden" name="is_active" value="${service.is_active ? 'true' : 'false'}">
                    <div class="form-group">
                        <label>Nama Layanan</label>
                        <input type="text" name="name" value="${escapeHtml(service.name)}" required>
                    </div>
                    ${servicePricingFields(`edit-service-${service.id}`, service)}
                    <div class="service-form-grid">
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
                    <div class="service-modal-actions">
                        <button type="button" class="btn btn-secondary" data-service-action="close-modal">Batal</button>
                        <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Simpan</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    setTimeout(() => {
        syncServicePricingMode(`edit-service-${service.id}`);
        renderServiceUsageList(`edit-service-${service.id}`);
    }, 0);
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
            closeServiceModal();
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
window.openServiceModal = openServiceModal;
window.closeServiceModal = closeServiceModal;
window.openEditServiceModal = openEditServiceModal;
window.submitEditService = submitEditService;
window.toggleService = toggleService;
window.deleteService = deleteService;
