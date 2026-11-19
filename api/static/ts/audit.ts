type AuditLabelMap = Record<string, string>;

interface Window {
    renderAuditLogs?: () => Promise<void>;
}

let auditDelegationReady = false;

function ensureAuditEventDelegation(): void {
    if (auditDelegationReady) return;
    auditDelegationReady = true;

    document.addEventListener('click', (event) => {
        const actionElement = (event.target as HTMLElement | null)?.closest<HTMLElement>('[data-audit-action]');
        if (!actionElement) return;
        const action = actionElement.dataset.auditAction || '';
        if (!action) return;
        event.preventDefault();

        switch (action) {
            case 'refresh':
                renderAuditLogs();
                break;
            case 'detail':
                showAuditDetail(Number(actionElement.dataset.auditIndex || 0));
                break;
            case 'close-detail':
                closeAuditDetail(actionElement.closest('.audit-modal-overlay'));
                break;
            case 'copy-value':
                copyAuditValue(actionElement, Number(actionElement.dataset.auditIndex || 0), actionElement.dataset.auditKey || '');
                break;
        }
    });
}

function formatAuditTimestamp(value?: string): string {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString('id-ID', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

function formatAuditValue(key: string, value: unknown): string {
    if (value === null || value === undefined || value === '') return '-';
    if (/price|total|subtotal|amount/i.test(key) && !Number.isNaN(Number(value))) return formatRupiah(Number(value));
    if (typeof value === 'boolean') return value ? 'Ya' : 'Tidak';
    if (Array.isArray(value)) return `${value.length} item`;
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
}

function formatAuditLabel(key: string): string {
    if (auditLabelMap[key]) return auditLabelMap[key];
    return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (char) => char.toUpperCase());
}

function isLongAuditValue(key: string, value: unknown): boolean {
    const text = formatAuditValue(key, value);
    return /reference|token|id|code/i.test(key) || text.length > 28;
}

const auditLabelMap: AuditLabelMap = {
    patient_id: 'ID pasien',
    patient_name: 'Pasien',
    phone: 'No HP',
    old_phone: 'No HP lama',
    gender: 'Gender',
    old_name: 'Nama lama',
    service_name: 'Layanan',
    therapist_name: 'Terapis',
    quantity: 'Jumlah',
    unit_label: 'Unit',
    price: 'Harga',
    total: 'Total',
    is_free_visit: 'Gratis',
    free_visit_reason: 'Alasan gratis',
    discount_rule_name: 'Diskon',
    herbal_count: 'Produk/herbal',
    herbal_total: 'Total herbal',
    item_count: 'Jumlah item',
    buyer_name: 'Pembeli',
    invoice_number: 'No invoice',
    invoice_type: 'Tipe invoice',
    reason: 'Alasan',
    rule_id: 'ID rule',
    name: 'Nama',
    item_name: 'Item',
    old_item_name: 'Item lama',
    unit: 'Unit',
    stock: 'Stok',
    min_stock: 'Stok min.',
    initial_qty: 'Stok awal',
    change: 'Perubahan',
    quantity_before: 'Stok awal',
    quantity_after: 'Stok akhir',
    stock_before: 'Stok awal',
    stock_after: 'Stok akhir',
    old_price: 'Harga lama',
    old_quantity: 'Jumlah lama',
    discount_type: 'Jenis diskon',
    discount_value: 'Nilai diskon',
    voucher_code: 'Kode voucher',
    source_type: 'Source Type',
    source_id: 'Source ID',
    payment_status: 'Payment Status',
    payment_method: 'Payment Method',
    amount_paid: 'Amount Paid',
    payment_provider: 'Payment Provider',
    payment_reference: 'Payment Reference',
    usage_limit: 'Batas pakai',
    per_patient_limit: 'Batas/pasien',
    end_date: 'Berakhir',
    type: 'Tipe',
    is_active: 'Aktif',
    priority: 'Prioritas',
    clinic_name: 'Nama klinik',
    clinic_phone: 'No klinik',
    base_price: 'Harga dasar',
    discount_percentage: 'Diskon lama',
    price_per_point: 'Harga/titik',
    min_visits_for_discount: 'Mulai kunjungan',
    created_services: 'Layanan dibuat',
    path: 'File',
};

function renderAuditDetails(row: AuditLogRow, idx: number): string {
    const meta = row.metadata && typeof row.metadata === 'object' ? row.metadata : {};
    const entries = Object.entries(meta).filter(([, value]) => value !== null && value !== undefined && value !== '');
    if (!entries.length) {
        return `<div class="audit-empty" style="text-align:center; padding: 20px; color: var(--text-muted);">Tidak ada metadata tambahan.</div>`;
    }
    return `
        <div class="audit-meta-grid">
            ${entries.map(([key, value]) => {
                const isLong = isLongAuditValue(key, value);
                const strValue = formatAuditValue(key, value);
                const escapedStr = escapeHtml(strValue);
                return `
                <div class="audit-meta-item">
                    <span class="audit-meta-key">${escapeHtml(formatAuditLabel(key))}</span>
                    <div class="audit-meta-value ${isLong ? 'long' : ''}">
                        ${isLong ? `<pre>${escapedStr}</pre><button type="button" class="audit-copy-btn" data-audit-action="copy-value" data-audit-index="${idx}" data-audit-key="${escapeHtml(key)}" title="Copy"><i class="fas fa-copy"></i></button>` : escapedStr}
                    </div>
                </div>
                `;
            }).join('')}
        </div>`;
}

function renderAuditRow(row: AuditLogRow, idx?: number): string {
    const index = typeof idx === 'number' ? idx : 0;
    return `
        <tr>
            <td>${escapeHtml(formatAuditTimestamp(row.created_at))}</td>
            <td><span class="audit-action">${escapeHtml(row.action || '-')}</span></td>
            <td>${escapeHtml(row.entity_type || '-')}${row.entity_id ? `<br><small>${escapeHtml(row.entity_id)}</small>` : ''}</td>
            <td>
                <div class="audit-description">${escapeHtml(row.description || '-')}</div>
            </td>
            <td>
                <button type="button" class="audit-detail-btn" data-audit-action="detail" data-audit-index="${index}">Detail</button>
            </td>
        </tr>
    `;
}

async function renderAuditLogs(): Promise<void> {
    ensureAuditEventDelegation();
    const rows = await apiGetJson<AuditLogRow[]>('/audit_logs?limit=100');
    const arr = Array.isArray(rows) ? rows : [];
    // expose rows for modal detail rendering
    window._audit_rows = arr;
    const tableRows = arr.map((r, i) => renderAuditRow(r, i)).join('');

    const displayArea = document.getElementById('display-area');
    if (!displayArea) return;
    displayArea.innerHTML = `
        <div class="card audit-log-card">
            <div class="card-header audit-log-header">
                <div>
                    <h3><i class="fas fa-history"></i> Log Aktivitas</h3>
                    <p>Riwayat perubahan data dan aksi sensitif di aplikasi lokal.</p>
                </div>
                <button type="button" class="btn btn-secondary" data-audit-action="refresh" style="width:auto;">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
            </div>
            <div class="audit-table-wrap">
                <table class="audit-log-table">
                    <thead>
                        <tr>
                            <th>Waktu</th>
                            <th>Aksi</th>
                            <th>Objek</th>
                            <th>Keterangan</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRows || '<tr><td colspan="4" class="audit-empty">Belum ada aktivitas tercatat.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function renderAuditCard(row: AuditLogRow, idx: number): string {
    return `
        <div class="audit-card">
            <div class="audit-card-head">
                <div>
                    <div class="audit-card-time">${escapeHtml(formatAuditTimestamp(row.created_at))}</div>
                    <div class="audit-card-summary">${escapeHtml(row.description || '-')}</div>
                </div>
                <div class="audit-card-actions">
                    <button type="button" class="audit-detail-btn" data-audit-action="detail" data-audit-index="${idx}">Detail</button>
                </div>
            </div>
        </div>
    `;
}

function showAuditDetail(idx: number): void {
    try {
        const rows: AuditLogRow[] = window._audit_rows || [];
        const row = rows[idx];
        if (!row) return;

        // avoid duplicate overlays
        if (document.querySelector('.audit-modal-overlay')) return;

        const overlay = document.createElement('div');
        overlay.className = 'audit-modal-overlay';

        const modal = document.createElement('div');
        modal.className = 'audit-modal';

        modal.innerHTML = `
            <div class="audit-modal-header">
                <div class="audit-modal-header-left">
                    <div class="audit-modal-icon"><i class="fas fa-history"></i></div>
                    <div>
                        <div class="audit-modal-title">Log Aktivitas</div>
                        <div class="audit-modal-subtitle">Detail aktivitas</div>
                    </div>
                </div>
                <div class="audit-modal-header-right">
                    <button type="button" class="audit-modal-close" aria-label="Tutup">&times;</button>
                </div>
            </div>
            <div class="audit-modal-body">
                ${renderAuditDetails(row, idx)}
            </div>
            <div class="audit-modal-footer">
                <button type="button" class="btn" data-audit-action="close-detail">Tutup</button>
            </div>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        document.body.classList.add('audit-modal-open');

        // close handlers
        const closeBtn = modal.querySelector('.audit-modal-close');
        if (closeBtn) closeBtn.addEventListener('click', () => closeAuditDetail(overlay));
        overlay.addEventListener('click', (ev) => { if (ev.target === overlay) closeAuditDetail(overlay); });
        document.addEventListener('keydown', function onKey(e) { if (e.key === 'Escape') { document.removeEventListener('keydown', onKey); closeAuditDetail(overlay); } });
    }
    catch (err) {
        console.error('showAuditDetail error', err);
    }
}

function closeAuditDetail(overlayEl: Element | null): void {
    try {
        const overlay = overlayEl instanceof Element ? overlayEl : document.querySelector('.audit-modal-overlay');
        if (!overlay) return;
        overlay.remove();
        document.body.classList.remove('audit-modal-open');
    }
    catch (err) {
        console.error('closeAuditDetail error', err);
    }
}

window.renderAuditLogs = renderAuditLogs;
window.showAuditDetail = showAuditDetail;
window.closeAuditDetail = closeAuditDetail;

async function copyAuditValue(btn: HTMLElement, idx: number, key: string): Promise<void> {
    try {
        const rows: AuditLogRow[] = window._audit_rows || [];
        const meta = rows[idx]?.metadata && typeof rows[idx].metadata === 'object' ? rows[idx].metadata : {};
        const text = formatAuditValue(key, (meta as Record<string, unknown>)[key]);
        await navigator.clipboard.writeText(text);
        const icon = btn.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-check';
            icon.style.color = 'var(--success)';
            setTimeout(() => {
                icon.className = 'fas fa-copy';
                icon.style.color = '';
            }, 2000);
        }
    } catch (e) {
        console.error('Failed to copy', e);
    }
}

window.copyAuditValue = copyAuditValue;
