"use strict";
let helpDelegationReady = false;
function ensureHelpEventDelegation() {
    if (helpDelegationReady)
        return;
    helpDelegationReady = true;
    document.addEventListener('click', async (event) => {
        const actionElement = event.target?.closest('[data-help-action]');
        if (!actionElement)
            return;
        const action = actionElement.dataset.helpAction || '';
        if (!action)
            return;
        event.preventDefault();
        try {
            if (action === 'open-external') {
                const button = actionElement;
                await openDesktopExternalUrl(button.dataset.url || '', 'whatsapp_help');
            }
            if (action === 'open-folder') {
                await openSupportFolder(actionElement.dataset.kind || '');
            }
        }
        catch (error) {
            showToast(sanitizeAppErrorMessage(error, action === 'open-folder' ? 'Gagal membuka folder.' : 'Tautan bantuan tidak dapat dibuka.'), 'error');
        }
    });
}
async function renderHelp() {
    ensureHelpEventDelegation();
    const displayArea = document.getElementById('display-area');
    if (!displayArea)
        return;
    displayArea.innerHTML = `
        <div class="help-page">
            <section class="help-hero">
                <div>
                    <span class="section-kicker">Bantuan</span>
                    <h2>Panduan Cepat Aplikasi</h2>
                    <p>Ringkasan langkah kerja utama untuk operasional klinik harian.</p>
                </div>
                <div id="help-support-card" class="help-support-card">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Memuat info bantuan...</span>
                </div>
            </section>

            <section class="help-grid">
                ${helpGuideCard('Tambah Pasien', [
        'Buka menu Pasien.',
        'Klik Tambah Pasien.',
        'Isi nama, nomor WhatsApp, gender, dan alamat.',
        'Simpan, lalu cek data pasien muncul di tabel.'
    ])}
                ${helpGuideCard('Tambah Kunjungan', [
        'Buka menu Kunjungan atau detail pasien.',
        'Pilih pasien, layanan, terapis, quantity, dan harga.',
        'Tambahkan produk/herbal bila ada transaksi tambahan.',
        'Simpan kunjungan dan cek stok otomatis bila layanan memakai stok.'
    ])}
                ${helpGuideCard('Cetak Invoice', [
        'Buka menu Invoice atau detail kunjungan.',
        'Pilih transaksi kunjungan atau penjualan produk/herbal.',
        'Klik cetak/generate invoice.',
        'Preview PDF, lalu print sesuai kebutuhan.'
    ])}
                ${helpGuideCard('Jual Produk / Herbal', [
        'Buka menu Produk / Herbal.',
        'Klik tombol Jual Herbal.',
        'Pilih produk/herbal yang dibeli pasien.',
        'Isi jumlah penjualan.',
        'Klik Simpan Penjualan.'
    ])}
                ${helpGuideCard('Stok Produk / Herbal', [
        'Buka menu Produk / Herbal.',
        'Tambah produk/herbal atau pilih item yang sudah ada.',
        'Gunakan koreksi/retur stok untuk perbaikan stok.',
        'Isi alasan koreksi agar riwayat tetap jelas.'
    ])}
                ${helpGuideCard('Inventori Alat', [
        'Buka menu Inventory.',
        'Tambah stok alat dari pembelian baru dengan Tambah Stok.',
        'Stok alat layanan otomatis berkurang saat kunjungan disimpan.',
        'Gunakan Koreksi Keluar hanya untuk stok fisik rusak, hilang, stok opname, atau salah input.'
    ])}
                ${helpGuideCard('Follow-up Pasien', [
        'Buka menu Follow-up Pasien.',
        'Cek pasien dengan status perlu follow-up.',
        'Klik WhatsApp untuk membuat pesan.',
        'Catat hasil follow-up setelah pasien membalas atau booking.'
    ])}
                ${helpGuideCard('Laporan Owner', [
        'Buka menu Laporan Owner.',
        'Pilih periode dan sumber pasien baru.',
        'Pantau pendapatan, kunjungan, top layanan, dan pasien prioritas.',
        'Klik Export Excel jika laporan perlu dikirim.'
    ])}
                ${helpGuideCard('Export Excel', [
        'Buka Pengaturan, bagian Ekspor Data.',
        'Pilih jenis data: semua data, pasien, produk/herbal, inventory, atau audit.',
        'Klik Excel atau JSON.',
        'File tersimpan di folder exports aplikasi.'
    ])}
                ${helpGuideCard('Backup & Restore', [
        'Buka Pengaturan, bagian Backup.',
        'Klik buat backup sebelum update atau restore.',
        'Untuk restore, pilih file backup lalu konfirmasi.',
        'Aplikasi membuat backup pengaman sebelum restore.'
    ])}
                ${helpGuideCard('Ubah PIN', [
        'Buka Pengaturan, bagian Keamanan Admin.',
        'Isi PIN lama, PIN baru, dan konfirmasi PIN baru.',
        'Klik Ubah PIN Admin.',
        'Gunakan PIN baru untuk unlock dan aksi sensitif.'
    ])}
            </section>

            <section class="help-info-grid">
                <div class="help-info-panel">
                    <h3><i class="fas fa-headset"></i> Kontak Bantuan</h3>
                    <div id="help-support-detail" class="help-muted">Memuat kontak bantuan...</div>
                </div>
                <div class="help-info-panel">
                    <h3><i class="fas fa-info-circle"></i> Informasi Aplikasi</h3>
                    <div id="help-app-info" class="help-muted">Memuat informasi aplikasi...</div>
                </div>
            </section>
        </div>
    `;
    await loadHelpInfo();
}
function helpGuideCard(title, steps) {
    return `
        <article class="help-guide-card">
            <h3>${escapeHtml(title)}</h3>
            <ol>
                ${steps.map(step => `<li>${escapeHtml(step)}</li>`).join('')}
            </ol>
        </article>
    `;
}
async function loadHelpInfo() {
    try {
        const data = await apiGetJson('/support/app_info');
        renderHelpSupport(data.support || {});
        renderHelpAppInfo(data);
    }
    catch (error) {
        const safe = sanitizeAppErrorMessage(error);
        const supportCard = document.getElementById('help-support-card');
        const supportDetail = document.getElementById('help-support-detail');
        const appInfo = document.getElementById('help-app-info');
        if (supportCard)
            supportCard.innerHTML = `<i class="fas fa-exclamation-circle"></i><span>${escapeHtml(safe)}</span>`;
        if (supportDetail)
            supportDetail.textContent = safe;
        if (appInfo)
            appInfo.textContent = safe;
    }
}
function renderHelpSupport(support) {
    const name = support.support_name || 'Bantuan Lancar Dynamic';
    const whatsapp = String(support.support_whatsapp || '').replace(/\D/g, '');
    const email = support.support_email || '';
    const waUrl = whatsapp ? `https://wa.me/${whatsapp}?text=${encodeURIComponent('Halo, saya butuh bantuan aplikasi Lancar Dynamic Admin.')}` : '';
    const summary = document.getElementById('help-support-card');
    if (summary) {
        summary.innerHTML = `
            <div>
                <strong>${escapeHtml(name)}</strong>
                <span>${whatsapp ? `WA ${escapeHtml(whatsapp)}` : 'Nomor WhatsApp belum diset'}</span>
            </div>
            ${waUrl ? `<button class="help-wa-btn help-external-link" type="button" data-help-action="open-external" data-url="${escapeHtml(waUrl)}"><i class="fab fa-whatsapp"></i> WhatsApp</button>` : `<button class="help-wa-btn disabled" type="button" disabled><i class="fab fa-whatsapp"></i> WhatsApp</button>`}
        `;
    }
    const detail = document.getElementById('help-support-detail');
    if (detail) {
        detail.innerHTML = `
            <div class="help-detail-row"><span>Nama</span><strong>${escapeHtml(name)}</strong></div>
            <div class="help-detail-row"><span>WhatsApp</span><strong>${whatsapp ? escapeHtml(whatsapp) : 'Belum diset'}</strong></div>
            <div class="help-detail-row"><span>Email</span><strong>${email ? escapeHtml(email) : '-'}</strong></div>
            ${waUrl ? `<button class="btn btn-primary help-full-btn help-external-link" type="button" data-help-action="open-external" data-url="${escapeHtml(waUrl)}"><i class="fab fa-whatsapp"></i> Hubungi Bantuan via WhatsApp</button>` : ''}
        `;
    }
}
function renderHelpAppInfo(data) {
    const license = data.license || {};
    const appInfo = document.getElementById('help-app-info');
    if (!appInfo)
        return;
    appInfo.innerHTML = `
        <div class="help-detail-row"><span>Versi</span><strong>${escapeHtml(data.app_version || '-')}</strong></div>
        <div class="help-path-row"><span>Data Klinik</span><code>${escapeHtml(data.database_path || '-')}</code></div>
        <div class="help-path-row"><span>Backup</span><code>${escapeHtml(data.backup_dir || '-')}</code></div>
        <div class="help-path-row"><span>Catatan Bantuan</span><code>${escapeHtml(data.logs_dir || '-')}</code></div>
        <div class="help-path-row"><span>Export</span><code>${escapeHtml(data.exports_dir || '-')}</code></div>
        <div class="help-detail-row"><span>Lisensi</span><strong>${license.valid ? 'Aktif' : (license.status || 'Tidak aktif')}</strong></div>
        <div class="help-folder-actions">
            <button type="button" class="crm-row-btn" data-help-action="open-folder" data-kind="backups"><i class="fas fa-folder-open"></i> Buka Folder Backup</button>
            <button type="button" class="crm-row-btn" data-help-action="open-folder" data-kind="logs"><i class="fas fa-file-alt"></i> Buka Folder Catatan</button>
        </div>
    `;
}
async function openSupportFolder(kind) {
    try {
        const response = await window.LancarApi.openPath(kind);
        if (response.status !== 'success')
            throw new Error(window.LancarApi.getErrorMessage(response, 'Gagal membuka folder.'));
        showToast('Folder dibuka.', 'success');
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal membuka folder.'), 'error');
    }
}
window.renderHelp = renderHelp;
window.openSupportFolder = openSupportFolder;
