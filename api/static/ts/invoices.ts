// ─── INVOICES ─────────────────────────────────────────────────────────────────

type InvoiceId = string | number;

type GatewayPaymentSource = {
    source_type: 'visit' | 'herbal';
    source_id: string;
};

type InvoiceUpdateTarget = {
    invoice_type: 'visit' | 'herbal';
    visit_id?: string;
    transaction_id?: string;
    sale_group_id?: string;
};

type BadgeStyle = {
    bg: string;
    color: string;
};

type InvoiceApiPayload = ApiResponse & {
    payment?: {
        payment_provider?: string;
        payment_url?: string;
    };
    pdf_status?: string;
};

function openInvoice(path: string): void {
    fetch('/open_invoice?path=' + encodeURIComponent(path))
        .then(res => res.json())
        .then(data => {
            if (data.status && data.status.toLowerCase() !== 'success') {
                showToast('Gagal membuka file: ' + (data.detail || 'File tidak ditemukan'), 'error');
            }
        })
        .catch(() => showToast('Koneksi gagal saat mencoba membuka file invoice PDF.', 'error'));
}

function printInvoice(path: string): void {
    fetch('/print_invoice?path=' + encodeURIComponent(path))
        .then(res => res.json())
        .then(data => {
            if (data.status && data.status.toLowerCase() === 'success') {
                showToast(data.message || 'Memulai proses cetak ke printer default...', 'success');
            } else {
                showToast('Gagal mencetak: ' + (data.detail || 'File tidak ditemukan'), 'error');
            }
        })
        .catch(() => showToast('Koneksi gagal saat mencoba mencetak file invoice PDF.', 'error'));
}

function generateInvoiceForVisit(visitId: InvoiceId): void {
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
                    throw new Error(err.detail || `Server error ${res.status}`);
                }).catch(() => {
                    throw new Error(`Server error ${res.status} - periksa log server`);
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
            } else {
                showToast("Gagal membuat invoice: " + (data.detail || "Terjadi kesalahan server"), "error");
            }
        })
        .catch(err => showToast("Gagal membuat invoice: " + sanitizeAppErrorMessage(err, "Gagal membuat invoice."), "error"));
}

function generateInvoiceForHerbal(identifier: InvoiceId): void {
    showToast("Sedang mengekspor PDF herbal...", "info");
    const formData = new FormData();
    const idText = String(identifier || '');
    if (idText.startsWith('group:')) {
        formData.append("sale_group_id", idText.slice(6));
    } else {
        formData.append("transaction_id", idText);
    }

    fetch('/generate_herbal_invoice', {
        method: 'POST',
        body: formData
    })
        .then(res => {
            if (!res.ok) {
                return res.json().then(err => {
                    throw new Error(err.detail || `Server error ${res.status}`);
                }).catch(() => {
                    throw new Error(`Server error ${res.status} - periksa log server`);
                });
            }
            return res.json();
        })
        .then(data => {
            if (data.status === "success") {
                showToast(data.message || "Invoice herbal PDF berhasil dibuat!", "success");
                window._invoicesPage = 1;
                loadTab('invoices');
            } else {
                showToast("Gagal membuat invoice herbal: " + (data.detail || "Terjadi kesalahan server"), "error");
            }
        })
        .catch(err => showToast("Gagal membuat invoice herbal: " + sanitizeAppErrorMessage(err, "Gagal membuat invoice herbal."), "error"));
}

function _paymentProviderLabel(provider: unknown): string {
    const labels: Record<string, string> = {
        gateway_mock: 'Pembayaran Internal',
        midtrans: 'Midtrans',
        manual: 'Manual'
    };
    return labels[String(provider || 'manual').toLowerCase()] || 'Provider Tidak Didukung';
}

function _isSupportedGatewayProvider(provider: unknown): boolean {
    return ['gateway_mock', 'midtrans'].includes(String(provider || '').toLowerCase());
}

function _paymentProviderBadgeStyle(provider: unknown): BadgeStyle {
    const normalized = String(provider || 'manual').toLowerCase();
    if (normalized === 'midtrans') return { bg: '#ede9fe', color: '#6d28d9' };
    if (normalized === 'gateway_mock') return { bg: '#dcfce7', color: '#047857' };
    if (normalized === 'manual') return { bg: '#f1f5f9', color: '#475569' };
    return { bg: '#fee2e2', color: '#b91c1c' };
}

function _paymentStatusLabel(status: unknown): string {
    const normalized = String(status || '').toLowerCase();
    const labels: Record<string, string> = {
        paid: 'Lunas',
        unpaid: 'Belum Bayar',
        partial: 'Sebagian',
        pending: 'Menunggu',
        expired: 'Kedaluwarsa',
        failed: 'Gagal'
    };
    return labels[normalized] || String(status || '-');
}

function _paymentMethodLabel(method: unknown): string {
    const normalized = String(method || '').toLowerCase();
    const labels: Record<string, string> = {
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

function _gatewaySourceFromInvoiceId(invoiceId: InvoiceId): GatewayPaymentSource | null {
    const strId = String(invoiceId || '');
    if (strId.startsWith('v_')) return { source_type: 'visit', source_id: strId.slice(2) };
    if (strId.startsWith('hg_')) return { source_type: 'herbal', source_id: 'group:' + strId.slice(3) };
    if (strId.startsWith('h_')) return { source_type: 'herbal', source_id: strId.slice(2) };
    return null;
}

function _canUseGateway(method: unknown): boolean {
    return ['qris', 'ewallet', 'virtual_account', 'credit_card'].includes(String(method || '').toLowerCase());
}

function _absolutePaymentUrl(paymentUrl: unknown): string {
    const url = String(paymentUrl || '').trim();
    if (!url) return '';
    try {
        return new URL(url, window.location.origin).href;
    } catch (e) {
        return url;
    }
}

async function createGatewayPayment(invoiceId: InvoiceId, amount: number | string, method: string, button?: HTMLButtonElement | null): Promise<void> {
    const source = _gatewaySourceFromInvoiceId(invoiceId);
    if (!source) {
        showToast('Sumber transaksi tidak valid.', 'error');
        return;
    }
    const actionButton = button || null;
    const originalHtml = actionButton ? actionButton.innerHTML : '';
    let paymentWindow: Window | null = null;
    try {
        paymentWindow = window.open('', '_blank');
        if (paymentWindow) {
            paymentWindow.opener = null;
            paymentWindow.document.write('<!doctype html><title>Membuat Link Pembayaran</title><p style="font-family:system-ui,sans-serif;padding:24px;">Membuat link pembayaran...</p>');
        }
    } catch (e) {
        paymentWindow = null;
    }
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
        const data = await response.json().catch(() => ({})) as InvoiceApiPayload;
        if (!response.ok || data.status !== 'success') {
            throw new Error(String(data.detail || 'Gagal membuat link pembayaran.'));
        }
        const providerLabel = _paymentProviderLabel(data.payment?.payment_provider || 'manual');
        const paymentUrl = _absolutePaymentUrl(data.payment?.payment_url || '');
        const isInternalPayment = String(data.payment?.payment_provider || '').toLowerCase() === 'gateway_mock';
        if (paymentUrl && !isInternalPayment) {
            if (paymentWindow) {
                paymentWindow.location.href = paymentUrl;
            } else {
                showToast('Link berhasil dibuat. Popup browser diblokir, klik ikon buka link pada invoice.', 'warning');
            }
        } else if (paymentWindow) {
            paymentWindow.close();
        }
        showToast(
            isInternalPayment
                ? `${providerLabel} berhasil dibuat. Status menunggu pembayaran.`
                : `Link pembayaran ${providerLabel} berhasil dibuat.`,
            'success'
        );
        window._invoicesPage = 1;
        loadTab('invoices');
    } catch (error) {
        if (paymentWindow) paymentWindow.close();
        showToast(sanitizeAppErrorMessage(error, 'Gagal membuat link pembayaran.'), 'error');
    } finally {
        if (actionButton) {
            actionButton.disabled = false;
            actionButton.innerHTML = originalHtml;
        }
    }
}

function openGatewayPaymentUrl(paymentUrl: string): void {
    const url = _absolutePaymentUrl(paymentUrl);
    if (!url) {
        showToast('Link pembayaran belum tersedia.', 'warning');
        return;
    }
    window.open(url, '_blank', 'noopener');
}

async function checkGatewayStatus(paymentReference: string): Promise<void> {
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
    } catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal mengecek status pembayaran.'), 'error');
    }
}

async function voidInvoice(type: 'visit' | 'herbal', identifier: InvoiceId): Promise<void> {
    const idText = String(identifier || '');
    const html = `
        <div style="font-size:13px;color:var(--text-muted);margin-bottom:12px;">
            Invoice akan ditandai VOID. Ini tidak otomatis mengubah stok atau membuat retur.
        </div>
        <div class="form-group">
            <label>Alasan Pembatalan</label>
            <textarea id="void-invoice-reason" rows="4" minlength="5" required placeholder="Contoh: Invoice salah cetak / transaksi dibatalkan"></textarea>
        </div>
        <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:18px;">
            <button type="button" class="btn" onclick="closeModal()" style="background:#f1f5f9;color:#475569;">Batal</button>
            <button type="button" class="btn btn-primary" onclick="submitVoidInvoice('${type}', '${idText.replace(/'/g, "\\'")}')" style="background:#ef4444;">
                <i class="fas fa-ban"></i> Void Invoice
            </button>
        </div>
    `;
    openModal('Void / Cancel Invoice', html);
}

async function submitVoidInvoice(type: 'visit' | 'herbal', identifier: InvoiceId): Promise<void> {
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
    if (!ok) return;
    const form = new FormData();
    form.append('invoice_type', type);
    form.append('reason', reason);
    if (type === 'visit') {
        form.append('visit_id', String(identifier));
    } else if (String(identifier).startsWith('group:')) {
        form.append('sale_group_id', String(identifier).slice(6));
    } else {
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
    } catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal membatalkan invoice.'), 'error');
    }
}

function _invoiceUpdateTarget(invoiceId: InvoiceId): InvoiceUpdateTarget | null {
    const source = _gatewaySourceFromInvoiceId(invoiceId);
    if (!source) return null;
    if (source.source_type === 'visit') {
        return { invoice_type: 'visit', visit_id: source.source_id };
    }
    if (String(source.source_id || '').startsWith('group:')) {
        return { invoice_type: 'herbal', sale_group_id: String(source.source_id).slice(6) };
    }
    return { invoice_type: 'herbal', transaction_id: source.source_id };
}

function manualInvoicePayment(invoiceId: InvoiceId, status: PaymentStatus, amount: number | string, currentMethod = 'cash'): void {
    const target = _invoiceUpdateTarget(invoiceId);
    if (!target) {
        showToast('Sumber transaksi tidak valid.', 'error');
        return;
    }
    const isPartial = status === 'partial';
    const escapedId = String(invoiceId || '').replace(/'/g, "\\'");
    const safeMethod = ['cash', 'qris', 'transfer', 'ewallet'].includes(String(currentMethod || '').toLowerCase())
        ? String(currentMethod).toLowerCase()
        : 'cash';
    const html = `
        <div style="font-size:13px;color:var(--text-muted);margin-bottom:12px;">
            ${isPartial ? 'Catat pembayaran sebagian manual.' : 'Tandai transaksi sebagai lunas manual.'}
        </div>
        <div class="form-group">
            <label>Metode Pembayaran</label>
            <select id="manual-payment-method">
                <option value="cash" ${safeMethod === 'cash' ? 'selected' : ''}>Tunai</option>
                <option value="qris" ${safeMethod === 'qris' ? 'selected' : ''}>QRIS Manual</option>
                <option value="transfer" ${safeMethod === 'transfer' ? 'selected' : ''}>Transfer</option>
                <option value="ewallet" ${safeMethod === 'ewallet' ? 'selected' : ''}>E-Wallet</option>
            </select>
        </div>
        ${isPartial ? `
            <div class="form-group">
                <label>Jumlah DP</label>
                <input type="number" id="manual-payment-amount" min="1" max="${Math.max(0, Math.round(Number(amount || 0) - 1))}" placeholder="Masukkan jumlah bayar">
                <small style="display:block;margin-top:6px;color:var(--text-muted);">Total tagihan: ${formatRupiah(amount)}</small>
            </div>
        ` : `<input type="hidden" id="manual-payment-amount" value="${Math.round(Number(amount || 0))}">`}
        <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:18px;">
            <button type="button" class="btn" onclick="closeModal()" style="background:#f1f5f9;color:#475569;">Batal</button>
            <button type="button" class="btn btn-primary" onclick="submitManualInvoicePayment('${escapedId}', '${status}', ${Number(amount || 0)})">
                <i class="fas fa-check-circle"></i> ${isPartial ? 'Simpan DP' : 'Tandai Lunas'}
            </button>
        </div>
    `;
    openModal(isPartial ? 'Catat DP Manual' : 'Tandai Lunas Manual', html);
}

async function submitManualInvoicePayment(invoiceId: InvoiceId, status: PaymentStatus, totalAmount: number | string): Promise<void> {
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
    if (target.visit_id) form.append('visit_id', String(target.visit_id));
    if (target.transaction_id) form.append('transaction_id', String(target.transaction_id));
    if (target.sale_group_id) form.append('sale_group_id', String(target.sale_group_id));
    form.append('payment_status', status);
    form.append('payment_method', method);
    form.append('amount_paid', String(Math.round(amount)));
    try {
        const response = await fetch('/update_invoice_payment', { method: 'POST', body: form });
        const data = await response.json().catch(() => ({})) as InvoiceApiPayload;
        if (!response.ok || data.status !== 'success') {
            throw new Error(String(data.detail || 'Gagal memperbarui status pembayaran.'));
        }
        closeModal();
        const shouldRefreshPdf = await showConfirm(
            `${data.message || 'Status pembayaran berhasil diperbarui.'}\n\nPDF invoice adalah snapshot. Update PDF sekarang agar status pembayaran di PDF ikut terbaru?`,
            'info',
            {
                confirmText: 'Update PDF Sekarang',
                cancelText: 'Nanti',
                maxWidth: '460px'
            }
        );
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
    } catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal memperbarui status pembayaran.'), 'error');
    }
}


function renderInvoices(data: InvoiceItem[]): void {
    window._invoicesPage = window._invoicesPage || 1;
    const totalIncome = data.reduce((s, i) => s + ((i.invoice_status === 'void') ? 0 : (i.price || 0)), 0);
    const totalHerbal = data.filter(i => String(i.id).startsWith('h')).length;
    const totalVisits = data.length - totalHerbal;
    const activePeriod = window._invoicesPeriod || 'all';
    const periodMap: Record<string, string> = {
        '7d': '7 Hari',
        '30d': '30 Hari',
        '6m': '6 Bulan',
        '1y': '1 Tahun',
        'all': 'Semua'
    };
    const periodTitle = periodMap[activePeriod] || 'Semua';

    let html = `
        <!-- Summary bar -->
        <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; margin-bottom:20px;">
            <div class="stat-card" style="margin-bottom:0; border-left:3px solid var(--info);">
                <div class="stat-icon blue"><i class="fas fa-file-invoice"></i></div>
                <div class="stat-details"><h4>Total Transaksi</h4><h2>${data.length}</h2></div>
            </div>
            <div class="stat-card" style="margin-bottom:0; border-left:3px solid #3b82f6;">
                <div class="stat-icon purple"><i class="fas fa-stethoscope"></i></div>
                <div class="stat-details"><h4>Kunjungan</h4><h2>${totalVisits}</h2></div>
            </div>
            <div class="stat-card" style="margin-bottom:0; border-left:3px solid #10b981;">
                <div class="stat-icon green"><i class="fas fa-leaf"></i></div>
                <div class="stat-details"><h4>Herbal</h4><h2>${totalHerbal}</h2></div>
            </div>
            <div class="stat-card" style="margin-bottom:0; border-left:3px solid var(--success);">
                <div class="stat-icon green"><i class="fas fa-money-bill-wave"></i></div>
                <div class="stat-details">
                    <h4>Total Pemasukan</h4>
                    <h2 style="font-size:20px;">${formatRupiah(totalIncome)}</h2>
                </div>
            </div>
        </div>

        <div class="card" style="padding:0;">
            <div class="card-header" style="padding:18px 20px 12px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0;"><i class="fas fa-file-invoice-dollar"></i> Semua Transaksi (Kunjungan & Herbal)</h3>
                    <span style="font-size:12px; color:var(--text-muted); display:inline-block; margin-top:4px;">Periode aktif: ${periodTitle}. Halaman ${window._invoicesPage}. Menampilkan maksimal 100 transaksi.</span>
                </div>
                
                <!-- Period Filter Pills -->
                <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; justify-content:flex-end;">
                <input type="search" id="invoice-search-input" value="${escapeHtml(window._invoicesSearch || '')}" placeholder="Cari transaksi..."
                       oninput="onInvoiceSearchInput(this.value)"
                       style="width:180px; padding:7px 10px; border:1px solid var(--border-color); border-radius:8px; font-size:12px;">
                <div style="display:flex; background:var(--background-alt); border:1px solid var(--border-color); border-radius:20px; overflow:hidden;">
                    ${Object.entries(periodMap).map(([k, v]) => `
                        <button onclick="window._invoicesPeriod='${k}'; window._invoicesPage=1; loadTab('invoices')" 
                                style="border:none; background:${(window._invoicesPeriod || 'all') === k ? 'var(--primary)' : 'transparent'}; 
                                       color:${(window._invoicesPeriod || 'all') === k ? 'white' : 'var(--text-muted)'}; 
                                       padding:6px 14px; font-size:12px; font-weight:600; cursor:pointer; transition:all 0.2s;">
                            ${v}
                        </button>
                    `).join('')}
                </div>
                </div>
            </div>`;

    if (data.length === 0) {
        html += `
            <div style="padding:60px; text-align:center; color:var(--text-muted);">
                <i class="fas fa-history" style="font-size:48px; opacity:0.15; display:block; margin-bottom:16px;"></i>
                <p style="font-size:15px; font-weight:500;">Belum ada Data Transaksi.</p>
                <p style="font-size:12px; margin-top:8px;">Data transaksi kunjungan pasien dan penjualan produk/herbal akan otomatis muncul di sini.</p>
            </div>`;
    } else {
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
            const safePath = rawPath.replace(/'/g, "\\'");

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
            const paymentInfo = `
                <div class="invoice-payment-meta">
                    <span>Status: <strong>${escapeHtml(_paymentStatusLabel(i.payment_status || 'paid'))}</strong></span>
                    <span>Metode: <strong>${escapeHtml(_paymentMethodLabel(paymentMethod))}</strong></span>
                    ${providerBadge}
                </div>
                ${i.payment_reference && !isInternalGateway ? `<div class="invoice-payment-ref">Ref: <strong>${escapeHtml(i.payment_reference)}</strong></div>` : ''}
                ${hasPaymentUrl ? `<div class="invoice-payment-link"><a href="${escapeHtml(i.payment_url)}" target="_blank" rel="noopener">Link Pembayaran</a></div>` : ''}
            `;
            const gatewayActions = (!isVoid && canUseGateway && (provider === 'manual' || hasSupportedGatewayProvider))
                ? `
                    ${hasPaymentUrl ? `
                        <button class="invoice-action-btn" onclick="openGatewayPaymentUrl('${String(i.payment_url || '').replace(/'/g, "\\'")}')" title="Buka Link Pembayaran"
                            style="background:#eff6ff;color:#1d4ed8;border:none;border-radius:8px;padding:7px 10px;font-weight:700;cursor:pointer;font-size:12px;">
                            <i class="fas fa-external-link-alt"></i>
                        </button>
                        ${hasSupportedGatewayProvider ? `<button class="invoice-action-btn" onclick="checkGatewayStatus('${String(i.payment_reference || '').replace(/'/g, "\\'")}')" title="Cek Status"
                            style="background:#ecfdf5;color:#047857;border:none;border-radius:8px;padding:7px 10px;font-weight:700;cursor:pointer;font-size:12px;">
                            <i class="fas fa-sync-alt"></i>
                        </button>` : ''}
                    ` : `
                        <button class="invoice-action-btn invoice-action-btn-text invoice-gateway-create-btn" type="button" onclick="createGatewayPayment('${strId}', ${Number(i.price || 0)}, '${paymentMethod}', this)" title="Buat Link Pembayaran">
                            <i class="fas fa-link"></i><span>Link Bayar</span>
                        </button>
                    `}
                `
                : '';
            const manualPaymentActions = (!isVoid && ['unpaid', 'pending', 'partial'].includes(paymentStatus))
                ? `
                    <button class="invoice-action-btn invoice-action-btn-text" type="button" onclick="manualInvoicePayment('${strId}', 'paid', ${Number(i.price || 0)}, '${paymentMethod}')" title="Tandai Lunas Manual"
                        style="background:#dcfce7;color:#047857;border:none;border-radius:8px;padding:7px 10px;font-weight:700;cursor:pointer;font-size:12px;">
                        <i class="fas fa-check-circle"></i><span>Tandai Lunas</span>
                    </button>
                    ${paymentStatus !== 'partial' ? `<button class="invoice-action-btn invoice-action-btn-text" type="button" onclick="manualInvoicePayment('${strId}', 'partial', ${Number(i.price || 0)}, '${paymentMethod}')" title="Catat DP Manual"
                        style="background:#fef3c7;color:#92400e;border:none;border-radius:8px;padding:7px 10px;font-weight:700;cursor:pointer;font-size:12px;">
                        <i class="fas fa-receipt"></i><span>Catat DP</span>
                    </button>` : ''}
                `
                : '';
            const paymentLinkAction = (!isVoid && !hasPaymentUrl && paymentStatus === 'unpaid')
                ? `
                    <button class="invoice-action-btn invoice-action-btn-text invoice-gateway-create-btn" type="button" onclick="createGatewayPayment('${strId}', ${Number(i.price || 0)}, '${_canUseGateway(paymentMethod) ? paymentMethod : 'qris'}', this)" title="Buat Link Pembayaran">
                        <i class="fas fa-link"></i><span>Buat Link Pembayaran</span>
                    </button>
                `
                : '';

            let actionHtml = '';
            if (isHerbal) {
                if (hasInvoicePath && fileExists) {
                    actionHtml = `
                        ${stalePdfNotice}
                        <button class="invoice-action-btn" onclick="openInvoice('${safePath}')" title="Buka PDF Herbal"
                            style="background:linear-gradient(135deg,#3b82f6,#6366f1); color:white; border:none; border-radius:8px; padding:7px 10px; font-weight:600; cursor:pointer; font-size:12px; transition:all 0.2s; box-shadow:0 2px 8px rgba(99,102,241,0.3);"
                            onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 12px rgba(99,102,241,0.45)'"
                            onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 8px rgba(99,102,241,0.3)'">
                            <i class="fas fa-file-pdf"></i>
                        </button>
                        <button class="invoice-action-btn" onclick="printInvoice('${safePath}')" title="Print Herbal"
                            style="background:linear-gradient(135deg,#10b981,#059669); color:white; border:none; border-radius:8px; padding:7px 10px; font-weight:600; cursor:pointer; font-size:12px; transition:all 0.2s; box-shadow:0 2px 8px rgba(16,185,129,0.3);"
                            onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 12px rgba(16,185,129,0.45)'"
                            onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 8px rgba(16,185,129,0.3)'">
                            <i class="fas fa-print"></i>
                        </button>
                        ${isVoid ? '' : `<button class="invoice-action-btn" onclick="generateInvoiceForHerbal('${strId.startsWith('hg_') ? 'group:' + numId : numId}')" title="Update PDF dengan status pembayaran terbaru"
                            style="background:#e0f2fe;color:#0369a1;border:none;border-radius:8px;padding:7px 10px;font-weight:600;cursor:pointer;font-size:12px;">
                            <i class="fas fa-file-circle-check"></i>
                        </button>`}
                        ${isVoid ? '' : `<button class="invoice-action-btn" onclick="voidInvoice('herbal', '${voidTarget}')" title="Void Invoice Herbal"
                            style="background:#fee2e2;color:#b91c1c;border:none;border-radius:8px;padding:7px 10px;font-weight:600;cursor:pointer;font-size:12px;">
                            <i class="fas fa-ban"></i>
                        </button>`}
                    `;
                } else {
                    actionHtml = `
                        ${missingFileNotice}
                        <button class="invoice-action-btn invoice-action-btn-text" onclick="generateInvoiceForHerbal('${strId.startsWith('hg_') ? 'group:' + numId : numId}')" title="Generate PDF Invoice Herbal"
                            style="background:linear-gradient(135deg,#10b981,#059669); color:white; border:none; border-radius:8px; padding:7px 14px; font-weight:600; cursor:pointer; font-size:12px; transition:all 0.2s; box-shadow:0 2px 8px rgba(16,185,129,0.3);"
                            onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 12px rgba(16,185,129,0.45)'"
                            onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 8px rgba(16,185,129,0.3)'">
                            <i class="fas fa-file-signature"></i> ${isMissingFile ? 'Buat Ulang' : 'Buat Invoice'}
                        </button>
                    `;
                }
            } else {
                if (hasInvoicePath && fileExists) {
                    actionHtml = `
                        ${stalePdfNotice}
                        <button class="invoice-action-btn" onclick="openInvoice('${safePath}')" title="Buka PDF"
                            style="background:linear-gradient(135deg,#3b82f6,#6366f1); color:white; border:none; border-radius:8px; padding:7px 10px; font-weight:600; cursor:pointer; font-size:12px; transition:all 0.2s; box-shadow:0 2px 8px rgba(99,102,241,0.3);"
                            onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 12px rgba(99,102,241,0.45)'"
                            onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 8px rgba(99,102,241,0.3)'">
                            <i class="fas fa-file-pdf"></i>
                        </button>
                        <button class="invoice-action-btn" onclick="printInvoice('${safePath}')" title="Print Langsung"
                            style="background:linear-gradient(135deg,#10b981,#059669); color:white; border:none; border-radius:8px; padding:7px 10px; font-weight:600; cursor:pointer; font-size:12px; transition:all 0.2s; box-shadow:0 2px 8px rgba(16,185,129,0.3);"
                            onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 12px rgba(16,185,129,0.45)'"
                            onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 8px rgba(16,185,129,0.3)'">
                            <i class="fas fa-print"></i>
                        </button>
                        ${isVoid ? '' : `<button class="invoice-action-btn" onclick="generateInvoiceForVisit(${numId})" title="Update PDF dengan status pembayaran terbaru"
                            style="background:#e0f2fe;color:#0369a1;border:none;border-radius:8px;padding:7px 10px;font-weight:600;cursor:pointer;font-size:12px;">
                            <i class="fas fa-file-circle-check"></i>
                        </button>`}
                        ${isVoid ? '' : `<button class="invoice-action-btn" onclick="voidInvoice('visit', '${voidTarget}')" title="Void Invoice"
                            style="background:#fee2e2;color:#b91c1c;border:none;border-radius:8px;padding:7px 10px;font-weight:600;cursor:pointer;font-size:12px;">
                            <i class="fas fa-ban"></i>
                        </button>`}
                    `;
                } else {
                    actionHtml = `
                        ${missingFileNotice}
                        <button class="invoice-action-btn invoice-action-btn-text" onclick="generateInvoiceForVisit(${numId})" title="Generate PDF Invoice"
                            style="background:linear-gradient(135deg,#f59e0b,#d97706); color:white; border:none; border-radius:8px; padding:7px 14px; font-weight:600; cursor:pointer; font-size:12px; transition:all 0.2s; box-shadow:0 2px 8px rgba(245,158,11,0.3);"
                            onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 12px rgba(245,158,11,0.45)'"
                            onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 8px rgba(245,158,11,0.3)'">
                            <i class="fas fa-file-signature"></i> ${isMissingFile ? 'Buat Ulang' : 'Buat Invoice'}
                        </button>
                    `;
                }
            }

            html += `<tr>
                <td style="color:var(--text-muted);">
                    <i class="fas fa-calendar-alt" style="color:#cbd5e1; margin-right:6px;"></i>
                    ${escapeHtml(i.date)}
                </td>
                <td>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div style="width:30px; height:30px; border-radius:50%; background:linear-gradient(135deg,#6366f1,#8b5cf6); display:flex; align-items:center; justify-content:center; color:white; font-size:11px; font-weight:700; flex-shrink:0;">
                            ${escapeHtml(i.name).charAt(0).toUpperCase()}
                        </div>
                        <span style="font-weight:600;">${escapeHtml(i.name)}</span>
                        ${isVoid ? `<span title="${voidTitle}" style="background:#fee2e2;color:#b91c1c;font-size:10px;font-weight:800;padding:3px 6px;border-radius:4px;">VOID</span>` : ''}
                    </div>
                    ${paymentInfo}
                </td>
                <td style="text-align:right; font-weight:700; color:${isVoid ? 'var(--text-muted)' : 'var(--success)'};">${formatRupiah(i.price)}</td>
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
            <div style="display:flex; justify-content:flex-end; gap:8px; padding:12px 16px; border-top:1px solid var(--border-color);">
                <button type="button" class="btn btn-secondary" style="width:auto;" ${window._invoicesPage <= 1 ? 'disabled' : ''} onclick="window._invoicesPage=Math.max(1,(window._invoicesPage||1)-1); loadTab('invoices')">
                    <i class="fas fa-chevron-left"></i> Sebelumnya
                </button>
                <button type="button" class="btn btn-secondary" style="width:auto;" ${data.length < 100 ? 'disabled' : ''} onclick="window._invoicesPage=(window._invoicesPage||1)+1; loadTab('invoices')">
                    Selanjutnya <i class="fas fa-chevron-right"></i>
                </button>
            </div>`;
    }

    html += `</div>`;
    const displayArea = document.getElementById('display-area');
    if (displayArea) displayArea.innerHTML = html;
    if (window._invoiceSearchRestoreFocus) {
        const input = /** @type {HTMLInputElement | null} */ (document.getElementById('invoice-search-input'));
        const cursor = Number(window._invoiceSearchCursor ?? String(window._invoicesSearch || '').length);
        if (input) {
            requestAnimationFrame(() => {
                input.focus();
                const pos = Math.min(cursor, input.value.length);
                try {
                    input.setSelectionRange(pos, pos);
                } catch (e) { }
            });
        }
        window._invoiceSearchRestoreFocus = false;
    }
}

async function refreshInvoicesList({ preserveSearchFocus = false }: { preserveSearchFocus?: boolean } = {}): Promise<void> {
    const period = window._invoicesPeriod || 'all';
    const page = window._invoicesPage || 1;
    const search = window._invoicesSearch || '';
    const endpoint = `/invoices?period=${period}&page=${page}&page_size=100&search=${encodeURIComponent(search)}`;
    if (preserveSearchFocus) window._invoiceSearchRestoreFocus = true;

    try {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error('Gagal memuat invoice.');
        const data = await response.json();
        renderInvoices(data);
    } catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Gagal memuat invoice.'), 'error');
    }
}

function onInvoiceSearchInput(value: string): void {
    const input = /** @type {HTMLInputElement | null} */ (document.getElementById('invoice-search-input'));
    window._invoiceSearchCursor = input ? input.selectionStart : String(value || '').length;
    clearTimeout(window._invoiceSearchTimer);
    window._invoiceSearchTimer = setTimeout(() => {
        window._invoicesSearch = value || '';
        window._invoicesPage = 1;
        refreshInvoicesList({ preserveSearchFocus: true });
    }, 300);
}
