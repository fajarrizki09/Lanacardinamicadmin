"use strict";
let whatsappGatewayDelegationReady = false;
function ensureWhatsAppGatewayEventDelegation() {
    if (whatsappGatewayDelegationReady)
        return;
    whatsappGatewayDelegationReady = true;
    document.addEventListener('click', (event) => {
        const actionElement = event.target?.closest('[data-whatsapp-action]');
        if (!actionElement)
            return;
        const action = actionElement.dataset.whatsappAction || '';
        if (!action)
            return;
        event.preventDefault();
        if (action === 'open-browser')
            openWhatsAppWebBrowser();
    });
    document.addEventListener('submit', (event) => {
        const form = event.target;
        if (form?.dataset?.whatsappFormAction === 'send-test-link') {
            sendWhatsAppTestLink(event);
        }
    });
}
function openWhatsAppWebBrowser() {
    const url = 'https://web.whatsapp.com';
    window.open(url, '_blank');
    setWhatsAppResult(whatsappStatusRow('WhatsApp Web dibuka di browser. Pastikan akun WhatsApp sudah login di browser.', 'success'));
    setWhatsAppLoginPanel(`
        <div class="wa-profile-card is-idle">
            <div class="wa-profile-heading">
                <div>
                    <span class="wa-profile-eyebrow">Petunjuk</span>
                    <strong>WhatsApp Web</strong>
                </div>
            </div>
            <p class="wa-profile-guidance">
                1. Buka browser dan login ke WhatsApp Web (scan QR dari WhatsApp HP jika belum login).<br>
                2. Setelah login, kirim pesan follow-up pasien secara manual melalui browser.<br>
                3. Gunakan tombol di bawah untuk membuka obrolan percobaan ke nomor tujuan.
            </p>
        </div>
    `);
}
function sendWhatsAppTestLink(event) {
    event.preventDefault();
    const form = event.target;
    const phoneInput = form?.elements.namedItem('phone');
    const messageInput = form?.elements.namedItem('message');
    const phone = phoneInput ? phoneInput.value.trim() : '';
    const message = messageInput ? messageInput.value.trim() : 'Tes koneksi WhatsApp Lancar Dynamic Admin.';
    if (!phone) {
        setWhatsAppResult(whatsappStatusRow('Nomor WhatsApp tujuan wajib diisi.', 'error'));
        return;
    }
    const digits = phone.replace(/\D/g, '');
    const chatId = digits.startsWith('62') ? digits : '62' + digits.replace(/^0/, '');
    const url = `https://wa.me/${chatId}?text=${encodeURIComponent(message)}`;
    window.open(url, '_blank');
    setWhatsAppResult(whatsappStatusRow('Membuka obrolan WhatsApp di browser.', 'success'));
}
async function renderWhatsAppGateway() {
    ensureWhatsAppGatewayEventDelegation();
    const displayArea = document.getElementById('display-area');
    if (!displayArea)
        return;
    displayArea.innerHTML = `
        <div class="wa-gateway-container">
            <div class="card settings-whatsapp-card wa-card-green">
                <div class="card-header">
                    <h3><i class="fab fa-whatsapp wa-icon-green"></i> WhatsApp Klinik</h3>
                </div>
                <p class="settings-security-copy">
                    Buka WhatsApp Web di browser tempat akun WhatsApp sudah login. Kirim follow-up pasien secara manual melalui browser.
                </p>
                <div id="whatsapp-settings-result" class="wa-result-panel"></div>
                <div id="whatsapp-login-panel" class="wa-login-panel"></div>
                <div class="wa-actions-row">
                    <button type="button" class="btn btn-primary wa-btn-refresh" data-whatsapp-action="open-browser">
                        <i class="fas fa-external-link-alt"></i> Buka WhatsApp Web di Browser
                    </button>
                </div>
            </div>
            <div class="card wa-card-teal">
                <div class="card-header">
                    <h3><i class="fas fa-paper-plane wa-icon-teal"></i> Kirim Pesan Percobaan</h3>
                </div>
                <form id="whatsapp-test-form" data-whatsapp-form-action="send-test-link">
                    <div class="form-group">
                        <label>Nomor WhatsApp Tujuan</label>
                        <input type="text" name="phone" placeholder="081234567890" autocomplete="off">
                    </div>
                    <div class="form-group">
                        <label>Pesan Percobaan</label>
                        <textarea name="message" rows="3" class="wa-test-textarea" placeholder="Tes koneksi WhatsApp Lancar Dynamic Admin.">Tes koneksi WhatsApp Lancar Dynamic Admin.</textarea>
                    </div>
                    <button type="submit" class="btn btn-secondary wa-btn-send"><i class="fab fa-whatsapp"></i> Buka Obrolan di Browser</button>
                </form>
            </div>
        </div>
    `;
    setWhatsAppResult(whatsappStatusRow('Klik Buka WhatsApp Web di Browser untuk memulai.', 'info'));
    setWhatsAppLoginPanel(`
        <div class="wa-profile-card is-idle">
            <div class="wa-profile-heading">
                <div>
                    <span class="wa-profile-eyebrow">Status</span>
                    <strong>Siap digunakan</strong>
                </div>
            </div>
            <p class="wa-profile-guidance">Pastikan WhatsApp Web sudah login di browser sebelum mengirim pesan.</p>
        </div>
    `);
}
window.renderWhatsAppGateway = renderWhatsAppGateway;
