"use strict";
// ─── INVOICES ─────────────────────────────────────────────────────────────────
let invoiceDelegationReady = false;
function invoiceDataValue(value) {
    return escapeHtml(String(value || '').replace(/\\/g, '/'));
}
function ensureInvoiceEventDelegation() {
    if (invoiceDelegationReady)
        return;
    invoiceDelegationReady = true;
    document.addEventListener('input', (event) => {
        const target = event.target;
        if (target?.dataset?.action === 'invoice-search') {
            onInvoiceSearchInput(target.value);
        }
    });
    document.addEventListener('click', (event) => {
        const button = event.target?.closest('[data-invoice-action]');
        if (!button)
            return;
        const action = button.dataset.invoiceAction || '';
        if (!action)
            return;
        event.preventDefault();
        const sourceId = button.dataset.sourceId || '';
        const amount = Number(button.dataset.amount || 0);
        const method = button.dataset.paymentMethod || 'cash';
        const path = button.dataset.path || '';
        const url = button.dataset.url || '';
        const reference = button.dataset.reference || '';
        const invoiceType = button.dataset.invoiceType || '';
        const status = button.dataset.status || '';
        switch (action) {
            case 'close-modal':
                closeModal();
                break;
            case 'submit-void':
                if (invoiceType === 'visit' || invoiceType === 'herbal') {
                    submitVoidInvoice(invoiceType, sourceId);
                }
                break;
            case 'submit-manual-payment':
                submitManualInvoicePayment(sourceId, status, amount);
                break;
            case 'open-payment-url':
                openGatewayPaymentUrl(url);
                break;
            case 'check-gateway-status':
                checkGatewayStatus(reference);
                break;
            case 'create-gateway-payment':
                createGatewayPayment(sourceId, amount, method, button);
                break;
            case 'manual-payment':
                manualInvoicePayment(sourceId, status, amount, method);
                break;
            case 'open-invoice':
                openInvoice(path);
                break;
            case 'reveal-invoice':
                revealInvoice(path);
                break;
            case 'print-invoice':
                printInvoice(path, button.dataset.printSource || 'invoice');
                break;
            case 'generate-herbal':
                generateInvoiceForHerbal(sourceId);
                break;
            case 'generate-visit':
                generateInvoiceForVisit(Number(sourceId));
                break;
            case 'void-invoice':
                if (invoiceType === 'visit' || invoiceType === 'herbal') {
                    voidInvoice(invoiceType, sourceId);
                }
                break;
            case 'period':
                window._invoicesPeriod = button.dataset.period || 'all';
                window._invoicesPage = 1;
                loadTab('invoices');
                break;
            case 'page-prev':
                window._invoicesPage = Math.max(1, (window._invoicesPage || 1) - 1);
                loadTab('invoices');
                break;
            case 'page-next':
                window._invoicesPage = (window._invoicesPage || 1) + 1;
                loadTab('invoices');
                break;
        }
    });
}
async function openInvoice(path) {
    try {
        const data = await window.LancarApi.openInvoiceFile(path, 'open');
        if (data.status && data.status.toLowerCase() !== 'success') {
            showToast('Gagal membuka file: ' + window.LancarApi.getErrorMessage(data, 'File tidak ditemukan'), 'error');
        }
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Koneksi gagal saat mencoba membuka file invoice PDF.'), 'error');
    }
}
async function revealInvoice(path) {
    try {
        const data = await window.LancarApi.openInvoiceFile(path, 'reveal');
        if (data.status && data.status.toLowerCase() !== 'revealed') {
            showToast('Gagal membuka lokasi file: ' + window.LancarApi.getErrorMessage(data, 'File tidak ditemukan'), 'error');
        }
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Lokasi invoice PDF tidak dapat dibuka.'), 'error');
    }
}
async function printInvoice(path, source = 'invoice') {
    try {
        const data = await window.LancarApi.printFile(path, source);
        const status = String(data.status || '').toLowerCase();
        if (status === 'printed' || status === 'success') {
            showToast(data.message || 'Memulai proses cetak ke printer default...', 'success');
            return;
        }
        if (status === 'open_fallback') {
            showToast(data.message || 'Print langsung tidak tersedia. File dibuka di viewer.', 'info');
            return;
        }
        showToast('Gagal mencetak: ' + window.LancarApi.getErrorMessage(data, 'File tidak ditemukan'), 'error');
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Koneksi gagal saat mencoba mencetak file invoice PDF.'), 'error');
    }
}
function generateInvoiceForVisit(visitId) {
    showToast("Sedang mengekspor PDF...", "info");
    const formData = new FormData();
    formData.append("visit_id", String(visitId));
    fetch('/generate_invoice', {
        method: 'POST',
        body: formData
    })
        .then(res => {
        // Tangkap HTTP error (4xx, 5xx) sebelum parsing JSON
        if (!res.ok) {
            return res.json().then(err => {
                throw new Error(err.detail || 'Invoice belum bisa dibuat.');
            }).catch(() => {
                throw new Error('Invoice belum bisa dibuat. Coba lagi beberapa saat.');
            });
        }
        return res.json();
    })
        .then(data => {
        if (data.status === "success") {
            showToast(data.message || "Invoice PDF berhasil dibuat!", "success");
            // Reload the invoices tab to show the new buttons
            window._invoicesPage = 1;
            loadTab('invoices');
        }
        else {
            showToast("Gagal membuat invoice: " + (data.detail || "Terjadi kesalahan saat membuat invoice."), "error");
        }
    })
        .catch(err => showToast("Gagal membuat invoice: " + sanitizeAppErrorMessage(err, "Gagal membuat invoice."), "error"));
}
function generateInvoiceForHerbal(identifier) {
    showToast("Sedang mengekspor PDF herbal...", "info");
    const formData = new FormData();
    const idText = String(identifier || '');
    if (idText.startsWith('group:')) {
        formData.append("sale_group_id", idText.slice(6));
    }
    else {
        formData.append("transaction_id", idText);
    }
    fetch('/generate_herbal_invoice', {
        method: 'POST',
        body: formData
    })
        .then(res => {
        if (!res.ok) {
            return res.json().then(err => {
                throw new Error(err.detail || 'Invoice herbal belum bisa dibuat.');
            }).catch(() => {
                throw new Error('Invoice herbal belum bisa dibuat. Coba lagi beberapa saat.');
            });
        }
        return res.json();
    })
        .then(data => {
        if (data.status === "success") {
            showToast(data.message || "Invoice herbal PDF berhasil dibuat!", "success");
            window._invoicesPage = 1;
            loadTab('invoices');
        }
        else {
            showToast("Gagal membuat invoice herbal: " + (data.detail || "Terjadi kesalahan saat membuat invoice herbal."), "error");
        }
    })
        .catch(err => showToast("Gagal membuat invoice herbal: " + sanitizeAppErrorMessage(err, "Gagal membuat invoice herbal."), "error"));
}
function _paymentProviderLabel(provider) {
    const labels = {
        gateway_mock: 'Pembayaran Internal',
        midtrans: 'Midtrans',
        manual: 'Manual'
    };
    return labels[String(provider || 'manual').toLowerCase()] || 'Provider Tidak Didukung';
}
function _isSupportedGatewayProvider(provider) {
    return ['gateway_mock', 'midtrans'].includes(String(provider || '').toLowerCase());
}
function _paymentProviderBadgeStyle(provider) {
    const normalized = String(provider || 'manual').toLowerCase();
    if (normalized === 'midtrans')
        return { bg: 'var(--color-info-100)', color: 'var(--color-info-700)' };
    if (normalized === 'gateway_mock')
        return { bg: 'var(--color-success-100)', color: 'var(--color-success-700)' };
    if (normalized === 'manual')
        return { bg: 'var(--color-surface-100)', color: 'var(--color-surface-600)' };
    return { bg: 'var(--color-danger-100)', color: 'var(--color-danger-700)' };
}
function _paymentStatusLabel(status) {
    const normalized = String(status || '').toLowerCase();
    const labels = {
        paid: 'Lunas',
        unpaid: 'Belum Bayar',
        partial: 'Sebagian',
        pending: 'Menunggu',
        expired: 'Kedaluwarsa',
        failed: 'Gagal'
    };
    return labels[normalized] || String(status || '-');
}
function _paymentMethodLabel(method) {
    const normalized = String(method || '').toLowerCase();
    const labels = {
        cash: 'Tunai',
        qris: 'QRIS',
        transfer: 'Transfer',
        debit: 'Debit',
        ewallet: 'E-Wallet',
        virtual_account: 'Virtual Account',
        credit_card: 'Kartu Kredit',
        other: 'Lainnya',
        free: 'Gratis'
    };
    return labels[normalized] || String(method || '-');
}
function _gatewaySourceFromInvoiceId(invoiceId) {
    const strId = String(invoiceId || '');
    if (strId.startsWith('v_'))
        return { source_type: 'visit', source_id: strId.slice(2) };
    if (strId.startsWith('hg_'))
        return { source_type: 'herbal', source_id: 'group:' + strId.slice(3) };
    if (strId.startsWith('h_'))
        return { source_type: 'herbal', source_id: strId.slice(2) };
    return null;
}
function _canUseGateway(method) {
    return ['qris', 'ewallet', 'virtual_account', 'credit_card'].includes(String(method || '').toLowerCase());
}
function _absolutePaymentUrl(paymentUrl) {
    const url = String(paymentUrl || '').trim();
    if (!url)
        return '';
    try {
        return new URL(url, window.location.origin).href;
    }
    catch (e) {
        return url;
    }
}
async function createGatewayPayment(invoiceId, amount, method, button) {
    const source = _gatewaySourceFromInvoiceId(invoiceId);
    if (!source) {
        showToast('Sumber transaksi tidak valid.', 'error');
        return;
    }
    const actionButton = button || null;
    const originalHtml = actionButton ? actionButton.innerHTML : '';
    const form = new FormData();
    form.append('source_type', source.source_type);
    form.append('source_id', source.source_id);
    form.append('amount', String(Math.round(Number(amount || 0))));
    form.append('payment_method', method);
    try {
        if (actionButton) {
            actionButton.disabled = true;
            actionButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Membuat...</span>';
        }
        showToast('Membuat link pembayaran...', 'info');
        const response = await fetch('/payments/gateway/create', { method: 'POST', body: form });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') {
            throw new Error(String(data.detail || 'Gagal membuat link pembayaran.'));
        }
        const providerLabel = _paymentProviderLabel(data.payment?.payment_provider || 'manual');
        const paymentUrl = _absolutePaymentUrl(data.payment?.payment_url || '');
        const isInternalPayment = String(data.payment?.payment_provider || '').toLowerCase() === 'gateway_mock';
        if (paymentUrl && !isInternalPayment) {
            await openDesktopExternalUrl(paymentUrl, 'payment');
        }
        showToast(isInternalPayment
            ? `${providerLabel} berhasil dibuat. Status menunggu pembayaran.`
            : `Link pembayaran ${providerLabel} berhasil dibuat.`, 'success');
        window._invoicesPage = 1;
        loadTab('invoices');
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal membuat link pembayaran.'), 'error');
    }
    finally {
        if (actionButton) {
            actionButton.disabled = false;
            actionButton.innerHTML = originalHtml;
        }
    }
}
async function openGatewayPaymentUrl(paymentUrl) {
    const url = _absolutePaymentUrl(paymentUrl);
    if (!url) {
        showToast('Link pembayaran belum tersedia.', 'warning');
        return;
    }
    try {
        await openDesktopExternalUrl(url, 'payment');
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Link pembayaran tidak diizinkan.'), 'error');
    }
}
async function checkGatewayStatus(paymentReference) {
    const reference = String(paymentReference || '').trim();
    if (!reference) {
        showToast('Referensi pembayaran belum tersedia.', 'warning');
        return;
    }
    try {
        const response = await fetch('/payments/gateway/status/' + encodeURIComponent(reference));
        const data = await response.json();
        if (!response.ok || data.status !== 'success') {
            throw new Error(data.detail || 'Gagal mengecek status pembayaran.');
        }
        const payment = data.payment || {};
        showToast(`Status pembayaran: ${(payment.payment_status || '-').toUpperCase()}`, 'info');
        loadTab('invoices');
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal mengecek status pembayaran.'), 'error');
    }
}
async function voidInvoice(type, identifier) {
    const idText = String(identifier || '');
    const html = `
        <div class="invoice-modal-text">
            Invoice akan ditandai VOID. Ini tidak otomatis mengubah stok atau membuat retur.
        </div>
        <div class="form-group">
            <label for="void-invoice-reason">Alasan Pembatalan</label>
            <textarea id="void-invoice-reason" rows="4" minlength="5" required placeholder="Contoh: Invoice salah cetak / transaksi dibatalkan"></textarea>
        </div>
        <div class="invoice-modal-actions">
            <button type="button" class="btn btn-secondary" data-invoice-action="close-modal">Batal</button>
            <button type="button" class="btn btn-danger" data-invoice-action="submit-void" data-invoice-type="${type}" data-source-id="${escapeHtml(idText)}">
                <i class="fas fa-ban" aria-hidden="true"></i> Void Invoice
            </button>
        </div>
    `;
    openModal('Void / Cancel Invoice', html);
}
async function submitVoidInvoice(type, identifier) {
    const reasonInput = /** @type {HTMLTextAreaElement | null} */ (document.getElementById('void-invoice-reason'));
    const reason = reasonInput?.value.trim() || '';
    if (reason.length < 5) {
        showToast('Alasan pembatalan wajib diisi minimal 5 karakter.', 'warning');
        return;
    }
    const ok = await showConfirm('Batalkan invoice ini? Status akan berubah menjadi VOID.', 'warning', {
        confirmText: 'Ya, Void',
        cancelText: 'Batal',
        maxWidth: '420px'
    });
    if (!ok)
        return;
    const form = new FormData();
    form.append('invoice_type', type);
    form.append('reason', reason);
    if (type === 'visit') {
        form.append('visit_id', String(identifier));
    }
    else if (String(identifier).startsWith('group:')) {
        form.append('sale_group_id', String(identifier).slice(6));
    }
    else {
        form.append('transaction_id', String(identifier));
    }
    try {
        const response = await fetch('/void_invoice', { method: 'POST', body: form });
        const data = await response.json();
        if (!response.ok || data.status !== 'success') {
            throw new Error(data.detail || data.message || 'Gagal membatalkan invoice.');
        }
        closeModal();
        showToast(data.message, 'success');
        window._invoicesPage = 1;
        loadTab('invoices');
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal membatalkan invoice.'), 'error');
    }
}
function _invoiceUpdateTarget(invoiceId) {
    const source = _gatewaySourceFromInvoiceId(invoiceId);
    if (!source)
        return null;
    if (source.source_type === 'visit') {
        return { invoice_type: 'visit', visit_id: source.source_id };
    }
    if (String(source.source_id || '').startsWith('group:')) {
        return { invoice_type: 'herbal', sale_group_id: String(source.source_id).slice(6) };
    }
    return { invoice_type: 'herbal', transaction_id: source.source_id };
}
function manualInvoicePayment(invoiceId, status, amount, currentMethod = 'cash') {
    const target = _invoiceUpdateTarget(invoiceId);
    if (!target) {
        showToast('Sumber transaksi tidak valid.', 'error');
        return;
    }
    const isPartial = status === 'partial';
    const safeMethod = ['cash', 'qris', 'transfer', 'ewallet'].includes(String(currentMethod || '').toLowerCase())
        ? String(currentMethod).toLowerCase()
        : 'cash';
    const html = `
        <div class="invoice-modal-text">
            ${isPartial ? 'Catat pembayaran sebagian manual.' : 'Tandai transaksi sebagai lunas manual.'}
        </div>
        <div class="form-group">
            <label for="manual-payment-method">Metode Pembayaran</label>
            <select id="manual-payment-method">
                <option value="cash" ${safeMethod === 'cash' ? 'selected' : ''}>Tunai</option>
                <option value="qris" ${safeMethod === 'qris' ? 'selected' : ''}>QRIS Manual</option>
                <option value="transfer" ${safeMethod === 'transfer' ? 'selected' : ''}>Transfer</option>
                <option value="ewallet" ${safeMethod === 'ewallet' ? 'selected' : ''}>E-Wallet</option>
            </select>
        </div>
        ${isPartial ? `
            <div class="form-group">
                <label for="manual-payment-amount">Jumlah DP</label>
                <input type="number" id="manual-payment-amount" min="1" max="${Math.max(0, Math.round(Number(amount || 0) - 1))}" placeholder="Masukkan jumlah bayar">
                <small class="form-helper">Total tagihan: ${formatRupiah(amount)}</small>
            </div>
        ` : `<input type="hidden" id="manual-payment-amount" value="${Math.round(Number(amount || 0))}">`}
        <div class="invoice-modal-actions">
            <button type="button" class="btn btn-secondary" data-invoice-action="close-modal">Batal</button>
            <button type="button" class="btn btn-primary" data-invoice-action="submit-manual-payment" data-source-id="${escapeHtml(String(invoiceId || ''))}" data-status="${status}" data-amount="${Number(amount || 0)}">
                <i class="fas fa-check-circle" aria-hidden="true"></i> ${isPartial ? 'Simpan DP' : 'Tandai Lunas'}
            </button>
        </div>
    `;
    openModal(isPartial ? 'Catat DP Manual' : 'Tandai Lunas Manual', html);
}
async function submitManualInvoicePayment(invoiceId, status, totalAmount) {
    const target = _invoiceUpdateTarget(invoiceId);
    const methodInput = /** @type {HTMLSelectElement | null} */ (document.getElementById('manual-payment-method'));
    const amountInput = /** @type {HTMLInputElement | null} */ (document.getElementById('manual-payment-amount'));
    const method = methodInput?.value || 'cash';
    const amount = status === 'partial' ? Number(amountInput?.value || 0) : Number(totalAmount || 0);
    if (!target) {
        showToast('Sumber transaksi tidak valid.', 'error');
        return;
    }
    if (status === 'partial' && (!(amount > 0) || amount >= Number(totalAmount || 0))) {
        showToast('Jumlah DP wajib lebih dari Rp0 dan lebih kecil dari total tagihan.', 'warning');
        return;
    }
    const form = new FormData();
    form.append('invoice_type', target.invoice_type);
    if (target.visit_id)
        form.append('visit_id', String(target.visit_id));
    if (target.transaction_id)
        form.append('transaction_id', String(target.transaction_id));
    if (target.sale_group_id)
        form.append('sale_group_id', String(target.sale_group_id));
    form.append('payment_status', status);
    form.append('payment_method', method);
    form.append('amount_paid', String(Math.round(amount)));
    try {
        const response = await fetch('/update_invoice_payment', { method: 'POST', body: form });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') {
            throw new Error(String(data.detail || 'Gagal memperbarui status pembayaran.'));
        }
        closeModal();
        const shouldRefreshPdf = await showConfirm(`${data.message || 'Status pembayaran berhasil diperbarui.'}\n\nPDF invoice adalah snapshot. Update PDF sekarang agar status pembayaran di PDF ikut terbaru?`, 'info', {
            confirmText: 'Update PDF Sekarang',
            cancelText: 'Nanti',
            maxWidth: '460px'
        });
        if (shouldRefreshPdf) {
            const target = _invoiceUpdateTarget(invoiceId);
            if (target?.invoice_type === 'visit' && target.visit_id) {
                generateInvoiceForVisit(target.visit_id);
                return;
            }
            if (target?.invoice_type === 'herbal') {
                generateInvoiceForHerbal(target.sale_group_id ? `group:${target.sale_group_id}` : target.transaction_id);
                return;
            }
        }
        showToast(data.message || 'Status pembayaran berhasil diperbarui.', 'success');
        window._invoicesPage = 1;
        loadTab('invoices');
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal memperbarui status pembayaran.'), 'error');
    }
}
function renderInvoices(data) {
    ensureInvoiceEventDelegation();
    window._invoicesPage = window._invoicesPage || 1;
    const totalIncome = data.reduce((s, i) => s + ((i.invoice_status === 'void') ? 0 : (i.price || 0)), 0);
    const totalHerbal = data.filter(i => String(i.id).startsWith('h')).length;
    const totalVisits = data.length - totalHerbal;
    const activePeriod = window._invoicesPeriod || 'all';
    const periodMap = {
        '7d': '7 Hari',
        '30d': '30 Hari',
        '6m': '6 Bulan',
        '1y': '1 Tahun',
        'all': 'Semua'
    };
    const periodTitle = periodMap[activePeriod] || 'Semua';
    let html = `
        <!-- Summary bar -->
        <div class="invoice-stats-grid">
            <div class="stat-card total">
                <div class="stat-icon blue"><i class="fas fa-file-invoice"></i></div>
                <div class="stat-details"><h4>Total Transaksi</h4><h2>${data.length}</h2></div>
            </div>
            <div class="stat-card visits">
                <div class="stat-icon purple"><i class="fas fa-stethoscope"></i></div>
                <div class="stat-details"><h4>Kunjungan</h4><h2>${totalVisits}</h2></div>
            </div>
            <div class="stat-card herbal">
                <div class="stat-icon green"><i class="fas fa-leaf"></i></div>
                <div class="stat-details"><h4>Herbal</h4><h2>${totalHerbal}</h2></div>
            </div>
            <div class="stat-card income">
                <div class="stat-icon green"><i class="fas fa-money-bill-wave"></i></div>
                <div class="stat-details">
                    <h4>Total Pemasukan</h4>
                    <h2>${formatRupiah(totalIncome)}</h2>
                </div>
            </div>
        </div>

        <div class="card invoice-card-wrapper">
            <div class="invoice-header">
                <div class="invoice-header-title">
                    <h3><i class="fas fa-file-invoice-dollar" aria-hidden="true"></i> Semua Transaksi (Kunjungan & Herbal)</h3>
                    <span class="invoice-header-meta">Periode aktif: ${periodTitle}. Halaman ${window._invoicesPage}. Menampilkan maksimal 100 transaksi.</span>
                </div>
                
                <!-- Period Filter Pills -->
                <div class="invoice-controls">
                <input type="search" id="invoice-search-input" value="${escapeHtml(window._invoicesSearch || '')}" placeholder="Cari transaksi..."
                       data-action="invoice-search"
                       aria-label="Cari transaksi"
                       class="invoice-search-input">
                <div class="invoice-period-filter" role="group" aria-label="Filter periode transaksi">
                    ${Object.entries(periodMap).map(([k, v]) => `
                        <button type="button" data-invoice-action="period" data-period="${escapeHtml(k)}"
                                aria-pressed="${(window._invoicesPeriod || 'all') === k ? 'true' : 'false'}"
                                class="${(window._invoicesPeriod || 'all') === k ? 'active' : ''}">
                            ${v}
                        </button>
                    `).join('')}
                </div>
                </div>
            </div>`;
    if (data.length === 0) {
        html += `
            <div class="invoice-empty-state">
                <i class="fas fa-history"></i>
                <p>Belum ada Data Transaksi.</p>
                <small>Data transaksi kunjungan pasien dan penjualan produk/herbal akan otomatis muncul di sini.</small>
            </div>`;
    }
    else {
        html += `<div class="table-container"><table class="invoice-table"><thead><tr>
            <th style="width:190px;">Tanggal</th>
            <th>Klien</th>
            <th style="text-align:right; width:160px;">Nilai Tagihan</th>
            <th style="text-align:center; width:250px;">Aksi</th>
        </tr></thead><tbody>`;
        data.forEach((i, idx) => {
            // Konversi backslash Windows ke forward slash agar aman di-embed dalam JS string HTML onclick.
            // Backslash di dalam string JS inline akan diinterpretasikan sebagai escape sequences (\U, \H dll)
            // sehingga seluruh path rusak. Server-side _resolve_invoice_path sudah handle forward slash.
            const rawPath = (i.path || '').replace(/\\/g, '/');
            const safePath = invoiceDataValue(rawPath);
            const strId = String(i.id);
            const isHerbal = strId.startsWith('h_') || strId.startsWith('hg_');
            const isVisit = strId.startsWith('v_');
            const numId = strId.replace('v_', '').replace('h_', '').replace('hg_', '');
            const isVoid = i.invoice_status === 'void';
            const pdfStatus = String(i.pdf_status || '').toLowerCase();
            const hasInvoicePath = !!i.path && pdfStatus !== 'not_generated';
            const fileExists = i.file_exists !== false && pdfStatus !== 'missing';
            const isMissingFile = pdfStatus === 'missing' || (hasInvoicePath && !fileExists);
            const isStalePdf = pdfStatus === 'stale';
            const provider = String(i.payment_provider || 'manual').toLowerCase();
            const paymentMethod = i.payment_method || 'cash';
            const paymentStatus = String(i.payment_status || 'paid').toLowerCase();
            const canUseGateway = _canUseGateway(paymentMethod);
            const isInternalGateway = provider === 'gateway_mock';
            const hasPaymentUrl = !!i.payment_url && !isInternalGateway;
            const hasSupportedGatewayProvider = _isSupportedGatewayProvider(provider);
            const voidTitle = isVoid ? `Void: ${escapeHtml(i.void_reason || '-')}` : 'Void Invoice';
            const voidTarget = isHerbal ? (strId.startsWith('hg_') ? 'group:' + numId : numId) : numId;
            const missingFileNotice = isMissingFile
                ? `<span class="invoice-missing-file-badge" title="Path invoice tersimpan, tapi file PDF tidak ditemukan di folder invoice.">
                    <i class="fas fa-exclamation-triangle"></i> File hilang
                </span>`
                : '';
            const stalePdfNotice = isStalePdf
                ? `<span class="invoice-missing-file-badge" title="Status pembayaran berubah setelah PDF dibuat.">
                    <i class="fas fa-sync-alt"></i> PDF perlu update
                </span>`
                : '';
            const providerBadgeStyle = _paymentProviderBadgeStyle(provider);
            const providerBadge = `<span class="invoice-provider-badge" title="Provider Pembayaran" style="background:${providerBadgeStyle.bg};color:${providerBadgeStyle.color};">${_paymentProviderLabel(provider)}</span>`;
            const statusBadgeClass = isVoid
                ? 'status-void'
                : paymentStatus === 'paid'
                    ? 'status-paid'
                    : 'status-pending';
            const statusBadgeText = isVoid
                ? 'Void'
                : paymentStatus === 'paid'
                    ? 'Paid'
                    : 'Pending';
            const paymentInfo = `
                <div class="invoice-payment-meta">
                    <span class="invoice-status-pill ${statusBadgeClass}"><i class="fas fa-circle" aria-hidden="true"></i>${statusBadgeText}</span>
                    <span>Metode: <strong>${escapeHtml(_paymentMethodLabel(paymentMethod))}</strong></span>
                    ${providerBadge}
                </div>
                ${i.payment_reference && !isInternalGateway ? `<div class="invoice-payment-ref">Ref: <strong>${escapeHtml(i.payment_reference)}</strong></div>` : ''}
                ${hasPaymentUrl ? `<div class="invoice-payment-link"><button type="button" data-invoice-action="open-payment-url" data-url="${invoiceDataValue(i.payment_url)}">Link Pembayaran</button></div>` : ''}
            `;
            const gatewayActions = (!isVoid && canUseGateway && (provider === 'manual' || hasSupportedGatewayProvider))
                ? `
                    ${hasPaymentUrl ? `
                        <button class="invoice-action-btn invoice-action-btn-link" data-invoice-action="open-payment-url" data-url="${invoiceDataValue(i.payment_url)}" title="Buka Link Pembayaran">
                            <i class="fas fa-external-link-alt"></i><span>Buka Link</span>
                        </button>
                        ${hasSupportedGatewayProvider ? `<button class="invoice-action-btn invoice-action-btn-check" data-invoice-action="check-gateway-status" data-reference="${invoiceDataValue(i.payment_reference)}" title="Cek Status">
                            <i class="fas fa-sync-alt"></i><span>Cek Status</span>
                        </button>` : ''}
                    ` : `
                        <button class="invoice-action-btn invoice-action-btn-text invoice-gateway-create-btn" type="button" data-invoice-action="create-gateway-payment" data-source-id="${escapeHtml(strId)}" data-amount="${Number(i.price || 0)}" data-payment-method="${escapeHtml(paymentMethod)}" title="Buat Link Pembayaran">
                            <i class="fas fa-link"></i><span>Link Bayar</span>
                        </button>
                    `}
                `
                : '';
            const manualPaymentActions = (!isVoid && ['unpaid', 'pending', 'partial'].includes(paymentStatus))
                ? `
                    <button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-paid" type="button" data-invoice-action="manual-payment" data-source-id="${escapeHtml(strId)}" data-status="paid" data-amount="${Number(i.price || 0)}" data-payment-method="${escapeHtml(paymentMethod)}" title="Tandai Lunas Manual">
                        <i class="fas fa-check-circle"></i><span>Tandai Lunas</span>
                    </button>
                    ${paymentStatus !== 'partial' ? `<button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-partial" type="button" data-invoice-action="manual-payment" data-source-id="${escapeHtml(strId)}" data-status="partial" data-amount="${Number(i.price || 0)}" data-payment-method="${escapeHtml(paymentMethod)}" title="Catat DP Manual">
                        <i class="fas fa-receipt"></i><span>Catat DP</span>
                    </button>` : ''}
                `
                : '';
            const paymentLinkAction = (!isVoid && !hasPaymentUrl && paymentStatus === 'unpaid')
                ? `
                    <button class="invoice-action-btn invoice-action-btn-text invoice-gateway-create-btn" type="button" data-invoice-action="create-gateway-payment" data-source-id="${escapeHtml(strId)}" data-amount="${Number(i.price || 0)}" data-payment-method="${escapeHtml(_canUseGateway(paymentMethod) ? paymentMethod : 'qris')}" title="Buat Link Pembayaran">
                        <i class="fas fa-link"></i><span>Buat Link Pembayaran</span>
                    </button>
                `
                : '';
            let actionHtml = '';
            if (isHerbal) {
                if (hasInvoicePath && fileExists) {
                    actionHtml = `
                        ${stalePdfNotice}
                        <button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-pdf" data-invoice-action="open-invoice" data-path="${safePath}" title="Buka PDF Herbal">
                            <i class="fas fa-file-pdf"></i><span>Lihat</span>
                        </button>
                        <button class="invoice-action-btn invoice-action-btn-text" data-invoice-action="reveal-invoice" data-path="${safePath}" title="Reveal Lokasi PDF Herbal">
                            <i class="fas fa-folder-open"></i><span>Lokasi</span>
                        </button>
                        <button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-print" data-invoice-action="print-invoice" data-path="${safePath}" data-print-source="herbal_invoice" title="Print Herbal">
                            <i class="fas fa-print"></i><span>Print</span>
                        </button>
                        ${isVoid ? '' : `<button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-update" data-invoice-action="generate-herbal" data-source-id="${escapeHtml(strId.startsWith('hg_') ? 'group:' + numId : numId)}" title="Update PDF dengan status pembayaran terbaru">
                            <i class="fas fa-file-circle-check"></i><span>Update</span>
                        </button>`}
                        ${isVoid ? '' : `<button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-void" data-invoice-action="void-invoice" data-invoice-type="herbal" data-source-id="${escapeHtml(voidTarget)}" title="Void Invoice Herbal">
                            <i class="fas fa-ban"></i><span>Void</span>
                        </button>`}
                    `;
                }
                else {
                    actionHtml = `
                        ${missingFileNotice}
                        <button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-generate-herbal" data-invoice-action="generate-herbal" data-source-id="${escapeHtml(strId.startsWith('hg_') ? 'group:' + numId : numId)}" title="Generate PDF Invoice Herbal">
                            <i class="fas fa-file-signature"></i> <span>${isMissingFile ? 'Buat Ulang' : 'Buat Invoice'}</span>
                        </button>
                    `;
                }
            }
            else {
                if (hasInvoicePath && fileExists) {
                    actionHtml = `
                        ${stalePdfNotice}
                        <button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-pdf" data-invoice-action="open-invoice" data-path="${safePath}" title="Buka PDF">
                            <i class="fas fa-file-pdf"></i><span>Lihat</span>
                        </button>
                        <button class="invoice-action-btn invoice-action-btn-text" data-invoice-action="reveal-invoice" data-path="${safePath}" title="Reveal Lokasi PDF">
                            <i class="fas fa-folder-open"></i><span>Lokasi</span>
                        </button>
                        <button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-print" data-invoice-action="print-invoice" data-path="${safePath}" data-print-source="invoice" title="Print Langsung">
                            <i class="fas fa-print"></i><span>Print</span>
                        </button>
                        ${isVoid ? '' : `<button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-update" data-invoice-action="generate-visit" data-source-id="${escapeHtml(numId)}" title="Update PDF dengan status pembayaran terbaru">
                            <i class="fas fa-file-circle-check"></i><span>Update</span>
                        </button>`}
                        ${isVoid ? '' : `<button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-void" data-invoice-action="void-invoice" data-invoice-type="visit" data-source-id="${escapeHtml(voidTarget)}" title="Void Invoice">
                            <i class="fas fa-ban"></i><span>Void</span>
                        </button>`}
                    `;
                }
                else {
                    actionHtml = `
                        ${missingFileNotice}
                        <button class="invoice-action-btn invoice-action-btn-text invoice-action-btn-generate" data-invoice-action="generate-visit" data-source-id="${escapeHtml(numId)}" title="Generate PDF Invoice">
                            <i class="fas fa-file-signature"></i> <span>${isMissingFile ? 'Buat Ulang' : 'Buat Invoice'}</span>
                        </button>
                    `;
                }
            }
            html += `<tr>
                <td class="invoice-row-date">
                    <i class="fas fa-calendar-alt"></i>
                    ${escapeHtml(i.date)}
                </td>
                <td>
                    <div class="invoice-row-client">
                        <div class="invoice-row-avatar">
                            ${escapeHtml(i.name).charAt(0).toUpperCase()}
                        </div>
                        <span class="invoice-row-name">${escapeHtml(i.name)}</span>
                        ${isVoid ? `<span class="invoice-void-badge" title="${voidTitle}">VOID</span>` : ''}
                    </div>
                    ${paymentInfo}
                </td>
                <td class="invoice-row-amount ${isVoid ? 'void' : 'paid'}">${formatRupiah(i.price)}</td>
                <td class="invoice-actions-cell">
                    <div class="invoice-actions">
                        ${manualPaymentActions}
                        ${paymentLinkAction}
                        ${actionHtml}
                        ${gatewayActions}
                    </div>
                </td>
            </tr>`;
        });
        html += `</tbody></table></div>
            <div class="invoice-pagination">
                <button type="button" class="btn btn-secondary" ${window._invoicesPage <= 1 ? 'disabled' : ''} data-invoice-action="page-prev">
                    <i class="fas fa-chevron-left"></i> Sebelumnya
                </button>
                <button type="button" class="btn btn-secondary" ${data.length < 100 ? 'disabled' : ''} data-invoice-action="page-next">
                    Selanjutnya <i class="fas fa-chevron-right"></i>
                </button>
            </div>`;
    }
    html += `</div>`;
    const displayArea = document.getElementById('display-area');
    if (displayArea)
        displayArea.innerHTML = html;
    if (window._invoiceSearchRestoreFocus) {
        const input = /** @type {HTMLInputElement | null} */ (document.getElementById('invoice-search-input'));
        const cursor = Number(window._invoiceSearchCursor ?? String(window._invoicesSearch || '').length);
        if (input) {
            requestAnimationFrame(() => {
                input.focus();
                const pos = Math.min(cursor, input.value.length);
                try {
                    input.setSelectionRange(pos, pos);
                }
                catch (e) { }
            });
        }
        window._invoiceSearchRestoreFocus = false;
    }
}
async function refreshInvoicesList({ preserveSearchFocus = false } = {}) {
    const period = window._invoicesPeriod || 'all';
    const page = window._invoicesPage || 1;
    const search = window._invoicesSearch || '';
    const endpoint = `/invoices?period=${period}&page=${page}&page_size=100&search=${encodeURIComponent(search)}`;
    if (preserveSearchFocus)
        window._invoiceSearchRestoreFocus = true;
    try {
        const response = await fetch(endpoint);
        if (!response.ok)
            throw new Error('Gagal memuat invoice.');
        const data = await response.json();
        renderInvoices(data);
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal memuat invoice.'), 'error');
    }
}
function onInvoiceSearchInput(value) {
    const input = /** @type {HTMLInputElement | null} */ (document.getElementById('invoice-search-input'));
    window._invoiceSearchCursor = input ? input.selectionStart : String(value || '').length;
    clearTimeout(window._invoiceSearchTimer);
    window._invoiceSearchTimer = setTimeout(() => {
        window._invoicesSearch = value || '';
        window._invoicesPage = 1;
        refreshInvoicesList({ preserveSearchFocus: true });
    }, 300);
}
