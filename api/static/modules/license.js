"use strict";
const licenseForm = /** @type {HTMLFormElement | null} */ (document.getElementById('license-form'));
const licenseMessage = document.getElementById('license-message');
const licenseStatus = document.getElementById('license-status');
const submitButton = /** @type {HTMLButtonElement | null} */ (document.getElementById('license-submit'));
const clinicInput = /** @type {HTMLInputElement | null} */ (document.getElementById('clinic-id'));
const keyInput = /** @type {HTMLInputElement | null} */ (document.getElementById('license-key'));
const metaClinicId = document.getElementById('meta-clinic-id');
const metaStatus = document.getElementById('meta-status');
const metaExpired = document.getElementById('meta-expired');
function setMessage(message, type = '') {
    if (!licenseMessage)
        return;
    licenseMessage.textContent = message || '';
    licenseMessage.className = `message ${type}`.trim();
}
function setStatus(message, type = '') {
    if (!licenseStatus)
        return;
    licenseStatus.innerHTML = message;
    licenseStatus.className = `status-box ${type}`.trim();
}
function escapeLicenseHtml(value) {
    return String(value || '').replace(/[&<>"']/g, (char) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
    }[char] || char));
}
function tokenHeaders() {
    const headers = new Headers();
    if (window._appToken) {
        headers.set('X-App-Token', window._appToken);
    }
    return headers;
}
function readError(payload, fallback) {
    if (!payload || typeof payload !== 'object')
        return fallback;
    return String(payload.detail || payload.message || fallback || '').trim();
}
function formatDate(value) {
    const text = String(value || '').trim();
    if (!text)
        return '-';
    const dateOnly = text.slice(0, 10);
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateOnly)) {
        const [year, month, day] = dateOnly.split('-').map(Number);
        return new Date(year, month - 1, day).toLocaleDateString('id-ID', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
        });
    }
    const parsed = new Date(text);
    if (Number.isNaN(parsed.getTime()))
        return text;
    return parsed.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: 'long',
        year: 'numeric',
    });
}
function renderSummary(data = {}) {
    const valid = data.valid === true && data.status !== 'expired' && data.verify_status !== 'invalid';
    const clinicId = data.clinic_id || '';
    const expiredAt = data.expired_at || '';
    const statusText = valid ? 'Aktif' : (data.status || data.verify_status || 'Belum valid');
    if (clinicInput && !clinicInput.value && clinicId) {
        clinicInput.value = clinicId;
    }
    if (metaClinicId)
        metaClinicId.textContent = clinicId || '-';
    if (metaStatus)
        metaStatus.textContent = statusText;
    if (metaExpired)
        metaExpired.textContent = formatDate(expiredAt);
    if (valid) {
        setStatus(`<i class="fas fa-check-circle"></i> Lisensi aktif. Dashboard akan dibuka...`, 'success');
        window.setTimeout(() => {
            window.location.replace('/');
        }, 900);
        return;
    }
    const message = data.message ? ` ${escapeLicenseHtml(data.message)}` : '';
    setStatus(`<i class="fas fa-exclamation-circle"></i> Lisensi belum aktif.${message}`, 'danger');
}
async function loadLicensePageStatus() {
    try {
        const response = await fetch('/license_status', {
            headers: tokenHeaders(),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(readError(data, 'Gagal memuat status lisensi.'));
        }
        renderSummary(data);
    }
    catch (error) {
        renderSummary(window._initialLicense || {});
        setMessage(error.message || 'Gagal memuat status lisensi.', 'error');
    }
}
async function submitLicense(event) {
    event.preventDefault();
    if (!licenseForm)
        return;
    setMessage('');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Memverifikasi...';
    }
    try {
        const response = await fetch('/license/activate', {
            method: 'POST',
            headers: tokenHeaders(),
            body: new FormData(licenseForm),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(readError(data, 'Lisensi tidak valid.'));
        }
        if (keyInput)
            keyInput.value = '';
        setMessage(data.message || 'Lisensi berhasil diaktifkan.', 'success');
        renderSummary(data.license || {});
    }
    catch (error) {
        setMessage(error.message || 'Lisensi tidak valid.', 'error');
        await loadLicensePageStatus();
    }
    finally {
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fas fa-check-circle"></i> Aktivasi Lisensi';
        }
    }
}
if (licenseForm) {
    licenseForm.addEventListener('submit', submitLicense);
}
loadLicensePageStatus();
