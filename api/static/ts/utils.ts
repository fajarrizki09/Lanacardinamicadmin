type ToastType = "success" | "error" | "warning" | "info";
type DialogType = ToastType;

type UtilityConfirmOptions = {
    confirmText?: string;
    cancelText?: string;
    maxWidth?: string;
    html?: boolean;
};

type DialogIcon = {
    icon: string;
    color: string;
};

type MessageLike = unknown;

function escapeHtml(unsafe: MessageLike): string {
    return (unsafe || '').toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function jsStringLiteral(value: MessageLike): string {
    return escapeHtml(JSON.stringify(String(value ?? '')));
}

function formatRupiah(amount: MessageLike): string {
    const value = Number(amount || 0);
    const safeValue = Number.isFinite(value) ? Math.round(value) : 0;
    return `Rp ${safeValue.toLocaleString('id-ID')}`;
}

function toggleVisitHistory(rowId: string): void {
    const row = document.getElementById(rowId);
    if (!row) return;
    const isHidden = row.style.display === 'none' || row.style.display === '';
    row.style.display = isHidden ? 'table-row' : 'none';
}

function readObjectMessage(message: Record<string, unknown>, fallback: string): string {
    if (message.msg) return String(message.msg);
    if (message.message) return String(message.message);
    if (message.detail) return formatUserMessage(message.detail, fallback);

    const loc = message.loc;
    const field = Array.isArray(loc) ? loc.filter(part => part !== 'body').join('.') : '';
    if (field && message.type) return `${field}: ${String(message.type)}`;

    try {
        return JSON.stringify(message);
    } catch (error) {
        return fallback;
    }
}

function formatUserMessage(message: MessageLike, fallback = 'Terjadi kesalahan.'): string {
    if (message === null || message === undefined || message === '') return fallback;
    if (typeof message === 'string') return message;
    if (message instanceof Error) return message.message || fallback;
    if (Array.isArray(message)) {
        return message.map(item => formatUserMessage(item, '')).filter(Boolean).join('\n') || fallback;
    }
    if (typeof message === 'object') {
        return readObjectMessage(message as Record<string, unknown>, fallback);
    }
    return String(message);
}

function getDialogIcon(type: DialogType, fallback: DialogType): DialogIcon {
    const iconMap: Record<DialogType, DialogIcon> = {
        info: { icon: 'fas fa-info-circle', color: '#3b82f6' },
        error: { icon: 'fas fa-exclamation-circle', color: '#ef4444' },
        success: { icon: 'fas fa-check-circle', color: '#10b981' },
        warning: { icon: 'fas fa-exclamation-triangle', color: '#f59e0b' },
    };
    return iconMap[type] || iconMap[fallback];
}

function showAlert(message: MessageLike, type: DialogType = "info"): void {
    const displayMessage = formatUserMessage(message);
    const old = document.getElementById('_customAlertOverlay');
    if (old) old.remove();

    const clinicName = window._clinicName || 'Lancar Dynamic Admin';
    const { icon, color } = getDialogIcon(type, 'info');

    const overlay = document.createElement('div');
    overlay.id = '_customAlertOverlay';
    overlay.style.cssText = `
        position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:99999;
        display:flex; align-items:center; justify-content:center;
        animation: fadeInOverlay 0.15s ease;
    `;

    overlay.innerHTML = `
        <style>
            @keyframes fadeInOverlay { from{opacity:0} to{opacity:1} }
            @keyframes slideUpBox { from{transform:translateY(20px);opacity:0} to{transform:translateY(0);opacity:1} }
        </style>
        <div class="system-dialog-panel" style="
            background:var(--color-surface); color:var(--color-text); border:1px solid var(--color-border); border-radius:14px; box-shadow:0 20px 60px rgba(0,0,0,0.25);
            width:100%; max-width:360px; overflow:hidden;
            animation: slideUpBox 0.2s ease; font-family:'Inter',sans-serif;
        ">
            <div style="background:${color}; padding:14px 20px; display:flex; align-items:center; gap:10px;">
                <i class="${icon}" style="color:#fff; font-size:18px;"></i>
                <span style="color:#fff; font-weight:700; font-size:15px;">${escapeHtml(clinicName)}</span>
            </div>
            <div class="system-dialog-body" style="padding:20px 22px;">
                <p style="margin:0; color:var(--color-text); font-size:14px; line-height:1.6;">${escapeHtml(displayMessage)}</p>
            </div>
            <div style="padding:0 22px 18px; text-align:right;">
                <button id="_customAlertOk"
                    style="background:${color}; color:#fff; border:none; border-radius:8px;
                           padding:8px 24px; font-size:14px; font-weight:600; cursor:pointer;
                           transition:opacity 0.15s;"
                    onmouseover="this.style.opacity='0.85'"
                    onmouseout="this.style.opacity='1'">OK</button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);
    const okButton = document.getElementById('_customAlertOk');
    okButton?.focus();

    const close = () => {
        overlay.style.opacity = '0';
        overlay.style.transition = 'opacity 0.15s';
        setTimeout(() => overlay.remove(), 150);
    };

    okButton?.addEventListener('click', close);
    overlay.addEventListener('click', (event) => { if (event.target === overlay) close(); });
    document.addEventListener('keydown', function onKey(event) {
        if (event.key === 'Enter' || event.key === 'Escape') {
            close();
            document.removeEventListener('keydown', onKey);
        }
    });
}

function showToast(message: MessageLike, type: ToastType = "info"): void {
    const displayMessage = formatUserMessage(message);
    const validTypes: ToastType[] = ['success', 'error', 'warning', 'info'];
    const toastType: ToastType = validTypes.includes(type) ? type : 'info';
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${toastType} tw-toast tw-toast-${toastType}`;
    toast.setAttribute('role', toastType === 'error' ? 'alert' : 'status');
    toast.innerHTML = `
        <span class="toast-message">${escapeHtml(displayMessage)}</span>
        <button type="button" class="toast-close" aria-label="Tutup notifikasi">&times;</button>
    `;
    container.appendChild(toast);

    const close = () => {
        toast.classList.add('toast-hide');
        setTimeout(() => toast.remove(), 180);
    };
    toast.querySelector('.toast-close')?.addEventListener('click', close);
    setTimeout(close, toastType === 'error' ? 5200 : 3600);
}

window.alert = (message) => showAlert(message, 'info');

function showConfirm(message: MessageLike, type: DialogType = "warning", options: UtilityConfirmOptions = {}): Promise<boolean> {
    return new Promise((resolve) => {
        const old = document.getElementById('_customConfirmOverlay');
        if (old) old.remove();

        const clinicName = window._clinicName || 'Lancar Dynamic Admin';
        const { icon, color } = getDialogIcon(type, 'warning');

        const confirmText = options.confirmText || 'Ya, Lanjutkan';
        const cancelText = options.cancelText || 'Batal';
        const maxWidth = options.maxWidth || '380px';
        const bodyContent = options.html
            ? String(message)
            : `<p style="margin:0; color:var(--color-text); font-size:14px; line-height:1.6; white-space:pre-line;">${escapeHtml(formatUserMessage(message))}</p>`;
        const overlay = document.createElement('div');
        overlay.id = '_customConfirmOverlay';
        overlay.style.cssText = `
            position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:99999;
            display:flex; align-items:center; justify-content:center;
            animation: fadeInOverlay 0.15s ease;
        `;

        overlay.innerHTML = `
            <style>
                @keyframes fadeInOverlay { from{opacity:0} to{opacity:1} }
                @keyframes slideUpBox { from{transform:translateY(20px);opacity:0} to{transform:translateY(0);opacity:1} }
            </style>
            <div class="system-dialog-panel" style="
                background:var(--color-surface); color:var(--color-text); border:1px solid var(--color-border); border-radius:14px; box-shadow:0 20px 60px rgba(0,0,0,0.25);
                width:100%; max-width:${maxWidth}; overflow:hidden;
                animation: slideUpBox 0.2s ease; font-family:'Inter',sans-serif;
            ">
                <div style="background:${color}; padding:14px 20px; display:flex; align-items:center; gap:10px;">
                    <i class="${icon}" style="color:#fff; font-size:18px;"></i>
                    <span style="color:#fff; font-weight:700; font-size:15px;">Konfirmasi - ${escapeHtml(clinicName)}</span>
                </div>
                <div class="system-dialog-body" style="padding:24px 22px;">
                    ${bodyContent}
                </div>
                <div style="padding:0 22px 20px; display:flex; justify-content:flex-end; gap:10px;">
                    <button id="_customConfirmNo" class="system-dialog-cancel"
                        style="background:var(--color-surface-muted); color:var(--color-text); border:1px solid var(--color-border); border-radius:8px;
                               padding:9px 18px; font-size:13px; font-weight:600; cursor:pointer;
                               transition:background 0.15s;"
                        onmouseover="this.style.background='var(--color-surface-raised)'"
                        onmouseout="this.style.background='var(--color-surface-muted)'">${escapeHtml(cancelText)}</button>
                    <button id="_customConfirmYes"
                        style="background:${color}; color:#fff; border:none; border-radius:8px;
                               padding:9px 18px; font-size:13px; font-weight:600; cursor:pointer;
                               transition:opacity 0.15s;"
                        onmouseover="this.style.opacity='0.85'"
                        onmouseout="this.style.opacity='1'">${escapeHtml(confirmText)}</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
        const confirmNo = document.getElementById('_customConfirmNo');
        const confirmYes = document.getElementById('_customConfirmYes');
        confirmNo?.focus();

        const close = () => {
            overlay.style.opacity = '0';
            overlay.style.transition = 'opacity 0.15s';
            setTimeout(() => overlay.remove(), 150);
        };

        confirmYes?.addEventListener('click', () => { close(); resolve(true); });
        confirmNo?.addEventListener('click', () => { close(); resolve(false); });
        overlay.addEventListener('click', (event) => { if (event.target === overlay) { close(); resolve(false); } });
        document.addEventListener('keydown', function onKey(event) {
            if (event.key === 'Escape') {
                close();
                resolve(false);
                document.removeEventListener('keydown', onKey);
            }
        });
    });
}
