"use strict";
window._ownerReportPeriod = window._ownerReportPeriod || 'month';
window._ownerNewPatientSource = window._ownerNewPatientSource || 'first_visit';
async function renderOwnerReport() {
    const displayArea = document.getElementById('display-area');
    const params = new URLSearchParams({
        period: window._ownerReportPeriod || 'month',
        new_patient_source: window._ownerNewPatientSource || 'first_visit',
    });
    const dateFromInput = document.getElementById('owner-date-from');
    const dateToInput = document.getElementById('owner-date-to');
    const dateFrom = dateFromInput?.value || '';
    const dateTo = dateToInput?.value || '';
    if (dateFrom || dateTo) {
        params.set('date_from', dateFrom);
        params.set('date_to', dateTo);
    }
    const response = await fetch(`/owner_report/summary?${params.toString()}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok)
        throw new Error(data.detail || 'Gagal memuat laporan owner.');
    const summary = data.summary || {};
    const period = data.period || {};
    const periodText = `${period.date_from || '-'} sampai ${period.date_to || '-'}`;
    const newPatientSourceText = window._ownerNewPatientSource === 'registration'
        ? 'pasien baru dari tanggal daftar'
        : 'pasien baru dari kunjungan pertama';
    displayArea.innerHTML = `
        <div class="owner-report-page">
            <div class="owner-header-row">
                <div class="owner-header-main">
                    <h2>Performa Klinik</h2>
                    <p class="owner-header-subtitle">
                        <i class="fas fa-calendar-alt"></i> ${escapeHtml(periodText)} &middot; ${escapeHtml(newPatientSourceText)}
                    </p>
                </div>
                <div class="owner-header-badges">
                    <span class="owner-badge-tiny"><strong>${Number(summary.active_patients || 0)}</strong> pasien aktif</span>
                    <span class="owner-badge-tiny"><strong>${Number(summary.total_whatsapp_followups || 0)}</strong> follow-up WA</span>
                    <span class="owner-badge-tiny"><strong>${Number(summary.followup_booked || 0)}</strong> booking follow-up</span>
                </div>
            </div>

            <section class="owner-filter-card">
                <div class="owner-filter-compact-grid">
                    <label>
                        <span>Periode</span>
                        <select id="owner-period-select" onchange="changeOwnerReportPeriod(this.value)">
                            <option value="month" ${window._ownerReportPeriod === 'month' ? 'selected' : ''}>Bulan ini</option>
                            <option value="year" ${window._ownerReportPeriod === 'year' ? 'selected' : ''}>Tahun ini</option>
                        </select>
                    </label>
                    <label>
                        <span>Pasien Baru</span>
                        <select id="owner-new-patient-source" onchange="changeOwnerNewPatientSource(this.value)">
                            <option value="first_visit" ${window._ownerNewPatientSource === 'first_visit' ? 'selected' : ''}>Kunjungan pertama</option>
                            <option value="registration" ${window._ownerNewPatientSource === 'registration' ? 'selected' : ''}>Tanggal daftar</option>
                        </select>
                    </label>
                    <label>
                        <span>Dari</span>
                        <input id="owner-date-from" type="date" value="${escapeHtml(dateFrom)}">
                    </label>
                    <label>
                        <span>Sampai</span>
                        <input id="owner-date-to" type="date" value="${escapeHtml(dateTo)}">
                    </label>
                    <button type="button" class="btn-owner-compact btn-owner-primary" onclick="renderOwnerReport()">
                        <i class="fas fa-filter"></i> Terapkan
                    </button>
                    <button type="button" id="owner-export-excel-btn" class="btn-owner-compact btn-owner-outline" onclick="exportOwnerReportExcel()">
                        <i class="fas fa-file-excel"></i> Export Excel
                    </button>
                </div>
            </section>

            <div class="owner-kpi-grid">
                ${ownerKpiCard('fa-wallet', 'Pendapatan', formatRupiah(summary.total_revenue || 0), `Kunjungan ${formatRupiah(summary.visit_revenue || 0)} &middot; Herbal ${formatRupiah(summary.herbal_revenue || 0)}`, 'is-revenue')}
                ${ownerKpiCard('fa-notes-medical', 'Kunjungan', Number(summary.total_visits || 0), `${Number(summary.unique_patients || 0)} pasien unik`)}
                ${ownerKpiCard('fa-user-plus', 'Pasien Baru', Number(summary.new_patients || 0), `${Number(summary.active_patients || 0)} pasien aktif`)}
                ${ownerKpiCard('fa-hourglass-half', 'Piutang / Pending', formatRupiah(summary.pending_revenue || 0), `Kunjungan ${formatRupiah(summary.pending_visit_revenue || 0)} &middot; Herbal ${formatRupiah(summary.pending_herbal_revenue || 0)}`)}
                ${ownerKpiCard('fa-phone-volume', 'Perlu Follow-up', Number(summary.patients_need_followup || 0), `${Number(summary.dormant_patients || 0)} lama tidak datang`)}
            </div>

            <div class="owner-report-grid">
                ${ownerReportPanel('Kategori Layanan', renderOwnerCategoryRows(data.top_service_categories || []), 'Kategori layanan dengan kontribusi revenue tertinggi.')}
                ${ownerReportPanel('Top Layanan', renderOwnerServiceRows(data.top_services || []), 'Layanan dengan kunjungan terbanyak.')}
                ${ownerReportPanel('Top Produk / Herbal', renderOwnerHerbalRows(data.top_herbals || []), 'Produk / herbal dengan penjualan tertinggi.')}
                ${ownerReportPanel('Pasien Loyal', renderOwnerPatientRows(data.top_loyal_patients || []), 'Pasien dengan kunjungan dan transaksi tertinggi.')}
                ${ownerReportPanel('Perlu Follow-up', renderOwnerFollowupRows(data.patients_need_followup || []), 'Prioritas dari segmentasi CRM.')}
            </div>
        </div>
    `;
}
function ownerKpiCard(icon, label, value, hint, extraClass = '') {
    return `
        <div class="owner-kpi-card ${extraClass}" title="${escapeHtml(String(value))}">
            <div class="owner-kpi-icon"><i class="fas ${icon}"></i></div>
            <div class="owner-kpi-details">
                <span class="owner-kpi-label">${escapeHtml(label)}</span>
                <strong class="owner-kpi-value">${escapeHtml(String(value))}</strong>
                <small class="owner-kpi-hint">${hint || ''}</small>
            </div>
        </div>
    `;
}
function ownerReportPanel(title, body, note) {
    return `
        <section class="owner-list-card">
            <div class="owner-list-header">
                <h3>${escapeHtml(title)}</h3>
                <p>${escapeHtml(note || '')}</p>
            </div>
            <div class="owner-list-body">
                ${body}
            </div>
        </section>
    `;
}
function renderOwnerEmptyRow(message) {
    return `
        <div class="owner-empty-state">
            <i class="fas fa-folder-open"></i>
            <p>${escapeHtml(message || 'Belum ada data.')}</p>
        </div>
    `;
}
function renderOwnerCategoryRows(rows) {
    if (!rows.length)
        return renderOwnerEmptyRow('Belum ada kategori layanan pada periode ini.');
    return rows.map(row => `
        <div class="owner-list-item">
            <div class="owner-item-info">
                <span class="owner-item-name">${escapeHtml(ownerCategoryLabel(row.name || row.category || 'uncategorized'))}</span>
                <span class="owner-item-sub">${Number(row.visits || 0)} kunjungan</span>
            </div>
            <span class="owner-item-value">${formatRupiah(row.revenue || 0)}</span>
        </div>
    `).join('');
}
function ownerCategoryLabel(value) {
    const normalized = String(value || '').trim().toLowerCase();
    const map = {
        therapy: 'Terapi',
        consultation: 'Konsultasi',
        package: 'Paket',
        product: 'Produk',
        other: 'Lainnya',
        uncategorized: 'Tanpa Kategori',
    };
    return map[normalized] || normalized.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase()) || 'Tanpa Kategori';
}
function renderOwnerServiceRows(rows) {
    if (!rows.length)
        return renderOwnerEmptyRow('Belum ada layanan pada periode ini.');
    return rows.map(row => `
        <div class="owner-list-item">
            <div class="owner-item-info">
                <span class="owner-item-name">${escapeHtml(row.name || 'Layanan')}</span>
                <span class="owner-item-sub">${Number(row.visits || 0)} kunjungan</span>
            </div>
            <span class="owner-item-value">${formatRupiah(row.revenue || 0)}</span>
        </div>
    `).join('');
}
function renderOwnerHerbalRows(rows) {
    if (!rows.length)
        return renderOwnerEmptyRow('Belum ada penjualan produk/herbal pada periode ini.');
    return rows.map(row => `
        <div class="owner-list-item">
            <div class="owner-item-info">
                <span class="owner-item-name">${escapeHtml(row.name || 'Produk / Herbal')}</span>
                <span class="owner-item-sub">${Number(row.quantity || 0)} terjual</span>
            </div>
            <span class="owner-item-value">${formatRupiah(row.revenue || 0)}</span>
        </div>
    `).join('');
}
function renderOwnerPatientRows(rows) {
    if (!rows.length)
        return renderOwnerEmptyRow('Belum ada pasien loyal.');
    return rows.map(row => `
        <div class="owner-list-item">
            <div class="owner-item-info">
                <span class="owner-item-name">${escapeHtml(row.name || 'Pasien')}</span>
                <span class="owner-item-sub">${Number(row.visits || 0)} kunjungan &middot; terakhir ${escapeHtml(row.last_visit || '-')}</span>
            </div>
            <span class="owner-item-value">${formatRupiah(row.revenue || 0)}</span>
        </div>
    `).join('');
}
function renderOwnerFollowupRows(rows) {
    if (!rows.length)
        return renderOwnerEmptyRow('Tidak ada prioritas follow-up.');
    return rows.slice(0, 6).map(row => `
        <div class="owner-list-item owner-followup-item">
            <div class="owner-item-info">
                <span class="owner-item-name">${escapeHtml(row.name || 'Pasien')}</span>
                <span class="owner-item-sub">${escapeHtml(row.segment_label || row.segment || 'Perlu follow-up')}</span>
                <span class="owner-item-sub">${Number(row.days_since_last_visit || 0)} hari tidak datang</span>
            </div>
            <button type="button" class="owner-detail-btn" onclick="openCRMFollowup(${Number(row.id || 0)})">
                <i class="fas fa-pen"></i> Detail
            </button>
        </div>
    `).join('');
}
function changeOwnerReportPeriod(value) {
    window._ownerReportPeriod = value || 'month';
    const from = document.getElementById('owner-date-from');
    const to = document.getElementById('owner-date-to');
    if (from)
        from.value = '';
    if (to)
        to.value = '';
    renderOwnerReport();
}
function changeOwnerNewPatientSource(value) {
    window._ownerNewPatientSource = value || 'first_visit';
    renderOwnerReport();
}
async function exportOwnerReportExcel() {
    const button = document.getElementById('owner-export-excel-btn');
    const original = button ? button.innerHTML : '';
    const params = new URLSearchParams({
        report_type: 'owner_summary',
        period: window._ownerReportPeriod || 'month',
        new_patient_source: window._ownerNewPatientSource || 'first_visit',
    });
    const dateFromInput = document.getElementById('owner-date-from');
    const dateToInput = document.getElementById('owner-date-to');
    const dateFrom = dateFromInput?.value || '';
    const dateTo = dateToInput?.value || '';
    if (dateFrom || dateTo) {
        params.set('date_from', dateFrom);
        params.set('date_to', dateTo);
    }
    try {
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Export...';
        }
        const downloadUrl = `/reports/export_excel?${params.toString()}`;
        const response = await fetch(downloadUrl);
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Gagal export Excel.');
        }
        const disposition = response.headers.get('content-disposition') || '';
        const filenameMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i);
        const filename = filenameMatch ? decodeURIComponent(filenameMatch[1]) : 'laporan_owner.xlsx';
        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = objectUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
        showToast('Laporan Excel berhasil dibuat.', 'success');
    }
    catch (error) {
        const message = error instanceof Error ? error.message : error;
        showToast(sanitizeAppErrorMessage(message, 'Gagal export Excel.'), 'error');
    }
    finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = original;
        }
    }
}
window.renderOwnerReport = renderOwnerReport;
window.changeOwnerReportPeriod = changeOwnerReportPeriod;
window.changeOwnerNewPatientSource = changeOwnerNewPatientSource;
window.exportOwnerReportExcel = exportOwnerReportExcel;
