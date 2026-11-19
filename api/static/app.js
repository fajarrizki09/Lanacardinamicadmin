"use strict";
// ─── APP ENTRY POINT ─────────────────────────────────────────────────────────
// Navigation setup only. All rendering logic lives in /static/modules/*.js
window._adminPin = '';
window._adminUnlocked = false;
const USER_FRIENDLY_ERROR_MESSAGE = 'Terjadi kesalahan. Silakan coba lagi atau hubungi admin.';
const TECHNICAL_ERROR_PATTERN = /(sqlalchemy|sqlite3|traceback|operationalerror|integrityerror|databaseerror|programmingerror|permissionerror|filenotfounderror|winerror|errno|site-packages|\.py\b|[a-z]:\\|\/users\/|\/home\/)/i;
const ADMIN_IDLE_LOCK_MS = 15 * 60 * 1000;
let adminIdleTimer = null;
let adminIdleListenersReady = false;
let tabLoadSequence = 0;
function sanitizeAppErrorMessage(value, fallback = USER_FRIENDLY_ERROR_MESSAGE) {
    let message = '';
    if (typeof value === 'string') {
        message = value.trim();
    }
    else if (Array.isArray(value)) {
        message = '';
    }
    else if (value && typeof value === 'object') {
        message = String(value.detail || value.message || '').trim();
    }
    if (!message)
        return fallback;
    if (TECHNICAL_ERROR_PATTERN.test(message))
        return fallback;
    return message;
}
async function sanitizeErrorResponse(response) {
    if (response.ok)
        return response;
    const headers = new Headers(response.headers);
    const contentType = headers.get('content-type') || '';
    headers.set('content-type', 'application/json');
    if (contentType.includes('application/json')) {
        try {
            const payload = await response.clone().json();
            const detail = sanitizeAppErrorMessage(payload.detail || payload.message);
            return new Response(JSON.stringify({ ...payload, detail }), {
                status: response.status,
                statusText: response.statusText,
                headers,
            });
        }
        catch (error) {
            return response;
        }
    }
    return new Response(JSON.stringify({ detail: USER_FRIENDLY_ERROR_MESSAGE }), {
        status: response.status,
        statusText: response.statusText,
        headers,
    });
}
const nativeFetch = window.fetch.bind(window);
function withAppTokenHeaders(input, init = {}) {
    const requestInit = { ...init };
    const headers = new Headers(requestInit.headers || (input instanceof Request ? input.headers : {}));
    if (window._appToken) {
        headers.set('X-App-Token', window._appToken);
    }
    requestInit.headers = headers;
    return requestInit;
}
function appFetchRaw(input, init = {}) {
    return nativeFetch(input, withAppTokenHeaders(input, init));
}
window.fetch = async (input, init = {}) => {
    const requestInit = withAppTokenHeaders(input, init);
    const method = (requestInit.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
    const isAdminPinEndpoint = url.includes('/admin_pin/');
    if (window._adminPin && !isAdminPinEndpoint && method !== 'OPTIONS') {
        const headers = new Headers(requestInit.headers || {});
        headers.set('X-Admin-Pin', window._adminPin);
        requestInit.headers = headers;
    }
    const response = await nativeFetch(input, requestInit);
    return sanitizeErrorResponse(response);
};
document.addEventListener("DOMContentLoaded", async () => {
    resetUIZoomToDefault();
    initShellPreferences();
    const unlocked = await ensureAdminUnlocked();
    if (!unlocked)
        return;
    await ensureFirstRunSetup();
    const tabs = document.querySelectorAll('.nav-links li');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const target = tab.getAttribute('data-tab');
            loadTab(target);
            updatePageHeader(target);
        });
    });
    document.querySelectorAll('[data-quick-tab]').forEach(button => {
        button.addEventListener('click', () => {
            const tab = button.getAttribute('data-quick-tab');
            document.querySelector(`.nav-links li[data-tab="${tab}"]`)?.click();
        });
    });
    // Initial load
    initModals();
    loadLicenseStatus();
    loadClinicSettings();
    loadTab('dashboard');
});
function initShellPreferences() {
    const collapseButton = document.getElementById('sidebar-collapse-toggle');
    const themeButton = document.getElementById('theme-toggle');
    const collapsed = localStorage.getItem('lancar_sidebar_collapsed') === '1';
    const theme = localStorage.getItem('lancar_theme') || 'light';
    document.body.classList.toggle('sidebar-collapsed', collapsed);
    document.body.classList.toggle('theme-dark', theme === 'dark');
    updateShellButtons();
    collapseButton?.addEventListener('click', () => {
        const nextCollapsed = !document.body.classList.contains('sidebar-collapsed');
        document.body.classList.toggle('sidebar-collapsed', nextCollapsed);
        localStorage.setItem('lancar_sidebar_collapsed', nextCollapsed ? '1' : '0');
        updateShellButtons();
    });
    themeButton?.addEventListener('click', () => {
        const nextDark = !document.body.classList.contains('theme-dark');
        document.body.classList.toggle('theme-dark', nextDark);
        localStorage.setItem('lancar_theme', nextDark ? 'dark' : 'light');
        updateShellButtons();
    });
}
function updateShellButtons() {
    const collapseIcon = document.querySelector('#sidebar-collapse-toggle i');
    const collapseButton = document.getElementById('sidebar-collapse-toggle');
    const themeIcon = document.querySelector('#theme-toggle i');
    const isCollapsed = document.body.classList.contains('sidebar-collapsed');
    const isDark = document.body.classList.contains('theme-dark');
    if (collapseIcon)
        collapseIcon.className = `fas ${isCollapsed ? 'fa-angles-right' : 'fa-angles-left'}`;
    if (collapseButton) {
        collapseButton.setAttribute('aria-label', isCollapsed ? 'Buka sidebar' : 'Tutup sidebar');
        collapseButton.setAttribute('title', isCollapsed ? 'Buka sidebar' : 'Tutup sidebar');
    }
    if (themeIcon)
        themeIcon.className = `fas ${isDark ? 'fa-sun' : 'fa-moon'}`;
}
function resetUIZoomToDefault() {
    document.body.style.zoom = '100%';
    document.body.classList.remove('is-ui-zoomed');
    localStorage.removeItem('lancar_ui_zoom');
    window.getUIZoom = () => 100;
}
async function ensureFirstRunSetup() {
    try {
        const response = await fetch('/first_run/status');
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.completed)
            return true;
        return await showFirstRunWizard(data.settings || {});
    }
    catch (error) {
        return true;
    }
}
function nextFrame() {
    return new Promise(resolve => requestAnimationFrame(() => resolve()));
}
function renderFirstRunWizard(message = '') {
    let overlay = document.getElementById('first-run-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'first-run-overlay';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:99990;background:rgba(15,23,42,.42);display:grid;place-items:center;padding:18px;font-family:Inter,Arial,sans-serif;';
        document.body.appendChild(overlay);
    }
    overlay.innerHTML = `
        <form id="first-run-form" class="runtime-modal-panel" style="width:min(620px,calc(100vw - 28px));max-height:calc(100vh - 32px);overflow:auto;background:var(--color-surface);color:var(--color-text);border-radius:12px;box-shadow:0 24px 80px rgba(15,23,42,.22);padding:22px;border:1px solid var(--color-border);">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:16px;">
                <div>
                    <h2 style="margin:0;color:var(--color-text);font-size:21px;line-height:1.25;">Setup Awal Klinik</h2>
                    <p style="margin:6px 0 0;color:var(--color-text-muted);font-size:13px;line-height:1.5;">Isi data dasar agar invoice, layanan, dan dashboard siap dipakai.</p>
                </div>
                <button type="button" id="first-run-skip" class="btn btn-secondary" style="width:auto;">Lewati</button>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div class="form-group"><label>Nama Klinik</label><input id="first-clinic-name" type="text" value="${escapeHtml(window._clinicName || '')}" required></div>
                <div class="form-group"><label>Nomor WhatsApp</label><input id="first-clinic-phone" type="text" placeholder="08xxxx"></div>
                <div class="form-group" style="grid-column:1 / -1;"><label>Alamat Klinik</label><input id="first-clinic-address" type="text" placeholder="Alamat singkat klinik"></div>
                <div class="form-group"><label>Logo Klinik (opsional)</label><input id="first-clinic-logo" type="text" placeholder="Path logo"></div>
                <div class="form-group"><label>Prefix Invoice</label><input id="first-invoice-prefix" type="text" value="INV" maxlength="8"></div>
            </div>
            <div style="margin-top:14px;padding:12px;border:1px solid var(--color-border);border-radius:10px;background:var(--color-surface-muted);">
                <strong style="display:block;margin-bottom:9px;color:var(--color-text);font-size:13px;">Layanan Awal</strong>
                <div class="first-service-grid" style="display:grid;grid-template-columns:1.2fr .6fr .6fr;gap:8px;margin-bottom:8px;">
                    <input type="text" value="Terapi Reguler" placeholder="Nama layanan">
                    <input type="text" value="titik" placeholder="Satuan">
                    <input type="number" value="10000" min="0" placeholder="Harga">
                    <input type="text" value="Pijat Terapi" placeholder="Nama layanan">
                    <input type="text" value="sesi" placeholder="Satuan">
                    <input type="number" value="85000" min="0" placeholder="Harga">
                    <input type="text" value="Konsultasi Herbal" placeholder="Nama layanan">
                    <input type="text" value="sesi" placeholder="Satuan">
                    <input type="number" value="50000" min="0" placeholder="Harga">
                </div>
                <small style="color:var(--color-text-muted);">Minimal satu layanan. Maksimal tiga layanan awal pada wizard ini.</small>
            </div>
            <div id="first-run-message" style="min-height:18px;margin:12px 0;color:#dc2626;font-size:12px;">${escapeHtml(message)}</div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;">
                <button type="submit" class="btn btn-primary" style="width:auto;"><i class="fas fa-save"></i> Simpan Setup</button>
                <button type="button" id="first-run-demo" class="btn btn-secondary" style="width:auto;"><i class="fas fa-magic"></i> Isi Data Contoh</button>
            </div>
        </form>
    `;
    return overlay;
}
async function showFirstRunWizard(settings = {}) {
    renderFirstRunWizard();
    const form = document.getElementById('first-run-form');
    const message = document.getElementById('first-run-message');
    const saveSetup = async (skipped = false) => {
        const formData = new FormData();
        formData.set('skipped', skipped ? 'true' : 'false');
        formData.set('clinic_name', document.getElementById('first-clinic-name')?.value.trim() || '');
        formData.set('clinic_address', document.getElementById('first-clinic-address')?.value.trim() || '');
        formData.set('clinic_phone', document.getElementById('first-clinic-phone')?.value.trim() || '');
        formData.set('clinic_logo_path', document.getElementById('first-clinic-logo')?.value.trim() || '');
        formData.set('invoice_prefix', document.getElementById('first-invoice-prefix')?.value.trim() || 'INV');
        const inputs = [...document.querySelectorAll('.first-service-grid input')];
        const services = [];
        for (let index = 0; index < inputs.length; index += 3) {
            const name = inputs[index]?.value.trim();
            if (!name)
                continue;
            services.push({
                name,
                unit_label: inputs[index + 1]?.value.trim() || 'sesi',
                default_quantity: 1,
                price_per_unit: Number(inputs[index + 2]?.value || 0),
            });
        }
        formData.set('services', JSON.stringify(services));
        const response = await fetch('/first_run/complete', { method: 'POST', body: formData });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success')
            throw new Error(data.detail || 'Gagal menyimpan setup awal.');
        document.getElementById('first-run-overlay')?.remove();
        showToast(data.message || 'Setup awal berhasil disimpan.', 'success');
        await loadClinicSettings();
        return true;
    };
    return await new Promise((resolve) => {
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            try {
                resolve(await saveSetup(false));
            }
            catch (error) {
                message.textContent = error.message;
            }
        });
        document.getElementById('first-run-skip')?.addEventListener('click', async () => {
            const ok = await showConfirm('Lewati setup awal? Data klinik masih memakai nilai default.', 'warning');
            if (!ok)
                return;
            try {
                resolve(await saveSetup(true));
            }
            catch (error) {
                message.textContent = error.message;
            }
        });
        document.getElementById('first-run-demo')?.addEventListener('click', async () => {
            const ok = await showConfirm('Data contoh akan bercampur dengan data yang sudah ada. Lanjutkan?', 'warning');
            if (!ok)
                return;
            try {
                const response = await fetch('/demo_data/seed', { method: 'POST' });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || data.status !== 'success')
                    throw new Error(data.detail || 'Gagal mengisi data contoh.');
                showToast(data.message || 'Data contoh berhasil ditambahkan.', 'success');
            }
            catch (error) {
                message.textContent = error.message;
            }
        });
    });
}
function setupAdminIdleLock() {
    if (!adminIdleListenersReady) {
        ['click', 'keydown', 'mousemove', 'touchstart'].forEach((eventName) => {
            document.addEventListener(eventName, resetAdminIdleTimer, { passive: true });
        });
        adminIdleListenersReady = true;
    }
    resetAdminIdleTimer();
}
function resetAdminIdleTimer() {
    if (!window._adminUnlocked)
        return;
    if (adminIdleTimer)
        clearTimeout(adminIdleTimer);
    adminIdleTimer = setTimeout(lockAdminSession, ADMIN_IDLE_LOCK_MS);
}
function lockAdminSession() {
    window._adminPin = '';
    window._adminUnlocked = false;
    if (adminIdleTimer)
        clearTimeout(adminIdleTimer);
    adminIdleTimer = null;
    ensureAdminUnlocked('Sesi terkunci karena tidak ada aktivitas. Masukkan PIN untuk lanjut.');
}
function renderAdminLock(message = '') {
    let overlay = document.getElementById('admin-lock-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'admin-lock-overlay';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:100000;background:var(--color-bg);display:grid;place-items:center;font-family:Inter,Arial,sans-serif;overflow:auto;padding:18px;box-sizing:border-box;';
        document.body.appendChild(overlay);
    }
    overlay.innerHTML = `
        <div id="admin-lock-panel" class="runtime-modal-panel" style="width:min(420px,calc(100vw - 36px));background:var(--color-surface);color:var(--color-text);border:1px solid var(--color-border);border-radius:12px;box-shadow:0 24px 70px rgba(15,23,42,.14);padding:24px;box-sizing:border-box;">
            <form id="admin-lock-form">
                <div style="width:46px;height:46px;border-radius:10px;background:#ecfdf5;color:#047857;display:grid;place-items:center;margin-bottom:16px;">
                    <i class="fas fa-lock"></i>
                </div>
                <h1 id="admin-lock-title" style="font-size:20px;line-height:1.25;margin:0 0 8px;color:var(--color-text);">Masukkan PIN Admin</h1>
                <p id="admin-lock-copy" style="margin:0 0 18px;color:var(--color-text-muted);font-size:13px;line-height:1.5;">PIN diperlukan untuk membuka dashboard dan menjalankan aksi sensitif.</p>
                <label style="display:block;font-size:12px;font-weight:700;color:var(--color-text-muted);margin-bottom:6px;">PIN Admin</label>
                <input id="admin-lock-pin" type="password" inputmode="numeric" pattern="[0-9]*" autocomplete="current-password" required style="width:100%;box-sizing:border-box;border:1px solid var(--color-border);border-radius:8px;padding:11px 12px;font-size:20px;letter-spacing:7px;text-align:center;">
                <div id="admin-lock-confirm-wrap" style="display:none;margin-top:10px;">
                    <label style="display:block;font-size:12px;font-weight:700;color:var(--color-text-muted);margin-bottom:6px;">Ulangi PIN</label>
                    <input id="admin-lock-confirm" type="password" inputmode="numeric" pattern="[0-9]*" autocomplete="new-password" style="width:100%;box-sizing:border-box;border:1px solid var(--color-border);border-radius:8px;padding:11px 12px;font-size:20px;letter-spacing:7px;text-align:center;">
                </div>
                <div id="admin-lock-message" style="min-height:18px;margin:10px 0;color:#dc2626;font-size:12px;">${escapeHtml(message)}</div>
                <button type="submit" id="admin-lock-submit" class="btn btn-primary" style="width:100%;justify-content:center;">
                    <i class="fas fa-unlock"></i> Lanjut
                </button>
            </form>
            <div id="admin-lock-reset-box" style="display:none;margin-top:16px;padding-top:16px;border-top:1px solid var(--color-border);">
                <div style="display:grid;grid-template-columns:28px 1fr;gap:10px;align-items:start;margin-bottom:12px;">
                    <span style="width:28px;height:28px;border-radius:8px;background:#ecfeff;color:#0e7490;display:grid;place-items:center;"><i class="fas fa-life-ring"></i></span>
                    <div>
                        <strong id="admin-lock-reset-title" style="display:block;font-size:13px;line-height:1.3;color:var(--color-text);">Lupa PIN?</strong>
                        <span id="admin-lock-reset-copy" style="display:block;color:var(--color-text-muted);font-size:12px;line-height:1.45;margin-top:2px;">Minta kode reset dari pusat lisensi, lalu buat PIN admin baru di komputer ini.</span>
                    </div>
                </div>
                <button type="button" id="admin-lock-reset-request" class="btn btn-secondary" style="width:100%;justify-content:center;">
                    <i class="fas fa-paper-plane"></i> Minta Kode Reset
                </button>
                <form id="admin-lock-reset-form" style="display:none;margin-top:12px;">
                    <label style="display:block;font-size:12px;font-weight:700;color:#334155;margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em;">Kode Reset Lisensi</label>
                    <input id="admin-lock-reset-token" type="text" inputmode="numeric" autocomplete="one-time-code" required style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:11px 12px;font-size:14px;margin-bottom:10px;">
                    <label style="display:block;font-size:12px;font-weight:700;color:#334155;margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em;">PIN Admin Baru</label>
                    <input id="admin-lock-reset-new-pin" type="password" inputmode="numeric" pattern="[0-9]*" autocomplete="new-password" required style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:11px 12px;font-size:18px;letter-spacing:6px;text-align:center;">
                    <small style="display:block;color:#64748b;font-size:11px;line-height:1.35;margin:5px 0 12px;">PIN tetap tersimpan di komputer ini. Pusat lisensi hanya memberi izin reset.</small>
                    <label style="display:block;font-size:12px;font-weight:700;color:#334155;margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em;">Konfirmasi PIN Baru</label>
                    <input id="admin-lock-reset-confirm-pin" type="password" inputmode="numeric" pattern="[0-9]*" autocomplete="new-password" required style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:11px 12px;font-size:18px;letter-spacing:6px;text-align:center;">
                    <button type="submit" id="admin-lock-reset-submit" class="btn btn-primary" style="width:100%;justify-content:center;margin-top:14px;">
                        <i class="fas fa-rotate"></i> Reset PIN Admin
                    </button>
                </form>
                <div id="admin-lock-reset-message" style="min-height:18px;margin-top:10px;color:#dc2626;font-size:12px;line-height:1.45;"></div>
            </div>
        </div>
    `;
    return overlay;
}
async function ensureAdminUnlocked(initialMessage = '') {
    try {
        const statusResponse = await appFetchRaw('/admin_pin/status');
        const status = await statusResponse.json();
        const pinSet = !!status.pin_set;
        renderAdminLock(initialMessage);
        const title = document.getElementById('admin-lock-title');
        const copy = document.getElementById('admin-lock-copy');
        const confirmWrap = document.getElementById('admin-lock-confirm-wrap');
        const pinInput = document.getElementById('admin-lock-pin');
        const form = document.getElementById('admin-lock-form');
        const resetBox = document.getElementById('admin-lock-reset-box');
        const resetRequestButton = document.getElementById('admin-lock-reset-request');
        const resetForm = document.getElementById('admin-lock-reset-form');
        const resetMessage = document.getElementById('admin-lock-reset-message');
        const resetTitle = document.getElementById('admin-lock-reset-title');
        const resetCopy = document.getElementById('admin-lock-reset-copy');
        if (!pinSet) {
            title.textContent = 'Buat PIN Admin';
            copy.textContent = 'Buat PIN 4-8 digit untuk mengamankan restore, hapus data, koreksi stok, dan pengaturan.';
            confirmWrap.style.display = 'block';
            pinInput.autocomplete = 'new-password';
        }
        else if (resetBox) {
            resetBox.style.display = 'block';
        }
        pinInput.focus();
        return await new Promise((resolve) => {
            form.addEventListener('submit', async (event) => {
                event.preventDefault();
                const message = document.getElementById('admin-lock-message');
                const submit = document.getElementById('admin-lock-submit');
                const pin = pinInput.value.trim();
                const confirm = document.getElementById('admin-lock-confirm')?.value.trim() || '';
                if (!/^[0-9]{4,8}$/.test(pin)) {
                    message.textContent = 'PIN harus berisi 4-8 digit.';
                    return;
                }
                if (!pinSet && pin !== confirm) {
                    message.textContent = 'Konfirmasi PIN belum sama.';
                    return;
                }
                submit.disabled = true;
                submit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memeriksa...';
                try {
                    const formData = new FormData();
                    formData.set('pin', pin);
                    const endpoint = pinSet ? '/admin_pin/check' : '/admin_pin/set';
                    const response = await appFetchRaw(endpoint, { method: 'POST', body: formData });
                    const data = await response.json().catch(() => ({}));
                    if (!response.ok || data.status !== 'success') {
                        throw new Error(sanitizeAppErrorMessage(data.detail || 'PIN salah.', 'PIN salah.'));
                    }
                    window._adminPin = pin;
                    window._adminUnlocked = true;
                    document.getElementById('admin-lock-overlay')?.remove();
                    setupAdminIdleLock();
                    resolve(true);
                }
                catch (error) {
                    message.textContent = sanitizeAppErrorMessage(error.message, 'PIN salah.');
                    submit.disabled = false;
                    submit.innerHTML = '<i class="fas fa-unlock"></i> Lanjut';
                    pinInput.select();
                }
            });
            if (pinSet && resetRequestButton && resetForm && resetMessage) {
                resetRequestButton.addEventListener('click', async () => {
                    const originalText = resetRequestButton.innerHTML;
                    resetRequestButton.disabled = true;
                    resetRequestButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Mengirim...';
                    resetMessage.style.color = '#0f766e';
                    resetMessage.textContent = 'Menghubungi pusat lisensi untuk membuat permintaan reset...';
                    try {
                        const response = await appFetchRaw('/admin_pin/reset/request', { method: 'POST' });
                        const data = await response.json().catch(() => ({}));
                        if (!response.ok || data.status !== 'success') {
                            throw new Error(sanitizeAppErrorMessage(data.detail || 'Gagal meminta kode reset PIN.', 'Gagal meminta kode reset PIN.'));
                        }
                        const suffix = data.reset_request_id ? ` ID permintaan: ${data.reset_request_id}` : '';
                        resetMessage.style.color = '#0f766e';
                        resetMessage.textContent = `${data.message || 'Permintaan reset PIN dikirim.'}${suffix}`;
                        resetForm.dataset.resetReady = 'true';
                        form.style.display = 'none';
                        resetRequestButton.style.display = 'none';
                        resetBox.style.marginTop = '0';
                        resetBox.style.paddingTop = '0';
                        resetBox.style.borderTop = 'none';
                        if (resetTitle)
                            resetTitle.textContent = 'Reset PIN Admin';
                        if (resetCopy)
                            resetCopy.textContent = 'Masukkan kode reset dari pusat lisensi, lalu buat PIN admin baru.';
                        resetForm.style.display = 'block';
                        document.getElementById('admin-lock-reset-token')?.focus();
                    }
                    catch (error) {
                        resetMessage.style.color = '#dc2626';
                        resetMessage.textContent = sanitizeAppErrorMessage(error.message, 'Gagal meminta reset PIN.');
                    }
                    finally {
                        resetRequestButton.disabled = false;
                        resetRequestButton.innerHTML = originalText;
                    }
                });
                resetForm.addEventListener('submit', async (event) => {
                    event.preventDefault();
                    const resetSubmit = document.getElementById('admin-lock-reset-submit');
                    const resetReady = resetForm.dataset.resetReady === 'true';
                    const resetPin = document.getElementById('admin-lock-reset-token')?.value.trim() || '';
                    const newPin = document.getElementById('admin-lock-reset-new-pin')?.value.trim() || '';
                    const confirmPin = document.getElementById('admin-lock-reset-confirm-pin')?.value.trim() || '';
                    const originalText = resetSubmit ? resetSubmit.innerHTML : '';
                    if (!resetPin) {
                        resetMessage.style.color = '#dc2626';
                        resetMessage.textContent = 'Kode reset lisensi wajib diisi.';
                        return;
                    }
                    if (!resetReady) {
                        resetMessage.style.color = '#dc2626';
                        resetMessage.textContent = 'Kode reset belum siap. Klik Minta Kode Reset ulang.';
                        return;
                    }
                    if (!/^[0-9]{4,8}$/.test(newPin)) {
                        resetMessage.style.color = '#dc2626';
                        resetMessage.textContent = 'PIN admin baru harus berisi 4-8 digit angka.';
                        return;
                    }
                    if (newPin !== confirmPin) {
                        resetMessage.style.color = '#dc2626';
                        resetMessage.textContent = 'Konfirmasi PIN baru belum sama.';
                        return;
                    }
                    if (resetSubmit) {
                        resetSubmit.disabled = true;
                        resetSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Mereset PIN...';
                    }
                    try {
                        const formData = new FormData();
                        formData.set('reset_pin', resetPin);
                        formData.set('new_pin', newPin);
                        const response = await appFetchRaw('/admin_pin/reset/confirm', { method: 'POST', body: formData });
                        const data = await response.json().catch(() => ({}));
                        if (!response.ok || data.status !== 'success') {
                            throw new Error(sanitizeAppErrorMessage(data.detail || 'Kode reset tidak valid atau sudah kedaluwarsa.', 'Kode reset tidak valid atau sudah kedaluwarsa.'));
                        }
                        window._adminPin = newPin;
                        window._adminUnlocked = true;
                        document.getElementById('admin-lock-overlay')?.remove();
                        setupAdminIdleLock();
                        resolve(true);
                    }
                    catch (error) {
                        resetMessage.style.color = '#dc2626';
                        resetMessage.textContent = sanitizeAppErrorMessage(error.message, 'Gagal reset PIN admin.');
                    }
                    finally {
                        if (resetSubmit) {
                            resetSubmit.disabled = false;
                            resetSubmit.innerHTML = originalText;
                        }
                    }
                });
            }
        });
    }
    catch (error) {
        renderAdminLock('Gagal menyiapkan PIN admin. Restart aplikasi lalu coba lagi.');
        return false;
    }
}
async function loadClinicSettings() {
    try {
        const response = await fetch('/settings');
        if (!response.ok)
            throw new Error('Gagal memuat pengaturan klinik');
        const settings = await response.json();
        applyClinicSettings(settings);
    }
    catch (error) {
        applyClinicSettings({});
    }
}
function applyClinicSettings(settings) {
    const clinicName = (settings.clinic_name || 'Lancar Dynamic Admin').trim();
    const sidebarClinicName = document.getElementById('sidebar-clinic-name');
    window._clinicName = clinicName;
    window._clinicSettings = settings || {};
    document.title = `${clinicName} - Aplikasi Klinik`;
    if (sidebarClinicName) {
        sidebarClinicName.textContent = clinicName;
        sidebarClinicName.title = clinicName;
    }
}
async function loadLicenseStatus() {
    const indicator = document.getElementById('license-indicator');
    if (!indicator)
        return;
    try {
        const response = await fetch('/license_status');
        if (!response.ok)
            throw new Error('Gagal memuat status lisensi');
        const data = await response.json();
        const isValid = data.valid === true && data.status !== 'expired';
        const expiredText = data.expired_at ? formatLicenseDate(data.expired_at) : '-';
        const statusLabel = isValid ? 'Lisensi Aktif' : 'Lisensi Bermasalah';
        const keyText = data.license_key || 'Key belum tersedia';
        const expiryLabel = data.expired_at ? `Berlaku s/d ${expiredText}` : 'Masa berlaku tidak tersedia';
        const detail = [
            data.clinic_id ? `Clinic ID: ${data.clinic_id}` : '',
            `Key: ${keyText}`,
            data.expired_at ? `Expired: ${expiredText}` : ''
        ].filter(Boolean).join('\n');
        indicator.className = `license-indicator ${isValid ? 'active' : 'invalid'}`;
        indicator.title = detail || statusLabel;
        indicator.innerHTML = `
            <i class="fas ${isValid ? 'fa-shield-alt' : 'fa-exclamation-triangle'}"></i>
            <span class="license-text">
                <strong>${statusLabel}</strong>
                <small>${expiryLabel}</small>
            </span>
        `;
    }
    catch (error) {
        indicator.className = 'license-indicator invalid';
        indicator.title = error.message;
        indicator.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>Status lisensi gagal dimuat</span>
        `;
    }
}
function formatLicenseDate(value) {
    const text = String(value || '').trim();
    if (!text)
        return '-';
    if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
        const [year, month, day] = text.split('-').map(Number);
        return new Date(year, month - 1, day).toLocaleDateString('id-ID', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    }
    const date = new Date(text);
    if (Number.isNaN(date.getTime()))
        return value;
    return date.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}
// ── GLOBAL FORM INTERCEPTOR ──────────────────────────────────────────────────
// Prevent traditional form submissions that reload the page and reset the tab.
document.addEventListener('submit', async (e) => {
    if (e.defaultPrevented)
        return;
    const form = e.target;
    // Don't intercept if it's the import form (handled separately)
    if (form.id === 'import-form')
        return;
    // Only intercept POST forms
    if (form.method && form.method.toUpperCase() === 'POST') {
        e.preventDefault();
        const isVisitSubmit = form.action && form.action.endsWith('/add_visit');
        let preparedFormData = null;
        let visitRestorePatientId = null;
        if (isVisitSubmit && typeof confirmVisitSubmission === 'function') {
            preparedFormData = await confirmVisitSubmission(form);
            if (!preparedFormData)
                return;
            visitRestorePatientId = preparedFormData.get('patient_id') || document.getElementById('visit_patient_id')?.value || null;
        }
        // Find submit button to show loading state
        const btn = form.querySelector('button[type="submit"]');
        const originalText = btn ? btn.innerHTML : '';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memproses...';
        }
        try {
            const formData = preparedFormData || new FormData(form);
            const res = await fetch(form.action, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.status === 'success') {
                if (form.id === 'settings-form') {
                    await loadClinicSettings();
                }
                // Reload current active tab
                const activeTab = document.querySelector('.nav-links li.active');
                if (activeTab) {
                    const tabName = activeTab.getAttribute('data-tab');
                    await loadTab(tabName);
                    if (isVisitSubmit && tabName === 'visits' && visitRestorePatientId && typeof _dtShowVisits === 'function') {
                        await _dtShowVisits(Number(visitRestorePatientId));
                    }
                }
            }
            else {
                showToast(data.detail || 'Terjadi kesalahan saat menyimpan data.', 'error');
            }
        }
        catch (error) {
            showToast(sanitizeAppErrorMessage(error.message, 'Terjadi kesalahan saat menyimpan data.'), 'error');
        }
        finally {
            if (isVisitSubmit && typeof resetVisitSubmitLoading === 'function') {
                resetVisitSubmitLoading();
            }
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }
    }
});
function updatePageHeader(target) {
    const title = document.getElementById('page-title');
    const subtitle = title.nextElementSibling;
    const breadcrumb = document.getElementById('breadcrumb');
    const headers = {
        dashboard: ['Dashboard', 'Ringkasan Klinik & Aktivitas Hari Ini'],
        patients: ['Manajemen Pasien', 'Data Registrasi & Direktori'],
        visits: ['Kunjungan Pasien', 'Pencatatan Kunjungan & Riwayat Terapi'],
        therapists: ['Direktori Terapis', 'Data Terapis & Spesialisasi'],
        services: ['Layanan Terapi', 'Kelola jenis layanan dan harga default'],
        inventory: ['Inventori Alat Kesehatan', 'Pemantauan Stok Alat Medis'],
        herbals: ['Produk / Herbal', 'Monitor Sisa Stok & Harga'],
        analytics: ['Analitik Klinik', 'Ringkasan Performa & Tagihan'],
        'owner-report': ['Laporan Owner', 'Ringkasan bisnis klinik dan performa pasien'],
        audit: ['Log Aktivitas', 'Riwayat perubahan dan aksi penting'],
        crm: ['Follow-up Pasien', 'Kategori pasien, WhatsApp, dan hasil follow-up'],
        'whatsapp-gateway': ['WhatsApp Klinik', 'Login WhatsApp, cek akun, dan kirim follow-up'],
        invoices: ['Manajemen Transaksi', 'Rekaman Tagihan Kunjungan & Penjualan Produk / Herbal'],
        vouchers: ['Voucher & Diskon', 'Kelola voucher, rule kunjungan, dan simulasi harga akhir'],
        settings: ['Pengaturan Sistem', 'Konfigurasi Klinik, Lisensi & Ekspor Data'],
        help: ['Bantuan', 'Panduan cepat, folder data, dan kontak bantuan'],
    };
    const [t, s] = headers[target] || ['', ''];
    title.textContent = t;
    subtitle.textContent = s;
    if (breadcrumb) {
        const group = {
            dashboard: 'Operasional',
            patients: 'Operasional',
            visits: 'Operasional',
            therapists: 'Operasional',
            services: 'Operasional',
            inventory: 'Operasional',
            herbals: 'Operasional',
            invoices: 'Operasional',
            crm: 'Komunikasi',
            'whatsapp-gateway': 'Komunikasi',
            analytics: 'Analisis',
            'owner-report': 'Analisis',
            vouchers: 'Analisis',
            audit: 'Sistem',
            settings: 'Sistem',
            help: 'Sistem',
        }[target] || 'Workspace';
        breadcrumb.innerHTML = `<span>${group}</span><i class="fas fa-chevron-right"></i><strong>${t}</strong>`;
    }
}
async function loadTab(tabName) {
    const loadId = ++tabLoadSequence;
    window._activeTabName = tabName;
    const displayArea = document.getElementById('display-area');
    const loader = document.getElementById('loader');
    let loadingTimer = null;
    // Destroy existing DataTable instance if navigating away from patient-backed tabs
    if (window._patientsDT && tabName !== 'patients' && tabName !== 'visits') {
        try {
            window._patientsDT.destroy();
        }
        catch (e) { }
        window._patientsDT = null;
    }
    displayArea.classList.remove('hidden');
    displayArea.style.display = 'block';
    loadingTimer = window.setTimeout(() => {
        if (loadId !== tabLoadSequence)
            return;
        displayArea.classList.add('is-tab-loading');
        displayArea.innerHTML = renderTabSkeleton(tabName);
        loader.style.display = 'flex';
    }, 180);
    await nextFrame();
    if (loadId !== tabLoadSequence)
        return;
    try {
        if (tabName === 'dashboard') {
            await renderDashboard();
        }
        else if (tabName === 'patients') {
            // Patients tab uses server-side DataTable — render layout first, then DT fetches
            await renderPatients();
        }
        else if (tabName === 'visits') {
            await renderVisits();
        }
        else if (tabName === 'crm') {
            await renderCRM();
        }
        else if (tabName === 'whatsapp-gateway') {
            await renderWhatsAppGateway();
        }
        else if (tabName === 'owner-report') {
            await renderOwnerReport();
        }
        else if (tabName === 'audit') {
            await renderAuditLogs();
        }
        else if (tabName === 'help') {
            await renderHelp();
        }
        else if (tabName === 'vouchers') {
            renderVouchers();
        }
        else {
            let endpoint = '/' + tabName;
            if (tabName === 'analytics') {
                const period = window._analyticsPeriod || '6m';
                endpoint += '?period=' + period;
            }
            else if (tabName === 'invoices') {
                const period = window._invoicesPeriod || 'all';
                const page = window._invoicesPage || 1;
                const search = window._invoicesSearch || '';
                endpoint += `?period=${period}&page=${page}&page_size=100&search=${encodeURIComponent(search)}`;
            }
            const response = await fetch(endpoint);
            if (loadId !== tabLoadSequence)
                return;
            if (!response.ok)
                throw new Error('Network response was not ok');
            const data = await response.json();
            if (loadId !== tabLoadSequence)
                return;
            if (tabName === 'therapists')
                renderTherapists(data);
            else if (tabName === 'services')
                renderServices(data);
            else if (tabName === 'inventory')
                renderInventory(data);
            else if (tabName === 'herbals')
                renderHerbals(data);
            else if (tabName === 'analytics')
                renderAnalytics(data);
            else if (tabName === 'invoices')
                renderInvoices(data);
            else if (tabName === 'settings')
                renderSettings(data);
        }
        if (loadId !== tabLoadSequence)
            return;
        if (loadingTimer !== null)
            window.clearTimeout(loadingTimer);
        loader.style.display = 'none';
        displayArea.classList.remove('is-tab-loading');
        displayArea.classList.remove('hidden');
        displayArea.style.display = 'block';
    }
    catch (e) {
        if (loadId !== tabLoadSequence)
            return;
        if (loadingTimer !== null)
            window.clearTimeout(loadingTimer);
        loader.style.display = 'none';
        displayArea.classList.remove('is-tab-loading');
        displayArea.classList.remove('hidden');
        displayArea.style.display = 'block';
        displayArea.innerHTML = `
            <div class="card" style="border-left: 5px solid var(--danger);">
                <h3 style="color: var(--danger);"><i class="fas fa-exclamation-triangle"></i> Gagal Memuat Data</h3>
                <p style="margin-top: 10px;">${sanitizeAppErrorMessage(e.message)}</p>
            </div>
        `;
    }
}
function renderTabSkeleton(tabName = '') {
    const isVisit = tabName === 'visits';
    return `
        <div class="ui-skeleton-page ${isVisit ? 'is-visit' : ''}" aria-hidden="true">
            <div class="ui-skeleton-row">
                <div class="ui-skeleton-card"></div>
                <div class="ui-skeleton-card"></div>
                <div class="ui-skeleton-card"></div>
                <div class="ui-skeleton-card"></div>
            </div>
            <div class="ui-skeleton-layout">
                <div class="ui-skeleton-panel">
                    <span></span><span></span><span></span><span></span>
                </div>
                <div class="ui-skeleton-panel">
                    <span></span><span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;
}
