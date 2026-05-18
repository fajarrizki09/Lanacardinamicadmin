"use strict";
// ─── SETTINGS ─────────────────────────────────────────────────────────────────
function renderSettings(s, options = {}) {
    const onlyDiscount = options.onlyDiscount === true;
    const pricePerPoint = s.price_per_point ?? 10000;
    const basePrice = s.base_price ?? 100000;
    const paymentProvider = ['gateway_mock', 'midtrans'].includes(String(s.payment_gateway_default_provider || '').toLowerCase())
        ? String(s.payment_gateway_default_provider).toLowerCase()
        : 'gateway_mock';
    const paymentProviderRegistry = s.payment_gateway_provider_registry || {};
    const comingSoonProviders = Object.entries(paymentProviderRegistry)
        .filter(([, info]) => info.status === 'coming_soon')
        .map(([id, info]) => ({ id, label: info.display_name || id }));
    const comingSoonHtml = comingSoonProviders.length
        ? `<div class="settings-info-row" style="margin-bottom:14px;">
                <i class="fas fa-clock"></i>
                <span>Segera Hadir: ${comingSoonProviders.map(p => escapeHtml(p.label)).join(', ')}. Adapter belum tersedia, jadi belum bisa dipilih sebagai provider aktif.</span>
           </div>`
        : '';
    const html = `
        <div class="settings-compact-grid">
            <!-- Settings Form -->
            <div class="card settings-system-card" style="height:fit-content; border-top:3px solid var(--primary);">
                <div class="card-header">
                    <h3><i class="fas fa-sliders-h"></i> Konfigurasi Sistem</h3>
                </div>

                <div style="margin-bottom:18px;">
                    <form action="/settings" method="post" id="settings-form">
                        <input type="hidden" name="discount_percentage" value="0">
                        <input type="hidden" name="min_visits_for_discount" value="999999">
                        <input type="hidden" name="price_per_point" value="${pricePerPoint}">
                        <input type="hidden" name="base_price" value="${basePrice}">

                        <!-- Section: Klinik -->
                        <div class="settings-form-section" style="display:flex; align-items:center; gap:8px; margin:0 0 12px; padding:8px 12px; background:#f0fdf4; border-radius:8px; border-left:3px solid var(--success);">
                            <i class="fas fa-clinic-medical" style="color:var(--success);"></i>
                            <span style="font-size:12px; font-weight:700; color:var(--success); text-transform:uppercase; letter-spacing:0.5px;">Identitas Klinik</span>
                        </div>
                        <div class="form-group">
                            <label>Nama Klinik</label>
                            <input type="text" name="clinic_name" value="${escapeHtml(s.clinic_name || 'Lancar Dynamic Admin')}">
                        </div>
                        <div class="form-group">
                            <label>Tagline Klinik</label>
                            <input type="text" name="clinic_tagline" value="${escapeHtml(s.clinic_tagline || 'Clinic Management System')}">
                        </div>
                        <div class="form-group">
                            <label>Nomor Telepon</label>
                            <input type="text" name="clinic_phone" value="${escapeHtml(s.clinic_phone || '')}">
                        </div>
                        <div class="form-group">
                            <label>Email Klinik</label>
                            <input type="email" name="clinic_email" value="${escapeHtml(s.clinic_email || '')}">
                        </div>
                        <div class="form-group">
                            <label>Alamat Klinik</label>
                            <input type="text" name="clinic_address" value="${escapeHtml(s.clinic_address || '')}">
                        </div>
                        <div class="form-group">
                            <label>Website Klinik</label>
                            <input type="text" name="clinic_website" value="${escapeHtml(s.clinic_website || '')}">
                        </div>
                        <div class="form-group">
                            <label>Logo Klinik</label>
                            <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                                <input type="file" id="clinic-logo-file" accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp" onchange="uploadClinicLogo(this)" style="background:white; cursor:pointer; flex:1 1 210px;">
                                <button type="button" class="btn btn-secondary" onclick="clearClinicLogoPath()" style="width:auto;">
                                    <i class="fas fa-times"></i> Hapus
                                </button>
                            </div>
                            <input type="text" id="clinic-logo-path" name="clinic_logo_path" value="${escapeHtml(s.clinic_logo_path || '')}" placeholder="Path logo akan terisi setelah pilih file" style="margin-top:8px;">
                            <small class="settings-logo-help">Contoh: PNG/JPG/WebP, ideal 512x512 px atau rasio persegi, maksimal 2 MB. File akan disalin ke folder data aplikasi.</small>
                            <div id="clinic-logo-result" style="margin-top:8px;"></div>
                        </div>
                        <div class="form-group">
                            <label>Footer Invoice</label>
                            <input type="text" name="invoice_footer" value="${escapeHtml(s.invoice_footer || '')}">
                        </div>
                        <div class="form-group">
                            <label>Label Admin</label>
                            <input type="text" name="admin_label" value="${escapeHtml(s.admin_label || 'Admin Klinik,')}">
                        </div>
                        <div class="settings-form-section" style="display:flex; align-items:center; gap:8px; margin:18px 0 12px; padding:8px 12px; background:#eff6ff; border-radius:8px; border-left:3px solid #2563eb;">
                            <i class="fas fa-credit-card" style="color:#2563eb;"></i>
                            <span style="font-size:12px; font-weight:700; color:#1d4ed8; text-transform:uppercase; letter-spacing:0.5px;">Payment Gateway</span>
                        </div>
                        <div class="form-group">
                            <label class="activation-switch is-${s.payment_gateway_enabled ? 'on' : 'off'}" for="payment-gateway-enabled">
                                <input type="checkbox" id="payment-gateway-enabled" name="payment_gateway_enabled" value="true" ${s.payment_gateway_enabled ? 'checked' : ''}>
                                <span class="activation-track" aria-hidden="true"><span></span></span>
                                <span class="activation-copy">
                                    <strong>Gateway Pembayaran</strong>
                                    <small>Jika belum punya API key, biarkan nonaktif. Pembayaran manual tetap bisa dipakai.</small>
                                </span>
                            </label>
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                            <div class="form-group">
                                <label>Provider Default</label>
                                <select name="payment_gateway_default_provider">
                                    <option value="gateway_mock" ${paymentProvider === 'gateway_mock' ? 'selected' : ''}>Pembayaran Internal</option>
                                    <option value="midtrans" ${paymentProvider === 'midtrans' ? 'selected' : ''}>Midtrans</option>
                                </select>
                                <small class="settings-logo-help">Hanya provider dengan adapter aktif yang bisa dipilih. Provider Segera Hadir belum bisa disimpan sebagai provider aktif.</small>
                            </div>
                            <div class="form-group">
                                <label>Environment</label>
                                <select name="payment_gateway_environment">
                                    <option value="sandbox" ${(s.payment_gateway_environment || 'sandbox') === 'sandbox' ? 'selected' : ''}>Sandbox</option>
                                    <option value="production" ${s.payment_gateway_environment === 'production' ? 'selected' : ''}>Production</option>
                                </select>
                            </div>
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                            <div class="form-group">
                                <label>Midtrans Server Key</label>
                                <input type="password" name="midtrans_server_key" placeholder="Kosongkan jika belum tersedia" autocomplete="off">
                            </div>
                            <div class="form-group">
                                <label>Midtrans Client Key</label>
                                <input type="text" name="midtrans_client_key" value="${escapeHtml(s.midtrans_client_key || '')}" placeholder="Opsional">
                            </div>
                            <div class="form-group">
                                <label>Midtrans Merchant ID</label>
                                <input type="text" name="midtrans_merchant_id" value="${escapeHtml(s.midtrans_merchant_id || '')}" placeholder="Opsional">
                            </div>
                        </div>
                        <div class="settings-info-row" style="margin-bottom:14px;">
                            <i class="fas fa-info-circle"></i>
                            <span>Tanpa API key gateway, gunakan status Lunas, Belum Bayar, DP, Tunai, QRIS manual, atau Transfer dari form kunjungan. Gateway hanya diperlukan untuk membuat link pembayaran otomatis.</span>
                        </div>
                        ${comingSoonHtml}
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Simpan Semua Pengaturan
                        </button>
                    </form>
                </div>
            </div>

            <!-- Export & Import -->
            <div class="settings-card-stack" style="display:flex; flex-direction:column; gap:18px;">
                <div class="card settings-license-card" style="height:fit-content; border-top:3px solid #6366f1;">
                    <div class="card-header">
                        <h3><i class="fas fa-shield-alt" style="color:#6366f1;"></i> Lisensi Aplikasi</h3>
                    </div>
                    <div id="license-settings-status" style="padding:10px 12px; border-radius:8px; background:#f8fafc; border:1px solid #e2e8f0; color:var(--text-muted); font-size:13px; margin-bottom:14px;">
                        <i class="fas fa-spinner fa-spin"></i> Memuat status lisensi...
                    </div>
                    <form id="license-settings-form" onsubmit="submitLicenseActivation(event)">
                        <div class="form-group">
                            <label>Clinic ID</label>
                            <input type="text" id="license-clinic-id" name="clinic_id" placeholder="Clinic ID" required>
                        </div>
                        <div class="form-group">
                            <label>Kode Lisensi Baru</label>
                            <input type="password" id="license-key-input" name="license_key" placeholder="Tempel kode lisensi baru" required>
                        </div>
                        <button type="submit" class="btn btn-primary" style="background:linear-gradient(135deg,#6366f1,#4f46e5); box-shadow:0 4px 12px rgba(99,102,241,0.28);">
                            <i class="fas fa-key"></i> Aktivasi / Ganti Lisensi
                        </button>
                    </form>
                    <div id="license-settings-result" style="margin-top:12px;"></div>
                </div>

                <div class="card settings-security-card" style="height:fit-content; border-top:3px solid #0f766e;">
                    <div class="card-header">
                        <h3><i class="fas fa-user-shield" style="color:#0f766e;"></i> Keamanan Admin</h3>
                    </div>
                    <p class="settings-security-copy">
                        Ubah PIN lokal yang dipakai untuk membuka aplikasi dan menjalankan aksi sensitif.
                    </p>
                    <form id="admin-pin-change-form" class="admin-pin-change-form" onsubmit="submitAdminPinChange(event)">
                        <div class="form-group">
                            <label>PIN Lama</label>
                            <input type="password" id="admin-current-pin" name="current_pin" inputmode="numeric" pattern="[0-9]*" autocomplete="current-password" required>
                        </div>
                        <div class="form-group">
                            <label>PIN Baru</label>
                            <input type="password" id="admin-new-pin" name="new_pin" inputmode="numeric" pattern="[0-9]*" autocomplete="new-password" required>
                            <small class="settings-security-help">Gunakan 4-8 digit angka.</small>
                        </div>
                        <div class="form-group">
                            <label>Konfirmasi PIN Baru</label>
                            <input type="password" id="admin-confirm-pin" inputmode="numeric" pattern="[0-9]*" autocomplete="new-password" required>
                        </div>
                        <button type="submit" class="btn btn-primary" style="background:linear-gradient(135deg,#0f766e,#115e59); box-shadow:0 4px 12px rgba(15,118,110,0.26);">
                            <i class="fas fa-lock"></i> Ubah PIN Admin
                        </button>
                    </form>
                    <div id="admin-pin-change-result" style="margin-top:12px;"></div>
                    <div class="admin-pin-reset-box">
                        <div class="admin-pin-reset-heading">
                            <i class="fas fa-life-ring"></i>
                            <div>
                                <strong>Lupa PIN?</strong>
                                <span>Minta kode reset dari server lisensi, lalu buat PIN admin baru di komputer ini.</span>
                            </div>
                        </div>
                        <button type="button" id="admin-pin-reset-request-btn" class="btn btn-secondary" onclick="requestAdminPinReset()">
                            <i class="fas fa-paper-plane"></i> Minta Kode Reset
                        </button>
                        <form id="admin-pin-reset-form" class="admin-pin-change-form" onsubmit="submitAdminPinReset(event)">
                            <div class="form-group">
                                <label>Kode Reset Server Lisensi</label>
                                <input type="text" id="admin-reset-token" autocomplete="one-time-code" placeholder="Masukkan kode dari server lisensi" required>
                            </div>
                            <div class="form-group">
                                <label>PIN Admin Baru</label>
                                <input type="password" id="admin-reset-new-pin" inputmode="numeric" pattern="[0-9]*" autocomplete="new-password" required>
                                <small class="settings-security-help">PIN tetap disimpan lokal. Server lisensi hanya memberi izin reset.</small>
                            </div>
                            <div class="form-group">
                                <label>Konfirmasi PIN Baru</label>
                                <input type="password" id="admin-reset-confirm-pin" inputmode="numeric" pattern="[0-9]*" autocomplete="new-password" required>
                            </div>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-rotate"></i> Reset PIN Admin
                            </button>
                        </form>
                        <div id="admin-pin-reset-result" style="margin-top:12px;"></div>
                    </div>
                </div>

                <div class="card settings-demo-card" style="height:fit-content; border-top:3px solid #8b5cf6;">
                    <div class="card-header">
                        <h3><i class="fas fa-magic" style="color:#8b5cf6;"></i> Data Contoh</h3>
                    </div>
                    <p class="settings-security-copy">
                        Isi data demo untuk mencoba alur pasien, layanan, stok, dan kunjungan tanpa input manual.
                    </p>
                    <div style="display:flex;gap:10px;flex-wrap:wrap;">
                        <button type="button" class="btn btn-primary" onclick="seedDemoData()" style="width:auto;background:linear-gradient(135deg,#8b5cf6,#6d28d9);">
                            <i class="fas fa-magic"></i> Isi Data Contoh
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="clearDemoData()" style="width:auto;">
                            <i class="fas fa-broom"></i> Hapus Demo
                        </button>
                    </div>
                    <div id="demo-data-result" style="margin-top:12px;"></div>
                </div>

                <!-- Export -->
                <div class="card settings-export-card" style="height:fit-content; border-top:3px solid #10b981;">
                    <div class="card-header">
                        <h3><i class="fas fa-file-export" style="color:#10b981;"></i> Ekspor Data</h3>
                    </div>
                    <p style="color:var(--text-muted); font-size:13px; margin-bottom:16px; line-height:1.6;">
                        Ekspor data operasional untuk backup, pengecekan, atau migrasi manual.
                    </p>
                    <div id="settings-export-folder" class="settings-info-row" style="margin-bottom:12px;">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>Memuat lokasi folder export...</span>
                    </div>
                    <div class="form-group">
                        <label>Jenis Data</label>
                        <select id="settings-export-kind">
                            <option value="all">Semua Data Operasional</option>
                            <option value="patients">Pasien & Kunjungan</option>
                            <option value="herbals">Herbal & Transaksi Herbal</option>
                            <option value="inventory">Inventory & Transaksi Inventory</option>
                            <option value="audit_logs">Audit Log</option>
                        </select>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                        <button type="button"
                           id="settings-export-xlsx-btn"
                           onclick="exportSettingsData('xlsx')"
                           style="background:linear-gradient(135deg,#10b981,#059669); color:white; border:none; border-radius:8px; padding:11px 16px; font-weight:600; cursor:pointer; font-size:13px; text-decoration:none; text-align:center; display:flex; align-items:center; justify-content:center; gap:8px; box-shadow:0 4px 12px rgba(16,185,129,0.3); transition:all 0.2s;"
                           onmouseover="this.style.transform='translateY(-1px)'"
                           onmouseout="this.style.transform=''">
                            <i class="fas fa-file-excel"></i> Excel (.xlsx)
                        </button>
                        <button type="button"
                           id="settings-export-json-btn"
                           onclick="exportSettingsData('json')"
                           style="background:linear-gradient(135deg,#3b82f6,#6366f1); color:white; border:none; border-radius:8px; padding:11px 16px; font-weight:600; cursor:pointer; font-size:13px; text-decoration:none; text-align:center; display:flex; align-items:center; justify-content:center; gap:8px; box-shadow:0 4px 12px rgba(59,130,246,0.3); transition:all 0.2s;"
                           onmouseover="this.style.transform='translateY(-1px)'"
                           onmouseout="this.style.transform=''">
                            <i class="fas fa-file-code"></i> JSON
                        </button>
                    </div>
                    <button type="button" class="btn btn-secondary" onclick="openSettingsExportFolder()" style="width:auto;margin-top:10px;">
                        <i class="fas fa-folder-open"></i> Buka Folder Export
                    </button>
                    <div id="settings-export-result" style="margin-top:12px;"></div>
                </div>

                <!-- Import -->
                <div class="card settings-import-card" style="height:fit-content; border-top:3px solid var(--warning);">
                    <div class="card-header">
                        <h3><i class="fas fa-file-import" style="color:var(--warning);"></i> Impor Data</h3>
                    </div>
                    <div style="background:var(--warning-light); border:1px solid #fcd34d; border-radius:8px; padding:12px 14px; margin-bottom:16px; font-size:13px; color:#92400e; display:flex; gap:10px; align-items:flex-start;">
                        <i class="fas fa-exclamation-triangle" style="margin-top:2px; color:var(--warning); flex-shrink:0;"></i>
                        <span>Data baru akan digabung (merge) dengan data yang ada. Pasien dengan nomor HP sama tidak akan diduplikasi.</span>
                    </div>
                    <form id="import-form" onsubmit="submitImport(event)">
                        <div class="form-group">
                            <label>Pilih File JSON / Excel</label>
                            <input type="file" id="import-file" name="file" accept=".json,.xlsx,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" required style="background:white; cursor:pointer;">
                        </div>
                        <button type="submit" class="btn btn-primary" style="background:linear-gradient(135deg,#f59e0b,#ef4444); box-shadow:0 4px 12px rgba(245,158,11,0.35);">
                            <i class="fas fa-upload"></i> Impor Sekarang
                        </button>
                    </form>
                    <div id="import-result" style="margin-top:12px;"></div>
                </div>

                <!-- Backup Management -->
                <div class="card settings-backup-card" style="height:fit-content; border-top:3px solid #0ea5e9;">
                    <div class="card-header">
                        <h3><i class="fas fa-database" style="color:#0ea5e9;"></i> Manajemen Backup</h3>
                    </div>
                    <p style="color:var(--text-muted); font-size:13px; margin-bottom:14px; line-height:1.6;">
                        Buat backup database manual dan restore dari backup yang tersimpan.
                    </p>
                    <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:12px;">
                        <button type="button" class="btn btn-primary" onclick="createWebBackup()" style="width:auto; background:linear-gradient(135deg,#0ea5e9,#2563eb); box-shadow:0 4px 12px rgba(14,165,233,0.28);">
                            <i class="fas fa-plus"></i> Buat Backup
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="loadBackupManagement()" style="width:auto;">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                    </div>
                    <div id="backup-management-result"></div>
                    <div id="backup-management-list" class="backup-list">
                        <div class="settings-muted-row"><i class="fas fa-spinner fa-spin"></i> Memuat daftar backup...</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card discount-admin-card" style="margin-top:18px; border-top:3px solid #6366f1;">
            <div class="card-header" style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
                <div>
                    <h3><i class="fas fa-tags" style="color:#6366f1;"></i> Diskon & Voucher</h3>
                    <p class="discount-helper-text">Sistem hanya memakai 1 diskon per kunjungan: prioritas terkecil menang. Diskon kunjungan dihitung dari total riwayat pasien dan berlaku mulai kunjungan ke-N dan seterusnya.</p>
                </div>
                <button type="button" class="btn btn-secondary" onclick="resetDiscountRuleForm()" style="width:auto;">
                    <i class="fas fa-plus"></i> Baru
                </button>
            </div>
            <div class="discount-flow-strip">
                <div><strong>2 diskon cocok</strong><span>Yang dipakai hanya prioritas paling atas.</span></div>
                <div><strong>Diskon dimatikan</strong><span>Tidak berlaku untuk transaksi baru. Riwayat lama tetap tersimpan.</span></div>
                <div><strong>Diskon baru aktif</strong><span>Langsung ikut dihitung pada kunjungan berikutnya, jika nomor kunjungan sudah mencapai syarat.</span></div>
            </div>
            <div class="discount-admin-grid">
                <form id="discount-rule-form" class="discount-rule-form" onsubmit="submitDiscountRule(event)">
                <input type="hidden" id="discount-rule-id" name="rule_id" value="0">
                <div class="discount-type-picker" aria-label="Pilih tipe diskon">
                    <button type="button" data-type="visit_count" onclick="setDiscountRuleType('visit_count')"><i class="fas fa-redo"></i><span>Kunjungan</span></button>
                    <button type="button" data-type="voucher" onclick="setDiscountRuleType('voucher')"><i class="fas fa-ticket-alt"></i><span>Voucher</span></button>
                    <button type="button" data-type="period" onclick="setDiscountRuleType('period')"><i class="fas fa-calendar-alt"></i><span>Periode</span></button>
                    <button type="button" data-type="manual" onclick="setDiscountRuleType('manual')"><i class="fas fa-edit"></i><span>Harga Manual</span></button>
                </div>
                <div style="display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px;">
                    <div class="form-group">
                        <label>Nama Diskon</label>
                        <input type="text" id="discount-rule-name" name="name" placeholder="Promo Ramadhan" required>
                    </div>
                    <div class="form-group">
                        <label>Tipe</label>
                        <select id="discount-rule-type" name="type" required onchange="updateDiscountRuleTypeUI()">
                            <option value="visit_count">Jumlah Kunjungan</option>
                            <option value="voucher">Voucher</option>
                            <option value="manual">Manual</option>
                            <option value="period">Periode</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Jenis Diskon</label>
                        <select id="discount-rule-discount-type" name="discount_type" required>
                            <option value="percent">Persen</option>
                            <option value="fixed">Nominal</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Nilai Diskon</label>
                        <input type="number" id="discount-rule-value" name="discount_value" min="0" step="0.01" required>
                    </div>
                    <div class="form-group discount-field discount-field-condition">
                        <label id="discount-condition-label">Mulai Kunjungan Ke</label>
                        <input type="number" id="discount-rule-condition" name="condition_value" min="0" step="0.01" placeholder="Mis. kunjungan ke-5">
                        <small class="discount-input-help">Diskon berlaku pada kunjungan ke angka ini dan semua kunjungan setelahnya.</small>
                    </div>
                    <div class="form-group discount-field discount-field-voucher">
                        <label>Kode Voucher</label>
                        <input type="text" id="discount-rule-voucher" name="voucher_code" placeholder="SEHAT10">
                    </div>
                    <div class="form-group discount-field discount-field-voucher">
                        <label>Batas Total Pakai</label>
                        <input type="number" id="discount-rule-usage-limit" name="usage_limit" min="1" placeholder="Mis. 100">
                        <small class="discount-input-help">Kosongkan jika voucher tidak dibatasi total pemakaiannya.</small>
                    </div>
                    <div class="form-group discount-field discount-field-voucher">
                        <label>Batas per Pasien</label>
                        <input type="number" id="discount-rule-per-patient-limit" name="per_patient_limit" min="1" placeholder="Mis. 1">
                        <small class="discount-input-help">Isi 1 agar setiap pasien hanya bisa pakai sekali.</small>
                    </div>
                    <div class="form-group discount-field discount-field-voucher" style="grid-column:1 / -1;">
                        <label>Pasien Khusus</label>
                        <input type="hidden" id="discount-rule-target-patient-ids" name="target_patient_ids" value="">
                        <select id="discount-rule-target-patients" multiple size="6" onchange="syncDiscountTargetPatients()" style="min-height:130px;">
                            <option value="">Memuat daftar pasien...</option>
                        </select>
                        <small class="discount-input-help">Kosongkan jika voucher berlaku untuk semua pasien. Tahan Ctrl untuk memilih beberapa pasien.</small>
                    </div>
                    <div class="form-group discount-field discount-field-date">
                        <label>Mulai</label>
                        <input type="date" id="discount-rule-start" name="start_date" onchange="updateDiscountRuleTypeUI()">
                    </div>
                    <div class="form-group discount-field discount-field-date">
                        <label>Selesai</label>
                        <input type="date" id="discount-rule-end" name="end_date" onchange="updateDiscountRuleTypeUI()">
                    </div>
                    <div class="form-group">
                        <label>Prioritas</label>
                        <input type="number" id="discount-rule-priority" name="priority" value="100" min="0" required>
                        <small class="discount-input-help">Angka lebih kecil dipakai dulu saat beberapa diskon cocok.</small>
                    </div>
                    <div class="form-group activation-field">
                        <label>Status Aturan</label>
                        <label class="activation-switch is-on" id="discount-rule-active-control" for="discount-rule-active">
                            <input type="checkbox" id="discount-rule-active" checked onchange="syncDiscountActivationControl()">
                            <span class="activation-track" aria-hidden="true"><span></span></span>
                            <span class="activation-copy">
                                <strong id="discount-rule-active-title">Aktif</strong>
                                <small id="discount-rule-active-help">Diskon/voucher akan dihitung untuk transaksi baru.</small>
                            </span>
                        </label>
                    </div>
                </div>
                    <div class="discount-form-actions">
                        <button type="submit" class="btn btn-primary" style="width:auto;">
                            <i class="fas fa-save"></i> Simpan Diskon
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="runDiscountSimulation()" style="width:auto;">
                            <i class="fas fa-calculator"></i> Simulasi
                        </button>
                    </div>
                </form>
                <div class="discount-simulator">
                    <h4><i class="fas fa-flask"></i> Simulasi Diskon</h4>
                    <div class="form-group">
                        <label>Harga Kunjungan</label>
                        <input type="number" id="discount-sim-price" value="100000" min="0">
                    </div>
                    <div class="form-group">
                        <label>Jumlah Kunjungan Sebelumnya</label>
                        <input type="number" id="discount-sim-visits" value="4" min="0">
                        <small class="discount-input-help">Misalnya isi 4 untuk mengecek diskon pada kunjungan ke-5.</small>
                    </div>
                    <div class="form-group">
                        <label>Kode Voucher</label>
                        <input type="text" id="discount-sim-voucher" placeholder="Kosongkan jika tidak ada">
                    </div>
                    <label class="activation-switch compact" id="discount-sim-manual-control" for="discount-sim-manual">
                        <input type="checkbox" id="discount-sim-manual" onchange="syncManualSimulationControl()">
                        <span class="activation-track" aria-hidden="true"><span></span></span>
                        <span class="activation-copy">
                            <strong id="discount-sim-manual-title">Harga normal</strong>
                            <small id="discount-sim-manual-help">Simulasi memakai aturan diskon otomatis.</small>
                        </span>
                    </label>
                    <button type="button" class="btn btn-primary" onclick="runDiscountSimulation()">
                        <i class="fas fa-play"></i> Cek Simulasi
                    </button>
                    <div id="discount-simulation-result" class="discount-simulation-result">Isi simulasi untuk melihat diskon yang akan dipakai pada kunjungan berikutnya.</div>
                </div>
            </div>
            <div id="discount-rules-result" style="margin-bottom:12px;"></div>
            <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr style="background:#f8fafc; color:#475569; font-size:12px; text-transform:uppercase;">
                            <th style="padding:10px; text-align:left;">Nama</th>
                            <th style="padding:10px; text-align:left;">Tipe</th>
                            <th style="padding:10px; text-align:left;">Diskon</th>
                            <th style="padding:10px; text-align:left;">Kondisi</th>
                            <th style="padding:10px; text-align:left;">Periode</th>
                            <th style="padding:10px; text-align:left;">Status</th>
                            <th style="padding:10px; text-align:right;">Aksi</th>
                        </tr>
                    </thead>
                    <tbody id="discount-rules-body">
                        <tr><td colspan="7" style="padding:14px; color:var(--text-muted);">Memuat aturan diskon...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>`;
    const displayArea = document.getElementById('display-area');
    displayArea.innerHTML = html;
    const discountCard = displayArea.querySelector('.discount-admin-card');
    if (onlyDiscount) {
        if (discountCard) {
            displayArea.innerHTML = '';
            displayArea.appendChild(discountCard);
        }
        loadDiscountRules();
        loadDiscountPatientOptions();
        updateDiscountRuleTypeUI();
        syncDiscountActivationControl();
        syncManualSimulationControl();
        return;
    }
    if (discountCard)
        discountCard.remove();
    arrangeSettingsLayout();
    loadLicenseSettingsStatus();
    loadSettingsExportFolder();
    loadBackupManagement();
}
function renderVouchers() {
    renderSettings({}, { onlyDiscount: true });
    const displayArea = document.getElementById('display-area');
    const discountCard = displayArea?.querySelector('.discount-admin-card');
    if (!displayArea || !discountCard)
        return;
    discountCard.insertAdjacentHTML('beforebegin', `
        <div class="card free-visit-reasons-card" style="margin-bottom:18px; border-top:3px solid #10b981;">
            <div class="card-header" style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
                <div>
                    <h3><i class="fas fa-gift" style="color:#10b981;"></i> Promo Gratis</h3>
                    <p class="discount-helper-text">Daftar alasan yang muncul saat toggle Kunjungan Gratis aktif di form kunjungan.</p>
                </div>
                <button type="button" class="btn btn-secondary" onclick="resetFreeVisitReasons()" style="width:auto;">
                    <i class="fas fa-undo"></i> Default
                </button>
            </div>
            <form id="free-visit-reasons-form" onsubmit="submitFreeVisitReasons(event)">
                <div class="form-group">
                    <label>Alasan Kunjungan Gratis</label>
                    <textarea id="free-visit-reasons-input" name="reasons" rows="5" placeholder="Satu alasan per baris" style="width:100%; resize:vertical;"></textarea>
                    <small class="discount-input-help">Contoh: promo, keluarga, koreksi, garansi terapi. Satu baris menjadi satu pilihan.</small>
                </div>
                <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
                    <button type="submit" class="btn btn-primary" style="width:auto;">
                        <i class="fas fa-save"></i> Simpan Promo Gratis
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="loadFreeVisitReasons()" style="width:auto;">
                        <i class="fas fa-sync-alt"></i> Muat Ulang
                    </button>
                </div>
                <div id="free-visit-reasons-result" style="margin-top:12px;"></div>
            </form>
        </div>
    `);
    loadFreeVisitReasons();
}
async function loadDiscountPatientOptions(selectedIds = []) {
    const select = document.getElementById('discount-rule-target-patients');
    if (!select)
        return;
    const selectedSet = new Set((selectedIds || []).map(id => String(id)));
    try {
        const response = await fetch('/patients');
        const data = await response.json().catch(() => ({}));
        if (!response.ok)
            throw new Error(data.detail || 'Gagal memuat pasien.');
        const patients = Array.isArray(data.patients) ? data.patients : [];
        if (!patients.length) {
            select.innerHTML = '<option value="">Belum ada pasien.</option>';
            syncDiscountTargetPatients();
            return;
        }
        select.innerHTML = patients.map(patient => {
            const id = String(patient.id || '');
            const phone = patient.phone ? ` - ${patient.phone}` : '';
            return `<option value="${escapeHtml(id)}" ${selectedSet.has(id) ? 'selected' : ''}>${escapeHtml(patient.name || 'Pasien')}${escapeHtml(phone)}</option>`;
        }).join('');
        syncDiscountTargetPatients();
    }
    catch (error) {
        select.innerHTML = `<option value="">${escapeHtml(sanitizeAppErrorMessage(error.message, 'Gagal memuat pasien.'))}</option>`;
        syncDiscountTargetPatients();
    }
}
function syncDiscountTargetPatients() {
    const select = document.getElementById('discount-rule-target-patients');
    const hidden = document.getElementById('discount-rule-target-patient-ids');
    if (!select || !hidden)
        return;
    hidden.value = Array.from(select.selectedOptions || [])
        .map(option => option.value)
        .filter(Boolean)
        .join(',');
}
function defaultFreeVisitReasons() {
    return ['promo', 'keluarga', 'koreksi', 'gratis lain-lain'];
}
async function loadFreeVisitReasons() {
    const input = document.getElementById('free-visit-reasons-input');
    const result = document.getElementById('free-visit-reasons-result');
    if (!input)
        return;
    try {
        const response = await fetch('/free_visit_reasons');
        if (!response.ok)
            throw new Error('Gagal memuat alasan promo gratis.');
        const data = await response.json();
        const items = Array.isArray(data.items) && data.items.length ? data.items : defaultFreeVisitReasons();
        input.value = items.join('\n');
        if (result)
            result.innerHTML = '';
    }
    catch (error) {
        input.value = defaultFreeVisitReasons().join('\n');
        if (result) {
            result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#fef2f2; color:#dc2626; font-size:13px;">${escapeHtml(error.message)}</div>`;
        }
    }
}
function resetFreeVisitReasons() {
    const input = document.getElementById('free-visit-reasons-input');
    if (input)
        input.value = defaultFreeVisitReasons().join('\n');
}
async function submitFreeVisitReasons(event) {
    event.preventDefault();
    const input = document.getElementById('free-visit-reasons-input');
    const result = document.getElementById('free-visit-reasons-result');
    if (!input)
        return;
    const lines = input.value.split(/\r?\n/).map(item => item.trim()).filter(Boolean);
    if (!lines.length) {
        if (result)
            result.innerHTML = '<div style="padding:10px; border-radius:8px; background:#fef3c7; color:#92400e; font-size:13px;">Minimal isi satu alasan promo gratis.</div>';
        return;
    }
    const formData = new FormData();
    formData.set('reasons', lines.join('\n'));
    try {
        const response = await fetch('/free_visit_reasons', { method: 'POST', body: formData });
        const data = await response.json();
        if (!response.ok || data.status !== 'success')
            throw new Error(data.detail || 'Gagal menyimpan alasan promo gratis.');
        input.value = (data.items || lines).join('\n');
        if (result)
            result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#ecfdf5; color:#065f46; font-size:13px;">${escapeHtml(data.message)}</div>`;
        showToast(data.message, 'success');
    }
    catch (error) {
        if (result)
            result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#fef2f2; color:#dc2626; font-size:13px;">${escapeHtml(error.message)}</div>`;
        showToast(error.message, 'error');
    }
}
function arrangeSettingsLayout() {
    const root = document.querySelector('.settings-compact-grid');
    if (!root || root.querySelector('.settings-left-stack'))
        return;
    const systemCard = root.querySelector('.settings-system-card');
    const stack = root.querySelector('.settings-card-stack');
    const licenseCard = root.querySelector('.settings-license-card');
    const securityCard = root.querySelector('.settings-security-card');
    const demoCard = root.querySelector('.settings-demo-card');
    const exportCard = root.querySelector('.settings-export-card');
    const importCard = root.querySelector('.settings-import-card');
    const backupCard = root.querySelector('.settings-backup-card');
    if (!systemCard || !stack)
        return;
    const left = document.createElement('div');
    left.className = 'settings-left-stack';
    const right = document.createElement('div');
    right.className = 'settings-right-stack';
    left.appendChild(systemCard);
    if (exportCard)
        left.appendChild(exportCard);
    if (importCard)
        left.appendChild(importCard);
    if (licenseCard)
        right.appendChild(licenseCard);
    if (securityCard)
        right.appendChild(securityCard);
    if (demoCard)
        right.appendChild(demoCard);
    if (backupCard)
        right.appendChild(backupCard);
    root.replaceChildren(left, right);
}
async function uploadClinicLogo(input) {
    const result = document.getElementById('clinic-logo-result');
    const pathInput = document.getElementById('clinic-logo-path');
    const file = input?.files?.[0];
    if (!file)
        return;
    if (file.size > 2 * 1024 * 1024) {
        input.value = '';
        if (result)
            result.innerHTML = '<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>Ukuran logo maksimal 2 MB.</span></div>';
        showToast('Ukuran logo maksimal 2 MB.', 'error');
        return;
    }
    const allowedTypes = ['image/png', 'image/jpeg', 'image/webp'];
    const allowedExt = /\.(png|jpe?g|webp)$/i;
    if (!allowedTypes.includes(file.type) && !allowedExt.test(file.name || '')) {
        input.value = '';
        if (result)
            result.innerHTML = '<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>Format logo harus PNG, JPG, JPEG, atau WebP.</span></div>';
        showToast('Format logo harus PNG, JPG, JPEG, atau WebP.', 'error');
        return;
    }
    const formData = new FormData();
    formData.append('logo', file, file.name);
    if (result)
        result.innerHTML = '<div class="settings-info-row"><i class="fas fa-spinner fa-spin"></i><span>Menyimpan logo...</span></div>';
    try {
        const response = await fetch('/settings/logo', { method: 'POST', body: formData });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success')
            throw new Error(data.detail || 'Gagal menyimpan logo.');
        if (pathInput)
            pathInput.value = data.path || '';
        if (result)
            result.innerHTML = `<div class="settings-info-row success"><i class="fas fa-check-circle"></i><span>${escapeHtml(data.message || 'Logo klinik siap disimpan.')}</span></div>`;
        showToast('Logo klinik siap disimpan. Klik Simpan Semua Pengaturan.', 'success');
    }
    catch (error) {
        if (result)
            result.innerHTML = `<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>${escapeHtml(error.message || 'Gagal menyimpan logo.')}</span></div>`;
        showToast(error.message || 'Gagal menyimpan logo.', 'error');
    }
}
function clearClinicLogoPath() {
    const pathInput = document.getElementById('clinic-logo-path');
    const fileInput = document.getElementById('clinic-logo-file');
    const result = document.getElementById('clinic-logo-result');
    if (pathInput)
        pathInput.value = '';
    if (fileInput)
        fileInput.value = '';
    if (result)
        result.innerHTML = '<div class="settings-info-row"><i class="fas fa-info-circle"></i><span>Logo akan dikosongkan setelah pengaturan disimpan.</span></div>';
}
let discountRulesCache = [];
function setDiscountRuleType(type) {
    const typeSelect = document.getElementById('discount-rule-type');
    if (typeSelect)
        typeSelect.value = type;
    updateDiscountRuleTypeUI();
}
function updateDiscountRuleTypeUI() {
    const type = document.getElementById('discount-rule-type')?.value || 'visit_count';
    document.querySelectorAll('.discount-type-picker button').forEach(button => {
        button.classList.toggle('active', button.dataset.type === type);
    });
    document.querySelectorAll('.discount-field-condition').forEach(el => el.style.display = type === 'visit_count' ? '' : 'none');
    document.querySelectorAll('.discount-field-voucher').forEach(el => el.style.display = type === 'voucher' ? '' : 'none');
    document.querySelectorAll('.discount-field-date').forEach(el => el.style.display = type === 'period' ? '' : 'none');
    const condition = document.getElementById('discount-rule-condition');
    const voucher = document.getElementById('discount-rule-voucher');
    const usageLimit = document.getElementById('discount-rule-usage-limit');
    const perPatientLimit = document.getElementById('discount-rule-per-patient-limit');
    const start = document.getElementById('discount-rule-start');
    const end = document.getElementById('discount-rule-end');
    if (condition)
        condition.required = type === 'visit_count';
    if (voucher)
        voucher.required = type === 'voucher';
    if (usageLimit)
        usageLimit.required = false;
    if (perPatientLimit)
        perPatientLimit.required = false;
    if (start)
        start.required = type === 'period' && !end?.value;
    if (end)
        end.required = type === 'period' && !start?.value;
    const nameInput = document.getElementById('discount-rule-name');
    if (nameInput && !nameInput.value) {
        const names = {
            visit_count: 'Diskon kunjungan rutin',
            voucher: 'Voucher pasien',
            period: 'Promo periode',
            manual: 'Diskon harga manual',
        };
        nameInput.placeholder = names[type] || 'Nama diskon';
    }
}
function syncDiscountActivationControl() {
    const input = document.getElementById('discount-rule-active');
    const control = document.getElementById('discount-rule-active-control');
    const title = document.getElementById('discount-rule-active-title');
    const help = document.getElementById('discount-rule-active-help');
    const active = input ? input.checked : false;
    if (control) {
        control.classList.toggle('is-on', active);
        control.classList.toggle('is-off', !active);
    }
    if (title)
        title.textContent = active ? 'Aktif' : 'Nonaktif';
    if (help) {
        help.textContent = active
            ? 'Diskon/voucher akan dihitung untuk transaksi baru.'
            : 'Transaksi baru memakai harga normal sampai diaktifkan lagi.';
    }
}
function syncManualSimulationControl() {
    const input = document.getElementById('discount-sim-manual');
    const control = document.getElementById('discount-sim-manual-control');
    const title = document.getElementById('discount-sim-manual-title');
    const help = document.getElementById('discount-sim-manual-help');
    const active = input ? input.checked : false;
    if (control) {
        control.classList.toggle('is-on', active);
        control.classList.toggle('is-off', !active);
    }
    if (title)
        title.textContent = active ? 'Harga manual aktif' : 'Harga normal';
    if (help) {
        help.textContent = active
            ? 'Simulasi menganggap admin sudah mengubah harga manual.'
            : 'Simulasi memakai aturan diskon otomatis.';
    }
}
async function runDiscountSimulation() {
    const result = document.getElementById('discount-simulation-result');
    const params = new URLSearchParams({
        price: document.getElementById('discount-sim-price')?.value || '0',
        visit_count: document.getElementById('discount-sim-visits')?.value || '0',
        voucher_code: document.getElementById('discount-sim-voucher')?.value || '',
        manual_price_used: document.getElementById('discount-sim-manual')?.checked ? 'true' : 'false',
    });
    if (result)
        result.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menghitung simulasi...';
    try {
        const response = await fetch(`/discount_rules/simulate?${params.toString()}`);
        const data = await response.json();
        if (!response.ok)
            throw new Error(data.detail || 'Gagal menjalankan simulasi.');
        const selected = data.selected;
        const matches = data.matches || [];
        if (!selected) {
            result.innerHTML = `<div class="discount-sim-empty">${escapeHtml(data.message)}</div>`;
            return;
        }
        result.innerHTML = `
            <div class="discount-sim-selected">
                <span>Dipakai</span>
                <strong>${escapeHtml(selected.name)}</strong>
                <small>${formatDiscountRuleType(selected.type)} - hemat ${formatRupiah(selected.discount_amount)} - bayar ${formatRupiah(selected.final_price)}</small>
            </div>
            ${matches.length > 1 ? `<div class="discount-sim-conflict">${escapeHtml(data.message)} Cocok juga: ${matches.slice(1).map(item => escapeHtml(item.name)).join(', ')}</div>` : `<div class="discount-sim-note">${escapeHtml(data.message)}</div>`}
        `;
    }
    catch (error) {
        result.innerHTML = `<div class="settings-error-row">${escapeHtml(error.message)}</div>`;
    }
}
function formatBackupSize(bytes) {
    const value = Number(bytes || 0);
    if (value >= 1024 * 1024)
        return `${(value / (1024 * 1024)).toFixed(1)} MB`;
    if (value >= 1024)
        return `${(value / 1024).toFixed(1)} KB`;
    return `${value} B`;
}
function renderBackupManagement(data) {
    const list = document.getElementById('backup-management-list');
    const result = document.getElementById('backup-management-result');
    if (!list)
        return;
    const status = data.status || {};
    if (result && status.message) {
        result.innerHTML = `
            <div class="settings-info-row ${status.success ? 'success' : ''}">
                <i class="fas ${status.success ? 'fa-check-circle' : 'fa-info-circle'}"></i>
                <span>${escapeHtml(status.message)}</span>
            </div>`;
    }
    if (!data.items || !data.items.length) {
        list.innerHTML = '<div class="settings-muted-row">Belum ada file backup.</div>';
        return;
    }
    list.innerHTML = data.items.map(item => `
        <div class="backup-item">
            <div>
                <strong>${escapeHtml(item.name)}</strong>
                <span>${escapeHtml(item.modified_at)} - ${formatBackupSize(item.size)}</span>
            </div>
            <button type="button" onclick="restoreWebBackup('${escapeHtml(item.path)}')" title="Restore backup">
                <i class="fas fa-undo-alt"></i>
            </button>
        </div>
    `).join('');
}
async function loadBackupManagement() {
    const list = document.getElementById('backup-management-list');
    if (list)
        list.innerHTML = '<div class="settings-muted-row"><i class="fas fa-spinner fa-spin"></i> Memuat daftar backup...</div>';
    try {
        const response = await fetch('/backups');
        const data = await response.json();
        if (!response.ok)
            throw new Error(data.detail || 'Gagal memuat backup.');
        renderBackupManagement(data);
    }
    catch (error) {
        if (list)
            list.innerHTML = `<div class="settings-error-row">${escapeHtml(error.message)}</div>`;
    }
}
async function createWebBackup() {
    const result = document.getElementById('backup-management-result');
    if (result)
        result.innerHTML = '<div class="settings-info-row"><i class="fas fa-spinner fa-spin"></i><span>Membuat backup database...</span></div>';
    try {
        const response = await fetch('/backups/create', { method: 'POST' });
        const data = await response.json();
        if (!response.ok || data.status !== 'success')
            throw new Error(data.detail || 'Gagal membuat backup.');
        showToast(data.message || 'Backup berhasil dibuat.', 'success');
        await loadBackupManagement();
    }
    catch (error) {
        if (result)
            result.innerHTML = `<div class="settings-error-row">${escapeHtml(error.message)}</div>`;
    }
}
async function restoreWebBackup(path) {
    const ok = await showConfirm('Restore database dari backup ini? Database aktif akan dibuatkan backup pengaman terlebih dahulu.', 'warning');
    if (!ok)
        return;
    const result = document.getElementById('backup-management-result');
    if (result)
        result.innerHTML = '<div class="settings-info-row"><i class="fas fa-spinner fa-spin"></i><span>Restore backup...</span></div>';
    try {
        const formData = new FormData();
        formData.set('relative_path', path);
        const response = await fetch('/backups/restore', { method: 'POST', body: formData });
        const data = await response.json();
        if (!response.ok || data.status !== 'success')
            throw new Error(data.detail || 'Gagal restore backup.');
        showToast(data.message || 'Restore backup berhasil.', 'success');
        await loadBackupManagement();
    }
    catch (error) {
        if (result)
            result.innerHTML = `<div class="settings-error-row">${escapeHtml(error.message)}</div>`;
    }
}
function renderLicenseSettingsStatus(data) {
    const box = document.getElementById('license-settings-status');
    const clinicInput = document.getElementById('license-clinic-id');
    if (!box)
        return;
    const isValid = data && data.valid === true && data.status !== 'expired';
    const keyText = data && data.license_key ? data.license_key : 'Belum tersedia';
    const clinicId = data && data.clinic_id ? data.clinic_id : '';
    const expiredAt = data && data.expired_at ? formatLicenseSettingsDate(data.expired_at) : '-';
    const message = data && data.message ? data.message : '';
    if (clinicInput && !clinicInput.value)
        clinicInput.value = clinicId;
    box.style.background = isValid ? '#ecfdf5' : '#fef2f2';
    box.style.borderColor = isValid ? '#a7f3d0' : '#fecaca';
    box.style.color = isValid ? '#065f46' : '#991b1b';
    box.innerHTML = `
        <div style="display:flex; align-items:flex-start; gap:10px;">
            <i class="fas ${isValid ? 'fa-check-circle' : 'fa-exclamation-triangle'}" style="margin-top:2px;"></i>
            <div>
                <div style="font-weight:700;">${isValid ? 'Lisensi aktif' : 'Lisensi perlu diperiksa'}</div>
                <div style="margin-top:4px; line-height:1.45;">
                    Clinic ID: ${escapeHtml(clinicId || '-')}<br>
                    Key: ${escapeHtml(keyText)}<br>
                    Expired: ${escapeHtml(expiredAt)}
                    ${message ? `<br>${escapeHtml(message)}` : ''}
                </div>
            </div>
        </div>`;
}
function formatLicenseSettingsDate(value) {
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
        return text;
    return date.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}
async function loadLicenseSettingsStatus() {
    try {
        const response = await fetch('/license_status');
        const data = await response.json();
        if (!response.ok)
            throw new Error(data.detail || 'Gagal memuat status lisensi.');
        renderLicenseSettingsStatus(data);
    }
    catch (error) {
        renderLicenseSettingsStatus({ valid: false, message: error.message });
    }
}
async function submitLicenseActivation(event) {
    event.preventDefault();
    const form = event.target;
    const result = document.getElementById('license-settings-result');
    const button = form.querySelector('button[type="submit"]');
    const originalText = button ? button.innerHTML : '';
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memverifikasi...';
    }
    if (result) {
        result.innerHTML = '<div style="color:#4f46e5;font-size:13px;"><i class="fas fa-spinner fa-spin"></i> Menghubungi server lisensi...</div>';
    }
    try {
        const response = await fetch('/activate_license', {
            method: 'POST',
            body: new FormData(form),
        });
        const data = await response.json();
        if (!response.ok || data.status !== 'success')
            throw new Error(data.detail || 'Aktivasi lisensi gagal.');
        if (result) {
            result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#ecfdf5; color:#065f46; font-size:13px;">${escapeHtml(data.message)}</div>`;
        }
        document.getElementById('license-key-input').value = '';
        renderLicenseSettingsStatus(data.license || {});
        if (typeof loadLicenseStatus === 'function')
            await loadLicenseStatus();
    }
    catch (error) {
        if (result) {
            result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#fef2f2; color:#dc2626; font-size:13px;">${escapeHtml(error.message)}</div>`;
        }
        await loadLicenseSettingsStatus();
    }
    finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
}
async function submitAdminPinChange(event) {
    event.preventDefault();
    const form = event.target;
    const result = document.getElementById('admin-pin-change-result');
    const button = form.querySelector('button[type="submit"]');
    const originalText = button ? button.innerHTML : '';
    const currentPin = document.getElementById('admin-current-pin')?.value.trim() || '';
    const newPin = document.getElementById('admin-new-pin')?.value.trim() || '';
    const confirmPin = document.getElementById('admin-confirm-pin')?.value.trim() || '';
    const showPinResult = (message, type = 'error') => {
        if (!result)
            return;
        const ok = type === 'success';
        result.innerHTML = `
            <div class="${ok ? 'settings-info-row success' : 'settings-error-row'}">
                <i class="fas ${ok ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
                <span>${escapeHtml(message)}</span>
            </div>`;
    };
    if (!currentPin || !newPin || !confirmPin) {
        showPinResult('Semua field PIN wajib diisi.');
        return;
    }
    if (!/^[0-9]{4,8}$/.test(newPin)) {
        showPinResult('PIN baru harus berisi 4-8 digit angka.');
        return;
    }
    if (newPin !== confirmPin) {
        showPinResult('Konfirmasi PIN baru belum sama.');
        return;
    }
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Mengubah PIN...';
    }
    try {
        const formData = new FormData();
        formData.set('current_pin', currentPin);
        formData.set('new_pin', newPin);
        const response = await fetch('/admin_pin/change', { method: 'POST', body: formData });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') {
            const message = response.status === 403 ? 'PIN lama salah.' : (data.detail || 'Gagal mengubah PIN admin.');
            throw new Error(message);
        }
        window._adminPin = newPin;
        form.reset();
        showPinResult(data.message || 'PIN admin berhasil diubah.', 'success');
        showToast('PIN admin berhasil diubah.', 'success');
    }
    catch (error) {
        showPinResult(error.message || 'Gagal mengubah PIN admin.');
    }
    finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
}
function renderAdminPinResetResult(message, type = 'error') {
    const result = document.getElementById('admin-pin-reset-result');
    if (!result)
        return;
    const ok = type === 'success';
    result.innerHTML = `
        <div class="${ok ? 'settings-info-row success' : 'settings-error-row'}">
            <i class="fas ${ok ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${escapeHtml(message)}</span>
        </div>`;
}
async function requestAdminPinReset() {
    const button = document.getElementById('admin-pin-reset-request-btn');
    const originalText = button ? button.innerHTML : '';
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Mengirim...';
    }
    renderAdminPinResetResult('Menghubungi server lisensi untuk membuat permintaan reset...', 'success');
    try {
        const response = await fetch('/admin_pin/reset/request', { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') {
            throw new Error(data.detail || 'Gagal meminta kode reset PIN ke server lisensi.');
        }
        const suffix = data.reset_request_id ? ` ID permintaan: ${data.reset_request_id}` : '';
        const form = document.getElementById('admin-pin-reset-form');
        if (form)
            form.dataset.resetToken = data.reset_token || '';
        renderAdminPinResetResult(`${data.message || 'Permintaan reset PIN dikirim.'}${suffix}`, 'success');
        showToast('Permintaan reset PIN dikirim ke server lisensi.', 'success');
    }
    catch (error) {
        renderAdminPinResetResult(error.message || 'Gagal meminta reset PIN.');
    }
    finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
}
async function submitAdminPinReset(event) {
    event.preventDefault();
    const form = event.target;
    const button = form.querySelector('button[type="submit"]');
    const originalText = button ? button.innerHTML : '';
    const token = form.dataset.resetToken || '';
    const resetPin = document.getElementById('admin-reset-token')?.value.trim() || '';
    const newPin = document.getElementById('admin-reset-new-pin')?.value.trim() || '';
    const confirmPin = document.getElementById('admin-reset-confirm-pin')?.value.trim() || '';
    if (!resetPin) {
        renderAdminPinResetResult('Kode reset dari server lisensi wajib diisi.');
        return;
    }
    if (!token) {
        renderAdminPinResetResult('Token reset belum tersedia. Klik Minta Kode Reset ulang.');
        return;
    }
    if (!/^[0-9]{4,8}$/.test(newPin)) {
        renderAdminPinResetResult('PIN admin baru harus berisi 4-8 digit angka.');
        return;
    }
    if (newPin !== confirmPin) {
        renderAdminPinResetResult('Konfirmasi PIN baru belum sama.');
        return;
    }
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Mereset PIN...';
    }
    try {
        const formData = new FormData();
        formData.set('reset_token', token);
        formData.set('reset_pin', resetPin);
        formData.set('new_pin', newPin);
        const response = await fetch('/admin_pin/reset/confirm', { method: 'POST', body: formData });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') {
            throw new Error(data.detail || 'Kode reset tidak valid atau sudah kedaluwarsa.');
        }
        window._adminPin = newPin;
        window._adminUnlocked = true;
        form.reset();
        renderAdminPinResetResult(data.message || 'PIN admin berhasil direset.', 'success');
        showToast('PIN admin berhasil direset.', 'success');
    }
    catch (error) {
        renderAdminPinResetResult(error.message || 'Gagal reset PIN admin.');
    }
    finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
}
async function seedDemoData() {
    const result = document.getElementById('demo-data-result');
    const ok = await showConfirm('Data contoh akan bercampur dengan data asli jika database sudah berisi data. Lanjutkan?', 'warning');
    if (!ok)
        return;
    if (result)
        result.innerHTML = '<div class="settings-info-row"><i class="fas fa-spinner fa-spin"></i><span>Mengisi data contoh...</span></div>';
    try {
        const response = await fetch('/demo_data/seed', { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success')
            throw new Error(data.detail || 'Gagal mengisi data contoh.');
        if (result)
            result.innerHTML = `<div class="settings-info-row success"><i class="fas fa-check-circle"></i><span>${escapeHtml(data.message || 'Data contoh berhasil ditambahkan.')}</span></div>`;
        showToast(data.message || 'Data contoh berhasil ditambahkan.', 'success');
    }
    catch (error) {
        if (result)
            result.innerHTML = `<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>${escapeHtml(error.message)}</span></div>`;
    }
}
async function clearDemoData() {
    const result = document.getElementById('demo-data-result');
    const ok = await showConfirm('Hapus/nonaktifkan data demo yang dikenali sistem? Data asli tidak akan disentuh.', 'warning');
    if (!ok)
        return;
    if (result)
        result.innerHTML = '<div class="settings-info-row"><i class="fas fa-spinner fa-spin"></i><span>Menghapus data demo...</span></div>';
    try {
        const response = await fetch('/demo_data/clear', { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success')
            throw new Error(data.detail || 'Gagal menghapus data demo.');
        if (result)
            result.innerHTML = `<div class="settings-info-row success"><i class="fas fa-check-circle"></i><span>${escapeHtml(data.message || 'Data demo dihapus.')}</span></div>`;
        showToast(data.message || 'Data demo dihapus.', 'success');
    }
    catch (error) {
        if (result)
            result.innerHTML = `<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>${escapeHtml(error.message)}</span></div>`;
    }
}
async function exportSettingsData(format) {
    const safeFormat = format === 'json' ? 'json' : 'xlsx';
    const kind = document.getElementById('settings-export-kind')?.value || 'all';
    const button = document.getElementById(`settings-export-${safeFormat}-btn`);
    const result = document.getElementById('settings-export-result');
    const original = button ? button.innerHTML : '';
    const exportUrl = `/export/save?format=${safeFormat}&kind=${encodeURIComponent(kind)}`;
    try {
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyiapkan...';
        }
        if (result) {
            result.innerHTML = '<div class="settings-info-row"><i class="fas fa-spinner fa-spin"></i><span>Menyiapkan file export...</span></div>';
        }
        const response = await fetch(exportUrl);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.detail || 'Gagal export data.');
        }
        const message = safeFormat === 'json' ? 'Export JSON berhasil dibuat.' : 'Export Excel berhasil dibuat.';
        if (result) {
            result.innerHTML = `
                <div class="settings-info-row success">
                    <i class="fas fa-check-circle"></i>
                    <span>
                        ${escapeHtml(message)}<br>
                        <strong>${escapeHtml(data.filename || '')}</strong><br>
                        <small>${escapeHtml(data.path || '')}</small><br>
                        <button type="button" class="btn btn-secondary" onclick="openSettingsExportFolder()" style="width:auto;margin-top:8px;">
                            <i class="fas fa-folder-open"></i> Buka Folder
                        </button>
                    </span>
                </div>
            `;
        }
        showToast(message, 'success');
    }
    catch (error) {
        const message = sanitizeAppErrorMessage(error.message, 'Gagal export data.');
        if (result) {
            result.innerHTML = `<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>${escapeHtml(message)}</span></div>`;
        }
        showToast(message, 'error');
    }
    finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = original;
        }
    }
}
async function loadSettingsExportFolder() {
    const box = document.getElementById('settings-export-folder');
    if (!box)
        return;
    try {
        const response = await fetch('/support/app_info');
        const data = await response.json().catch(() => ({}));
        if (!response.ok)
            throw new Error(data.detail || 'Gagal memuat folder export.');
        box.innerHTML = `
            <i class="fas fa-folder"></i>
            <span>Folder export:<br><small>${escapeHtml(data.exports_dir || '-')}</small></span>
        `;
    }
    catch (error) {
        box.innerHTML = `<i class="fas fa-exclamation-circle"></i><span>${escapeHtml(sanitizeAppErrorMessage(error.message, 'Gagal memuat folder export.'))}</span>`;
        box.classList.add('settings-error-row');
    }
}
async function openSettingsExportFolder() {
    try {
        const response = await fetch('/support/open_folder?kind=exports', { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success')
            throw new Error(data.detail || 'Gagal membuka folder export.');
        showToast('Folder export dibuka.', 'success');
    }
    catch (error) {
        showToast(sanitizeAppErrorMessage(error.message, 'Gagal membuka folder export.'), 'error');
    }
}
function formatDiscountRuleType(value) {
    const labels = {
        visit_count: 'Jumlah Kunjungan',
        voucher: 'Voucher',
        manual: 'Manual',
        period: 'Periode'
    };
    return labels[value] || value || '-';
}
function formatDiscountRuleValue(rule) {
    if (rule.discount_type === 'percent')
        return `${Number(rule.discount_value || 0)}%`;
    return formatRupiah(Number(rule.discount_value || 0));
}
function formatDiscountRuleCondition(rule) {
    if (rule.type === 'visit_count')
        return rule.condition_value ? `Mulai kunjungan ke-${Number(rule.condition_value)} dan seterusnya` : '-';
    if (rule.type === 'voucher') {
        const used = Number(rule.usage_count || 0);
        const total = rule.usage_limit ? `${used}/${Number(rule.usage_limit)} kali` : `${used} kali`;
        const patient = rule.per_patient_limit ? `, max ${Number(rule.per_patient_limit)}x/pasien` : '';
        const targets = Array.isArray(rule.target_patient_names) && rule.target_patient_names.length
            ? ` - khusus: ${rule.target_patient_names.slice(0, 3).join(', ')}${rule.target_patient_names.length > 3 ? ' +' + (rule.target_patient_names.length - 3) : ''}`
            : '';
        return `${rule.voucher_code || '-'} - terpakai ${total}${patient}${targets}`;
    }
    if (rule.type === 'manual')
        return 'Harga manual';
    return 'Tanggal aktif';
}
function formatDiscountRulePeriod(rule) {
    const start = rule.start_date || '-';
    const end = rule.end_date || '-';
    if (start === '-' && end === '-')
        return '-';
    return `${start} s/d ${end}`;
}
async function loadDiscountRules() {
    const body = document.getElementById('discount-rules-body');
    if (!body)
        return;
    try {
        const response = await fetch('/discount_rules');
        if (!response.ok)
            throw new Error('Gagal memuat aturan diskon');
        discountRulesCache = await response.json();
        if (!discountRulesCache.length) {
            body.innerHTML = '<tr><td colspan="7" style="padding:14px; color:var(--text-muted);">Belum ada aturan diskon dinamis.</td></tr>';
            return;
        }
        body.innerHTML = discountRulesCache.map(rule => `
            <tr style="border-top:1px solid #e2e8f0; font-size:13px;">
                <td style="padding:10px;"><strong>${escapeHtml(rule.name)}</strong><br><span style="color:var(--text-muted);">Prioritas ${rule.priority}</span></td>
                <td style="padding:10px;">${formatDiscountRuleType(rule.type)}</td>
                <td style="padding:10px;">${formatDiscountRuleValue(rule)}</td>
                <td style="padding:10px;">${escapeHtml(formatDiscountRuleCondition(rule))}</td>
                <td style="padding:10px;">${escapeHtml(formatDiscountRulePeriod(rule))}</td>
                <td style="padding:10px;">
                    <button type="button" onclick="toggleDiscountRule(${rule.id}, ${!rule.is_active})"
                        class="activation-action ${rule.is_active ? 'is-on' : 'is-off'}"
                        title="${rule.is_active ? 'Klik untuk menonaktifkan diskon ini' : 'Klik untuk mengaktifkan diskon ini'}">
                        <i class="fas ${rule.is_active ? 'fa-toggle-on' : 'fa-toggle-off'}"></i>
                        <span>
                            <strong>${rule.is_active ? 'Aktif' : 'Nonaktif'}</strong>
                            <small>${rule.is_active ? 'Klik untuk matikan' : 'Klik untuk aktifkan'}</small>
                        </span>
                    </button>
                </td>
                <td style="padding:10px; text-align:right; white-space:nowrap;">
                    <button type="button" onclick="editDiscountRule(${rule.id})" title="Edit" style="border:none; background:#e0e7ff; color:#3730a3; border-radius:6px; padding:7px 9px; cursor:pointer;"><i class="fas fa-edit"></i></button>
                    <button type="button" onclick="deleteDiscountRule(${rule.id})" title="Hapus" style="border:none; background:#fee2e2; color:#991b1b; border-radius:6px; padding:7px 9px; cursor:pointer; margin-left:4px;"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('');
    }
    catch (error) {
        body.innerHTML = `<tr><td colspan="7" style="padding:14px; color:#dc2626;">${escapeHtml(error.message)}</td></tr>`;
    }
}
function resetDiscountRuleForm() {
    const form = document.getElementById('discount-rule-form');
    if (!form)
        return;
    form.reset();
    document.getElementById('discount-rule-id').value = '0';
    document.getElementById('discount-rule-priority').value = '100';
    document.getElementById('discount-rule-active').checked = true;
    loadDiscountPatientOptions([]);
    updateDiscountRuleTypeUI();
    syncDiscountActivationControl();
}
function editDiscountRule(ruleId) {
    const rule = discountRulesCache.find(item => item.id === ruleId);
    if (!rule)
        return;
    document.getElementById('discount-rule-id').value = rule.id;
    document.getElementById('discount-rule-name').value = rule.name || '';
    document.getElementById('discount-rule-type').value = rule.type || 'visit_count';
    document.getElementById('discount-rule-discount-type').value = rule.discount_type || 'percent';
    document.getElementById('discount-rule-value').value = rule.discount_value || 0;
    document.getElementById('discount-rule-condition').value = rule.condition_value || '';
    document.getElementById('discount-rule-voucher').value = rule.voucher_code || '';
    document.getElementById('discount-rule-usage-limit').value = rule.usage_limit || '';
    document.getElementById('discount-rule-per-patient-limit').value = rule.per_patient_limit || '';
    loadDiscountPatientOptions(rule.target_patient_ids || []);
    document.getElementById('discount-rule-start').value = rule.start_date || '';
    document.getElementById('discount-rule-end').value = rule.end_date || '';
    document.getElementById('discount-rule-priority').value = rule.priority || 100;
    document.getElementById('discount-rule-active').checked = !!rule.is_active;
    updateDiscountRuleTypeUI();
    syncDiscountActivationControl();
}
async function submitDiscountRule(event) {
    event.preventDefault();
    const form = event.target;
    const result = document.getElementById('discount-rules-result');
    syncDiscountTargetPatients();
    const formData = new FormData(form);
    formData.set('is_active', document.getElementById('discount-rule-active').checked ? 'true' : 'false');
    try {
        const response = await fetch('/discount_rules', { method: 'POST', body: formData });
        const data = await response.json();
        if (!response.ok || data.status !== 'success')
            throw new Error(data.detail || 'Gagal menyimpan aturan diskon.');
        result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#ecfdf5; color:#065f46; font-size:13px;">${escapeHtml(data.message)}</div>`;
        resetDiscountRuleForm();
        await loadDiscountRules();
    }
    catch (error) {
        result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#fef2f2; color:#dc2626; font-size:13px;">${escapeHtml(error.message)}</div>`;
    }
}
async function toggleDiscountRule(ruleId, isActive) {
    const formData = new FormData();
    formData.set('is_active', isActive ? 'true' : 'false');
    const response = await fetch(`/discount_rules/${ruleId}/toggle`, { method: 'POST', body: formData });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        showToast(data.detail || 'Gagal mengubah status aturan diskon.', 'error');
        return;
    }
    await loadDiscountRules();
}
async function deleteDiscountRule(ruleId) {
    const ok = await showConfirm('Hapus aturan diskon ini?', 'warning');
    if (!ok)
        return;
    const response = await fetch(`/discount_rules/${ruleId}/delete`, { method: 'POST' });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        showToast(data.detail || 'Gagal menghapus aturan diskon.', 'error');
        return;
    }
    await loadDiscountRules();
    resetDiscountRuleForm();
}
async function submitImport(event) {
    event.preventDefault();
    const fileInput = document.getElementById('import-file');
    const resultDiv = document.getElementById('import-result');
    if (!fileInput.files[0])
        return;
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file, file.name);
    resultDiv.innerHTML = '<div style="display:flex;align-items:center;gap:8px;color:#6366f1;font-size:13px;"><i class="fas fa-spinner fa-spin"></i> Sedang mengimpor data...</div>';
    try {
        const res = await fetch('/import', { method: 'POST', body: formData });
        const result = await res.json();
        const isSuccess = result.status === 'success';
        resultDiv.innerHTML = `
            <div style="display:flex;align-items:flex-start;gap:10px;padding:12px;border-radius:8px;background:${isSuccess ? '#ecfdf5' : '#fef3c7'};border:1px solid ${isSuccess ? '#a7f3d0' : '#fcd34d'};">
                <i class="fas ${isSuccess ? 'fa-check-circle' : 'fa-exclamation-circle'}" style="color:${isSuccess ? '#10b981' : '#f59e0b'};margin-top:1px;"></i>
                <span style="font-size:13px;color:${isSuccess ? '#065f46' : '#92400e'};">${result.message}</span>
            </div>`;
    }
    catch (e) {
        resultDiv.innerHTML = `<div style="padding:12px;border-radius:8px;background:#fef2f2;border:1px solid #fecaca;color:#dc2626;font-size:13px;"><i class="fas fa-times-circle"></i> Error: ${e.message}</div>`;
    }
}
