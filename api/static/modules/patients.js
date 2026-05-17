// ─── PATIENTS (Server-Side DataTable) ────────────────────────────────────────

function _normalizeTherapistsPayload(payload) {
    if (Array.isArray(payload)) return payload;
    if (payload && Array.isArray(payload.therapists)) return payload.therapists;
    return [];
}

function _cacheTherapists(payload) {
    const therapists = _normalizeTherapistsPayload(payload).filter(t => t && t.id);
    window._therapistsLoadError = null;
    window._therapistsList = therapists.map(t => ({
        id: t.id,
        name: t.name || '',
        gender: t.gender || '',
        specialization: t.specialization || '',
        is_active: t.is_active !== false,
        can_handle_any_gender: t.can_handle_any_gender === true
    }));
    window._therapistMap = {};
    window._therapistsList.forEach(t => { window._therapistMap[t.id] = t.name; });
    return window._therapistsList;
}

function _therapistsForGender(gender) {
    const therapists = window._therapistsList || [];
    return therapists.filter(t => !gender || t.gender === gender || t.can_handle_any_gender);
}

function _therapistGenderCopy(gender) {
    return gender || 'jenis kelamin pasien';
}

function _visitTherapistState(gender) {
    const hasPatient = Boolean(gender);
    const therapists = _therapistsForGender(gender);
    if (window._therapistsLoadError) {
        return {
            canSelect: false,
            option: window._therapistsLoadError,
            helper: 'Data terapis belum bisa dimuat. Coba muat ulang halaman sebelum mencatat kunjungan.'
        };
    }
    if (!hasPatient) {
        return {
            canSelect: therapists.length > 0,
            option: therapists.length ? '- Pilih Terapis -' : 'Belum ada terapis aktif',
            helper: therapists.length
                ? 'Pilih pasien dulu agar daftar terapis difilter sesuai jenis kelamin pasien.'
                : 'Belum ada terapis aktif. Tambahkan atau aktifkan terapis dulu di menu Terapis.'
        };
    }
    if (therapists.length === 0) {
        return {
            canSelect: false,
            option: `Belum ada terapis aktif yang bisa menangani pasien ${_therapistGenderCopy(gender)}`,
            helper: `Tambahkan terapis ${_therapistGenderCopy(gender)} atau aktifkan opsi lintas gender pada salah satu terapis.`
        };
    }
    return {
        canSelect: true,
        option: '- Pilih Terapis -',
        helper: `Terapis yang tampil: gender ${_therapistGenderCopy(gender)} atau terapis yang diizinkan menangani lintas gender.`
    };
}

window._visitHerbalsList = window._visitHerbalsList || [];
window._visitSelectedHerbals = window._visitSelectedHerbals || [];
window._visitDiscountRulesLoaded = window._visitDiscountRulesLoaded || false;
window._visitDiscountRuleMap = window._visitDiscountRuleMap || {};
window._visitConfirmInProgress = window._visitConfirmInProgress || false;
window._visitSubmitInProgress = window._visitSubmitInProgress || false;

function setVisitSubmitLoading(isLoading) {
    window._visitSubmitInProgress = !!isLoading;
    const submitButton = document.getElementById('visit-submit-button');
    if (!submitButton) return;
    if (isLoading) {
        if (!submitButton.dataset.originalHtml) submitButton.dataset.originalHtml = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
        submitButton.style.opacity = '0.7';
        submitButton.style.cursor = 'wait';
        return;
    }
    submitButton.disabled = false;
    if (submitButton.dataset.originalHtml) {
        submitButton.innerHTML = submitButton.dataset.originalHtml;
        delete submitButton.dataset.originalHtml;
    }
    submitButton.style.opacity = '1';
    submitButton.style.cursor = 'pointer';
}

function resetVisitSubmitLoading() {
    setVisitSubmitLoading(false);
}

function getVisitIdempotencyKey(form) {
    let input = form.querySelector('input[name="idempotency_key"]');
    if (!input) {
        input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'idempotency_key';
        form.appendChild(input);
    }
    if (!input.value) {
        const randomPart = (window.crypto && crypto.randomUUID)
            ? crypto.randomUUID()
            : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        input.value = `visit-${randomPart}`;
    }
    return input.value;
}

async function ensureVisitDiscountRulesLoaded() {
    if (window._visitDiscountRulesLoaded) return;
    try {
        const r = await fetch('/discount_rules');
        if (!r.ok) throw new Error('Gagal memuat rule diskon');
        const rules = await r.json();
        window._visitDiscountRuleMap = {};
        (Array.isArray(rules) ? rules : []).forEach(rule => {
            if (rule && rule.id) window._visitDiscountRuleMap[rule.id] = rule;
        });
    } catch (e) {
        window._visitDiscountRuleMap = {};
    } finally {
        window._visitDiscountRulesLoaded = true;
    }
}

function _visitDiscountKind(rule) {
    if (!rule) return 'Diskon';
    if (rule.type === 'voucher') return 'Voucher';
    if (rule.type === 'visit_count') return 'Rule kunjungan';
    if (rule.type === 'manual') return 'Harga manual';
    if (rule.type === 'period') return 'Promo periode';
    return 'Diskon';
}

function getVisitDiscountInfo(v) {
    const finalPrice = Number(v?.final_price ?? v?.price ?? 0);
    if (v?.is_free_visit) {
        return {
            title: 'Kunjungan gratis',
            detail: v.free_visit_reason || '-',
            finalPrice,
            color: '#059669',
            bg: '#ecfdf5',
            border: '#a7f3d0'
        };
    }

    const rule = v?.discount_rule_id ? window._visitDiscountRuleMap[v.discount_rule_id] : null;
    if (v?.discount_applied || v?.discount_rule_id || v?.discount_rule_name) {
        return {
            title: _visitDiscountKind(rule),
            detail: v.discount_rule_name || rule?.name || 'Diskon terpakai',
            finalPrice,
            color: '#7c3aed',
            bg: '#f5f3ff',
            border: '#ddd6fe'
        };
    }

    return {
        title: 'Harga normal',
        detail: 'Tanpa voucher atau rule diskon',
        finalPrice,
        color: '#475569',
        bg: '#f8fafc',
        border: '#e2e8f0'
    };
}

function renderVisitDiscountBadge(v) {
    const info = getVisitDiscountInfo(v);
    return `<div class="visit-price-cell">
        <strong class="visit-price-main" style="color:${info.color};">${formatRupiah(info.finalPrice)}</strong>
        <span class="visit-price-badge" style="color:${info.color};background:${info.bg};border-color:${info.border};">${escapeHtml(info.title)}</span>
        <span class="visit-price-sub">${escapeHtml(info.detail)}</span>
    </div>`;
}

function getVisitUnitLabel(v) {
    const services = Array.isArray(window._servicesList) ? window._servicesList : [];
    const byId = v?.service_id ? services.find(service => String(service.id) === String(v.service_id)) : null;
    const serviceName = String(v?.service_name || '').trim().toLowerCase();
    const byName = !byId && serviceName
        ? services.find(service => String(service.name || '').trim().toLowerCase() === serviceName)
        : null;
    const unit = byId?.unit_label || byName?.unit_label;
    if (unit) return String(unit).trim();
    if (serviceName === 'bekam') return 'titik';
    return 'sesi';
}

function _cacheVisitHerbals(payload) {
    const herbals = Array.isArray(payload) ? payload : [];
    window._visitHerbalsList = herbals
        .filter(h => h && h.id)
        .map(h => ({
            id: Number(h.id),
            name: h.name || '',
            stock: Number(h.stock || 0),
            price: Number(h.price || 0),
            unit: h.unit || 'pcs'
        }));
    return window._visitHerbalsList;
}

function _buildVisitHerbalOptions() {
    const herbals = window._visitHerbalsList || [];
    if (!herbals.length) return '<option value="">Belum ada produk/herbal aktif</option>';
    let opts = '<option value="">- Pilih Produk / Herbal -</option>';
    herbals.forEach(h => {
        opts += `<option value="${h.id}" data-stock="${h.stock}" data-price="${h.price}" data-unit="${escapeHtml(h.unit)}">${escapeHtml(h.name)} - stok ${h.stock} ${escapeHtml(h.unit)} - ${formatRupiah(h.price)}</option>`;
    });
    return opts;
}

function _buildTherapistOptions(gender) {
    const state = _visitTherapistState(gender);
    const therapists = _therapistsForGender(gender);
    if (therapists.length === 0) {
        return `<option value="">${escapeHtml(state.option)}</option>`;
    }

    let opts = `<option value="">${escapeHtml(state.option)}</option>`;
    therapists.forEach(t => {
        const scope = t.can_handle_any_gender && gender && t.gender !== gender ? ' - lintas gender' : '';
        opts += `<option value="${t.id}">${escapeHtml(t.name)}${scope}</option>`;
    });
    return opts;
}

function _refreshVisitTherapistSelect(gender) {
    const therapistSelect = document.getElementById('visit-therapist-select');
    const submitButton = document.getElementById('visit-submit-button');
    const helper = document.getElementById('visit-therapist-helper');
    const state = _visitTherapistState(gender);

    if (therapistSelect) {
        therapistSelect.innerHTML = _buildTherapistOptions(gender);
        therapistSelect.disabled = !state.canSelect;
        therapistSelect.setAttribute('aria-describedby', 'visit-therapist-helper');
    }
    if (helper) {
        helper.textContent = state.helper;
        helper.style.color = state.canSelect ? 'var(--text-muted)' : 'var(--danger)';
    }
    if (submitButton) {
        submitButton.disabled = !state.canSelect;
        submitButton.style.opacity = state.canSelect ? '1' : '0.65';
        submitButton.style.cursor = state.canSelect ? 'pointer' : 'not-allowed';
    }
}

function validateVisitTherapistSelected(event) {
    const patient = window._currentPatientData || {};
    const gender = patient.gender || '';
    const state = _visitTherapistState(gender);
    const therapistSelect = document.getElementById('visit-therapist-select');
    const selectedId = therapistSelect?.value;

    if (state.canSelect && selectedId) return true;

    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const message = !gender
        ? 'Pilih pasien dulu agar terapis bisa difilter sesuai jenis kelamin.'
        : state.canSelect
            ? 'Pilih terapis untuk kunjungan ini.'
            : state.helper;
    showToast(message, state.canSelect ? 'warning' : 'error');
    return false;
}

function validateVisitPatientSelected(event) {
    const patientInput = document.getElementById('visit_patient_id');
    if (patientInput && patientInput.value) return true;

    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    showToast('Cari dan aktifkan pasien terlebih dahulu dari pencarian di atas.', 'warning');
    return false;
}

async function renderPatients() {
    window._patientsTableMode = 'patients';
    try {
        const r = await fetch('/therapists?active_only=true');
        if (!r.ok) throw new Error('Gagal memuat terapis');
        const d = await r.json();
        _cacheTherapists(d);
    } catch (e) {
        window._therapistsList = [];
        window._therapistMap = {};
    }

    const html = `
        <div class="patients-page">
            <div class="card patient-form-card">
                <div class="card-header">
                    <h3><i class="fas fa-user-plus"></i> Registrasi Pasien Baru</h3>
                </div>
                <form action="/add_patient" method="post" class="patient-form-grid">
                    <div class="form-group">
                        <label>Nama Lengkap</label>
                        <input type="text" name="name" required placeholder="Contoh: Budi Santoso">
                    </div>
                    <div class="form-group">
                        <label>Nomor Telepon/WA</label>
                        <input type="text" name="phone" placeholder="08xxx (opsional)">
                    </div>
                    <div class="form-group">
                        <label>Alamat Domisili</label>
                        <input type="text" name="address" placeholder="Kota atau alamat lengkap...">
                    </div>
                    <div class="form-group">
                        <label>Jenis Kelamin</label>
                        <select name="gender">
                            <option value="Laki-laki">Laki-laki</option>
                            <option value="Perempuan">Perempuan</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary patient-submit-btn">
                        <i class="fas fa-plus"></i> Tambah Pasien
                    </button>
                </form>
            </div>

            <div class="card patient-list-card">
                <div class="patient-section-header">
                    <div class="patient-header-title">
                        <h3><i class="fas fa-address-book"></i> Direktori Pasien</h3>
                        <p>Daftar seluruh pasien yang terdaftar di sistem klinik.</p>
                    </div>
                    <span id="dt-total-badge">Memuat...</span>
                </div>
                <table id="patients-dt" class="patient-table display" style="width:100%;">
                    <thead>
                        <tr>
                            <th>Identitas Pasien</th>
                            <th>Gender</th>
                            <th>Kontak</th>
                            <th style="text-align:center;">Kunjungan</th>
                            <th style="text-align:center;">Aksi</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>`;

    document.getElementById('display-area').innerHTML = html;
    window._currentPatientData = null;
    _initPatientsDataTable();
}

async function renderVisits() {
    window._patientsTableMode = 'visits';
    await ensureVisitDiscountRulesLoaded();
    // 1. Fetch therapists list for form dropdowns (separate from main DT data)
    let trptOpts = _buildTherapistOptions();
    let serviceOpts = '<option value="" data-name="Bekam" data-unit="titik" data-qty="13" data-price="0">Layanan Terapi</option>';
    let freeReasonOpts = '';
    let herbalOpts = _buildVisitHerbalOptions();
    window._visitSelectedHerbals = [];
    window._visitPricePerPoint = window._visitPricePerPoint || 10000;
    try {
        const r = await fetch('/therapists?active_only=true');
        if (!r.ok) throw new Error('Gagal memuat terapis');
        const d = await r.json();
        _cacheTherapists(d);
        trptOpts = _buildTherapistOptions();
    } catch (e) {
        window._therapistsLoadError = 'Gagal memuat terapis';
        window._therapistsList = [];
        window._therapistMap = {};
        trptOpts = _buildTherapistOptions();
    }
    try {
        const r = await fetch('/visit_form_options');
        if (!r.ok) throw new Error('Gagal memuat opsi kunjungan');
        const options = await r.json();
        const services = options.services || [];
        window._servicesList = services;
        window._visitPricePerPoint = parseFloat(options.price_per_point || 10000);
        serviceOpts = services.map(s =>
            `<option value="${s.id}" data-name="${escapeHtml(s.name)}" data-unit="${escapeHtml(s.unit_label || 'sesi')}" data-qty="${s.default_quantity || 1}" data-price="${s.price_per_unit || 0}" data-notes="${escapeHtml(s.notes_template || '')}">${escapeHtml(s.name)}</option>`
        ).join('') || '<option value="" data-name="Bekam" data-unit="titik" data-qty="13" data-price="0">Layanan Terapi</option>';
        freeReasonOpts = (options.free_visit_reasons || ['promo', 'keluarga', 'koreksi', 'gratis lain-lain'])
            .map(reason => `<option value="${escapeHtml(reason)}">${escapeHtml(reason)}</option>`)
            .join('');
    } catch (e) {
        window._servicesList = [];
        serviceOpts = '<option value="" data-name="Bekam" data-unit="titik" data-qty="13" data-price="0">Layanan Terapi</option>';
        freeReasonOpts = ['promo', 'keluarga', 'koreksi', 'gratis lain-lain']
            .map(reason => `<option value="${escapeHtml(reason)}">${escapeHtml(reason)}</option>`)
            .join('');
    }
    try {
        const r = await fetch('/herbals');
        if (!r.ok) throw new Error('Gagal memuat herbal');
        const d = await r.json();
        _cacheVisitHerbals(d);
        herbalOpts = _buildVisitHerbalOptions();
    } catch (e) {
        window._visitHerbalsList = [];
        herbalOpts = '<option value="">Gagal memuat herbal</option>';
    }

    // 2. Build static layout HTML
    const html = `
        <div class="visit-page">
            <section class="visit-quick-picker">
                <div class="visit-quick-head">
                    <div>
                        <h3><i class="fas fa-search"></i> Cari Pasien untuk Kunjungan</h3>
                        <p>Cari pasien langsung dari sini, lalu form kunjungan siap diisi.</p>
                    </div>
                    <button type="button" class="visit-new-patient-btn" onclick="document.querySelector('[data-tab=&quot;patients&quot;]')?.click()">
                        <i class="fas fa-user-plus"></i> Pasien Baru
                    </button>
                </div>
                <div class="visit-patient-search-wrap">
                    <i class="fas fa-search"></i>
                    <input type="text" id="visit-patient-search" class="visit-patient-search" placeholder="Cari nama / nomor HP pasien..." autocomplete="off" oninput="onVisitPatientSearchInput(this.value)" onfocus="onVisitPatientSearchInput(this.value)">
                    <button type="button" id="visit-patient-search-clear" class="visit-search-clear" onclick="clearVisitPatientSearch()" aria-label="Bersihkan pencarian"><i class="fas fa-times"></i></button>
                    <div id="visit-patient-results" class="visit-patient-results" hidden></div>
                </div>
                <div id="visit-selected-patient-card" class="visit-selected-patient is-empty">
                    <div>
                        <div class="visit-selected-name">Belum ada pasien aktif</div>
                        <div class="visit-selected-meta">Cari nama atau nomor HP pasien untuk mulai mencatat kunjungan.</div>
                    </div>
                </div>
            </section>

            <section class="visit-main-layout">
            <!-- Form Registrasi Pasien -->
            <div class="card" style="display:none; height:fit-content; border-top:3px solid var(--primary);">
                <div class="card-header">
                    <h3><i class="fas fa-user-plus"></i> Registrasi Pasien</h3>
                </div>
                <form action="/add_patient" method="post">
                    <div class="form-group">
                        <label>Nama Pasien</label>
                        <input type="text" name="name" required placeholder="Nama lengkap...">
                    </div>
                    <div class="form-group">
                        <label>Telepon <span style="color:#aaa;font-size:10px;text-transform:none;">(opsional)</span></label>
                        <input type="text" name="phone" placeholder="08xx... (kosong = nomor sementara)">
                    </div>
                    <div class="form-group">
                        <label>Alamat</label>
                        <input type="text" name="address" placeholder="Alamat domisili...">
                    </div>
                    <div class="form-group">
                        <label>Jenis Kelamin</label>
                        <select name="gender">
                            <option value="Laki-laki">Laki-laki</option>
                            <option value="Perempuan">Perempuan</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Tambah Pasien</button>
                </form>
            </div>

            <!-- Form Catat Kunjungan -->
            <div class="card" style="height:fit-content; border-top:3px solid var(--success);">
                <div class="card-header">
                    <h3><i class="fas fa-notes-medical" style="color:var(--success);"></i> Catat Kunjungan Baru</h3>
                </div>
                <form action="/add_visit" method="post" class="visit-form-grid" onsubmit="return validateVisitPatientSelected(event)">
                    <input type="hidden" name="patient_id" id="visit_patient_id" required>
                    <div class="visit-form-section visit-patient-section">
                        <div class="visit-section-title"><i class="fas fa-user-check"></i> Pasien Terpilih</div>
                        <div class="form-group">
                            <label>Pasien</label>
                            <div id="selected-patient-badge" style="padding:8px 12px; background:#f0f4ff; border:1px solid #c7d2fe; border-radius:6px; font-size:13px; color:#4338ca; font-weight:500; min-height:37px;">
                                <i class="fas fa-info-circle"></i> Cari pasien di bagian atas form
                            </div>
                        </div>
                    </div>
                    <div class="visit-form-section visit-detail-section">
                        <div class="visit-section-title"><i class="fas fa-notes-medical"></i> Detail Kunjungan</div>
                        <div class="visit-section-grid">
                            <div class="form-group">
                                <label>Pilih Terapis</label>
                                <select name="therapist_id" id="visit-therapist-select" required>${trptOpts}</select>
                                <div id="visit-therapist-helper" class="field-helper"></div>
                            </div>
                            <div class="form-group">
                                <label>Layanan</label>
                                <select name="service_id" id="visit-service-select" onchange="onVisitServiceChange()">${serviceOpts}</select>
                                <input type="hidden" name="service_name" id="visit-service-name" value="Bekam">
                            </div>
                            <div class="form-group visit-metric-field">
                                <div class="visit-field-head">
                                    <label id="visit-quantity-label">Jumlah Layanan</label>
                                    <span class="visit-field-spacer" aria-hidden="true"></span>
                                </div>
                                <input type="number" name="point_count" id="visit-point-input" required placeholder="Quantity" min="1" oninput="calcVisitPrice(this.value)">
                            </div>
                            <div class="form-group visit-metric-field">
                                <div class="visit-field-head">
                                    <label>Harga Akhir (Rp)</label>
                                    <span id="price-hint" class="visit-price-hint"></span>
                                </div>
                                <input type="number" id="visit-price-input" name="price" required placeholder="Otomatis / manual" min="0" oninput="onVisitManualPriceInput()">
                                <input type="hidden" id="visit-manual-price-used" name="manual_price_used" value="false">
                            </div>
                        </div>
                    </div>
                    <div class="visit-form-section visit-herbal-section">
                        <label class="visit-herbal-title"><i class="fas fa-leaf"></i> Pembelian Produk / Herbal Tambahan</label>
                        <input type="hidden" name="herbal_items" id="visit-herbal-items-input" value="[]">
                        <div class="visit-herbal-entry">
                            <div class="visit-herbal-select-wrap">
                                <select id="visit-herbal-select" onchange="onVisitHerbalSelectChange()">${herbalOpts}</select>
                                <div id="visit-herbal-info" class="visit-herbal-info">Pilih produk/herbal untuk melihat stok dan harga.</div>
                            </div>
                            <input type="number" id="visit-herbal-qty" min="1" placeholder="Qty" oninput="onVisitHerbalQtyInput()">
                            <button type="button" class="btn btn-primary visit-herbal-add-btn" onclick="addVisitHerbalItem()"><i class="fas fa-plus"></i> Tambah</button>
                        </div>
                        <div id="visit-herbal-warning" class="visit-herbal-warning"></div>
                        <div class="visit-herbal-body">
                            <div id="visit-herbal-list" class="visit-herbal-list"></div>
                            <div class="visit-herbal-summary">
                                <div>
                                    <span>Subtotal Produk / Herbal</span>
                                    <strong id="visit-herbal-subtotal">Rp0</strong>
                                </div>
                                <div>
                                    <span>Total Akhir</span>
                                    <strong id="visit-grand-total">Rp0</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="visit-form-section visit-free-voucher-section">
                        <div class="visit-section-title"><i class="fas fa-ticket-alt"></i> Voucher / Gratis</div>
                        <div class="visit-section-grid">
                            <div class="form-group visit-free-field">
                                <label class="activation-switch visit-free-toggle is-off" id="visit-free-control" for="visit-free-checkbox">
                                    <input type="checkbox" name="is_free_visit" id="visit-free-checkbox" value="true" onchange="onVisitFreeChange()">
                                    <span class="activation-track" aria-hidden="true"><span></span></span>
                                    <span class="activation-copy">
                                        <strong id="visit-free-title">Kunjungan Gratis</strong>
                                        <small id="visit-free-help">Aktifkan jika kunjungan ini gratis/promo/koreksi.</small>
                                    </span>
                                </label>
                                <select name="free_visit_reason" id="visit-free-reason" disabled>${freeReasonOpts}</select>
                            </div>
                            <div class="form-group visit-voucher-field">
                                <label>Voucher <span style="color:#94a3b8;font-size:10px;text-transform:none;">(opsional)</span></label>
                                <input type="text" name="voucher_code" id="visit-voucher-input" placeholder="Contoh: SEHAT10">
                                <div id="visit-voucher-help" class="field-helper">Voucher aktif untuk kunjungan berbayar.</div>
                            </div>
                        </div>
                    </div>
                    <div class="visit-form-section visit-notes-section">
                        <div class="visit-section-title"><i class="fas fa-clipboard-list"></i> Catatan Medis</div>
                        <div class="form-group">
                            <label>Catatan</label>
                            <input type="text" name="medical_notes" id="visit-notes-input" placeholder="Keluhan, kondisi, dll...">
                        </div>
                    </div>
                    <div class="visit-form-section visit-payment-section">
                        <div class="visit-section-title"><i class="fas fa-wallet"></i> Pembayaran</div>
                        <div class="visit-payment-quick-actions" aria-label="Pilihan cepat pembayaran">
                            <button type="button" onclick="setVisitPaymentQuick('paid', 'cash')"><i class="fas fa-money-bill-wave"></i> Tunai Lunas</button>
                            <button type="button" onclick="setVisitPaymentQuick('paid', 'qris')"><i class="fas fa-qrcode"></i> QRIS Manual Lunas</button>
                            <button type="button" onclick="setVisitPaymentQuick('unpaid', 'other')"><i class="fas fa-clock"></i> Belum Dibayar</button>
                            <button type="button" onclick="setVisitPaymentQuick('partial', 'cash')"><i class="fas fa-receipt"></i> Catat DP</button>
                        </div>
                        <div class="visit-section-grid">
                            <div class="form-group">
                                <label>Status Tagihan</label>
                                <select name="payment_status" id="visit-payment-status" onchange="onVisitPaymentStatusChange()">
                                    <option value="unpaid" selected>Belum Dibayar</option>
                                    <option value="paid">Lunas</option>
                                    <option value="partial">Bayar Sebagian (DP)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Metode Pembayaran</label>
                                <select name="payment_method" id="visit-payment-method">
                                    <option value="cash">Tunai</option>
                                    <option value="qris">QRIS</option>
                                    <option value="transfer">Transfer</option>
                                    <option value="debit">Debit</option>
                                    <option value="ewallet">E-Wallet</option>
                                    <option value="virtual_account">Virtual Account</option>
                                    <option value="credit_card">Kartu Kredit</option>
                                    <option value="other" selected>Lainnya / Belum Ditentukan</option>
                                    <option value="free">Gratis</option>
                                </select>
                            </div>
                        </div>
                        <div id="visit-amount-paid-group" class="visit-amount-paid-group">
                            <label>Jumlah yang Dibayarkan (Rp)</label>
                            <input type="number" name="amount_paid" id="visit-amount-paid" placeholder="Masukkan jumlah bayar..." min="0">
                        </div>
                        <div id="visit-payment-revenue-hint" class="visit-payment-hint">Belum masuk pendapatan sampai ditandai lunas/sebagian.</div>
                    </div>
                    <button type="submit" id="visit-submit-button" class="btn btn-primary" style="background:linear-gradient(135deg,var(--success),#059669); box-shadow:0 4px 12px rgba(16,185,129,0.35);">
                        <i class="fas fa-plus-circle"></i> Catat Kunjungan
                    </button>
                </form>
            </div>

            <div class="card" id="visit-panel" style="padding:0; min-width:0; display:flex; flex-direction:column;">
                <div id="visit-panel-content" style="display:flex; flex-direction:column; height:100%; min-height:360px;">
                    <div style="flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; color:var(--text-muted); gap:12px; padding:32px;">
                        <i class="fas fa-hand-pointer" style="font-size:48px; opacity:0.12;"></i>
                        <p style="font-size:15px; font-weight:500;">Cari pasien dari bagian atas</p>
                        <p style="font-size:12px;">riwayat kunjungan pasien aktif akan tampil di sini</p>
                    </div>
                </div>
            </div>
            </section>

        <!-- ── Main section: DataTable kiri + Visit panel kanan ── -->
        <div style="display:block; margin-top:16px;">

            <!-- LEFT: DataTable -->
            <div class="card" style="padding:12px 16px 16px; flex:1; min-width:0;">
                <div class="visit-table-toolbar">
                    <strong><i class="fas fa-address-book"></i> Database Pasien</strong>
                    <span id="dt-total-badge" style="font-size:12px; color:var(--text-muted); flex-shrink:0;"></span>
                </div>
                <table id="patients-dt" class="display" style="width:100%; font-size:13px;">
                    <thead>
                        <tr>
                            <th>Nama</th>
                            <th>Jenis Kelamin</th>
                            <th>No HP</th>
                            <th style="text-align:center;">Kunjungan</th>
                            <th style="text-align:center;">Aksi</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>

            <!-- RIGHT: Visit detail panel -->
            <div class="card" id="visit-panel-legacy" style="display:none; padding:0; width:440px; min-width:340px; flex-shrink:0; flex-direction:column;">
                <div id="visit-panel-content-legacy" style="display:flex; flex-direction:column; height:100%; min-height:400px;">
                    <div style="flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; color:var(--text-muted); gap:12px;">
                        <i class="fas fa-hand-pointer" style="font-size:48px; opacity:0.12;"></i>
                        <p style="font-size:15px; font-weight:500;">Cari pasien dari bagian atas</p>
                        <p style="font-size:12px;">untuk melihat riwayat kunjungannya</p>
                    </div>
                </div>
            </div>

        </div>`;

    document.getElementById('display-area').innerHTML = html;
    const visitsRoot = document.getElementById('display-area').firstElementChild;
    if (visitsRoot) {
        const mainLayout = visitsRoot.querySelector('.visit-main-layout');
        const formCard = mainLayout?.querySelector(':scope > .card:nth-child(2)');
        const detailCard = mainLayout?.querySelector('#visit-panel');
        const visitsTableWrap = mainLayout?.nextElementSibling;
        formCard?.classList.add('visit-form-card', 'visit-panel', 'visit-form-panel');
        formCard?.querySelector('.card-header')?.classList.add('visit-panel-header');
        formCard?.querySelector('form')?.classList.add('visit-form-grid');
        detailCard?.classList.add('visit-detail-card', 'visit-panel', 'visit-history-panel');
        detailCard?.removeAttribute('style');
        if (visitsTableWrap) {
            visitsTableWrap.className = 'visit-table-zone';
            visitsTableWrap.removeAttribute('style');
            visitsTableWrap.querySelector(':scope > .card')?.classList.add('visit-table-card');
            visitsTableWrap.querySelector(':scope > .card > div')?.classList.add('patient-section-header');
        }
    }
    onVisitServiceChange();
    onVisitPaymentStatusChange();
    syncVisitFreeControl();
    syncVisitHerbalItems();
    window._currentPatientData = null;
    _refreshVisitTherapistSelect();

    // 3. Init DataTable server-side
    _initPatientsDataTable();

    // 4. Setup Search Results Delegate
    setupVisitSearchDelegate();
}

function setupVisitSearchDelegate() {
    const results = document.getElementById('visit-patient-results');
    const input = document.getElementById('visit-patient-search');
    if (!results || !input) return;

    // Click Delegation
    results.addEventListener('click', (e) => {
        const btn = e.target.closest('.visit-patient-result');
        if (!btn) return;
        const id = btn.dataset.patientId;
        if (id) _dtShowVisits(Number(id));
    });

    // Keyboard support
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeVisitPatientResults();
        } else if (e.key === 'Enter') {
            const first = results.querySelector('.visit-patient-result');
            if (first && !results.hidden) {
                e.preventDefault();
                first.click();
            }
        }
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
        if (!results.contains(e.target) && e.target !== input) {
            closeVisitPatientResults();
        }
    });
}

// ── DATATABLES INIT ───────────────────────────────────────────────────────────
function _initPatientsDataTable() {
    if (window._patientsDT) {
        try { window._patientsDT.destroy(); } catch (e) { }
        window._patientsDT = null;
    }

    window._patientsDT = $('#patients-dt').DataTable({
        serverSide: true,
        processing: true,
        searchDelay: 300,
        language: {
            processing: '<i class="fas fa-spinner fa-spin"></i> Memuat...',
            search: 'Cari:',
            lengthMenu: 'Tampilkan _MENU_ pasien',
            info: 'Menampilkan _START_-_END_ dari _TOTAL_ pasien',
            infoEmpty: 'Tidak ada data',
            infoFiltered: '(difilter dari _MAX_ total)',
            zeroRecords: 'Tidak ada pasien yang cocok',
            paginate: {
                first: 'Pertama',
                last: 'Terakhir',
                next: 'Selanjutnya',
                previous: 'Sebelumnya',
            }
        },
        ajax: function (dtParams, callback, settings) {
            // Map DataTables params to our API
            const orderColIdx = dtParams.order && dtParams.order[0] ? dtParams.order[0].column : 0;
            const orderDir = dtParams.order && dtParams.order[0] ? dtParams.order[0].dir : 'asc';
            const searchVal = dtParams.search ? dtParams.search.value : '';

            const url = `/patients_paginated?draw=${dtParams.draw}&start=${dtParams.start}&length=${dtParams.length}&search=${encodeURIComponent(searchVal)}&order_col=${orderColIdx}&order_dir=${orderDir}`;

            fetch(url)
                .then(r => r.json())
                .then(data => {
                    const badge = document.getElementById('dt-total-badge');
                    if (badge) badge.textContent = `Total: ${data.recordsTotal} pasien`;

                    callback({
                        draw: data.draw,
                        recordsTotal: data.recordsTotal,
                        recordsFiltered: data.recordsFiltered,
                        data: data.data
                    });
                })
                .catch(err => console.error('DT fetch error:', err));
        },
        columns: [
            {
                data: null,
                render: function (row) {
                    const genderColor = row.gender === 'Laki-laki' ? '#3b82f6' : '#ec4899';
                    const genderBg = row.gender === 'Laki-laki' ? '#eff6ff' : '#fdf2f8';
                    const genderIcon = row.gender === 'Laki-laki' ? 'fa-male' : 'fa-female';
                    return `
                        <div class="patient-name-cell">
                            <div class="patient-avatar" style="background:${genderBg}; color:${genderColor};">
                                <i class="fas ${genderIcon}"></i>
                            </div>
                            <div class="patient-name-text">
                                ${escapeHtml(row.name)}
                            </div>
                        </div>`;
                },
                orderable: true
            },
            {
                data: 'gender',
                render: function (val) {
                    const color = val === 'Laki-laki' ? '#1d4ed8' : '#be185d';
                    const bg = val === 'Laki-laki' ? '#dbeafe' : '#fce7f3';
                    const icon = val === 'Laki-laki' ? 'fa-mars' : 'fa-venus';
                    return `<span class="patient-gender-badge" style="color:${color}; background:${bg};">
                        <i class="fas ${icon}"></i> ${escapeHtml(val)}
                    </span>`;
                },
                orderable: true
            },
            {
                data: 'phone',
                render: function (val) {
                    if (!val || val.startsWith('TEMP-')) return '<span style="color:#94a3b8; font-size:12px; font-style:italic;">Belum diatur</span>';
                    return `<span style="font-size:13px; font-weight:600; color:#475569;">${escapeHtml(val)}</span>`;
                },
                orderable: true
            },
            {
                data: 'visits_count',
                className: 'dt-center',
                render: function (val) {
                    return `<span class="patient-visit-badge">${val}x</span>`;
                },
                orderable: false
            },
            {
                data: null,
                className: 'dt-center',
                orderable: false,
                render: function (row) {
                    if (window._patientsTableMode === 'patients') {
                        return `
                            <button onclick="_dtEditPatient(${row.id})" class="patient-edit-btn" title="Edit Data Pasien">
                                <i class="fas fa-pen"></i> Edit
                            </button>`;
                    }
                    return `
                        <div style="display:flex;gap:6px;justify-content:center;flex-wrap:wrap;">
                            <button onclick="_dtShowVisits(${row.id})" class="patient-edit-btn" title="Lihat Kunjungan" style="color:var(--primary); border-color:var(--primary-light);">
                                <i class="fas fa-history"></i> Riwayat
                            </button>
                            <button onclick="_dtEditPatient(${row.id})" class="patient-edit-btn" title="Edit Data Pasien">
                                <i class="fas fa-pen"></i> Edit
                            </button>
                        </div>`;
                }
            }
        ],
        order: [[0, 'asc']],
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        dom: '<"dt-top"lf>rt<"dt-bottom"ip>',
        createdRow: function (row, data) {
            $(row).css('cursor', 'pointer');
            $(row).on('click', function (e) {
                if ($(e.target).closest('button').length) return;
                if (window._patientsTableMode === 'patients') {
                    _dtEditPatient(data.id);
                    return;
                }
                _dtShowVisits(data.id);
                $('#patients-dt tbody tr').removeClass('dt-selected-row');
                $(row).addClass('dt-selected-row');
            });
        }
    });
}

// ── SHOW VISIT PANEL (by patient id, from cached row data) ────────────────────
async function _dtLoadPatientDetail(patientRow) {
    if (patientRow && Array.isArray(patientRow.visits)) return patientRow;
    const res = await fetch(`/patient_detail/${patientRow.id}`);
    if (!res.ok) throw new Error('Gagal memuat detail pasien');
    const detail = await res.json();
    Object.assign(patientRow, detail);
    return patientRow;
}

function closeVisitPatientResults() {
    const results = document.getElementById('visit-patient-results');
    if (results) {
        results.hidden = true;
        results.innerHTML = '';
    }
}

function updateVisitSelectedPatientCard(patient) {
    const card = document.getElementById('visit-selected-patient-card');
    if (!card || !patient) return;

    const visits = Array.isArray(patient.visits) ? patient.visits : [];
    const visitCount = patient.visits_count || visits.length || 0;
    const totalIncome = visits.reduce((sum, visit) => sum + (parseFloat(visit.price) || 0), 0);
    const phone = patient.phone && !patient.phone.startsWith('TEMP-') ? patient.phone : 'No HP belum diatur';
    const gender = patient.gender || '-';

    card.classList.remove('is-empty');
    card.innerHTML = `
        <div class="visit-selected-main">
            <div class="visit-selected-name">${escapeHtml(patient.name || 'Pasien')}</div>
            <div class="visit-selected-meta">
                <span><i class="fab fa-whatsapp"></i> ${escapeHtml(phone)}</span>
                <span><i class="fas fa-venus-mars"></i> ${escapeHtml(gender)}</span>
            </div>
        </div>
        <div class="visit-selected-stat">
            <strong>${visitCount}</strong>
            <span>Kunjungan</span>
        </div>
        <div class="visit-selected-stat">
            <strong>${formatRupiah(totalIncome)}</strong>
            <span>Total revenue</span>
        </div>
        <button type="button" class="visit-change-patient-btn" onclick="clearVisitPatientSearch(true)">Ganti Pasien</button>`;

    const search = document.getElementById('visit-patient-search');
    if (search) search.value = patient.name || '';
}

function renderVisitPatientResults(patients, query) {
    const results = document.getElementById('visit-patient-results');
    if (!results) return;

    if (!patients.length) {
        results.hidden = false;
        results.innerHTML = `<div class="visit-patient-result-empty">Tidak ada pasien cocok untuk "${escapeHtml(query)}".</div>`;
        return;
    }

    results.hidden = false;
    results.innerHTML = patients.map(patient => {
        const phone = patient.phone && !patient.phone.startsWith('TEMP-') ? patient.phone : 'No HP belum diatur';
        const visits = patient.visits_count || 0;
        return `
            <button type="button" class="visit-patient-result" data-patient-id="${patient.id}">
                <span class="visit-patient-result-main">
                    <strong>${escapeHtml(patient.name || 'Pasien')}</strong>
                    <small>${escapeHtml(phone)}${patient.id ? ` · ID ${escapeHtml(String(patient.id))}` : ''}</small>
                </span>
                <span class="visit-patient-result-count">${visits}x</span>
            </button>`;
    }).join('');
}

async function searchVisitPatients(query) {
    const trimmed = String(query || '').trim();
    if (trimmed.length < 2) {
        closeVisitPatientResults();
        return;
    }

    const results = document.getElementById('visit-patient-results');
    if (results) {
        results.hidden = false;
        results.innerHTML = '<div class="visit-patient-result-empty"><i class="fas fa-spinner fa-spin"></i> Mencari pasien...</div>';
    }

    try {
        const url = `/patients_paginated?draw=1&start=0&length=8&search=${encodeURIComponent(trimmed)}&order_col=0&order_dir=asc`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Gagal mencari pasien');
        const data = await res.json();
        const patients = Array.isArray(data.data) ? [...data.data] : [];

        if (/^\d+$/.test(trimmed) && !patients.some(patient => String(patient.id) === trimmed)) {
            try {
                const detailRes = await fetch(`/patient_detail/${trimmed}`);
                if (detailRes.ok) patients.unshift(await detailRes.json());
            } catch (e) { }
        }

        renderVisitPatientResults(patients, trimmed);
    } catch (e) {
        if (results) {
            results.hidden = false;
            results.innerHTML = `<div class="visit-patient-result-empty">${escapeHtml(e.message || 'Gagal mencari pasien.')}</div>`;
        }
    }
}

function onVisitPatientSearchInput(value) {
    clearTimeout(window._visitPatientSearchTimer);
    window._visitPatientSearchTimer = setTimeout(() => searchVisitPatients(value), 220);
}

function clearVisitPatientSearch(focus = false) {
    const input = document.getElementById('visit-patient-search');
    if (input) input.value = '';
    closeVisitPatientResults();
    if (focus) input?.focus();
}

async function _dtShowVisits(patientId) {
    // Find row data in current DT page
    const table = window._patientsDT;
    if (!table) return;

    let patientRow = null;
    table.rows().every(function () {
        const d = this.data();
        if (d && d.id === patientId) { patientRow = d; }
    });

    if (!patientRow) patientRow = { id: patientId };

    // Highlight table row
    $('#patients-dt tbody tr').removeClass('dt-selected-row');
    table.rows().every(function () {
        if (this.data() && this.data().id === patientId) {
            $(this.node()).addClass('dt-selected-row');
        }
    });

    try {
        patientRow = await _dtLoadPatientDetail(patientRow);
        await ensureVisitDiscountRulesLoaded();
    } catch (e) {
        const panel = document.getElementById('visit-panel-content');
        if (panel) {
            panel.innerHTML = `<div style="padding:24px;color:var(--danger);font-weight:600;">${escapeHtml(e.message)}</div>`;
        }
        return;
    }

    // Cache for visit form
    window._currentPatientData = patientRow;

    // Update visit form patient selector
    const visitPtIdInput = document.getElementById('visit_patient_id');
    if (visitPtIdInput) visitPtIdInput.value = patientRow.id;

    const badge = document.getElementById('selected-patient-badge');
    if (badge) {
        const genderColor = patientRow.gender === 'Laki-laki' ? '#3b82f6' : '#ec4899';
        badge.innerHTML = `<i class="fas fa-user" style="color:${genderColor};"></i> <strong>${escapeHtml(patientRow.name)}</strong> <span style="color:#94a3b8;font-size:11px;">(${escapeHtml(patientRow.gender)})</span>`;
    }
    updateVisitSelectedPatientCard(patientRow);
    closeVisitPatientResults();

    scrollVisitFormIntoView();

    // Filter therapist dropdown by patient gender
    _refreshVisitTherapistSelect(patientRow.gender);

    // Build visit detail panel
    const therapistMap = window._therapistMap || {};
    const visits = patientRow.visits || [];
    const visitCount = patientRow.visits_count || visits.length;
    const totalIncome = visits.reduce((s, v) => s + (parseFloat(v.price) || 0), 0);
    const genderColor = patientRow.gender === 'Laki-laki' ? '#3b82f6' : '#ec4899';
    const genderBg = patientRow.gender === 'Laki-laki' ? '#eff6ff' : '#fdf2f8';
    const genderIcon = patientRow.gender === 'Laki-laki' ? 'fa-male' : 'fa-female';

    let content = `
        <div class="visit-patient-header">
            <div class="visit-patient-avatar" style="background:${genderBg};color:${genderColor};">
                <i class="fas ${genderIcon}"></i>
            </div>
            <div class="visit-patient-main">
                <div class="visit-patient-name-row">
                    <span class="visit-patient-name">${escapeHtml(patientRow.name)}</span>
                    <button class="visit-edit-btn" onclick="_dtEditPatient(${patientRow.id})">Edit</button>
                </div>
                <div class="visit-patient-meta">
                    <span>${patientRow.phone && patientRow.phone.startsWith('TEMP-') ? '<i class="fas fa-clock"></i> No HP blm diatur' : '<i class="fab fa-whatsapp" style="color:#25D366"></i> ' + escapeHtml(patientRow.phone)}</span>
                    <span><i class="fas fa-map-marker-alt"></i> ${escapeHtml(patientRow.address) || '-'}</span>
                </div>
            </div>
            <div class="visit-patient-stats">
                <div class="visit-stat-card">
                    <div class="visit-stat-value">${visitCount}</div>
                    <div class="visit-stat-label">Kunjungan</div>
                </div>
                <div class="visit-stat-card">
                    <div class="visit-stat-value money">${formatRupiah(totalIncome)}</div>
                    <div class="visit-stat-label">Total</div>
                </div>
            </div>
        </div>
                        <div class="visit-history-body">`;

    if (visits.length === 0) {
        content += `<div class="visit-empty-panel"><i class="fas fa-calendar-times"></i><p>Belum ada kunjungan tercatat.</p></div>`;
    } else {
        content += `
        <div class="visit-history-wrapper">
        <table class="visit-history-table">
            <colgroup>
                <col class="visit-col-date">
                <col class="visit-col-service">
                <col class="visit-col-therapist">
                <col class="visit-col-points">
                <col class="visit-col-price">
                <col class="visit-col-note">
            </colgroup>
            <thead>
                <tr>
                    <th class="visit-col-date">Tanggal</th>
                    <th class="visit-col-service">Layanan</th>
                    <th class="visit-col-therapist">Terapis</th>
                    <th class="visit-col-points">Jumlah Layanan</th>
                    <th class="visit-col-price">Harga</th>
                    <th class="visit-col-note">Catatan</th>
                </tr>
            </thead>
            <tbody>`;
        let cardContent = '<div class="visit-history-card-list">';
        visits.forEach((v, vi) => {
            const dt = new Date(v.date);
            const dPart = dt.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
            const tPart = dt.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
            const tName = v.therapist_id ? (therapistMap[v.therapist_id] || `#${v.therapist_id}`) : '-';
            const priceHTML = renderVisitDiscountBadge(v);
            const priceInfo = getVisitDiscountInfo(v);
            const unitLabel = getVisitUnitLabel(v);
            const noteText = v.medical_notes || '-';
            content += `
                                <tr>
                                    <td class="visit-col-date">
                                        <div class="visit-date-main">${escapeHtml(dPart)}</div>
                                        <div class="visit-date-time"><i class="fas fa-clock"></i> ${escapeHtml(tPart)}</div>
                                    </td>
                                    <td class="visit-col-service"><div class="visit-service-name" title="${escapeHtml(v.service_name || 'Layanan Terapi')}">${escapeHtml(v.service_name || 'Layanan Terapi')}</div></td>
                                    <td class="visit-col-therapist"><div class="visit-therapist-name" title="${escapeHtml(tName)}">${escapeHtml(tName)}</div></td>
                                    <td class="visit-col-points"><span class="visit-points-value">${v.point_count || 0}</span><span class="visit-points-unit">${escapeHtml(unitLabel)}</span></td>
                                    <td class="visit-col-price">${priceHTML}</td>
                                    <td class="visit-col-note">${noteText && noteText !== '-' ? `<div class="visit-note-text" title="${escapeHtml(noteText)}">${escapeHtml(noteText)}</div>` : '<span class="visit-note-empty">-</span>'}</td>
                                </tr>`;
            const noteLabel = noteText && noteText !== '-' ? noteText : '';
            cardContent += `
                                <article class="visit-history-card">
                                    <div class="visit-history-card-head">
                                        <div class="visit-history-card-service">${escapeHtml(v.service_name || 'Layanan Terapi')}</div>
                                        <div class="visit-history-card-date">${escapeHtml(dPart)}</div>
                                    </div>
                                    <div class="visit-history-card-grid">
                                        <div><div class="visit-history-card-label">Terapis</div><div class="visit-history-card-value">${escapeHtml(tName)}</div></div>
                                        <div><div class="visit-history-card-label">Jumlah Layanan</div><div class="visit-history-card-value">${v.point_count || 0} ${escapeHtml(unitLabel)}</div></div>
                                        <div><div class="visit-history-card-label">Harga</div><div class="visit-history-card-value visit-history-price">
                                            <strong style="color:${priceInfo.color};">${formatRupiah(priceInfo.finalPrice)}</strong>
                                            <span class="visit-history-price-badge" style="color:${priceInfo.color};background:${priceInfo.bg};border-color:${priceInfo.border};">${escapeHtml(priceInfo.title)}</span>
                                            <small>${escapeHtml(priceInfo.detail)}</small>
                                        </div></div>
                                        <div><div class="visit-history-card-label">Jam</div><div class="visit-history-card-value">${escapeHtml(tPart)}</div></div>
                                    </div>
                                    ${noteLabel ? `<div class="visit-note-text" title="${escapeHtml(noteLabel)}">${escapeHtml(noteLabel)}</div>` : ''}
                                </article>`;
        });
        cardContent += '</div>';
        content += `</tbody></table></div>${cardContent}`;
    }

    content += `</div>`;
    const panel = document.getElementById('visit-panel-content');
    if (panel) {
        panel.style.display = 'flex';
        panel.style.flexDirection = 'column';
        panel.style.height = '100%';
        panel.innerHTML = content;
    }
}

// ── EDIT PATIENT (bridge ke openFullEditModal di modal.js) ────────────────────
async function _dtEditPatient(patientId) {
    // Find the patient data row in DT cache
    const table = window._patientsDT;
    if (!table) return;

    let patientRow = null;
    table.rows().every(function () {
        const d = this.data();
        if (d && d.id === patientId) { patientRow = d; }
    });

    if (!patientRow) return;

    try {
        patientRow = await _dtLoadPatientDetail(patientRow);
        await ensureVisitDiscountRulesLoaded();
    } catch (e) {
        showToast(e.message, 'error');
        return;
    }

    // Reshape into format expected by openFullEditModal (idx-based)
    // We temporarily store data in window._patientsData as array of one
    // and set _currentPatientIdx = 0 for compat with modal.js
    window._patientsData = [patientRow];
    window._currentPatientIdx = 0;
    openFullEditModal(0);
}

// ── AUTO PRICE CALC ───────────────────────────────────────────────────────────
function _selectedVisitHerbal() {
    const select = document.getElementById('visit-herbal-select');
    const id = Number(select?.value || 0);
    return (window._visitHerbalsList || []).find(h => h.id === id) || null;
}

function _visitHerbalUsedQty(herbalId) {
    return (window._visitSelectedHerbals || [])
        .filter(item => item.herbal_id === herbalId)
        .reduce((sum, item) => sum + item.quantity, 0);
}

function onVisitHerbalSelectChange() {
    const herbal = _selectedVisitHerbal();
    const info = document.getElementById('visit-herbal-info');
    if (!info) return;
    if (!herbal) {
        info.textContent = 'Pilih produk/herbal untuk melihat stok dan harga.';
        return;
    }
    info.textContent = `${herbal.name} - stok ${herbal.stock} ${herbal.unit} - ${formatRupiah(herbal.price)}`;
    onVisitHerbalQtyInput();
}

function onVisitHerbalQtyInput() {
    const herbal = _selectedVisitHerbal();
    const qty = Number(document.getElementById('visit-herbal-qty')?.value || 0);
    const warning = document.getElementById('visit-herbal-warning');
    if (!warning) return;
    warning.style.display = 'none';
    warning.textContent = '';
    if (!herbal || qty <= 0) return;
    const used = _visitHerbalUsedQty(herbal.id);
    if (used + qty > herbal.stock) {
        warning.textContent = `Stok ${herbal.name} tidak cukup. Tersedia ${herbal.stock}, sudah dipilih ${used}.`;
        warning.style.display = 'block';
    }
}

function scrollVisitFormIntoView() {
    const formCard = document.querySelector('.visit-form-card');
    const main = document.querySelector('main');
    if (!formCard) return;

    if (main) {
        const mainTop = main.getBoundingClientRect().top;
        const formTop = formCard.getBoundingClientRect().top;
        const targetTop = main.scrollTop + formTop - mainTop - 12;
        main.scrollTo({ top: Math.max(0, targetTop), behavior: 'smooth' });
        return;
    }

    formCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function addVisitHerbalItem() {
    const herbal = _selectedVisitHerbal();
    const qtyInput = document.getElementById('visit-herbal-qty');
    const qty = Number(qtyInput?.value || 0);
    if (!herbal) {
        showToast('Pilih produk/herbal terlebih dahulu.', 'warning');
        return;
    }
    if (!Number.isInteger(qty) || qty <= 0) {
        showToast('Jumlah pembelian produk/herbal harus lebih dari 0.', 'warning');
        return;
    }
    const used = _visitHerbalUsedQty(herbal.id);
    if (used + qty > herbal.stock) {
        showToast('Stok produk/herbal tidak cukup. Silakan cek ulang pembelian.', 'error');
        return;
    }
    const existing = (window._visitSelectedHerbals || []).find(item => item.herbal_id === herbal.id);
    if (existing) {
        existing.quantity += qty;
    } else {
        window._visitSelectedHerbals.push({
            herbal_id: herbal.id,
            name: herbal.name,
            quantity: qty,
            unit: herbal.unit,
            price: herbal.price,
            stock: herbal.stock
        });
    }
    if (qtyInput) qtyInput.value = '';
    syncVisitHerbalItems();
}

function removeVisitHerbalItem(herbalId) {
    window._visitSelectedHerbals = (window._visitSelectedHerbals || []).filter(item => item.herbal_id !== herbalId);
    syncVisitHerbalItems();
}

function _visitHerbalSubtotal() {
    return (window._visitSelectedHerbals || []).reduce((sum, item) => sum + (Number(item.price || 0) * Number(item.quantity || 0)), 0);
}

function _visitServiceTotal() {
    return Number(document.getElementById('visit-price-input')?.value || 0);
}

function _visitGrandTotal() {
    return Math.max(0, _visitServiceTotal() + _visitHerbalSubtotal());
}

function syncVisitHerbalItems() {
    const items = window._visitSelectedHerbals || [];
    const hidden = document.getElementById('visit-herbal-items-input');
    if (hidden) {
        hidden.value = JSON.stringify(items.map(item => ({ herbal_id: item.herbal_id, quantity: item.quantity })));
    }

    const list = document.getElementById('visit-herbal-list');
    if (list) {
        if (!items.length) {
            list.innerHTML = '<div class="visit-herbal-empty">Belum ada herbal dipilih.</div>';
        } else {
            const rows = items.map(item => {
                const subtotal = Number(item.price || 0) * Number(item.quantity || 0);
                return `
                    <div class="visit-herbal-table-row">
                        <div class="visit-herbal-product">
                            <div class="visit-herbal-name">${escapeHtml(item.name)}</div>
                            <div class="visit-herbal-meta">${item.quantity} ${escapeHtml(item.unit)}</div>
                        </div>
                        <div class="visit-herbal-price">${formatRupiah(subtotal)}</div>
                        <button type="button" class="visit-herbal-remove" onclick="removeVisitHerbalItem(${item.herbal_id})" title="Hapus herbal"><i class="fas fa-trash"></i></button>
                    </div>`;
            }).join('');
            list.innerHTML = `
                <div class="visit-herbal-table">
                    <div class="visit-herbal-table-head">
                        <span>Produk</span>
                        <span>Harga</span>
                        <span></span>
                    </div>
                    ${rows}
                </div>`;
        }
    }

    const herbalSubtotal = _visitHerbalSubtotal();
    const herbalSubtotalEl = document.getElementById('visit-herbal-subtotal');
    const grandTotalEl = document.getElementById('visit-grand-total');
    if (herbalSubtotalEl) herbalSubtotalEl.textContent = formatRupiah(herbalSubtotal);
    if (grandTotalEl) grandTotalEl.textContent = formatRupiah(_visitGrandTotal());
    onVisitPaymentStatusChange();
    onVisitHerbalQtyInput();
}

function validateVisitHerbalStock() {
    for (const item of (window._visitSelectedHerbals || [])) {
        if (item.quantity > item.stock) {
            showToast('Stok produk/herbal tidak cukup. Silakan cek ulang pembelian.', 'error');
            return false;
        }
    }
    return true;
}

function getVisitHerbalConfirmItems() {
    const items = window._visitSelectedHerbals || [];
    return items.map(item => ({
        name: item.name,
        qty: `${item.quantity} ${item.unit}`,
        subtotal: Number(item.price || 0) * Number(item.quantity || 0),
    }));
}

async function getVisitDiscountPreview(formData, visitPrice) {
    const isFreeVisit = document.getElementById('visit-free-checkbox')?.checked;
    if (isFreeVisit || Number(visitPrice || 0) <= 0) return null;

    const patient = window._currentPatientData || {};
    const visitCount = Number(patient.visits_count ?? (Array.isArray(patient.visits) ? patient.visits.length : 0)) || 0;
    const manualPriceUsed = ['1', 'true', 'yes', 'on'].includes(String(formData.get('manual_price_used') || '').toLowerCase());
    const params = new URLSearchParams({
        price: String(visitPrice || 0),
        visit_count: String(visitCount),
        patient_id: String(patient.id || formData.get('patient_id') || ''),
        voucher_code: String(formData.get('voucher_code') || ''),
        manual_price_used: String(manualPriceUsed)
    });

    try {
        const response = await fetch(`/discount_rules/simulate?${params.toString()}`);
        if (!response.ok) return null;
        const data = await response.json();
        return data && data.selected ? data.selected : null;
    } catch (e) {
        return null;
    }
}

function prepareVisitHerbalFormData(formData) {
    formData.set('herbal_items', JSON.stringify((window._visitSelectedHerbals || []).map(item => ({
        herbal_id: item.herbal_id,
        quantity: item.quantity
    }))));
    const freeCheckbox = document.getElementById('visit-free-checkbox');
    if (freeCheckbox?.checked) {
        formData.set('payment_status', 'paid');
        formData.set('payment_method', 'free');
        formData.set('amount_paid', '0');
        formData.set('voucher_code', '');
    } else if (formData.get('payment_status') === 'unpaid') {
        formData.set('payment_method', 'other');
        formData.set('amount_paid', '0');
    } else if (formData.get('payment_status') === 'paid' && !formData.get('amount_paid')) {
        formData.set('amount_paid', String(_visitGrandTotal()));
    }
    return formData;
}

async function confirmVisitSubmission(form) {
    if (window._visitSubmitInProgress || window._visitConfirmInProgress) {
        showToast('Kunjungan sedang disimpan. Tunggu proses sebelumnya selesai.', 'info');
        return null;
    }
    if (!validateVisitPatientSelected()) {
        return null;
    }
    if (!validateVisitTherapistSelected()) {
        return null;
    }
    if (!validateVisitHerbalStock()) {
        return null;
    }

    const formData = new FormData(form);
    prepareVisitHerbalFormData(formData);
    formData.set('idempotency_key', getVisitIdempotencyKey(form));

    const patient = window._currentPatientData || {};
    const serviceSelect = document.getElementById('visit-service-select');
    const serviceOption = serviceSelect ? serviceSelect.options[serviceSelect.selectedIndex] : null;
    const serviceName = serviceOption ? (serviceOption.dataset.name || serviceOption.textContent || 'Bekam') : 'Bekam';
    const quantityLabel = document.getElementById('visit-quantity-label')?.textContent || 'Jumlah';
    const quantity = document.getElementById('visit-point-input')?.value || '-';
    const visitPrice = _visitServiceTotal();
    const therapistSelect = document.getElementById('visit-therapist-select');
    const therapistName = therapistSelect ? therapistSelect.options[therapistSelect.selectedIndex]?.textContent || '-' : '-';
    const notes = document.getElementById('visit-notes-input')?.value.trim() || '-';
    const herbalItems = getVisitHerbalConfirmItems();
    const herbalSubtotal = _visitHerbalSubtotal();
    const discountPreview = await getVisitDiscountPreview(formData, visitPrice);
    const discountedVisitPrice = discountPreview ? Number(discountPreview.final_price ?? visitPrice) : visitPrice;
    const discountAmount = discountPreview ? Number(discountPreview.discount_amount || Math.max(0, visitPrice - discountedVisitPrice)) : 0;
    const total = discountedVisitPrice + herbalSubtotal;
    if (formData.get('payment_status') === 'paid' && formData.get('payment_method') !== 'free') {
        formData.set('amount_paid', String(total));
    }
    if (formData.get('payment_status') === 'partial' && Number(formData.get('amount_paid') || 0) <= 0) {
        showToast('Jumlah DP wajib lebih dari Rp0.', 'warning');
        return null;
    }

    const herbalHtml = herbalItems.length
        ? herbalItems.map(item => `
            <div class="visit-confirm-herbal-row">
                <span>${escapeHtml(item.name)} <small>x${escapeHtml(item.qty)}</small></span>
                <strong>${formatRupiah(item.subtotal)}</strong>
            </div>`).join('')
        : '<div class="visit-confirm-empty">Tidak ada pembelian produk/herbal.</div>';
    const discountHtml = discountPreview ? `
            <div class="visit-confirm-section visit-confirm-discount">
                <div class="visit-confirm-section-title">Voucher / Diskon Otomatis</div>
                <div class="visit-confirm-herbal-row">
                    <span>Aturan aktif <small>${escapeHtml(_visitDiscountKind(discountPreview))}</small></span>
                    <strong>${escapeHtml(discountPreview.name || 'Diskon aktif')}</strong>
                </div>
                <div class="visit-confirm-herbal-row">
                    <span>Potongan</span>
                    <strong>-${formatRupiah(discountAmount)}</strong>
                </div>
                <div class="visit-confirm-herbal-row">
                    <span>Biaya setelah diskon</span>
                    <strong>${formatRupiah(discountedVisitPrice)}</strong>
                </div>
            </div>` : '';

    const message = `
        <div class="visit-confirm">
            <p class="visit-confirm-lead">Cek ulang data kunjungan sebelum disimpan.</p>
            <div class="visit-confirm-card">
                <div><span>Pasien</span><strong>${escapeHtml(patient.name || '-')}</strong></div>
                <div><span>Terapis</span><strong>${escapeHtml(therapistName)}</strong></div>
                <div><span>Layanan</span><strong>${escapeHtml(serviceName)}</strong></div>
                <div><span>${escapeHtml(quantityLabel)}</span><strong>${escapeHtml(quantity)}</strong></div>
                <div><span>Biaya kunjungan</span><strong>${formatRupiah(visitPrice)}</strong></div>
                <div><span>Status Tagihan</span><strong style="text-transform:capitalize;">${escapeHtml(formData.get('payment_status'))}</strong></div>
                <div><span>Metode</span><strong style="text-transform:capitalize;">${escapeHtml(formData.get('payment_method'))}</strong></div>
                ${formData.get('payment_status') === 'partial' ? `<div><span>Sudah Bayar</span><strong>${formatRupiah(formData.get('amount_paid'))}</strong></div>` : ''}
                <div><span>Catatan</span><strong>${escapeHtml(notes)}</strong></div>
            </div>
            ${discountHtml}
            <div class="visit-confirm-section">
                <div class="visit-confirm-section-title">Produk / Herbal</div>
                ${herbalHtml}
            </div>
            <div class="visit-confirm-total">
                <span>Total Akhir</span>
                <strong>${formatRupiah(total)}</strong>
            </div>
        </div>`;

    window._visitConfirmInProgress = true;
    let ok = false;
    try {
        ok = await showConfirm(message, 'warning', {
            confirmText: 'Ya, Simpan Kunjungan',
            cancelText: 'Batal',
            maxWidth: '520px',
            html: true
        });
    } finally {
        window._visitConfirmInProgress = false;
    }
    if (!ok) {
        resetVisitSubmitLoading();
        return null;
    }
    setVisitSubmitLoading(true);
    return formData;
}

async function calcVisitPrice(pointValue) {
    const priceInput = document.getElementById('visit-price-input');
    const hint = document.getElementById('price-hint');
    const freeCheckbox = document.getElementById('visit-free-checkbox');
    if (!priceInput || !pointValue || pointValue <= 0) return;
    if (freeCheckbox && freeCheckbox.checked) {
        priceInput.value = 0;
        priceInput.dataset.autoPrice = '0';
        if (hint) hint.textContent = 'gratis';
        setVisitManualPriceUsed(false);
        syncVisitHerbalItems();
        return;
    }
    const serviceSelect = document.getElementById('visit-service-select');
    const selected = serviceSelect ? serviceSelect.options[serviceSelect.selectedIndex] : null;
    const serviceName = selected ? (selected.dataset.name || selected.textContent || 'Bekam') : 'Bekam';
    const servicePrice = selected ? parseFloat(selected.dataset.price || 0) : 0;
    if (serviceName.toLowerCase() !== 'bekam') {
        const calc = parseInt(pointValue) * servicePrice;
        const rounded = Math.round(calc);
        priceInput.value = rounded;
        priceInput.dataset.autoPrice = String(rounded);
        if (hint) hint.textContent = `-> ${formatRupiah(calc)} `;
        setVisitManualPriceUsed(false);
        syncVisitHerbalItems();
        return;
    }
    const calc = parseInt(pointValue) * (window._visitPricePerPoint || 10000);
    priceInput.value = calc;
    priceInput.dataset.autoPrice = String(calc);
    if (hint) hint.textContent = `-> ${formatRupiah(calc)} `;
    setVisitManualPriceUsed(false);
    syncVisitHerbalItems();
}

function setVisitManualPriceUsed(value) {
    const manualInput = document.getElementById('visit-manual-price-used');
    const hint = document.getElementById('price-hint');
    if (manualInput) manualInput.value = value ? 'true' : 'false';
    if (hint && value) hint.textContent = 'harga manual';
}

function onVisitManualPriceInput() {
    const priceInput = document.getElementById('visit-price-input');
    const freeCheckbox = document.getElementById('visit-free-checkbox');
    if (!priceInput || (freeCheckbox && freeCheckbox.checked)) {
        setVisitManualPriceUsed(false);
        syncVisitHerbalItems();
        return;
    }
    const autoPrice = Number(priceInput.dataset.autoPrice || 0);
    const currentPrice = Number(priceInput.value || 0);
    setVisitManualPriceUsed(autoPrice > 0 && currentPrice !== autoPrice);
    syncVisitHerbalItems();
}

// ── LEGACY COMPAT (dipertahankan agar modal.js tidak error) ──────────────────
function onVisitServiceChange() {
    const serviceSelect = document.getElementById('visit-service-select');
    const pointInput = document.getElementById('visit-point-input');
    const serviceNameInput = document.getElementById('visit-service-name');
    const quantityLabel = document.getElementById('visit-quantity-label');
    const notesInput = document.getElementById('visit-notes-input');
    if (!serviceSelect || !pointInput) return;

    const selected = serviceSelect.options[serviceSelect.selectedIndex];
    const serviceName = selected ? (selected.dataset.name || selected.textContent || 'Bekam') : 'Bekam';
    const unit = selected ? (selected.dataset.unit || 'titik') : 'titik';
    const qty = selected ? parseInt(selected.dataset.qty || 1) : 13;
    const notesTemplate = selected ? (selected.dataset.notes || '') : '';

    if (serviceNameInput) serviceNameInput.value = serviceName;
    if (quantityLabel) quantityLabel.textContent = 'Jumlah Layanan';
    if (notesInput) notesInput.placeholder = notesTemplate || 'Keluhan, kondisi, dll...';
    pointInput.value = qty || 1;
    calcVisitPrice(pointInput.value);
}

function onVisitFreeChange() {
    const freeCheckbox = document.getElementById('visit-free-checkbox');
    const reasonSelect = document.getElementById('visit-free-reason');
    const priceInput = document.getElementById('visit-price-input');
    const hint = document.getElementById('price-hint');
    const pointInput = document.getElementById('visit-point-input');
    const isFree = !!(freeCheckbox && freeCheckbox.checked);

    if (reasonSelect) {
        reasonSelect.disabled = !isFree;
        reasonSelect.required = isFree;
    }
    if (priceInput) {
        priceInput.readOnly = isFree;
        if (isFree) priceInput.value = 0;
    }
    if (hint && isFree) hint.textContent = 'gratis';
    if (isFree) setVisitManualPriceUsed(false);
    if (!isFree && pointInput) calcVisitPrice(pointInput.value);

    const statusSelect = document.getElementById('visit-payment-status');
    const methodSelect = document.getElementById('visit-payment-method');
    const amountInput = document.getElementById('visit-amount-paid');
    const voucherInput = document.getElementById('visit-voucher-input');
    const voucherHelp = document.getElementById('visit-voucher-help');

    // Kunjungan gratis harus selalu selesai/lunas karena nominalnya Rp0.
    if (isFree) {
        if (statusSelect) {
            if (statusSelect.value !== 'paid') {
                statusSelect.dataset.beforeFreeStatus = statusSelect.value || 'unpaid';
            }
            statusSelect.value = 'paid';
            statusSelect.disabled = true;
            statusSelect.setAttribute('aria-disabled', 'true');
            statusSelect.title = 'Kunjungan gratis otomatis berstatus lunas.';
        }
        if (methodSelect) {
            if (methodSelect.value !== 'free') {
                methodSelect.dataset.beforeFreeMethod = methodSelect.value || 'other';
            }
            methodSelect.value = 'free';
            methodSelect.disabled = true;
            methodSelect.setAttribute('aria-disabled', 'true');
            methodSelect.title = 'Kunjungan gratis otomatis memakai metode Gratis.';
        }
        if (amountInput) {
            amountInput.value = '0';
            amountInput.required = false;
            amountInput.disabled = true;
        }
        if (voucherInput) {
            voucherInput.dataset.beforeFreeVoucher = voucherInput.value || '';
            voucherInput.value = '';
            voucherInput.disabled = true;
            voucherInput.placeholder = 'Tidak berlaku untuk kunjungan gratis';
        }
        if (voucherHelp) voucherHelp.textContent = 'Voucher dinonaktifkan karena kunjungan gratis.';
    } else if (statusSelect) {
        statusSelect.removeAttribute('aria-disabled');
        statusSelect.disabled = false;
        statusSelect.title = '';
        if (statusSelect.dataset.beforeFreeStatus) {
            statusSelect.value = statusSelect.dataset.beforeFreeStatus;
            delete statusSelect.dataset.beforeFreeStatus;
        }
        if (methodSelect) {
            methodSelect.removeAttribute('aria-disabled');
            methodSelect.disabled = false;
            methodSelect.title = '';
            if (methodSelect.dataset.beforeFreeMethod) {
                methodSelect.value = methodSelect.dataset.beforeFreeMethod;
                delete methodSelect.dataset.beforeFreeMethod;
            }
        }
        if (amountInput) {
            amountInput.disabled = false;
        }
        if (voucherInput) {
            voucherInput.disabled = false;
            voucherInput.placeholder = 'Contoh: SEHAT10';
            if (voucherInput.dataset.beforeFreeVoucher) {
                voucherInput.value = voucherInput.dataset.beforeFreeVoucher;
                delete voucherInput.dataset.beforeFreeVoucher;
            }
        }
        if (voucherHelp) voucherHelp.textContent = 'Voucher aktif untuk kunjungan berbayar.';
    }

    onVisitPaymentStatusChange();

    syncVisitHerbalItems();
    syncVisitFreeControl();
}

function onVisitPaymentStatusChange() {
    const statusSelect = document.getElementById('visit-payment-status');
    const freeCheckbox = document.getElementById('visit-free-checkbox');
    if (freeCheckbox?.checked && statusSelect && statusSelect.value !== 'paid') {
        statusSelect.value = 'paid';
    }
    const isFree = !!freeCheckbox?.checked;
    const status = isFree ? 'paid' : statusSelect?.value;
    const group = document.getElementById('visit-amount-paid-group');
    const amountInput = document.getElementById('visit-amount-paid');
    const methodSelect = document.getElementById('visit-payment-method');
    const paymentHint = document.getElementById('visit-payment-revenue-hint');
    const billTotal = _visitGrandTotal();

    if (group) {
        group.style.display = (status === 'partial') ? 'block' : 'none';
        if (isFree && amountInput) {
            amountInput.required = false;
            amountInput.value = '0';
            amountInput.disabled = true;
        } else if (status === 'unpaid' && amountInput) {
            amountInput.required = false;
            amountInput.value = '0';
            amountInput.disabled = true;
        } else if (status === 'paid' && amountInput) {
            amountInput.required = false;
            amountInput.value = String(billTotal);
            amountInput.disabled = true;
        } else if (status === 'partial' && amountInput) {
            amountInput.required = true;
            amountInput.disabled = false;
        } else if (amountInput) {
            amountInput.required = false;
            amountInput.value = '';
            amountInput.disabled = false;
        }
    }

    if (statusSelect) {
        statusSelect.disabled = isFree;
        statusSelect.toggleAttribute('aria-disabled', isFree);
    }

    if (methodSelect) {
        const directMethods = new Set(['cash', 'debit', 'credit_card']);
        Array.from(methodSelect.options).forEach(option => {
            const value = option.value;
            option.disabled = false;
            option.hidden = false;
            if (isFree) {
                option.disabled = value !== 'free';
                option.hidden = value !== 'free';
            } else if (value === 'free') {
                option.disabled = true;
                option.hidden = true;
            } else if (status === 'unpaid' && directMethods.has(value)) {
                option.disabled = true;
                option.hidden = true;
            }
        });

        if (isFree) {
            methodSelect.value = 'free';
            methodSelect.disabled = true;
            methodSelect.setAttribute('aria-disabled', 'true');
        } else if (status === 'unpaid') {
            methodSelect.value = 'other';
            methodSelect.disabled = true;
            methodSelect.setAttribute('aria-disabled', 'true');
            methodSelect.title = 'Belum ada metode karena pembayaran belum diterima.';
        } else {
            methodSelect.disabled = false;
            methodSelect.removeAttribute('aria-disabled');
            methodSelect.title = '';
            const previousStatus = statusSelect?.dataset.previousStatus || '';
            if (status !== 'unpaid' && previousStatus === 'unpaid' && methodSelect.value === 'other') {
                methodSelect.value = 'cash';
            }
            if (!methodSelect.value || methodSelect.selectedOptions[0]?.disabled) {
                methodSelect.value = status === 'unpaid' ? 'other' : 'cash';
            }
        }
    }

    if (paymentHint) {
        if (isFree) {
            paymentHint.textContent = 'Kunjungan gratis tidak menambah pendapatan.';
        } else if (status === 'paid') {
            paymentHint.textContent = 'Pembayaran lunas masuk pendapatan.';
        } else if (status === 'partial') {
            paymentHint.textContent = 'DP masuk pendapatan sebesar jumlah bayar.';
        } else {
            paymentHint.textContent = 'Belum ada pembayaran. Tagihan belum masuk pendapatan.';
        }
    }

    if (statusSelect) statusSelect.dataset.previousStatus = status || '';
}

function setVisitPaymentQuick(status, method) {
    const statusSelect = document.getElementById('visit-payment-status');
    const methodSelect = document.getElementById('visit-payment-method');
    const amountInput = document.getElementById('visit-amount-paid');
    const freeCheckbox = document.getElementById('visit-free-checkbox');
    if (freeCheckbox?.checked) {
        showToast('Kunjungan gratis otomatis memakai metode Gratis.', 'info');
        return;
    }
    if (statusSelect) statusSelect.value = status;
    if (methodSelect) methodSelect.value = method;
    onVisitPaymentStatusChange();
    if (status === 'paid' && amountInput) {
        amountInput.value = String(_visitGrandTotal());
    }
    if (status === 'unpaid' && amountInput) {
        amountInput.value = '0';
    }
    if (status === 'partial') {
        amountInput?.focus();
        amountInput?.select?.();
    }
}

function syncVisitFreeControl() {
    const input = document.getElementById('visit-free-checkbox');
    const control = document.getElementById('visit-free-control');
    const field = control ? control.closest('.visit-free-field') : null;
    const title = document.getElementById('visit-free-title');
    const help = document.getElementById('visit-free-help');
    const active = !!(input && input.checked);

    if (control) {
        control.classList.toggle('is-on', active);
        control.classList.toggle('is-off', !active);
    }
    if (field) {
        field.classList.toggle('is-free-active', active);
        field.classList.toggle('is-paid-active', !active);
    }
    if (title) title.textContent = active ? 'Kunjungan Gratis Aktif' : 'Kunjungan Gratis';
    if (help) {
        help.textContent = active
            ? 'Harga kunjungan menjadi Rp0 dan wajib pilih alasan gratis.'
            : 'Aktifkan jika kunjungan ini gratis/promo/koreksi.';
    }
}

function showPatientVisits(idx) {
    const patients = window._patientsData || [];
    const p = patients[idx];
    if (!p) return;
    _dtShowVisits(p.id);
}

function filterPatients() {
    // No-op: DataTable has its own built-in search
}
