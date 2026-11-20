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
    kontrol: "Kontrol rutin",
    routine_polite: "Kontrol sopan",
    routine_warm: "Kontrol hangat",
    routine_short: "Kontrol singkat",
    routine_neutral: "Kontrol netral",
    routine_friendly: "Kontrol santai",
    reaktivasi: "Aktifkan kembali",
    reactivation_polite: "Aktifkan kembali",
    reactivation_neutral: "Aktifkan kembali netral",
    promo: "Promo / paket",
    promo_polite: "Promo / paket",
    promo_neutral: "Promo netral",
    aftercare: "Aftercare",
    aftercare_polite: "Aftercare",
    aftercare_neutral: "Aftercare netral",
    kondisi: "Cek kondisi",
    kondisi_polite: "Cek kondisi (sopan)",
    kondisi_neutral: "Cek kondisi (netral)",
    custom: "Custom"
};

let CRM_TAG_OPTIONS = { service: [], manual: [] };
let CRM_PATIENT_CACHE = new Map<number, any>();
let crmDelegationReady = false;

const debouncedLoadCRMList = debounce(() => loadCRMList(), 350);

function ensureCRMEventDelegation() {
    if (crmDelegationReady) return;
    crmDelegationReady = true;

    document.addEventListener('click', (event) => {
        const target = event.target as HTMLElement | null;
        const actionElement = target?.closest<HTMLElement>('[data-crm-action]');
        if (!actionElement) return;
        const action = actionElement.dataset.crmAction || '';
        if (!action) return;
        event.preventDefault();

const patientId = actionElement.dataset.patientId || '';
        switch (action) {
            case 'refresh-list':
                loadCRMList();
                break;
            case 'open-followup':
                openCRMFollowup(patientId);
                break;
            case 'close-modal':
                actionElement.closest('.crm-modal-overlay')?.remove();
                break;
            case 'save-meta':
                saveCRMPatientMeta(patientId);
                break;
            case 'create-voucher':
                createCRMSpecialVoucher(patientId);
                break;
            case 'generate-message':
                generateCRMMessage(patientId);
                break;
            case 'copy-message':
                copyCRMMessage();
                break;
            case 'open-whatsapp':
                openCRMWhatsAppLink(patientId, event);
                break;
            case 'mark-contacted':
                markCRMWhatsAppContacted(patientId);
                break;
            case 'save-outcome':
                saveCRMFollowupOutcome(patientId);
                break;
            case 'clear-search':
                const searchInput = document.getElementById('crm-search-input') as HTMLInputElement;
                if (searchInput) {
                    searchInput.value = '';
                    const clearBtn = document.querySelector('.crm-search-clear') as HTMLButtonElement;
                    if (clearBtn) clearBtn.style.display = 'none';
                    loadCRMList();
                }
                break;
            case 'toggle-collapsible':
                const header = actionElement.closest('.crm-collapsible-header') as HTMLElement;
                const collapsible = header?.closest('.crm-collapsible') as HTMLElement;
                if (collapsible) {
                    const content = collapsible.querySelector('.crm-collapsible-content') as HTMLElement;
                    const icon = header?.querySelector('.crm-collapsible-icon') as HTMLElement;
                    if (content && icon) {
                        const isOpen = !content.classList.contains('crm-collapsed');
                        content.classList.toggle('crm-collapsed');
                        icon.style.transform = isOpen ? 'rotate(-90deg)' : 'rotate(0deg)';
                    }
                }
                break;
        }
    });

    document.addEventListener('change', (event) => {
        const target = event.target as HTMLElement | null;
        const action = target?.dataset?.crmAction || '';
        if (action === 'filter') loadCRMList();
        if (action === 'service-filter') onCRMServiceFilterChange();
        if (action === 'manual-tag-filter') onCRMManualTagFilterChange();
        if (action === 'voucher-change') onCRMVoucherSelectChange();
        if (action === 'message-template') generateCRMMessage(target.dataset.patientId || '');
    });

document.addEventListener('input', (event) => {
        const target = event.target as HTMLInputElement | null;
        if (target?.dataset?.crmAction === 'search') {
            debouncedLoadCRMList();
            const clearBtn = document.querySelector('.crm-search-clear') as HTMLButtonElement;
            if (clearBtn) clearBtn.style.display = target.value ? 'flex' : 'none';
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            document.querySelector('.crm-modal-overlay')?.remove();
        }
        if (event.key === 'Enter' && event.target === document.getElementById('crm-search-input')) {
            loadCRMList();
        }
    });

    document.addEventListener('submit', (event) => {
        const form = event.target as HTMLFormElement | null;
        if (form?.dataset?.crmFormAction === 'followup') {
            submitCRMFollowup(event);
        }
    });
}

function crmCleanText(value, fallback = '') {
    const text = String(value || '').trim();
    return text || fallback;
}

async function ensureCRMClinicSettingsLoaded() {
    if (window._clinicSettings && typeof window._clinicSettings === 'object') {
        return window._clinicSettings;
    }
    try {
        const settings = await fetchCRMJson('/settings');
        window._clinicSettings = settings || {};
        if (settings?.clinic_name) window._clinicName = settings.clinic_name;
    } catch (error) {
        window._clinicSettings = {};
    }
    return window._clinicSettings || {};
}

type CRMClinicSettings = {
    clinic_name?: string;
    clinic_tagline?: string;
    clinic_address?: string;
    clinic_phone?: string;
    clinic_website?: string;
};

function getCRMClinicMessageProfile(settings: CRMClinicSettings = {}) {
    return {
        clinicName: crmCleanText(settings.clinic_name || window._clinicName, 'Klinik'),
        clinicTagline: crmCleanText(settings.clinic_tagline),
        clinicAddress: crmCleanText(settings.clinic_address),
        clinicPhone: crmCleanText(settings.clinic_phone),
        clinicWebsite: crmCleanText(settings.clinic_website),
    };
}

function crmClinicContactSuffix(profile) {
    const parts = [];
    if (profile.clinicPhone) parts.push(`Telp/WA: ${profile.clinicPhone}`);
    if (profile.clinicWebsite) parts.push(profile.clinicWebsite);
    return parts.length ? `\n\n${parts.join(' | ')}` : '';
}

function getCRMFollowupDateContext(value) {
    const rawDate = crmCleanText(value);
    if (!rawDate) {
        return {
            dateText: 'waktu dekat',
            isOverdue: false,
            routineText: 'Kami ingin mengingatkan jadwal kontrol/terapi berikutnya pada waktu dekat.',
            scheduleText: 'Untuk menjaga konsistensi perawatan, kami dapat membantu menjadwalkan kunjungan berikutnya.'
        };
    }

    const date = new Date(`${rawDate}T00:00:00`);
    if (Number.isNaN(date.getTime())) {
        return {
            dateText: rawDate,
            isOverdue: false,
            routineText: `Kami ingin mengingatkan jadwal kontrol/terapi berikutnya pada ${rawDate}.`,
            scheduleText: `Untuk menjaga konsistensi perawatan, kami dapat membantu menjadwalkan kunjungan berikutnya pada ${rawDate}.`
        };
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    date.setHours(0, 0, 0, 0);
    const diffDays = Math.round((date.getTime() - today.getTime()) / 86400000);

    if (diffDays < 0) {
        const lateDays = Math.abs(diffDays);
        const lateText = lateDays === 1 ? 'kemarin' : `${lateDays} hari yang lalu`;
        return {
            dateText: rawDate,
            isOverdue: true,
            routineText: `Jadwal kontrol/terapi yang tercatat pada ${rawDate} sudah terlewat (${lateText}). Kami ingin membantu menjadwalkan ulang agar perawatan tetap berlanjut dengan baik.`,
            scheduleText: `Jadwal kunjungan yang tercatat pada ${rawDate} sudah terlewat (${lateText}). Kami dapat bantu atur ulang jadwal sesuai waktu yang paling nyaman.`
        };
    }

    if (diffDays === 0) {
        return {
            dateText: rawDate,
            isOverdue: false,
            routineText: `Kami ingin mengingatkan bahwa jadwal kontrol/terapi tercatat hari ini (${rawDate}).`,
            scheduleText: `Jadwal kunjungan tercatat hari ini (${rawDate}). Kami dapat bantu konfirmasi atau ubah jadwal jika diperlukan.`
        };
    }

    return {
        dateText: rawDate,
        isOverdue: false,
        routineText: `Kami ingin mengingatkan jadwal kontrol/terapi berikutnya pada ${rawDate}.`,
        scheduleText: `Untuk menjaga konsistensi perawatan, kami dapat membantu menjadwalkan kunjungan berikutnya pada ${rawDate}.`
    };
}

function buildCRMMessageTemplate(template, patient, profile) {
    const name = crmCleanText(patient?.name, 'Bapak/Ibu');
    const clinic = profile.clinicName;
    const tagline = profile.clinicTagline ? ` (${profile.clinicTagline})` : '';
    const dateContext = getCRMFollowupDateContext(patient?.follow_up_date);
    const contact = crmClinicContactSuffix(profile);

    if (template === 'routine') {
        const actionText = dateContext.isOverdue
            ? 'Silakan balas pesan ini untuk memilih jadwal pengganti yang paling nyaman. Terima kasih.'
            : 'Silakan balas pesan ini untuk konfirmasi jadwal yang paling nyaman. Terima kasih.';
        return `Halo ${name}, kami dari ${clinic}${tagline}. ${dateContext.routineText} ${actionText}${contact}`;
    }
    if (template === 'followup') {
        return `Halo ${name}, kami dari ${clinic}. Kami ingin follow-up kondisi setelah kunjungan/terapi sebelumnya. Apakah ada keluhan, perkembangan, atau hal yang ingin dikonsultasikan? Tim kami siap membantu.${contact}`;
    }
    if (template === 'schedule') {
        return `Selamat pagi/siang ${name}, kami dari ${clinic}. ${dateContext.scheduleText} Hari dan jam apa yang paling sesuai untuk Anda?${contact}`;
    }
    if (template === 'promo') {
        return `Halo ${name}, kami dari ${clinic}. Saat ini ada informasi promo/voucher yang mungkin sesuai untuk kunjungan berikutnya. Jika berkenan, kami dapat bantu kirimkan detailnya.${contact}`;
    }
    if (template === 'friendly') {
        return `Halo ${name}, ini admin ${clinic}. Kami ingin memastikan kondisi Anda tetap terpantau dengan baik. Jika ada pertanyaan, kebutuhan jadwal ulang, atau ingin konsultasi singkat, silakan balas pesan ini kapan saja.${contact}`;
    }
    return '';
}

async function fetchCRMJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Gagal memuat data follow-up pasien');
    }
    return response.json();
}

async function renderCRM() {
    ensureCRMEventDelegation();
    const display = document.getElementById('display-area');
    if (!display.innerHTML.trim()) {
        display.innerHTML = renderCRMLoading('Memuat data follow-up pasien...');
    }
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
        if (window._activeTabName && window._activeTabName !== 'crm') return;
        display.innerHTML = renderCRMError(error.message || 'Gagal memuat data follow-up pasien.');
        return;
    }
    if (window._activeTabName && window._activeTabName !== 'crm') return;
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
                    <div class="crm-toolbar-left">
                        <select id="crm-segment-filter" data-crm-action="filter">${crmOptions(CRM_SEGMENTS)}</select>
                        <select id="crm-status-filter" data-crm-action="filter">${crmOptions(CRM_STATUSES)}</select>
                        <select id="crm-service-filter" data-crm-action="service-filter">${crmTagOptions('service', 'Semua layanan', CRM_TAG_OPTIONS)}</select>
                        <select id="crm-manual-tag-filter" data-crm-action="manual-tag-filter">${crmTagOptions('manual', 'Semua tag', CRM_TAG_OPTIONS)}</select>
                    </div>
                    <div class="crm-toolbar-center">
                        <div class="crm-search-wrapper">
                            <input id="crm-search-input" type="search" placeholder="Cari nama / no HP..." data-crm-action="search" autocomplete="off">
                            <button type="button" class="crm-search-clear" data-crm-action="clear-search" title="Hapus pencarian" style="display:none;">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                    <div class="crm-toolbar-right">
                        <span class="crm-result-count" id="crm-result-count">${patients?.length || 0} pasien</span>
                        <button type="button" class="crm-refresh-btn" data-crm-action="refresh-list" title="Refresh daftar">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
                <div id="crm-patient-list">${renderCRMPatients(patients)}</div>
            </div>
        </div>
    `;

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
    CRM_PATIENT_CACHE = new Map((patients || []).map(patient => [Number(patient.id), patient]));
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
                    <i class="fas fa-lightbulb crm-recommendation-icon"></i>
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
                <div class="crm-status-flex">
                    <span class="badge ${crmFollowupBadge(patient.followup_status)}">${escapeHtml(followupLabel)}</span>
                    ${dueBadge}
                </div>
                ${patient.follow_up_date ? `<div class="crm-next-date"><i class="far fa-calendar-alt"></i> Follow-up: ${escapeHtml(patient.follow_up_date)}</div>` : ''}
                ${patient.followup_outcome ? `<div class="crm-outcome-note">Hasil: ${escapeHtml(outcomeLabel)}</div>` : ''}
            </div>

            <div class="crm-action-block">
                <div class="crm-inline-actions">
                    <button type="button" class="btn btn-sm btn-outline crm-inline-contacted" data-crm-action="mark-contacted" data-patient-id="${escapeHtml(patient.id)}" title="Tandai sudah dihubungi">
                        <i class="fas fa-check"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-wa crm-inline-wa" data-crm-action="open-whatsapp" data-patient-id="${escapeHtml(patient.id)}" data-patient-phone="${escapeHtml(patient.phone || '')}" data-patient-template="kontrol" title="Kirim WhatsApp">
                        <i class="fab fa-whatsapp"></i>
                    </button>
                </div>
                <button type="button" class="btn btn-primary crm-detail-btn" data-crm-action="open-followup" data-patient-id="${escapeHtml(patient.id)}" data-patient-phone="${escapeHtml(patient.phone || '')}">
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
            <input type="text" id="crm-custom-tags-input" class="crm-custom-tags-input" placeholder="Tambah tag custom, pisahkan dengan koma">
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
        const countEl = document.getElementById('crm-result-count');
        if (countEl) countEl.textContent = `${patients?.length || 0} pasien`;
        const clearBtn = document.querySelector('.crm-search-clear') as HTMLButtonElement;
        if (clearBtn) clearBtn.style.display = search ? 'flex' : 'none';
    } catch (error) {
        if (list) list.innerHTML = renderCRMError(error.message || 'Gagal memuat daftar follow-up pasien.');
    }
}

async function openCRMFollowup(patientId, focusWhatsApp = false, focusVoucher = false) {
    const cachedPatient = CRM_PATIENT_CACHE.get(Number(patientId));
    let patient = cachedPatient || {
        id: patientId,
        name: 'Memuat pasien...',
        recommendation: 'Mengambil data follow-up pasien.',
        tags: [],
        contact_preference: {},
    };
    let history = [];
    let messageLogs = [];
    let vouchers = { special: [], general: [] };
    const overlay = document.createElement('div');
    overlay.className = 'crm-modal-overlay';
    overlay.innerHTML = `
        <div class="crm-modal">
            <div class="crm-modal-header">
                <div>
                    <h3>${escapeHtml(patient.name)}</h3>
                    <p>${escapeHtml(patient.recommendation)}</p>
                </div>
                <button type="button" data-crm-action="close-modal"><i class="fas fa-times"></i></button>
            </div>
            <form id="crm-followup-form" data-crm-form-action="followup">
                <input type="hidden" name="patient_id" value="${patient.id}">
                <div class="crm-followup-form-body">
                    <div class="crm-followup-layout">
<div class="crm-followup-column crm-followup-left-column">
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
                            <div class="crm-collapsible" data-crm-collapsible="meta">
                                <button type="button" class="crm-collapsible-header" data-crm-action="toggle-collapsible">
                                    <i class="fas fa-chevron-down crm-collapsible-icon"></i>
                                    <span>Tag & Izin Kontak</span>
                                </button>
                                <div class="crm-collapsible-content">
                                    ${renderCRMManualTagEditor(patient)}
                                    ${renderCRMContactPreferenceEditor(patient)}
                                    <div class="crm-modal-actions-end">
                                        <button type="button" class="crm-row-btn" data-crm-action="save-meta" data-patient-id="${escapeHtml(patient.id)}">
                                            <i class="fas fa-save"></i> Simpan Tag & Izin
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="crm-followup-column crm-followup-right-column">
                            <div class="crm-collapsible" data-crm-collapsible="history">
                                <button type="button" class="crm-collapsible-header" data-crm-action="toggle-collapsible">
                                    <i class="fas fa-chevron-down crm-collapsible-icon"></i>
                                    <span>Riwayat follow-up</span>
                                </button>
                                <div class="crm-collapsible-content">
                                    <div id="crm-followup-history-list">${renderCRMInlineLoading('Memuat riwayat...')}</div>
                                </div>
                            </div>
                            <div class="crm-collapsible" data-crm-collapsible="voucher">
                                <button type="button" class="crm-collapsible-header" data-crm-action="toggle-collapsible">
                                    <i class="fas fa-chevron-down crm-collapsible-icon"></i>
                                    <span><i class="fas fa-ticket-alt"></i> Voucher Follow-up</span>
                                </button>
                                <div class="crm-collapsible-content">
                                    <div class="crm-voucher-tools" id="crm-voucher-tools">
                                        <div class="crm-voucher-row">
                                            <select id="crm-selected-voucher" data-crm-action="voucher-change">
                                                <option value="">Memuat voucher...</option>
                                            </select>
                                            <label class="crm-lock-override crm-voucher-confirm-wrap" id="crm-general-voucher-confirm-wrap">
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
                                            <button type="button" class="crm-row-btn" data-crm-action="create-voucher" data-patient-id="${escapeHtml(patient.id)}">
                                                <i class="fas fa-plus"></i> Buat Voucher Khusus
                                            </button>
                                        </div>
                                        <span class="crm-subtext">Voucher khusus otomatis hanya berlaku untuk pasien ini.</span>
                                    </div>
                                </div>
                            </div>
                            <div class="crm-collapsible" data-crm-collapsible="whatsapp">
                                <button type="button" class="crm-collapsible-header" data-crm-action="toggle-collapsible">
                                    <i class="fas fa-chevron-down crm-collapsible-icon"></i>
                                    <span><i class="fab fa-whatsapp"></i> Pesan WhatsApp</span>
                                </button>
                                <div class="crm-collapsible-content">
                                    <div class="whatsapp-message-panel">
                                        <div id="crm-whatsapp-lock-warning" class="crm-warning hidden">
                                            <i class="fas fa-exclamation-triangle"></i> Pasien tidak ingin dihubungi (JANGAN DIHUBUNGI).
                                        </div>
                                        <div id="crm-whatsapp-promo-warning" class="crm-warning hidden">
                                            <i class="fas fa-info-circle"></i> Pasien tidak ingin menerima pesan promosi (JANGAN PROMO).
                                        </div>
                                        <div class="whatsapp-template-row">
                                            <select id="crm-message-template" data-crm-action="message-template" data-patient-id="${escapeHtml(patient.id)}">
                                                ${Object.entries(CRM_MESSAGE_TEMPLATES).map(([value, label]) => `
                                                    <option value="${value}">${escapeHtml(label)}</option>
                                                `).join('')}
                                            </select>
                                            <button type="button" class="btn-action" data-crm-action="generate-message" data-patient-id="${escapeHtml(patient.id)}">
                                                <i class="fas fa-magic"></i> Generate
                                            </button>
                                        </div>
                                        <textarea id="crm-generated-message" class="whatsapp-message-textarea" placeholder="Isi pesan akan tampil di sini. Bisa diedit manual."></textarea>
                                        <div class="whatsapp-actions crm-followup-action-row">
                                            <button type="button" class="btn-outline" data-crm-action="copy-message">
                                                <i class="fas fa-copy"></i> Copy Pesan
                                            </button>
                                            <button type="button" class="btn-wa" id="crm-btn-open-wa" data-crm-action="open-whatsapp" data-patient-id="${escapeHtml(patient.id)}">
                                                <i class="fab fa-whatsapp"></i> Kirim via WhatsApp
                                            </button>
                                            <button type="button" class="btn-outline" data-crm-mark-contacted data-crm-action="mark-contacted" data-patient-id="${escapeHtml(patient.id)}">
                                                <i class="fas fa-check"></i> Sudah Dihubungi
                                            </button>
                                        </div>
                                        <span class="crm-subtext">Pesan dibuka di WhatsApp Web browser. Pastikan sudah login di browser.</span>
                                    </div>
                                </div>
                            </div>
                            <div class="crm-collapsible" data-crm-collapsible="log">
                                <button type="button" class="crm-collapsible-header" data-crm-action="toggle-collapsible">
                                    <i class="fas fa-chevron-down crm-collapsible-icon"></i>
                                    <span>Riwayat WhatsApp</span>
                                </button>
                                <div class="crm-collapsible-content">
                                    <div id="crm-message-log-list">${renderCRMInlineLoading('Memuat riwayat WhatsApp...')}</div>
                                </div>
                            </div>
                            <div class="crm-collapsible" data-crm-collapsible="outcome">
                                <button type="button" class="crm-collapsible-header" data-crm-action="toggle-collapsible">
                                    <i class="fas fa-chevron-down crm-collapsible-icon"></i>
                                    <span>Hasil Follow-up</span>
                                </button>
                                <div class="crm-collapsible-content">
                                    <div class="crm-outcome-grid">
                                        <select id="crm-followup-outcome">${crmOptions(CRM_OUTCOMES)}</select>
                                        <input type="date" id="crm-outcome-follow-up-date" value="${escapeHtml(patient.follow_up_date || '')}">
                                    </div>
                                    <textarea id="crm-followup-outcome-note" rows="3" placeholder="Catatan hasil follow-up..." class="crm-outcome-note-textarea"></textarea>
                                    <div class="crm-outcome-actions">
                                        <button type="button" class="crm-row-btn" data-crm-action="save-outcome" data-patient-id="${escapeHtml(patient.id)}">
                                            <i class="fas fa-clipboard-check"></i> Simpan Hasil
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="crm-modal-actions crm-followup-save-row">
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Simpan Follow-up</button>
                </div>
            </form>
        </div>
    `;

    document.body.appendChild(overlay);
    window._currentCRMPatient = patient;
    onCRMVoucherSelectChange();
    generateCRMMessage(patient.id);
    if (focusWhatsApp) {
        setTimeout(() => document.getElementById('crm-generated-message')?.focus(), 80);
    }
    if (focusVoucher) {
        setTimeout(() => document.getElementById('crm-new-voucher-name')?.focus(), 80);
    }

    const detailPromise = cachedPatient
        ? Promise.resolve(cachedPatient)
        : fetchCRMJson(`/crm/patient/${patientId}`);

    Promise.all([
        detailPromise.catch(() => patient),
        fetchCRMJson(`/crm/patient/${patientId}/followups`).catch(() => []),
        fetchCRMJson(`/crm/patient/${patientId}/message-logs`).catch(() => []),
        fetchCRMJson(`/crm/patient/${patientId}/vouchers`).catch(() => ({ special: [], general: [] })),
    ]).then(([freshPatient, freshHistory, freshMessageLogs, freshVouchers]) => {
        patient = freshPatient || patient;
        history = Array.isArray(freshHistory) ? freshHistory : [];
        messageLogs = Array.isArray(freshMessageLogs) ? freshMessageLogs : [];
        vouchers = freshVouchers || { special: [], general: [] };
        CRM_PATIENT_CACHE.set(Number(patientId), patient);
        window._currentCRMPatient = patient;

        const historyList = document.getElementById('crm-followup-history-list');
        const messageLogList = document.getElementById('crm-message-log-list');
        const voucherSelect = document.getElementById('crm-selected-voucher');
        if (historyList) historyList.innerHTML = renderCRMFollowupHistory(history);
        if (messageLogList) messageLogList.innerHTML = renderCRMMessageLogs(messageLogs);
        if (voucherSelect) voucherSelect.innerHTML = renderCRMVoucherOptions(vouchers);
        onCRMVoucherSelectChange();
        generateCRMMessage(patient.id);
    }).catch(() => {
        const historyList = document.getElementById('crm-followup-history-list');
        const messageLogList = document.getElementById('crm-message-log-list');
        const voucherSelect = document.getElementById('crm-selected-voucher');
        if (historyList) historyList.innerHTML = renderCRMErrorMini('Riwayat follow-up gagal dimuat.');
        if (messageLogList) messageLogList.innerHTML = renderCRMErrorMini('Riwayat WhatsApp gagal dimuat.');
        if (voucherSelect) voucherSelect.innerHTML = renderCRMVoucherOptions({ special: [], general: [] });
    });
}

async function openCRMWhatsApp(patientId) {
    try {
        await openCRMFollowup(patientId, true);
    } catch (error) {
        alert(error.message || 'Gagal membuka WhatsApp follow-up.');
    }
}

function renderCRMInlineLoading(message) {
    return `<div class="crm-inline-state"><i class="fas fa-spinner fa-spin"></i><span>${escapeHtml(message)}</span></div>`;
}

function renderCRMErrorMini(message) {
    return `<div class="crm-inline-state error"><i class="fas fa-exclamation-circle"></i><span>${escapeHtml(message)}</span></div>`;
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
    const template = document.getElementById('crm-message-template')?.value || 'kontrol';
    const textarea = document.getElementById('crm-generated-message');
    const btnWa = document.getElementById('crm-btn-open-wa');
    const promoWarning = document.getElementById('crm-whatsapp-promo-warning');
    const lockWarning = document.getElementById('crm-whatsapp-lock-warning');

    const patient = window._currentCRMPatient || {};

    // check permissions based on data tags
    const pref = patient?.contact_preference || {};
    const tags = patient?.tags || [];
    const dontContact = pref.jangan_dihubungi || tags.some(t => t.value === 'jangan-dihubungi');
    const dontPromo = pref.boleh_promo === false || tags.some(t => t.value === 'jangan-promo');
    const phoneInvalid = !patient?.phone || patient.phone.length < 5;

    if (dontContact || phoneInvalid) {
        if (btnWa) btnWa.disabled = true;
    } else {
        if (btnWa) btnWa.disabled = false;
    }

    if (lockWarning) {
        if (dontContact || phoneInvalid) {
            lockWarning.classList.remove('hidden');
            lockWarning.innerHTML = dontContact ? '<i class="fas fa-exclamation-triangle"></i> Pasien menolak dihubungi (JANGAN DIHUBUNGI).' : '<i class="fas fa-exclamation-triangle"></i> Nomor telepon tidak valid / kosong.';
        } else {
            lockWarning.classList.add('hidden');
        }
    }

    if (promoWarning) {
        if (dontPromo && template === 'promo') {
            promoWarning.classList.remove('hidden');
        } else {
            promoWarning.classList.add('hidden');
        }
    }

    if (template === 'custom') {
        if (textarea) {
            textarea.value = textarea.value || '';
        }
        return;
    }

    if (textarea) {
        textarea.value = 'Membuat pesan...';
    }

    try {
        const response = await fetch(`/crm/patient/${patientId}/message?template=${encodeURIComponent(template)}`);
        if (!response.ok) throw new Error('Gagal memuat template pesan');
        const data = await response.json();
        if (textarea) {
            textarea.value = data.message || '';
        }
    } catch (error) {
        console.error('Gagal generate pesan:', error);
        if (textarea) {
            textarea.value = 'Gagal memuat pesan. Silakan coba lagi.';
        }
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

async function openCRMWhatsAppLink(patientId, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const waBtn = document.getElementById('crm-btn-open-wa');
    if (waBtn?.disabled) return;

    // Get the clicked element to read data-patient-phone
    const clickedEl = event?.target as HTMLElement;
    const actionEl = clickedEl?.closest('[data-crm-action="open-whatsapp"]') as HTMLElement;
    const inlinePhone = actionEl?.dataset?.patientPhone || '';
    const inlineTemplate = actionEl?.dataset?.patientTemplate || '';

    const textarea = document.getElementById('crm-generated-message');
    let message = normalizeCRMMessageText(textarea?.value || '');

    const patient = window._currentCRMPatient || {};
    const pref = patient.contact_preference || {};
    const tags = patient.tags || [];
    const dontContact = pref.jangan_dihubungi || tags.some(t => t.value === 'jangan-dihubungi');
    const phone = inlinePhone || patient.phone;

    if (dontContact) {
        alert('Warning: Pasien ini memiliki preferensi JANGAN DIHUBUNGI.');
        return;
    }

    if (!phone || phone.length < 5) {
        alert('Nomor HP tidak valid.');
        return;
    }

    // If no message in textarea and no inline template, fetch from API
    if (!message && inlineTemplate) {
        try {
            const response = await fetch(`/crm/patient/${patientId}/message?template=${encodeURIComponent(inlineTemplate)}`);
            if (response.ok) {
                const data = await response.json();
                message = normalizeCRMMessageText(data.message || '');
            }
        } catch (error) {
            console.error('Gagal memuat template pesan:', error);
        }
    }

    // If still no message, use a default
    if (!message) {
        message = 'Halo, ini admin klinik. Apakah ada yang bisa kami bantu?';
    }

    const digits = String(phone).replace(/\D/g, '');
    const chatId = digits.startsWith('62') ? digits : '62' + digits.replace(/^0/, '');
    const url = `https://wa.me/${chatId}?text=${encodeURIComponent(message)}`;
    window.open(url, '_blank');

    showToast('Membuka obrolan WhatsApp di browser.', 'success');
}

async function readCRMActionPayload(response, fallbackMessage) {
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.toLowerCase().includes('application/json')) {
        return { detail: fallbackMessage };
    }
    try {
        return await response.json();
    } catch (error) {
        return { detail: fallbackMessage };
    }
}

async function markCRMWhatsAppContacted(patientId) {
    const form = document.getElementById('crm-followup-form');
    const followUpDate = form?.querySelector('[name="follow_up_date"]')?.value || '';
    const button = form?.querySelector('[data-crm-mark-contacted]');
    const fallbackMessage = 'Gagal memperbarui status follow-up. Periksa log aplikasi.';
    if (button?.disabled) return;
    if (button) button.disabled = true;
    try {
        const response = await fetch(`/crm/patient/${patientId}/mark-whatsapp-contacted`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ follow_up_date: followUpDate }),
        });
        const data = await readCRMActionPayload(response, fallbackMessage);
        if (!response.ok || data.status !== 'success') {
            alert(data.detail || fallbackMessage);
            return;
        }
        showToast(data.message || 'Status follow-up diperbarui menjadi Sudah Dihubungi.', 'success');
        form?.closest('.crm-modal-overlay')?.remove();
        await renderCRM();
    } catch (error) {
        alert(fallbackMessage);
    } finally {
        if (button && button.isConnected) button.disabled = false;
    }
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

// Global exports
window.renderCRM = renderCRM;
window.loadCRMList = loadCRMList;
window.openCRMFollowup = openCRMFollowup;
window.openCRMWhatsApp = openCRMWhatsApp;
window.onCRMVoucherSelectChange = onCRMVoucherSelectChange;
window.createCRMSpecialVoucher = createCRMSpecialVoucher;
window.saveCRMPatientMeta = saveCRMPatientMeta;
window.saveCRMFollowupOutcome = saveCRMFollowupOutcome;
window.generateCRMMessage = generateCRMMessage;
window.openCRMWhatsAppLink = openCRMWhatsAppLink;
window.markCRMWhatsAppContacted = markCRMWhatsAppContacted;
window.copyCRMMessage = copyCRMMessage;
window.submitCRMFollowup = submitCRMFollowup;
