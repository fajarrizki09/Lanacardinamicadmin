// FOLLOW-UP PASIEN

const CRM_SEGMENTS = {
    "": "Semua kategori pasien",
    new: "Pasien baru",
    active: "Aktif",
    loyal: "Rutin",
    high_value: "Pasien Prioritas",
    high_value_at_risk: "Pasien Prioritas Perlu Dihubungi",
    needs_followup: "Perlu follow-up",
    dormant: "Lama Tidak Datang",
};

const CRM_STATUSES = {
    "": "Semua status kontak",
    pending: "Belum dihubungi",
    contacted: "Sudah dihubungi",
    sudah_dihubungi: "Sudah dihubungi",
    waiting: "Menunggu respon",
    menunggu_respon: "Menunggu respon",
    perlu_follow_up: "Perlu follow-up",
    booked: "Sudah booking",
    booking_ulang: "Booking ulang",
    inactive: "Tidak aktif",
};

const CRM_OUTCOMES = {
    "": "Pilih hasil follow-up",
    no_response: "Tidak Dibalas",
    replied: "Pasien membalas",
    asked_schedule: "Minta Jadwal",
    booked: "Sudah booking",
    not_interested: "Tidak Berminat",
    contact_later: "Hubungi Nanti",
    invalid_number: "Nomor Tidak Valid",
};

const CRM_LABELS = {
    pending: "Belum dihubungi",
    contacted: "Sudah dihubungi",
    sudah_dihubungi: "Sudah dihubungi",
    waiting: "Menunggu respon",
    menunggu_respon: "Menunggu respon",
    perlu_follow_up: "Perlu follow-up",
    needs_followup: "Perlu follow-up",
    no_response: "Tidak Dibalas",
    replied: "Pasien membalas",
    asked_schedule: "Minta Jadwal",
    booked: "Sudah booking",
    booking_ulang: "Booking ulang",
    not_interested: "Tidak Berminat",
    contact_later: "Hubungi Nanti",
    invalid_number: "Nomor Tidak Valid",
    inactive: "Tidak aktif",
    overdue: "Terlambat",
    today: "Hari ini",
    scheduled: "Terjadwal",
    high_value: "Pasien Prioritas",
    high_value_at_risk: "Pasien Prioritas Perlu Dihubungi",
    dormant: "Lama Tidak Datang",
};

const CRM_MESSAGE_TEMPLATES = {
    routine_polite: "Kontrol sopan",
    routine_warm: "Kontrol hangat",
    routine_short: "Kontrol singkat",
    routine_neutral: "Kontrol netral",
    routine_friendly: "Kontrol santai",
    reactivation_polite: "Aktifkan kembali",
    reactivation_neutral: "Aktifkan kembali netral",
    promo_polite: "Promo / paket",
    promo_neutral: "Promo netral",
    aftercare_polite: "Aftercare",
    aftercare_neutral: "Aftercare netral",
};

let CRM_TAG_OPTIONS = { service: [], manual: [] };

async function fetchCRMJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Gagal memuat data follow-up pasien');
    }
    return response.json();
}

async function renderCRM() {
    const display = document.getElementById('display-area');
    display.innerHTML = renderCRMLoading('Memuat data follow-up pasien...');
    let summary;
    let patients;
    let tagOptions;
    let dailyTasks;
    let conversionReport;
    try {
        [summary, patients, tagOptions, dailyTasks, conversionReport] = await Promise.all([
            fetchCRMJson('/crm/summary'),
            fetchCRMJson('/crm/patients'),
            fetchCRMJson('/crm/tag-options').catch(() => ({ service: [], manual: [] })),
            fetchCRMJson('/crm/daily-tasks').catch(() => ({ total_tasks: 0, overdue: 0, due_today: 0, high_priority: 0 })),
            fetchCRMJson('/crm/conversion-report').catch(() => ({ conversion_rate: 0, total_confirmed_sent: 0 })),
        ]);
    } catch (error) {
        display.innerHTML = renderCRMError(error.message || 'Gagal memuat data follow-up pasien.');
        return;
    }
    CRM_TAG_OPTIONS = tagOptions || { service: [], manual: [] };

    display.innerHTML = `
        <div class="crm-shell">
            <div class="ops-summary">
                <div>
                    <span class="section-kicker">Follow-up Pasien</span>
                    <h2>Daftar Pasien yang Perlu Dihubungi</h2>
                    <p>Follow-up Pasien membantu admin melihat pasien yang perlu dihubungi kembali, mengirim WhatsApp, mencatat hasil respon, dan menjadwalkan follow-up berikutnya.</p>
                </div>
                <div class="ops-status ${summary.need_followup > 0 ? 'attention' : ''}">
                    <i class="fas ${summary.need_followup > 0 ? 'fa-phone-alt' : 'fa-check-circle'}"></i>
                    <span>${summary.need_followup || 0} perlu follow-up</span>
                </div>
            </div>

            <div class="stats-grid crm-stats">
                ${crmStatCard('fa-users', 'Total Pasien', summary.total_patients || 0)}
                ${crmStatCard('fa-phone-volume', 'Perlu Follow-up', summary.need_followup || 0)}
                ${crmStatCard('fa-gem', 'Pasien Prioritas', summary.high_value || 0)}
                ${crmStatCard('fa-tasks', 'Tugas Hari Ini', dailyTasks.total_tasks || 0)}
                ${crmStatCard('fa-chart-line', 'Berhasil Booking Lagi', `${conversionReport.conversion_rate || 0}%`)}
            </div>

            <div class="card crm-panel">
                <div class="crm-toolbar crm-toolbar-compact">
                    <select id="crm-segment-filter">${crmOptions(CRM_SEGMENTS)}</select>
                    <select id="crm-status-filter">${crmOptions(CRM_STATUSES)}</select>
                    <select id="crm-service-filter">${crmTagOptions('service', 'Semua layanan', CRM_TAG_OPTIONS)}</select>
                    <select id="crm-manual-tag-filter">${crmTagOptions('manual', 'Semua tag', CRM_TAG_OPTIONS)}</select>
                    <input id="crm-search-input" type="search" placeholder="Cari nama / no HP...">
                    <button type="button" class="crm-refresh-btn" onclick="loadCRMList()">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
                <div id="crm-patient-list">${renderCRMPatients(patients)}</div>
            </div>
        </div>
    `;

    document.getElementById('crm-segment-filter').addEventListener('change', loadCRMList);
    document.getElementById('crm-status-filter').addEventListener('change', loadCRMList);
    document.getElementById('crm-service-filter').addEventListener('change', onCRMServiceFilterChange);
    document.getElementById('crm-manual-tag-filter').addEventListener('change', onCRMManualTagFilterChange);
    document.getElementById('crm-search-input').addEventListener('input', debounce(loadCRMList, 350));
}

function renderCRMLoading(message = 'Memuat data...') {
    return `
        <div class="dashboard-empty compact crm-state">
            <i class="fas fa-spinner fa-spin"></i>
            <span>${escapeHtml(message)}</span>
        </div>
    `;
}

function renderCRMError(message) {
    return `
        <div class="dashboard-empty compact crm-state crm-state-error">
            <i class="fas fa-exclamation-circle"></i>
            <span>${escapeHtml(message || 'Gagal memuat data follow-up pasien.')}</span>
        </div>
    `;
}

function crmStatCard(icon, label, value) {
    const displayValue = typeof value === 'number' ? Number(value || 0) : escapeHtml(String(value || 0));
    return `
        <div class="stat-card">
            <div class="stat-icon green"><i class="fas ${icon}"></i></div>
            <div class="stat-details">
                <h4>${escapeHtml(label)}</h4>
                <h2>${displayValue}</h2>
            </div>
        </div>
    `;
}

function crmOptions(options) {
    return Object.entries(options)
        .map(([value, label]) => `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`)
        .join('');
}

function crmTagOptions(type, emptyLabel, options = CRM_TAG_OPTIONS) {
    const rows = options[type] || [];
    let html = `<option value="">${escapeHtml(emptyLabel)}</option>`;
    html += rows.map(tag => {
        const label = type === 'service' ? String(tag.label || '').replace(/^Layanan:\s*/i, '') : tag.label;
        return `<option value="${escapeHtml(tag.value)}">${escapeHtml(label || tag.value)}</option>`;
    }).join('');
    return html;
}

function onCRMServiceFilterChange() {
    const manualSelect = document.getElementById('crm-manual-tag-filter');
    if (document.getElementById('crm-service-filter')?.value && manualSelect) manualSelect.value = '';
    loadCRMList();
}

function onCRMManualTagFilterChange() {
    const serviceSelect = document.getElementById('crm-service-filter');
    if (document.getElementById('crm-manual-tag-filter')?.value && serviceSelect) serviceSelect.value = '';
    loadCRMList();
}

function crmHumanLabel(value, fallback = '') {
    const key = String(value || '').trim();
    if (!key) return fallback || '-';
    return CRM_LABELS[key] || fallback || key.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
}

function crmShortFollowupLabel(value, fallback = '') {
    const label = crmHumanLabel(value, fallback);
    const normalized = String(label || '').trim().toLowerCase();
    const shortLabels = {
        'high value perlu follow-up': 'Pasien Prioritas Perlu Dihubungi',
        'pasien prioritas perlu dihubungi': 'Pasien Prioritas Perlu Dihubungi',
        'perlu follow-up': 'Perlu follow-up',
        'menunggu respon': 'Menunggu respon',
        'belum dihubungi': 'Belum dihubungi',
        'booking ulang': 'Booking ulang',
        'sudah booking': 'Booking ulang',
        'sudah dihubungi': 'Sudah dihubungi',
    };
    return shortLabels[normalized] || label;
}

function maskPhone(phone) {
    const text = String(phone || '').trim();
    const digits = text.replace(/\D+/g, '');
    if (!digits) return '-';
    if (digits.length <= 8) return escapeHtml(text);
    return `${digits.slice(0, 7)}••••${digits.slice(-2)}`;
}

function renderCRMPatients(patients) {
    if (!patients.length) {
        return `
            <div class="dashboard-empty">
                <i class="fas fa-search"></i>
                <span>Tidak ada pasien sesuai filter.</span>
            </div>
        `;
    }

    return `
        <div class="crm-followup-list">
            ${patients.map(renderCRMRowCard).join('')}
        </div>
    `;
}

function renderCRMRowCard(patient) {
    const days = patient.days_since_last_visit;
    const lastVisit = patient.last_visit || '-';
    const staleText = days === null || days === undefined ? 'Belum pernah' : `${days} hari lalu`;
    const dueBadge = renderCRMDueBadge(patient);
    const serviceBadges = renderCRMServiceBadges(patient.tags || []);
    const followupLabel = crmShortFollowupLabel(patient.followup_status, patient.followup_status_label);
    const outcomeLabel = crmHumanLabel(patient.followup_outcome, patient.followup_outcome_label);
    const recommendation = compactCRMRecommendation(patient);

    return `
        <div class="crm-followup-card">
            <div class="crm-patient-block">
                <div class="crm-patient-name" title="${escapeHtml(patient.name)}">${escapeHtml(patient.name)}</div>
                <div class="crm-patient-phone"><i class="fas fa-phone-alt"></i> ${maskPhone(patient.phone)}</div>
                <div class="crm-patient-tags">${serviceBadges}</div>
                <div class="crm-recommendation">
                    <i class="fas fa-lightbulb" style="color:var(--warning); margin-right:4px;"></i>
                    ${escapeHtml(recommendation)}
                </div>
            </div>

            <div class="crm-metric-block">
                <span class="crm-metric-chip ${patient.segment === 'high_value' || patient.segment === 'high_value_at_risk' ? 'priority' : ''}">
                    ${escapeHtml(crmHumanLabel(patient.segment, patient.segment_label))}
                </span>
                <span class="crm-metric-chip">${Number(patient.total_visits || 0)}x kunjungan</span>
                <span class="crm-metric-chip crm-revenue-chip">${formatRupiah(patient.total_spent || 0)}</span>
            </div>

            <div class="crm-status-block">
                <div class="crm-status-label-top">Terakhir: ${escapeHtml(lastVisit)} (${escapeHtml(staleText)})</div>
                <div style="display:flex; align-items:center; gap:5px; flex-wrap:wrap;">
                    <span class="badge ${crmFollowupBadge(patient.followup_status)}">${escapeHtml(followupLabel)}</span>
                    ${dueBadge}
                </div>
                ${patient.follow_up_date ? `<div class="crm-next-date"><i class="far fa-calendar-alt"></i> Follow-up: ${escapeHtml(patient.follow_up_date)}</div>` : ''}
                ${patient.followup_outcome ? `<div class="crm-phone-muted" style="font-style:italic; font-size:10px;">Hasil: ${escapeHtml(outcomeLabel)}</div>` : ''}
            </div>

            <div class="crm-action-block">
                <button type="button" class="btn btn-primary crm-detail-btn" onclick="openCRMFollowup(${patient.id})">
                    Detail
                </button>
            </div>
        </div>
    `;
}

function renderCRMServiceBadges(tags) {
    const services = (tags || []).filter(tag => tag.type === 'service');
    const visibleServices = services.slice(0, 2);
    const hiddenServiceCount = Math.max(services.length - 2, 0);
    if (!visibleServices.length && !hiddenServiceCount) return '';
    return `
        <div class="crm-service-badges">
            ${visibleServices.map(renderCRMTagBadge).join('')}
            ${hiddenServiceCount > 0 ? `<span class="crm-badge crm-badge-more">+${hiddenServiceCount} layanan</span>` : ''}
        </div>
    `;
}

function renderCRMTagBadge(tag) {
    const label = String(tag.label || '').replace(/^Layanan:\s*/i, '');
    return `<span class="crm-tag-chip service">${escapeHtml(label)}</span>`;
}

function compactCRMRecommendation(patient) {
    const parts = [];
    if (patient.segment === 'high_value_at_risk') {
        parts.push('Pasien prioritas perlu dihubungi');
    } else if (patient.segment === 'needs_followup' || patient.segment === 'dormant') {
        parts.push(patient.segment === 'dormant' ? 'Lama tidak datang' : 'Perlu dihubungi');
    } else if (patient.segment === 'high_value') {
        parts.push('Pasien prioritas aktif');
    } else {
        parts.push(crmHumanLabel(patient.segment, patient.segment_label));
    }
    if (patient.top_service) parts.push(`Layanan: ${patient.top_service}`);
    if (patient.top_therapist) parts.push(`Terapis: ${patient.top_therapist}`);
    return parts.filter(Boolean).join(' - ');
}

function crmSegmentBadge(segment) {
    if (segment === 'high_value_at_risk') return 'badge-danger-soft';
    if (segment === 'needs_followup' || segment === 'dormant') return 'badge-warning-soft';
    if (segment === 'high_value' || segment === 'loyal') return 'badge-success-soft';
    return '';
}

function crmFollowupBadge(status) {
    if (status === 'pending') return 'badge-danger-soft';
    if (status === 'waiting' || status === 'menunggu_respon') return 'badge-warning-soft';
    if (status === 'booked') return 'badge-success-soft';
    if (status === 'inactive') return 'badge-muted-soft';
    if (status === 'contacted') return 'badge-info-soft';
    return '';
}

function renderCRMDueBadge(patient) {
    if (!patient.followup_due_status) return '';
    const badgeClass = patient.followup_due_status === 'scheduled' ? 'badge-info-soft' : 'badge-warning-soft';
    return `<span class="badge ${badgeClass} crm-due-badge">${escapeHtml(crmHumanLabel(patient.followup_due_status, patient.followup_due_label || ''))}</span>`;
}

function renderCRMManualTagEditor(patient) {
    const selected = new Set((patient.tags || []).filter(tag => tag.type === 'manual').map(tag => tag.value));
    const options = CRM_TAG_OPTIONS.manual || [];
    const checkboxes = options.map(tag => `
        <label class="crm-checkbox-pill">
            <input type="checkbox" class="crm-manual-tag-input" value="${escapeHtml(tag.value)}" data-label="${escapeHtml(tag.label)}" ${selected.has(tag.value) ? 'checked' : ''}>
            <span>${escapeHtml(tag.label)}</span>
        </label>
    `).join('');
    return `
        <div class="form-group">
            <label>Tag Manual</label>
            <div class="crm-checkbox-grid">${checkboxes || '<span class="crm-subtext">Belum ada opsi tag manual.</span>'}</div>
            <input type="text" id="crm-custom-tags-input" placeholder="Tambah tag custom, pisahkan dengan koma" style="margin-top:8px;">
        </div>
    `;
}

function renderCRMContactPreferenceEditor(patient) {
    const pref = patient.contact_preference || {};
    return `
        <div class="form-group">
            <label>Preferensi Kontak</label>
            <label class="crm-checkbox-line">
                <input type="checkbox" id="crm-pref-reminder" ${pref.boleh_reminder_kontrol !== false ? 'checked' : ''}>
                <span>Boleh reminder kontrol</span>
            </label>
            <label class="crm-checkbox-line">
                <input type="checkbox" id="crm-pref-promo" ${pref.boleh_promo !== false ? 'checked' : ''}>
                <span>Boleh promo</span>
            </label>
            <label class="crm-checkbox-line danger">
                <input type="checkbox" id="crm-pref-do-not-contact" ${pref.jangan_dihubungi ? 'checked' : ''}>
                <span>Jangan dihubungi</span>
            </label>
            <textarea id="crm-pref-note" rows="2" placeholder="Catatan kontak...">${escapeHtml(pref.catatan_kontak || '')}</textarea>
        </div>
    `;
}

async function loadCRMList() {
    const segment = document.getElementById('crm-segment-filter')?.value || '';
    const status = document.getElementById('crm-status-filter')?.value || '';
    const serviceTag = document.getElementById('crm-service-filter')?.value || '';
    const manualTag = document.getElementById('crm-manual-tag-filter')?.value || '';
    const search = document.getElementById('crm-search-input')?.value || '';
    const tagType = serviceTag ? 'service' : (manualTag ? 'manual' : '');
    const tag = serviceTag || manualTag;
    const params = new URLSearchParams({ segment, status, search, tag_type: tagType, tag });
    const list = document.getElementById('crm-patient-list');
    if (list) list.innerHTML = renderCRMLoading('Memuat daftar pasien...');
    try {
        const patients = await fetchCRMJson(`/crm/patients?${params.toString()}`);
        if (list) list.innerHTML = renderCRMPatients(patients);
    } catch (error) {
        if (list) list.innerHTML = renderCRMError(error.message || 'Gagal memuat daftar follow-up pasien.');
    }
}

async function openCRMFollowup(patientId, focusWhatsApp = false, focusVoucher = false) {
    let patient;
    let history = [];
    let messageLogs = [];
    let vouchers = { special: [], general: [] };
    try {
        patient = await fetchCRMJson(`/crm/patient/${patientId}`);
        [history, messageLogs, vouchers] = await Promise.all([
            fetchCRMJson(`/crm/patient/${patientId}/followups`).catch(() => []),
            fetchCRMJson(`/crm/patient/${patientId}/message-logs`).catch(() => []),
            fetchCRMJson(`/crm/patient/${patientId}/vouchers`).catch(() => ({ special: [], general: [] })),
        ]);
    } catch (error) {
        alert(error.message || 'Gagal membuka data follow-up pasien.');
        return;
    }
    const overlay = document.createElement('div');
    overlay.className = 'crm-modal-overlay';
    overlay.innerHTML = `
        <div class="crm-modal">
            <div class="crm-modal-header">
                <div>
                    <h3>${escapeHtml(patient.name)}</h3>
                    <p>${escapeHtml(patient.recommendation)}</p>
                </div>
                <button type="button" onclick="this.closest('.crm-modal-overlay').remove()"><i class="fas fa-times"></i></button>
            </div>
            <form id="crm-followup-form">
                <input type="hidden" name="patient_id" value="${patient.id}">
                <div class="crm-followup-layout">
                    <div class="crm-followup-column">
                        <div class="crm-form-row">
                            <div class="form-group">
                                <label>Status Kontak</label>
                                <select name="status">
                                    ${Object.entries(CRM_STATUSES).filter(([value]) => value).map(([value, label]) => `
                                        <option value="${value}" ${patient.followup_status === value ? 'selected' : ''}>${escapeHtml(label)}</option>
                                    `).join('')}
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Jadwal Follow-up Berikutnya</label>
                                <input type="date" name="follow_up_date" value="${escapeHtml(patient.follow_up_date || '')}">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Catatan</label>
                            <textarea name="note" rows="4" placeholder="Contoh: sudah WhatsApp, pasien akan cek jadwal...">${escapeHtml(patient.followup_note || '')}</textarea>
                        </div>
                        <div class="crm-history-box crm-meta-box">
                            <h4>Tag & Izin Kontak</h4>
                            ${renderCRMManualTagEditor(patient)}
                            ${renderCRMContactPreferenceEditor(patient)}
                            <div style="display:flex;justify-content:flex-end;margin-top:10px;">
                                <button type="button" class="crm-row-btn" onclick="saveCRMPatientMeta(${patient.id})">
                                    <i class="fas fa-save"></i> Simpan Tag & Izin
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="crm-followup-column">
                        <div class="crm-message-box">
                            <div class="crm-voucher-tools" id="crm-voucher-tools">
                                <h4><i class="fas fa-ticket-alt"></i> Voucher Follow-up</h4>
                                <div class="crm-voucher-row">
                                    <select id="crm-selected-voucher" onchange="onCRMVoucherSelectChange()">
                                        ${renderCRMVoucherOptions(vouchers)}
                                    </select>
                                    <label class="crm-lock-override" id="crm-general-voucher-confirm-wrap" style="margin:0;">
                                        <input type="checkbox" id="crm-general-voucher-confirm">
                                        Pakai voucher umum
                                    </label>
                                </div>
                                <div class="crm-voucher-row">
                                    <input type="text" id="crm-new-voucher-name" placeholder="Nama voucher khusus">
                                    <input type="text" id="crm-new-voucher-code" placeholder="Kode voucher">
                                </div>
                                <div class="crm-voucher-row crm-voucher-create-row">
                                    <select id="crm-new-voucher-type">
                                        <option value="fixed">Nominal</option>
                                        <option value="percent">Persen</option>
                                    </select>
                                    <input type="number" id="crm-new-voucher-value" min="0" step="0.01" placeholder="Nilai diskon">
                                    <input type="date" id="crm-new-voucher-end">
                                    <button type="button" class="crm-row-btn" onclick="createCRMSpecialVoucher(${patient.id})">
                                        <i class="fas fa-plus"></i> Buat Voucher Khusus
                                    </button>
                                </div>
                                <span class="crm-subtext">Voucher khusus otomatis hanya berlaku untuk pasien ini.</span>
                            </div>
                            <input type="hidden" id="crm-whatsapp-log-id" value="">
                            <div class="crm-message-toolbar">
                                <select id="crm-message-template">
                                    ${Object.entries(CRM_MESSAGE_TEMPLATES).map(([value, label]) => `
                                        <option value="${value}">${escapeHtml(label)}</option>
                                    `).join('')}
                                </select>
                                <button type="button" class="crm-row-btn" onclick="generateCRMMessage(${patient.id})">
                                    <i class="fas fa-magic"></i> Buat Pesan
                                </button>
                            </div>
                            <div id="crm-whatsapp-lock-warning" class="crm-lock-warning hidden" data-lock-active="false"></div>
                            <label id="crm-whatsapp-override-wrap" class="crm-lock-override hidden">
                                <input type="checkbox" id="crm-whatsapp-override-lock">
                                Tetap buka WhatsApp
                            </label>
                            <textarea id="crm-generated-message" rows="7" placeholder="Klik Buat Pesan untuk melihat isi WhatsApp."></textarea>
                            <div class="crm-message-actions">
                                <button type="button" class="crm-row-btn" onclick="copyCRMMessage()">
                                    <i class="fas fa-copy"></i> Salin
                                </button>
                                <button type="button" class="crm-wa-btn" onclick="openCRMWhatsAppLink(${patient.id})">
                                    <i class="fab fa-whatsapp"></i> Buka WhatsApp
                                </button>
                                <button type="button" class="crm-row-btn" onclick="markCRMWhatsAppContacted(${patient.id})">
                                    <i class="fas fa-check"></i> Tandai Sudah Dihubungi
                                </button>
                            </div>
                            <span class="crm-subtext">Pesan tidak dikirim otomatis. Status Sudah dihubungi hanya dicatat setelah admin menekan tombol konfirmasi.</span>
                        </div>
                        <div class="crm-history-box crm-log-box">
                            <h4>Riwayat WhatsApp</h4>
                            <div id="crm-message-log-list">${renderCRMMessageLogs(messageLogs)}</div>
                        </div>
                        <div class="crm-history-box crm-outcome-box">
                            <h4>Hasil Follow-up</h4>
                            <div style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:10px;">
                                <select id="crm-followup-outcome">${crmOptions(CRM_OUTCOMES)}</select>
                                <input type="date" id="crm-outcome-follow-up-date" value="${escapeHtml(patient.follow_up_date || '')}">
                            </div>
                            <textarea id="crm-followup-outcome-note" rows="3" placeholder="Catatan hasil follow-up..." style="margin-top:8px;"></textarea>
                            <div style="display:flex;justify-content:flex-end;margin-top:10px;">
                                <button type="button" class="crm-row-btn" onclick="saveCRMFollowupOutcome(${patient.id})">
                                    <i class="fas fa-clipboard-check"></i> Simpan Hasil
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="crm-history-box crm-followup-history-box">
                    <h4>Riwayat follow-up</h4>
                    ${renderCRMFollowupHistory(history)}
                </div>
                <div class="crm-modal-actions">
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Simpan Follow-up</button>
                </div>
            </form>
        </div>
    `;

    document.body.appendChild(overlay);
    document.getElementById('crm-followup-form').addEventListener('submit', submitCRMFollowup);
    onCRMVoucherSelectChange();
    generateCRMMessage(patient.id);
    if (focusWhatsApp) {
        setTimeout(() => document.getElementById('crm-generated-message')?.focus(), 80);
    }
    if (focusVoucher) {
        setTimeout(() => document.getElementById('crm-new-voucher-name')?.focus(), 80);
    }
}

async function openCRMWhatsApp(patientId) {
    try {
        await openCRMFollowup(patientId, true);
    } catch (error) {
        alert(error.message || 'Gagal membuka WhatsApp follow-up.');
    }
}

function renderCRMFollowupHistory(history) {
    if (!history.length) {
        return `<div class="crm-history-empty">Belum ada riwayat follow-up.</div>`;
    }
    return `
        <div class="crm-history-list">
            ${history.map(item => `
                <div class="crm-history-item">
                    <div>
                        <strong>${escapeHtml(crmHumanLabel(item.status, item.status_label || '-'))}</strong>
                        <span>${escapeHtml(item.created_at || '-')}</span>
                    </div>
                    ${item.follow_up_date ? `<span class="badge">Berikutnya: ${escapeHtml(item.follow_up_date)}</span>` : ''}
                    ${item.last_contacted_at ? `<span class="crm-subtext">Dihubungi: ${escapeHtml(item.last_contacted_at)}</span>` : ''}
                    ${item.outcome ? `<span class="crm-subtext">Hasil: ${escapeHtml(crmHumanLabel(item.outcome, item.outcome_label))}</span>` : ''}
                    ${item.note ? `<p>${escapeHtml(item.note)}</p>` : ''}
                </div>
            `).join('')}
        </div>
    `;
}

function renderCRMMessageLogs(logs) {
    if (!logs.length) {
        return `<div class="crm-history-empty">Belum ada riwayat WhatsApp.</div>`;
    }
    return `
        <div class="crm-history-list">
            ${logs.map(item => `
                <div class="crm-history-item">
                    <div>
                        <strong>${escapeHtml(item.message_type_label || item.message_type || '-')}</strong>
                        <span>${escapeHtml(item.created_at || '-')}</span>
                    </div>
                    <span class="badge">${escapeHtml(item.status_label || item.status || '-')}</span>
                    ${item.confirmed_at ? `<span class="crm-subtext">Terkonfirmasi: ${escapeHtml(item.confirmed_at)}</span>` : ''}
                    ${item.note ? `<p>${escapeHtml(item.note)}</p>` : ''}
                </div>
            `).join('')}
        </div>
    `;
}

function renderCRMVoucherOptions(vouchers) {
    const special = Array.isArray(vouchers?.special) ? vouchers.special : [];
    const general = Array.isArray(vouchers?.general) ? vouchers.general : [];
    let html = '<option value="">Tanpa voucher</option>';
    if (special.length) {
        html += '<optgroup label="Voucher khusus pasien">';
        html += special.map(v => `<option value="${v.id}" data-general="false">${escapeHtml(v.name)}${v.voucher_code ? ` - ${escapeHtml(v.voucher_code)}` : ''} (${escapeHtml(v.discount_label || '')})</option>`).join('');
        html += '</optgroup>';
    }
    if (general.length) {
        html += '<optgroup label="Voucher umum">';
        html += general.map(v => `<option value="${v.id}" data-general="true">${escapeHtml(v.name)}${v.voucher_code ? ` - ${escapeHtml(v.voucher_code)}` : ''} (${escapeHtml(v.discount_label || '')})</option>`).join('');
        html += '</optgroup>';
    }
    return html;
}

function onCRMVoucherSelectChange() {
    const selected = document.getElementById('crm-selected-voucher')?.selectedOptions?.[0];
    const wrap = document.getElementById('crm-general-voucher-confirm-wrap');
    const confirm = document.getElementById('crm-general-voucher-confirm');
    const isGeneral = selected?.dataset?.general === 'true';
    if (wrap) wrap.classList.toggle('hidden', !isGeneral);
    if (confirm && !isGeneral) confirm.checked = false;
}

function normalizeCRMMessageText(message) {
    let text = String(message || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim();
    if (!text) return '';
    text = text.replace(/\n{3,}/g, '\n\n');
    if (text.includes('\n')) return text;
    const parts = text.split(/(?<=[.!?])\s+(?=[A-Z0-9A-ZÀ-Þ])/).map(part => part.trim()).filter(Boolean);
    return parts.length > 1 ? parts.join('\n\n') : text;
}

async function refreshCRMVouchers(patientId) {
    const vouchers = await fetchCRMJson(`/crm/patient/${patientId}/vouchers`);
    const select = document.getElementById('crm-selected-voucher');
    if (select) {
        select.innerHTML = renderCRMVoucherOptions(vouchers);
        onCRMVoucherSelectChange();
    }
    await loadCRMList();
    return vouchers;
}

async function createCRMSpecialVoucher(patientId) {
    const name = document.getElementById('crm-new-voucher-name')?.value.trim() || '';
    const code = document.getElementById('crm-new-voucher-code')?.value.trim() || '';
    const value = document.getElementById('crm-new-voucher-value')?.value || '';
    if (!name || !code || !value) {
        showToast('Isi nama voucher, kode voucher, dan nilai diskon terlebih dahulu.', 'warning');
        return;
    }
    const formData = new FormData();
    formData.append('name', name);
    formData.append('voucher_code', code);
    formData.append('discount_type', document.getElementById('crm-new-voucher-type')?.value || 'fixed');
    formData.append('discount_value', value);
    formData.append('per_patient_limit', '1');
    formData.append('end_date', document.getElementById('crm-new-voucher-end')?.value || '');
    try {
        const response = await fetch(`/crm/patient/${patientId}/vouchers`, { method: 'POST', body: formData });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal membuat voucher khusus.');
        ['crm-new-voucher-name', 'crm-new-voucher-code', 'crm-new-voucher-value', 'crm-new-voucher-end'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        const select = document.getElementById('crm-selected-voucher');
        if (select) {
            select.innerHTML = renderCRMVoucherOptions(data.vouchers || { special: [], general: [] });
            select.value = String(data.rule_id || '');
        }
        onCRMVoucherSelectChange();
        showToast(data.message || 'Voucher khusus berhasil dibuat.', 'success');
        await loadCRMList();
    } catch (error) {
        alert(error.message || 'Gagal membuat voucher khusus.');
    }
}

function updateCRMWhatsAppState(data) {
    const logInput = document.getElementById('crm-whatsapp-log-id');
    const warningBox = document.getElementById('crm-whatsapp-lock-warning');
    const overrideWrap = document.getElementById('crm-whatsapp-override-wrap');
    const overrideInput = document.getElementById('crm-whatsapp-override-lock');
    if (logInput && data.log_id) logInput.value = data.log_id;
    const warning = data.lock_warning || '';
    if (warningBox) {
        warningBox.textContent = warning;
        warningBox.dataset.lockActive = data.lock_active ? 'true' : 'false';
        warningBox.classList.toggle('hidden', !warning);
    }
    if (overrideWrap) {
        overrideWrap.classList.toggle('hidden', !data.lock_active);
    }
    if (overrideInput && !data.lock_active) {
        overrideInput.checked = false;
    }
}

function collectCRMManualTags() {
    const tags = Array.from(document.querySelectorAll('.crm-manual-tag-input:checked')).map(input => ({
        type: 'manual',
        value: input.value,
        label: input.dataset.label || input.value
    }));
    const custom = document.getElementById('crm-custom-tags-input')?.value || '';
    custom.split(',').map(item => item.trim()).filter(Boolean).forEach(label => {
        const value = label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || label;
        if (!tags.some(tag => tag.value === value)) tags.push({ type: 'manual', value, label });
    });
    return tags;
}

async function saveCRMPatientMeta(patientId) {
    try {
        const tagForm = new FormData();
        tagForm.append('tags', JSON.stringify(collectCRMManualTags()));
        const tagResponse = await fetch(`/crm/patient/${patientId}/tags`, { method: 'POST', body: tagForm });
        const tagData = await tagResponse.json().catch(() => ({}));
        if (!tagResponse.ok) throw new Error(tagData.detail || 'Gagal menyimpan tag pasien.');

        const prefForm = new FormData();
        prefForm.append('boleh_reminder_kontrol', document.getElementById('crm-pref-reminder')?.checked ? 'true' : 'false');
        prefForm.append('boleh_promo', document.getElementById('crm-pref-promo')?.checked ? 'true' : 'false');
        prefForm.append('jangan_dihubungi', document.getElementById('crm-pref-do-not-contact')?.checked ? 'true' : 'false');
        prefForm.append('catatan_kontak', document.getElementById('crm-pref-note')?.value || '');
        const prefResponse = await fetch(`/crm/patient/${patientId}/contact-preference`, { method: 'POST', body: prefForm });
        const prefData = await prefResponse.json().catch(() => ({}));
        if (!prefResponse.ok) throw new Error(prefData.detail || 'Gagal menyimpan preferensi kontak.');

        showToast('Tag dan izin kontak tersimpan.', 'success');
        CRM_TAG_OPTIONS = await fetchCRMJson('/crm/tag-options').catch(() => CRM_TAG_OPTIONS);
        await loadCRMList();
    } catch (error) {
        alert(error.message || 'Gagal menyimpan data follow-up pasien.');
    }
}

async function saveCRMFollowupOutcome(patientId) {
    const outcome = document.getElementById('crm-followup-outcome')?.value || '';
    if (!outcome) {
        alert('Pilih hasil follow-up terlebih dahulu.');
        return;
    }
    const formData = new FormData();
    formData.append('outcome', outcome);
    formData.append('note', document.getElementById('crm-followup-outcome-note')?.value || '');
    formData.append('follow_up_date', document.getElementById('crm-outcome-follow-up-date')?.value || '');
    const response = await fetch(`/crm/patient/${patientId}/followup-outcome`, { method: 'POST', body: formData });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        alert(data.detail || 'Gagal menyimpan hasil follow-up.');
        return;
    }
    showToast(data.message || 'Hasil follow-up tersimpan.', 'success');
    document.querySelector('.crm-modal-overlay')?.remove();
    await renderCRM();
}

async function generateCRMMessage(patientId) {
    const template = document.getElementById('crm-message-template')?.value || 'routine';
    const textarea = document.getElementById('crm-generated-message');
    if (textarea) textarea.value = 'Membuat pesan...';
    try {
        const data = await requestCRMWhatsAppLink(patientId, template);
        if (textarea) textarea.value = normalizeCRMMessageText(data.message || '');
        updateCRMWhatsAppState(data);
    } catch (error) {
        if (textarea) textarea.value = '';
        alert(error.message || 'Gagal membuat pesan follow-up.');
    }
}

async function requestCRMWhatsAppLink(patientId, templateType, customMessage = '', overrideLock = false, markOpened = false) {
    const formData = new FormData();
    formData.append('template_type', templateType || 'routine');
    formData.append('override_lock', overrideLock ? 'true' : 'false');
    formData.append('mark_opened', markOpened ? 'true' : 'false');
    const selectedVoucher = document.getElementById('crm-selected-voucher');
    const voucherRuleId = selectedVoucher?.value || '';
    if (voucherRuleId) {
        formData.append('voucher_rule_id', voucherRuleId);
        formData.append('allow_general_voucher', document.getElementById('crm-general-voucher-confirm')?.checked ? 'true' : 'false');
    }
    if (customMessage && customMessage.trim()) {
        formData.append('custom_message', customMessage.trim());
    }
    const response = await fetch(`/crm/patient/${patientId}/whatsapp-link`, {
        method: 'POST',
        body: formData,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.detail || 'Gagal membuat link WhatsApp.');
    }
    return data;
}

async function openCRMWhatsAppLink(patientId) {
    const template = document.getElementById('crm-message-template')?.value || 'routine';
    const textarea = document.getElementById('crm-generated-message');
    const message = normalizeCRMMessageText(textarea?.value || '');
    if (textarea) textarea.value = message;
    const warningBox = document.getElementById('crm-whatsapp-lock-warning');
    const overrideInput = document.getElementById('crm-whatsapp-override-lock');
    const lockActive = warningBox?.dataset.lockActive === 'true';
    const overrideLock = !!overrideInput?.checked;
    if (lockActive && !overrideLock) {
        alert('Warning kontak aktif untuk pasien ini. Centang override manual jika tetap ingin membuka WhatsApp.');
        return;
    }
    const whatsappWindow = window.open('', '_blank');
    try {
        const data = await requestCRMWhatsAppLink(patientId, template, message, overrideLock, true);
        if (textarea) textarea.value = normalizeCRMMessageText(data.message || message);
        updateCRMWhatsAppState(data);
        if (whatsappWindow) {
            whatsappWindow.location.href = data.whatsapp_url;
        } else {
            window.location.href = data.whatsapp_url;
        }
        const logs = await fetchCRMJson(`/crm/patient/${patientId}/message-logs`);
        const logList = document.getElementById('crm-message-log-list');
        if (logList) logList.innerHTML = renderCRMMessageLogs(logs);
    } catch (error) {
        if (whatsappWindow) whatsappWindow.close();
        alert(error.message || 'Gagal membuka WhatsApp.');
    }
}

async function markCRMWhatsAppContacted(patientId) {
    const form = document.getElementById('crm-followup-form');
    const formData = new FormData();
    const followUpDate = form?.querySelector('[name="follow_up_date"]')?.value || '';
    const logId = document.getElementById('crm-whatsapp-log-id')?.value || '';
    if (logId) formData.append('log_id', logId);
    if (followUpDate) formData.append('follow_up_date', followUpDate);
    const response = await fetch(`/crm/patient/${patientId}/whatsapp-confirm`, {
        method: 'POST',
        body: formData,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        alert(data.detail || 'Gagal mencatat aktivitas WhatsApp.');
        return;
    }
    showToast(data.message || 'Aktivitas WhatsApp dicatat.', 'success');
    form?.closest('.crm-modal-overlay')?.remove();
    await renderCRM();
}

async function copyCRMMessage() {
    const textarea = document.getElementById('crm-generated-message');
    const message = normalizeCRMMessageText(textarea?.value || '');
    if (!message.trim()) {
        alert('Pesan masih kosong.');
        return;
    }
    if (textarea) textarea.value = message;
    try {
        await navigator.clipboard.writeText(message);
        showToast('Pesan follow-up disalin.', 'success');
    } catch (error) {
        textarea.select();
        document.execCommand('copy');
        showToast('Pesan follow-up disalin.', 'success');
    }
}

async function submitCRMFollowup(event) {
    event.preventDefault();
    const form = event.target;
    const response = await fetch('/crm/followup', {
        method: 'POST',
        body: new FormData(form),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        alert(data.detail || 'Gagal menyimpan follow-up.');
        return;
    }
    form.closest('.crm-modal-overlay').remove();
    showToast(data.message || 'Follow-up tersimpan.', 'success');
    await renderCRM();
}

function debounce(fn, wait) {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), wait);
    };
}
