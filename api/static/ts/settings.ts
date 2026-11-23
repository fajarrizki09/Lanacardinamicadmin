// ─── SETTINGS ─────────────────────────────────────────────────────────────────

type RenderSettingsOptions = {
    onlyDiscount?: boolean;
};

type PaymentProviderRegistryEntry = {
    status?: string;
    display_name?: string;
};

let settingsDelegationReady = false;

function ensureSettingsEventDelegation(): void {
    if (settingsDelegationReady) return;
    settingsDelegationReady = true;

    document.addEventListener('click', (event) => {
        const button = (event.target as HTMLElement | null)?.closest<HTMLElement>('[data-settings-action]');
        if (!button) return;
        const action = button.dataset.settingsAction || '';
        if (!action) return;
        event.preventDefault();

        switch (action) {
            case 'category':
                setSettingsCategory(button.dataset.settingsCategory || 'profile');
                break;
            case 'whatsapp-tab':
                break;
            case 'clear-logo':
                clearClinicLogoPath();
                break;
            case 'request-admin-pin-reset':
                requestAdminPinReset();
                break;
            case 'seed-demo':
                seedDemoData();
                break;
            case 'clear-demo':
                clearDemoData();
                break;
            case 'export':
                exportSettingsData(button.dataset.format || 'json');
                break;
            case 'open-export-folder':
                openSettingsExportFolder();
                break;
            case 'create-backup':
                createWebBackup();
                break;
            case 'refresh-backup':
                loadBackupManagement();
                break;
            case 'restore-backup':
                restoreWebBackup(button.dataset.path || '');
                break;
            case 'open-backup-folder':
                openBackupFolder();
                break;
            case 'reset-discount-form':
                resetDiscountRuleForm();
                break;
            case 'discount-type':
                setDiscountRuleType(button.dataset.type || 'visit_count');
                break;
            case 'run-discount-simulation':
                runDiscountSimulation();
                break;
            case 'toggle-discount-rule':
                toggleDiscountRule(Number(button.dataset.ruleId || 0), button.dataset.nextActive === 'true');
                break;
            case 'edit-discount-rule':
                editDiscountRule(Number(button.dataset.ruleId || 0));
                break;
            case 'delete-discount-rule':
                deleteDiscountRule(Number(button.dataset.ruleId || 0));
                break;
            case 'reset-free-visit-reasons':
                resetFreeVisitReasons();
                break;
            case 'reload-free-visit-reasons':
                loadFreeVisitReasons();
                break;
        }
    });

    document.addEventListener('input', (event) => {
        const input = event.target as HTMLInputElement | null;
        if (input?.dataset?.settingsAction === 'filter-sections') {
            filterSettingsSections(input.value);
        }
    });

    document.addEventListener('change', (event) => {
        const target = event.target as HTMLInputElement | HTMLSelectElement | null;
        const action = target?.dataset?.settingsAction || '';
        if (!action) return;

        switch (action) {
            case 'upload-logo':
                uploadClinicLogo(target as HTMLInputElement);
                break;
            case 'discount-type-ui':
                updateDiscountRuleTypeUI();
                break;
            case 'sync-discount-target-patients':
                syncDiscountTargetPatients();
                break;
            case 'sync-discount-activation':
                syncDiscountActivationControl();
                break;
            case 'sync-manual-simulation':
                syncManualSimulationControl();
                break;
        }
    });

    document.addEventListener('submit', (event) => {
        const form = event.target as HTMLFormElement | null;
        const action = form?.dataset?.settingsFormAction || '';
        if (!action) return;

        switch (action) {
            case 'license-activation':
                submitLicenseActivation(event);
                break;
            case 'admin-pin-change':
                submitAdminPinChange(event);
                break;
            case 'admin-pin-reset':
                submitAdminPinReset(event);
                break;
            case 'import':
                submitImport(event);
                break;
            case 'discount-rule':
                submitDiscountRule(event);
                break;
            case 'free-visit-reasons':
                submitFreeVisitReasons(event);
                break;
        }
    });
}

function renderSettings(s, options: RenderSettingsOptions = {}) {
    ensureSettingsEventDelegation();
    const onlyDiscount = options.onlyDiscount === true;
    const pricePerPoint = s.price_per_point ?? 10000;
    const basePrice = s.base_price ?? 100000;
    const paymentProvider = ['gateway_mock', 'midtrans'].includes(String(s.payment_gateway_default_provider || '').toLowerCase())
        ? String(s.payment_gateway_default_provider).toLowerCase()
        : 'gateway_mock';
    const paymentProviderRegistry: Record<string, PaymentProviderRegistryEntry> = s.payment_gateway_provider_registry || {};
    const comingSoonProviders = Object.entries(paymentProviderRegistry)
        .filter(([, info]) => info.status === 'coming_soon')
        .map(([id, info]) => ({ id, label: info.display_name || id }));
    const comingSoonHtml = comingSoonProviders.length
        ? `<div class="settings-info-row settings-info-coming-soon">
                <i class="fas fa-clock"></i>
                <span>Segera Hadir: ${comingSoonProviders.map(p => escapeHtml(p.label)).join(', ')}. Adapter belum tersedia, jadi belum bisa dipilih sebagai provider aktif.</span>
           </div>`
        : '';
    const html = `
        <section class="settings-workspace">
        <div class="settings-workspace-head">
            <div>
                <h2><i class="fas fa-sliders-h"></i> Pengaturan</h2>
                <p>Pilih kategori untuk membuka pengaturan yang diperlukan tanpa menelusuri halaman panjang.</p>
            </div>
            <label class="settings-search">
                <i class="fas fa-search"></i>
                <input type="search" id="settings-search-input" placeholder="Cari Midtrans, backup, PIN, tema..." data-settings-action="filter-sections">
            </label>
        </div>
        <nav class="settings-category-nav" aria-label="Kategori pengaturan">
            <button type="button" data-settings-action="category" data-settings-category="profile"><i class="fas fa-clinic-medical"></i><span>Profil & Pembayaran</span></button>
            <button type="button" data-settings-action="category" data-settings-category="license"><i class="fas fa-shield-alt"></i><span>Lisensi</span></button>
            <button type="button" data-settings-action="category" data-settings-category="security"><i class="fas fa-user-shield"></i><span>Keamanan / PIN</span></button>
            <button type="button" data-settings-action="category" data-settings-category="export"><i class="fas fa-file-export"></i><span>Ekspor</span></button>
            <button type="button" data-settings-action="category" data-settings-category="import"><i class="fas fa-file-import"></i><span>Impor</span></button>
            <button type="button" data-settings-action="category" data-settings-category="backup"><i class="fas fa-database"></i><span>Backup & Data</span></button>
            <button type="button" data-settings-action="category" data-settings-category="developer"><i class="fas fa-flask"></i><span>Data Contoh</span></button>
            <button type="button" class="settings-link-category" data-settings-action="whatsapp-tab"><i class="fab fa-whatsapp"></i><span>WhatsApp</span></button>
        </nav>
        <div id="settings-search-status" class="settings-search-status" hidden></div>
        <div class="settings-compact-grid">
            <!-- Settings Form -->
            <div class="card settings-system-card settings-card-border-primary">
                <div class="card-header">
                    <h3><i class="fas fa-sliders-h"></i> Konfigurasi Sistem</h3>
                </div>

                <div class="settings-form-wrapper">
                    <form action="/settings" method="post" id="settings-form">
                        <input type="hidden" name="discount_percentage" value="0">
                        <input type="hidden" name="min_visits_for_discount" value="999999">
                        <input type="hidden" name="price_per_point" value="${pricePerPoint}">
                        <input type="hidden" name="base_price" value="${basePrice}">

                        <!-- Section: Klinik -->
                        <div class="settings-section-clinic">
                            <i class="fas fa-clinic-medical"></i>
                            <span>Identitas Klinik</span>
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
                            <div class="settings-logo-upload-row">
                                <input type="file" id="clinic-logo-file" accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp" data-settings-action="upload-logo">
                                <button type="button" class="btn btn-secondary" data-settings-action="clear-logo">
                                    <i class="fas fa-times"></i> Hapus
                                </button>
                            </div>
                            <input type="text" id="clinic-logo-path" name="clinic_logo_path" value="${escapeHtml(s.clinic_logo_path || '')}" placeholder="Path logo akan terisi setelah pilih file" class="settings-logo-path-input">
                            <small class="settings-logo-help">Contoh: PNG/JPG/WebP, ideal 512x512 px atau rasio persegi, maksimal 2 MB. File akan disalin ke folder data aplikasi.</small>
                            <div id="clinic-logo-result" class="settings-logo-result"></div>
                        </div>
                        <div class="form-group">
                            <label>Footer Invoice</label>
                            <input type="text" name="invoice_footer" value="${escapeHtml(s.invoice_footer || '')}">
                        </div>
                        <div class="form-group">
                            <label>Label Admin</label>
                            <input type="text" name="admin_label" value="${escapeHtml(s.admin_label || 'Admin Klinik,')}">
                        </div>
                        <div class="settings-section-payment">
                            <i class="fas fa-credit-card"></i>
                            <span>Link Pembayaran</span>
                        </div>
                        <div class="form-group">
                            <label class="activation-switch is-${s.payment_gateway_enabled ? 'on' : 'off'}" for="payment-gateway-enabled">
                                <input type="checkbox" id="payment-gateway-enabled" name="payment_gateway_enabled" value="true" ${s.payment_gateway_enabled ? 'checked' : ''}>
                                <span class="activation-track" aria-hidden="true"><span></span></span>
                                <span class="activation-copy">
                                    <strong>Link Pembayaran Otomatis</strong>
                                    <small>Jika belum punya akun pembayaran online, biarkan nonaktif. Pembayaran manual tetap bisa dipakai.</small>
                                </span>
                            </label>
                        </div>
                        <div class="settings-payment-grid">
                            <div class="form-group">
                                <label>Penyedia Pembayaran</label>
                                <select name="payment_gateway_default_provider">
                                    <option value="gateway_mock" ${paymentProvider === 'gateway_mock' ? 'selected' : ''}>Pembayaran Internal</option>
                                    <option value="midtrans" ${paymentProvider === 'midtrans' ? 'selected' : ''}>Midtrans</option>
                                </select>
                                <small class="settings-logo-help">Pilih penyedia pembayaran yang sudah siap digunakan.</small>
                            </div>
                            <div class="form-group">
                                <label>Mode Penggunaan</label>
                                <select name="payment_gateway_environment">
                                    <option value="sandbox" ${(s.payment_gateway_environment || 'sandbox') === 'sandbox' ? 'selected' : ''}>Percobaan</option>
                                    <option value="production" ${s.payment_gateway_environment === 'production' ? 'selected' : ''}>Aktif</option>
                                </select>
                            </div>
                        </div>
                        <div class="settings-payment-grid-3col">
                            <div class="form-group">
                                <label>Midtrans Kunci Rahasia</label>
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
                        <div class="settings-info-row">
                            <i class="fas fa-info-circle"></i>
                            <span>Tanpa kunci pembayaran online, gunakan status Lunas, Belum Bayar, DP, Tunai, QRIS manual, atau Transfer dari form kunjungan. Fitur ini hanya diperlukan untuk membuat link pembayaran otomatis.</span>
                        </div>
                        ${comingSoonHtml}
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Simpan Semua Pengaturan
                        </button>
                    </form>
                </div>
            </div>

            <!-- Export & Import -->
            <div class="settings-card-stack">
                <div class="card settings-license-card settings-card-border-indigo">
                    <div class="card-header">
                        <h3><i class="fas fa-shield-alt settings-icon-indigo"></i> Lisensi Aplikasi</h3>
                    </div>
                    <div id="license-settings-status" class="settings-license-status">
                        <i class="fas fa-spinner fa-spin"></i> Memuat status lisensi...
                    </div>
                    <form id="license-settings-form" data-settings-form-action="license-activation">
                        <div class="form-group">
                            <label>Clinic ID</label>
                            <input type="text" id="license-clinic-id" name="clinic_id" placeholder="Clinic ID" required>
                        </div>
                        <div class="form-group">
                            <label>Kode Lisensi Baru</label>
                            <input type="password" id="license-key-input" name="license_key" placeholder="Tempel kode lisensi baru" required>
                        </div>
                        <button type="submit" class="btn btn-primary settings-license-btn">
                            <i class="fas fa-key"></i> Aktivasi / Ganti Lisensi
                        </button>
                    </form>
                    <div id="license-settings-result" class="settings-result-margin"></div>
                </div>

                <div class="card settings-security-card settings-card-border-teal">
                    <div class="card-header">
                        <h3><i class="fas fa-user-shield settings-icon-teal"></i> Keamanan Admin</h3>
                    </div>
                    <p class="settings-security-copy">
                        Ubah PIN lokal yang dipakai untuk membuka aplikasi dan menjalankan aksi sensitif.
                    </p>
                    <form id="admin-pin-change-form" class="admin-pin-change-form" data-settings-form-action="admin-pin-change">
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
                        <button type="submit" class="btn btn-primary settings-security-btn">
                            <i class="fas fa-lock"></i> Ubah PIN Admin
                        </button>
                    </form>
                    <div id="admin-pin-change-result" class="settings-result-margin"></div>
                    <div class="admin-pin-reset-box">
                        <div class="admin-pin-reset-heading">
                            <i class="fas fa-life-ring"></i>
                            <div>
                                <strong>Lupa PIN?</strong>
                                <span>Minta kode reset dari pusat lisensi, lalu buat PIN admin baru di komputer ini.</span>
                            </div>
                        </div>
                        <button type="button" id="admin-pin-reset-request-btn" class="btn btn-secondary" data-settings-action="request-admin-pin-reset">
                            <i class="fas fa-paper-plane"></i> Minta Kode Reset
                        </button>
                        <form id="admin-pin-reset-form" class="admin-pin-change-form" data-settings-form-action="admin-pin-reset">
                            <div class="form-group">
                                <label>Kode Reset Lisensi</label>
                                <input type="text" id="admin-reset-token" autocomplete="one-time-code" placeholder="Masukkan kode dari pusat lisensi" required>
                            </div>
                            <div class="form-group">
                                <label>PIN Admin Baru</label>
                                <input type="password" id="admin-reset-new-pin" inputmode="numeric" pattern="[0-9]*" autocomplete="new-password" required>
                                <small class="settings-security-help">PIN tetap tersimpan di komputer ini. Pusat lisensi hanya memberi izin reset.</small>
                            </div>
                            <div class="form-group">
                                <label>Konfirmasi PIN Baru</label>
                                <input type="password" id="admin-reset-confirm-pin" inputmode="numeric" pattern="[0-9]*" autocomplete="new-password" required>
                            </div>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-rotate"></i> Reset PIN Admin
                            </button>
                        </form>
                        <div id="admin-pin-reset-result" class="settings-result-margin"></div>
                    </div>
                </div>

                <div class="card settings-demo-card settings-card-border-purple">
                    <div class="card-header">
                        <h3><i class="fas fa-magic settings-icon-purple"></i> Data Contoh</h3>
                    </div>
                    <p class="settings-security-copy">
                        Isi data demo untuk mencoba alur pasien, layanan, stok, dan kunjungan tanpa input manual.
                    </p>
                    <div class="settings-demo-actions">
                        <button type="button" class="btn btn-primary settings-demo-btn" data-settings-action="seed-demo">
                            <i class="fas fa-magic"></i> Isi Data Contoh
                        </button>
                        <button type="button" class="btn btn-secondary" data-settings-action="clear-demo">
                            <i class="fas fa-broom"></i> Hapus Demo
                        </button>
                    </div>
                    <div id="demo-data-result" class="settings-demo-result"></div>
                </div>

                <!-- Export -->
                <div class="card settings-export-card settings-card-border-emerald">
                    <div class="card-header">
                        <h3><i class="fas fa-file-export settings-icon-emerald"></i> Ekspor Data</h3>
                    </div>
                    <p class="settings-export-description">
                        Ekspor data operasional untuk backup, pengecekan, atau migrasi manual.
                    </p>
                    <div id="settings-export-folder" class="settings-info-row settings-export-folder-row">
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
                    <div class="settings-export-grid">
                        <button type="button"
                           id="settings-export-xlsx-btn"
                           data-settings-action="export"
                           data-format="xlsx"
                           class="settings-export-btn-xlsx">
                            <i class="fas fa-file-excel"></i> Excel (.xlsx)
                        </button>
                        <button type="button"
                           id="settings-export-json-btn"
                           data-settings-action="export"
                           data-format="json"
                           class="settings-export-btn-json">
                            <i class="fas fa-file-code"></i> JSON
                        </button>
                    </div>
                    <button type="button" class="btn btn-secondary settings-export-folder-btn" data-settings-action="open-export-folder">
                        <i class="fas fa-folder-open"></i> Buka Folder Export
                    </button>
                    <div id="settings-export-result" class="settings-export-result"></div>
                </div>

                <!-- Import -->
                <div class="card settings-import-card settings-card-border-warning">
                    <div class="card-header">
                        <h3><i class="fas fa-file-import settings-icon-warning"></i> Impor Data</h3>
                    </div>
                    <div class="settings-import-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>Data baru akan digabung (merge) dengan data yang ada. Pasien dengan nomor HP sama tidak akan diduplikasi.</span>
                    </div>
                    <form id="import-form" data-settings-form-action="import">
                        <div class="form-group">
                            <label>Pilih File JSON / Excel</label>
                            <input type="file" id="import-file" name="file" accept=".json,.xlsx,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" required class="settings-import-file-input">
                        </div>
                        <button type="submit" class="btn btn-primary settings-import-btn">
                            <i class="fas fa-upload"></i> Impor Sekarang
                        </button>
                    </form>
                    <div id="import-result" class="settings-import-result"></div>
                </div>

                <!-- Backup Management -->
                <div class="card settings-backup-card settings-card-border-sky">
                    <div class="card-header">
                        <h3><i class="fas fa-database settings-icon-sky"></i> Manajemen Backup</h3>
                    </div>
                    <p class="settings-backup-description">
                        Buat backup database manual dan restore dari backup yang tersimpan.
                    </p>
                    <div class="settings-backup-actions">
                        <button type="button" class="btn btn-primary settings-backup-btn" data-settings-action="create-backup">
                            <i class="fas fa-plus"></i> Buat Backup
                        </button>
                        <button type="button" class="btn btn-secondary" data-settings-action="refresh-backup">
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
        </section>

        <div class="card discount-admin-card discount-card-border-indigo">
            <div class="card-header settings-card-header-flex">
                <div>
                    <h3><i class="fas fa-tags settings-icon-indigo"></i> Diskon & Voucher</h3>
                    <p class="discount-helper-text">Sistem hanya memakai 1 diskon per kunjungan: prioritas terkecil menang. Diskon kunjungan dihitung dari total riwayat pasien dan berlaku mulai kunjungan ke-N dan seterusnya.</p>
                </div>
                <button type="button" class="btn btn-secondary" data-settings-action="reset-discount-form">
                    <i class="fas fa-plus"></i> Baru
                </button>
            </div>
            <div class="discount-flow-strip">
                <div><strong>2 diskon cocok</strong><span>Yang dipakai hanya prioritas paling atas.</span></div>
                <div><strong>Diskon dimatikan</strong><span>Tidak berlaku untuk transaksi baru. Riwayat lama tetap tersimpan.</span></div>
                <div><strong>Diskon baru aktif</strong><span>Langsung ikut dihitung pada kunjungan berikutnya, jika nomor kunjungan sudah mencapai syarat.</span></div>
            </div>
            <div class="discount-admin-grid">
                <form id="discount-rule-form" class="discount-rule-form" data-settings-form-action="discount-rule">
                <input type="hidden" id="discount-rule-id" name="rule_id" value="0">
                <div class="discount-type-picker" aria-label="Pilih tipe diskon">
                    <button type="button" data-settings-action="discount-type" data-type="visit_count"><i class="fas fa-redo"></i><span>Kunjungan</span></button>
                    <button type="button" data-settings-action="discount-type" data-type="voucher"><i class="fas fa-ticket-alt"></i><span>Voucher</span></button>
                    <button type="button" data-settings-action="discount-type" data-type="period"><i class="fas fa-calendar-alt"></i><span>Periode</span></button>
                    <button type="button" data-settings-action="discount-type" data-type="manual"><i class="fas fa-edit"></i><span>Harga Manual</span></button>
                </div>
                <div class="discount-form-grid">
                    <div class="form-group">
                        <label>Nama Diskon</label>
                        <input type="text" id="discount-rule-name" name="name" placeholder="Promo Ramadhan" required>
                    </div>
                    <div class="form-group">
                        <label>Tipe</label>
                        <select id="discount-rule-type" name="type" required data-settings-action="discount-type-ui">
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
                        <select id="discount-rule-target-patients" multiple size="6" data-settings-action="sync-discount-target-patients" style="min-height:130px;">
                            <option value="">Memuat daftar pasien...</option>
                        </select>
                        <small class="discount-input-help">Kosongkan jika voucher berlaku untuk semua pasien. Tahan Ctrl untuk memilih beberapa pasien.</small>
                    </div>
                    <div class="form-group discount-field discount-field-date">
                        <label>Mulai</label>
                        <input type="date" id="discount-rule-start" name="start_date" data-settings-action="discount-type-ui">
                    </div>
                    <div class="form-group discount-field discount-field-date">
                        <label>Selesai</label>
                        <input type="date" id="discount-rule-end" name="end_date" data-settings-action="discount-type-ui">
                    </div>
                    <div class="form-group">
                        <label>Prioritas</label>
                        <input type="number" id="discount-rule-priority" name="priority" value="100" min="0" required>
                        <small class="discount-input-help">Angka lebih kecil dipakai dulu saat beberapa diskon cocok.</small>
                    </div>
                    <div class="form-group activation-field">
                        <label>Status Aturan</label>
                        <label class="activation-switch is-on" id="discount-rule-active-control" for="discount-rule-active">
                            <input type="checkbox" id="discount-rule-active" checked data-settings-action="sync-discount-activation">
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
                        <button type="button" class="btn btn-secondary" data-settings-action="run-discount-simulation" style="width:auto;">
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
                        <input type="checkbox" id="discount-sim-manual" data-settings-action="sync-manual-simulation">
                        <span class="activation-track" aria-hidden="true"><span></span></span>
                        <span class="activation-copy">
                            <strong id="discount-sim-manual-title">Harga normal</strong>
                            <small id="discount-sim-manual-help">Simulasi memakai aturan diskon otomatis.</small>
                        </span>
                    </label>
                    <button type="button" class="btn btn-primary" data-settings-action="run-discount-simulation">
                        <i class="fas fa-play"></i> Cek Simulasi
                    </button>
                    <div id="discount-simulation-result" class="discount-simulation-result">Isi simulasi untuk melihat diskon yang akan dipakai pada kunjungan berikutnya.</div>
                </div>
            </div>
            <div id="discount-rules-result" style="margin-bottom:12px;"></div>
            <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr style="background:var(--color-surface-muted); color:var(--color-text-muted); font-size:12px; text-transform:uppercase;">
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
    if (discountCard) discountCard.remove();
    arrangeSettingsLayout();
    syncSettingsActivationSwitches();
    loadLicenseSettingsStatus();
    loadSettingsExportFolder();
    loadBackupManagement();
}

function renderVouchers() {
    renderSettings({}, { onlyDiscount: true });
    const displayArea = document.getElementById('display-area');
    const discountCard = displayArea?.querySelector('.discount-admin-card');
    if (!displayArea || !discountCard) return;
    discountCard.insertAdjacentHTML('beforebegin', `
        <div class="card free-visit-reasons-card free-visit-card">
            <div class="card-header settings-card-header-flex">
                <div>
                    <h3><i class="fas fa-gift settings-icon-emerald"></i> Promo Gratis</h3>
                    <p class="discount-helper-text">Daftar alasan yang muncul saat toggle Kunjungan Gratis aktif di form kunjungan.</p>
                </div>
                <button type="button" class="btn btn-secondary" data-settings-action="reset-free-visit-reasons">
                    <i class="fas fa-undo"></i> Default
                </button>
            </div>
            <form id="free-visit-reasons-form" data-settings-form-action="free-visit-reasons">
                <div class="form-group">
                    <label>Alasan Kunjungan Gratis</label>
                    <textarea id="free-visit-reasons-input" name="reasons" rows="5" placeholder="Satu alasan per baris" class="free-visit-textarea"></textarea>
                    <small class="discount-input-help">Contoh: promo, keluarga, koreksi, garansi terapi. Satu baris menjadi satu pilihan.</small>
                </div>
                <div class="free-visit-actions">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> Simpan Promo Gratis
                    </button>
                    <button type="button" class="btn btn-secondary" data-settings-action="reload-free-visit-reasons">
                        <i class="fas fa-sync-alt"></i> Muat Ulang
                    </button>
                </div>
                <div id="free-visit-reasons-result" class="settings-result-margin"></div>
            </form>
        </div>
    `);
    loadFreeVisitReasons();
}

async function loadDiscountPatientOptions(selectedIds = []) {
    const select = document.getElementById('discount-rule-target-patients');
    if (!select) return;
    const selectedSet = new Set((selectedIds || []).map(id => String(id)));
    try {
        const response = await fetch('/patients');
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || 'Gagal memuat pasien.');
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
    } catch (error) {
        select.innerHTML = `<option value="">${escapeHtml(sanitizeAppErrorMessage(error.message, 'Gagal memuat pasien.'))}</option>`;
        syncDiscountTargetPatients();
    }
}

function syncDiscountTargetPatients() {
    const select = document.getElementById('discount-rule-target-patients');
    const hidden = document.getElementById('discount-rule-target-patient-ids');
    if (!select || !hidden) return;
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
    if (!input) return;
    try {
        const response = await fetch('/free_visit_reasons');
        if (!response.ok) throw new Error('Gagal memuat alasan promo gratis.');
        const data = await response.json();
        const items = Array.isArray(data.items) && data.items.length ? data.items : defaultFreeVisitReasons();
        input.value = items.join('\n');
        if (result) result.innerHTML = '';
    } catch (error) {
        input.value = defaultFreeVisitReasons().join('\n');
        if (result) {
            result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#fef2f2; color:#dc2626; font-size:13px;">${escapeHtml(error.message)}</div>`;
        }
    }
}

function resetFreeVisitReasons() {
    const input = document.getElementById('free-visit-reasons-input');
    if (input) input.value = defaultFreeVisitReasons().join('\n');
}

async function submitFreeVisitReasons(event) {
    event.preventDefault();
    const input = document.getElementById('free-visit-reasons-input');
    const result = document.getElementById('free-visit-reasons-result');
    if (!input) return;
    const lines = input.value.split(/\r?\n/).map(item => item.trim()).filter(Boolean);
    if (!lines.length) {
        if (result) result.innerHTML = '<div style="padding:10px; border-radius:8px; background:#fef3c7; color:#92400e; font-size:13px;">Minimal isi satu alasan promo gratis.</div>';
        return;
    }

    const formData = new FormData();
    formData.set('reasons', lines.join('\n'));
    try {
        const response = await fetch('/free_visit_reasons', { method: 'POST', body: formData });
        const data = await response.json();
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal menyimpan alasan promo gratis.');
        input.value = (data.items || lines).join('\n');
        if (result) result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#ecfdf5; color:#065f46; font-size:13px;">${escapeHtml(data.message)}</div>`;
        showToast(data.message, 'success');
    } catch (error) {
        if (result) result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#fef2f2; color:#dc2626; font-size:13px;">${escapeHtml(error.message)}</div>`;
        showToast(error.message, 'error');
    }
}

function arrangeSettingsLayout() {
    const root = document.querySelector('.settings-compact-grid');
    if (!root) return;

    if (!root.querySelector('.settings-left-stack')) {
        const systemCard = root.querySelector('.settings-system-card');
        const whatsappCard = root.querySelector('.settings-whatsapp-card');
        const stack = root.querySelector('.settings-card-stack');
        const licenseCard = root.querySelector('.settings-license-card');
        const securityCard = root.querySelector('.settings-security-card');
        const demoCard = root.querySelector('.settings-demo-card');
        const exportCard = root.querySelector('.settings-export-card');
        const importCard = root.querySelector('.settings-import-card');
        const backupCard = root.querySelector('.settings-backup-card');
        if (!systemCard || !stack) return;

        const left = document.createElement('div');
        left.className = 'settings-left-stack';
        const right = document.createElement('div');
        right.className = 'settings-right-stack';

        left.appendChild(systemCard);
        if (whatsappCard) left.appendChild(whatsappCard);
        if (exportCard) left.appendChild(exportCard);
        if (importCard) left.appendChild(importCard);
        if (licenseCard) right.appendChild(licenseCard);
        if (securityCard) right.appendChild(securityCard);
        if (demoCard) right.appendChild(demoCard);
        if (backupCard) right.appendChild(backupCard);

        root.replaceChildren(left, right);
    }

    const categories = [
        ['.settings-system-card', 'profile', 'profil klinik pembayaran payment gateway midtrans invoice struk tema tampilan'],
        ['.settings-license-card', 'license', 'lisensi aktivasi clinic id license'],
        ['.settings-security-card', 'security', 'keamanan pin reset admin'],
        ['.settings-export-card', 'export', 'ekspor export excel json folder'],
        ['.settings-import-card', 'import', 'impor import data'],
        ['.settings-backup-card', 'backup', 'backup restore database data'],
        ['.settings-demo-card', 'developer', 'developer diagnostik data contoh demo'],
    ];
    categories.forEach(([selector, category, keywords]) => {
        const card = root.querySelector(selector) as HTMLElement | null;
        if (!card) return;
        card.dataset.settingsCategory = category;
        card.dataset.settingsKeywords = keywords;
    });
    setSettingsCategory(window._settingsCategory || 'profile', false);
}

function setSettingsCategory(category: string, focus = true): void {
    window._settingsCategory = category;
    const searchInput = document.getElementById('settings-search-input') as HTMLInputElement | null;
    if (searchInput) searchInput.value = '';
    const status = document.getElementById('settings-search-status');
    if (status) status.hidden = true;
    document.querySelectorAll('.settings-category-nav [data-settings-category]').forEach(button => {
        button.classList.toggle('is-active', (button as HTMLElement).dataset.settingsCategory === category);
    });
    document.querySelectorAll('.settings-compact-grid .card[data-settings-category]').forEach(card => {
        const matches = (card as HTMLElement).dataset.settingsCategory === category;
        (card as HTMLElement).hidden = !matches;
    });
    if (focus) {
        const panel = document.querySelector(`.settings-compact-grid .card[data-settings-category="${category}"]`) as HTMLElement | null;
        panel?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function filterSettingsSections(rawQuery: string): void {
    const query = String(rawQuery || '').trim().toLowerCase();
    const status = document.getElementById('settings-search-status');
    const cards = Array.from(document.querySelectorAll('.settings-compact-grid .card[data-settings-category]')) as HTMLElement[];
    if (!query) {
        setSettingsCategory(window._settingsCategory || 'profile', false);
        return;
    }
    document.querySelectorAll('.settings-category-nav [data-settings-category]').forEach(button => button.classList.remove('is-active'));
    let shown = 0;
    cards.forEach(card => {
        const haystack = `${card.dataset.settingsKeywords || ''} ${card.textContent || ''}`.toLowerCase();
        const match = haystack.includes(query);
        card.hidden = !match;
        if (match) shown += 1;
    });
    if (status) {
        status.hidden = false;
        status.textContent = shown ? `${shown} kategori cocok untuk "${rawQuery}".` : `Tidak ada pengaturan yang cocok untuk "${rawQuery}".`;
    }
}

window.setSettingsCategory = setSettingsCategory;
window.filterSettingsSections = filterSettingsSections;

async function uploadClinicLogo(input) {
    const result = document.getElementById('clinic-logo-result');
    const pathInput = document.getElementById('clinic-logo-path');
    const file = input?.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
        input.value = '';
        if (result) result.innerHTML = '<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>Ukuran logo maksimal 2 MB.</span></div>';
        showToast('Ukuran logo maksimal 2 MB.', 'error');
        return;
    }

    const allowedTypes = ['image/png', 'image/jpeg', 'image/webp'];
    const allowedExt = /\.(png|jpe?g|webp)$/i;
    if (!allowedTypes.includes(file.type) && !allowedExt.test(file.name || '')) {
        input.value = '';
        if (result) result.innerHTML = '<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>Format logo harus PNG, JPG, JPEG, atau WebP.</span></div>';
        showToast('Format logo harus PNG, JPG, JPEG, atau WebP.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('logo', file, file.name);
    if (result) result.innerHTML = '<div class="settings-info-row"><i class="fas fa-spinner fa-spin"></i><span>Menyimpan logo...</span></div>';

    try {
        const response = await fetch('/settings/logo', { method: 'POST', body: formData });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal menyimpan logo.');
        if (pathInput) pathInput.value = data.path || '';
        if (result) result.innerHTML = `<div class="settings-info-row success"><i class="fas fa-check-circle"></i><span>${escapeHtml(data.message || 'Logo klinik siap disimpan.')}</span></div>`;
        showToast('Logo klinik siap disimpan. Klik Simpan Semua Pengaturan.', 'success');
    } catch (error) {
        if (result) result.innerHTML = `<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>${escapeHtml(error.message || 'Gagal menyimpan logo.')}</span></div>`;
        showToast(error.message || 'Gagal menyimpan logo.', 'error');
    }
}

function clearClinicLogoPath() {
    const pathInput = document.getElementById('clinic-logo-path');
    const fileInput = document.getElementById('clinic-logo-file');
    const result = document.getElementById('clinic-logo-result');
    if (pathInput) pathInput.value = '';
    if (fileInput) fileInput.value = '';
    if (result) result.innerHTML = '<div class="settings-info-row"><i class="fas fa-info-circle"></i><span>Logo akan dikosongkan setelah pengaturan disimpan.</span></div>';
}

function setWhatsAppResult(html) {
    const result = document.getElementById('whatsapp-settings-result');
    if (result) result.innerHTML = html;
}

function setWhatsAppLoginPanel(html, visible = true) {
    const panel = document.getElementById('whatsapp-login-panel');
    if (!panel) return;
    panel.style.display = visible ? 'block' : 'none';
    panel.innerHTML = html;
}

function whatsappStatusRow(message, type = 'info') {
    const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
    const className = type === 'error' ? 'settings-error-row' : `settings-info-row ${type === 'success' ? 'success' : ''}`;
    return `<div class="${className}"><i class="fas ${icon}"></i><span>${escapeHtml(message)}</span></div>`;
}

function normalizeOpenWAErrorMessage(message) {
    const text = String(message || '').trim();
    if (/Cannot POST\s+\/layanan\/koneksis\//i.test(text)) {
        return 'Server WhatsApp yang sedang berjalan masih versi lama. Tutup aplikasi, pastikan proses Node WhatsApp ikut tertutup, lalu buka aplikasi kembali.';
    }
    if (/berhenti saat startup/i.test(text)) {
        return 'Node gateway berhenti saat startup. Buka log WhatsApp Gateway untuk melihat penyebab runtime, lalu coba mulai ulang.';
    }
    if (/startup timeout|tidak siap setelah/i.test(text)) {
        return 'Gateway belum siap dalam batas waktu. Periksa log WhatsApp Gateway lalu coba mulai ulang.';
    }
    if (/Folder openwa_server belum tersedia/i.test(text)) {
        return 'Runtime WhatsApp tidak ditemukan di instalasi aplikasi. Instal ulang RC atau periksa log startup.';
    }
    if (/Dependency OpenWA belum terinstall/i.test(text)) {
        return 'Dependency WhatsApp tidak lengkap pada instalasi aplikasi. Instal ulang RC yang valid.';
    }
    if (/Port gateway WhatsApp digunakan/i.test(text)) {
        return 'Port WhatsApp sedang digunakan proses lain atau session lama. Tutup proses tersebut lalu mulai ulang dari aplikasi.';
    }
    if (/WinError 10061|actively refused|connection refused|Tidak bisa terhubung ke OpenWA/i.test(text)) {
        return 'Node gateway tidak berjalan. Klik Perbarui Status untuk memulai ulang gateway.';
    }
    if (/Gateway token|token invalid|HTTP 403|tidak dikelola aplikasi/i.test(text)) {
        return 'Token gateway tidak valid atau gateway bukan milik aplikasi. Tutup proses WhatsApp lama lalu buka ulang aplikasi.';
    }
    if (/QR tidak tersedia|QR belum tersedia/i.test(text)) {
        return 'QR belum tersedia. Tunggu beberapa detik lalu klik Perbarui Status.';
    }
    return text
        .replace(/OpenWA/gi, 'WhatsApp')
        .replace(/Baileys/gi, 'WhatsApp')
        .replace(/server lokal/gi, 'layanan WhatsApp')
        .replace(/server/gi, 'layanan')
        .replace(/session/gi, 'koneksi')
        .replace(/Base URL\/port/gi, 'pengaturan koneksi')
        .replace(/API/gi, 'layanan')
        .replace(/QR OpenWA/gi, 'QR WhatsApp');
}

function syncSettingsActivationSwitches() {
    document.querySelectorAll('.settings-compact-grid .activation-switch input[type="checkbox"]').forEach(input => {
        const checkbox = input as HTMLInputElement;
        const control = checkbox.closest('.activation-switch');
        if (!control) return;
        const applyState = () => {
            control.classList.toggle('is-on', checkbox.checked);
            control.classList.toggle('is-off', !checkbox.checked);
        };
        applyState();
        checkbox.addEventListener('change', applyState);
    });
}

function getOpenWASessionIdFromForm() {
    const input = document.querySelector('#whatsapp-settings-form input[name="openwa_session_id"]') as HTMLInputElement | null;
    return String(input?.value || 'clinic').trim() || 'clinic';
}

function buildSessionFormData() {
    const formData = new FormData();
    const sessionId = getOpenWASessionIdFromForm();
    if (sessionId) formData.set('session_id', sessionId);
    return formData;
}

function applyLocalOpenWASettings() {
    const form = document.getElementById('whatsapp-settings-form') as HTMLFormElement | null;
    if (!form) return;
    const baseUrl = form.querySelector('input[name="openwa_base_url"]') as HTMLInputElement | null;
    const sessionId = form.querySelector('input[name="openwa_session_id"]') as HTMLInputElement | null;
    if (baseUrl) baseUrl.value = 'http://127.0.0.1:3000/api';
    if (sessionId && !String(sessionId.value || '').trim()) sessionId.value = 'clinic';
}

async function checkLocalOpenWAServer() {
    setWhatsAppResult(whatsappStatusRow('Mengecek kesiapan WhatsApp...', 'info'));
    try {
        const response = await fetch('/whatsapp/server/status');
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal mengecek kesiapan WhatsApp.');
        applyLocalOpenWASettings();
        const message = data.running
            ? 'WhatsApp siap digunakan.'
            : 'WhatsApp belum siap. Klik Perbarui Status atau buka ulang aplikasi.';
        setWhatsAppResult(whatsappStatusRow(message, data.running ? 'success' : 'info'));
        setWhatsAppLoginPanel(`<span><strong>Status WhatsApp:</strong><br>${escapeHtml(message)}</span>`);
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Gagal mengecek kesiapan WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        showToast(message, 'error');
    }
}

async function installLocalOpenWAServer() {
    setWhatsAppResult(whatsappStatusRow('Menyiapkan komponen WhatsApp. Proses ini bisa beberapa menit...', 'info'));
    setWhatsAppLoginPanel('<span><i class="fas fa-spinner fa-spin"></i> WhatsApp sedang disiapkan. Jangan tutup aplikasi.</span>');
    try {
        const response = await fetch('/whatsapp/server/install', { method: 'POST', body: new FormData() });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'WhatsApp gagal disiapkan.');
        setWhatsAppResult(whatsappStatusRow(data.message || 'WhatsApp berhasil disiapkan.', 'success'));
        setWhatsAppLoginPanel('<span><strong>WhatsApp siap.</strong><br>Klik <b>Perbarui Status</b> untuk melanjutkan login.</span>');
        showToast(data.message || 'WhatsApp berhasil disiapkan.', 'success');
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'WhatsApp gagal disiapkan.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        setWhatsAppLoginPanel(`<span>${escapeHtml(message)}</span>`);
        showToast(message, 'error');
    }
}

async function openOpenWADashboard() {
    try {
        await openDesktopExternalUrl('http://127.0.0.1:3000', 'gateway_dashboard');
    } catch (error) {
        showToast(sanitizeAppErrorMessage(error, 'Dashboard WhatsApp tidak dapat dibuka.'), 'error');
    }
}

async function startLocalOpenWAServer() {
    setWhatsAppResult(whatsappStatusRow('Menyiapkan WhatsApp...', 'info'));
    setWhatsAppLoginPanel('<span><i class="fas fa-spinner fa-spin"></i> WhatsApp sedang disiapkan. Tunggu beberapa detik...</span>');
    try {
        const response = await fetch('/whatsapp/server/start', { method: 'POST', body: new FormData() });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal menyiapkan WhatsApp.');
        applyLocalOpenWASettings();
        setWhatsAppResult(whatsappStatusRow(data.message || 'WhatsApp disiapkan.', 'success'));
        setWhatsAppLoginPanel('<span><strong>WhatsApp sedang dimulai.</strong><br>Tunggu beberapa detik, lalu klik <b>Perbarui Status</b>.</span>');
        showToast(data.message || 'WhatsApp disiapkan.', 'success');
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Gagal menyiapkan WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        setWhatsAppLoginPanel(`<span>${escapeHtml(message)}</span>`);
        showToast(message, 'error');
    }
}

function extractOpenWAQR(data) {
    const candidates = [
        typeof data === 'string' ? data : '',
        data?.qr?.qr,
        data?.qr?.qrcode,
        data?.qr?.qrCode,
        data?.qr?.base64,
        data?.qr?.image,
        data?.qr,
        data?.qrcode,
        data?.qrCode,
        data?.base64,
        data?.image,
        data?.data?.qr,
        data?.data?.qrcode,
        data?.data?.qrCode,
        data?.data?.base64,
        data?.data?.image,
        data?.data?.data?.qr,
        data?.data?.data?.qrcode,
        data?.data?.data?.qrCode,
        data?.data?.data?.base64,
    ].filter(Boolean).map(value => String(value));
    return candidates.find(value => value.startsWith('data:image/'))
        || candidates.find(value => /^https?:\/\//.test(value))
        || '';
}

function renderOpenWADataSummary(data) {
    try {
        return `<pre style="white-space:pre-wrap;word-break:break-word;margin:8px 0 0;font-size:11px;max-height:180px;overflow:auto;">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
    } catch (error) {
        return '';
    }
}

let openwaAutoRefreshTimer = null;

function extractOpenWAStatus(data) {
    return String(data?.session?.status || data?.session?.sessionStatus || data?.data?.status || data?.data?.sessionStatus || data?.status || '').trim();
}

function extractOpenWAAccount(data) {
    const account = data?.session?.account || data?.data?.account || data?.account || null;
    if (!account) return null;
    return {
        name: String(account.name || '').trim(),
        phone: String(account.phone || '').trim(),
        id: String(account.id || '').trim(),
    };
}

function renderWhatsAppLoginState(data) {
    const status = extractOpenWAStatus(data);
    const account = extractOpenWAAccount(data);
    const qr = extractOpenWAQR(data);
    const imageSrc = qr && (qr.startsWith('data:image/') || /^https?:\/\//.test(qr)) ? qr : '';
    if (status === 'connected') {
        return `
            <div class="wa-profile-card is-connected">
                <div class="wa-profile-heading">
                    <span class="wa-connection-indicator" aria-hidden="true"></span>
                    <div>
                        <span class="wa-profile-eyebrow">Status login</span>
                        <strong>WhatsApp sudah login</strong>
                    </div>
                    <span class="wa-status-pill"><i class="fas fa-check-circle"></i> Terhubung</span>
                </div>
                <div class="wa-profile-grid">
                    <div class="wa-profile-field">
                        <span>Nama akun</span>
                        <strong>${escapeHtml(account?.name || 'Tidak tersedia')}</strong>
                    </div>
                    <div class="wa-profile-field">
                        <span>Nomor WhatsApp</span>
                        <strong>${escapeHtml(account?.phone || 'Tidak tersedia')}</strong>
                    </div>
                    <div class="wa-profile-field">
                        <span>Status koneksi</span>
                        <strong>Aktif dan siap mengirim</strong>
                    </div>
                </div>
            </div>`;
    }
    return `
        <div class="wa-profile-card is-waiting">
            <div class="wa-profile-heading">
                <span class="wa-connection-indicator" aria-hidden="true"></span>
                <div>
                    <span class="wa-profile-eyebrow">Status login</span>
                    <strong>Menunggu login WhatsApp</strong>
                </div>
                <span class="wa-status-pill">Belum terhubung</span>
            </div>
            <p class="wa-profile-guidance">Buka WhatsApp di HP &gt; Perangkat Tertaut &gt; Tautkan Perangkat, lalu scan QR berikut.</p>
            ${imageSrc
            ? `<div class="wa-qr-frame"><img src="${escapeHtml(imageSrc)}" alt="QR Login WhatsApp"></div>`
            : `<div class="wa-qr-pending"><i class="fas fa-spinner fa-spin"></i> Menunggu QR WhatsApp. Klik Perbarui Status bila belum muncul.</div>`}
        </div>`;
}

async function autoWhatsAppGatewayLogin(showSuccessToast = false) {
    if (openwaAutoRefreshTimer) {
        clearTimeout(openwaAutoRefreshTimer);
        openwaAutoRefreshTimer = null;
    }
    setWhatsAppResult(whatsappStatusRow('Menyiapkan WhatsApp...', 'info'));
    setWhatsAppLoginPanel('<span><i class="fas fa-spinner fa-spin"></i> Menunggu QR WhatsApp...</span>');
    try {
        const response = await fetch('/whatsapp/auto-login', { method: 'POST', body: new FormData() });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal menyiapkan WhatsApp.');
        setWhatsAppLoginPanel(renderWhatsAppLoginState(data));
        const status = extractOpenWAStatus(data);
        const message = status === 'connected'
            ? 'WhatsApp sudah login.'
            : (extractOpenWAQR(data) ? 'QR WhatsApp siap. Scan QR yang tampil.' : 'QR belum tersedia. Tunggu beberapa detik lalu klik Perbarui Status.');
        setWhatsAppResult(whatsappStatusRow(message, status === 'connected' ? 'success' : 'info'));
        if (showSuccessToast) showToast(message, status === 'connected' ? 'success' : 'info');
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Gagal menyiapkan WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        setWhatsAppLoginPanel(`<span>${escapeHtml(message)}</span>`);
        showToast(message, 'error');
    }
}

async function createOpenWASession() {
    setWhatsAppResult(whatsappStatusRow('Menyiapkan koneksi WhatsApp...', 'info'));
    try {
        const response = await fetch('/whatsapp/session/create', { method: 'POST', body: buildSessionFormData() });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal menyiapkan koneksi WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(data.message || 'Session WhatsApp dibuat.', 'success'));
        setWhatsAppLoginPanel('<span><strong>Koneksi WhatsApp siap.</strong><br>Langkah berikutnya: klik <b>Perbarui Status</b>, lalu scan QR jika diminta.</span>');
        showToast(data.message || 'Koneksi WhatsApp siap.', 'success');
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Gagal menyiapkan koneksi WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        showToast(message, 'error');
    }
}

async function startOpenWASession() {
    setWhatsAppResult(whatsappStatusRow('Memulai login WhatsApp...', 'info'));
    try {
        const response = await fetch('/whatsapp/session/start', { method: 'POST', body: buildSessionFormData() });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal memulai login WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(data.message || 'Session WhatsApp dijalankan.', 'success'));
        setWhatsAppLoginPanel('<span><strong>Login WhatsApp dimulai.</strong><br>Klik <b>Perbarui Status</b>, lalu scan dari WhatsApp > Perangkat Tertaut.</span>');
        showToast(data.message || 'Login WhatsApp dimulai.', 'success');
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Gagal memulai login WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        showToast(message, 'error');
    }
}

async function logoutWhatsAppSession() {
    const ok = await showConfirm(
        'Logout WhatsApp dari aplikasi ini?\n\nSetelah logout, koneksi lama akan dihapus dan Anda perlu scan QR ulang.',
        'warning',
        { confirmText: 'Ya, Logout', cancelText: 'Batal' }
    );
    if (!ok) return;
    if (openwaAutoRefreshTimer) {
        clearTimeout(openwaAutoRefreshTimer);
        openwaAutoRefreshTimer = null;
    }
    setWhatsAppResult(whatsappStatusRow('Logout WhatsApp...', 'info'));
    setWhatsAppLoginPanel('<span><i class="fas fa-spinner fa-spin"></i> Menghapus koneksi WhatsApp lama...</span>');
    try {
        const response = await fetch('/whatsapp/session/logout', { method: 'POST', body: buildSessionFormData() });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal logout WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(data.message || 'WhatsApp berhasil logout.', 'success'));
        setWhatsAppLoginPanel('<span><strong>WhatsApp sudah logout.</strong><br>Klik <b>Perbarui Status</b> untuk membuat QR baru, lalu scan dari WhatsApp HP.</span>');
        showToast(data.message || 'WhatsApp berhasil logout.', 'success');
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Gagal logout WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        setWhatsAppLoginPanel(`<span>${escapeHtml(message)}</span>`);
        showToast(message, 'error');
    }
}

async function showOpenWAQRCode() {
    setWhatsAppResult(whatsappStatusRow('Mengambil QR login WhatsApp...', 'info'));
    setWhatsAppLoginPanel('<span><i class="fas fa-spinner fa-spin"></i> Menunggu QR WhatsApp...</span>');
    try {
        const sessionId = encodeURIComponent(getOpenWASessionIdFromForm());
        const response = await fetch(`/whatsapp/session/qr${sessionId ? `?session_id=${sessionId}` : ''}`);
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal mengambil QR WhatsApp.');
        const qr = extractOpenWAQR(data);
        const imageSrc = qr && (qr.startsWith('data:image/') || /^https?:\/\//.test(qr)) ? qr : '';
        if (!imageSrc) throw new Error('QR belum tersedia.');
        setWhatsAppResult(whatsappStatusRow('QR login siap. Scan dari WhatsApp > Perangkat Tertaut.', 'success'));
        setWhatsAppLoginPanel(renderWhatsAppLoginState({ status: 'waiting', qr: imageSrc }));
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Gagal mengambil QR WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        setWhatsAppLoginPanel(`<span>${escapeHtml(message)}</span>`);
        showToast(message, 'error');
    }
}

async function checkOpenWAStatus() {
    setWhatsAppResult(whatsappStatusRow('Mengecek status WhatsApp...', 'info'));
    try {
        const sessionId = encodeURIComponent(getOpenWASessionIdFromForm());
        const response = await fetch(`/whatsapp/session/status${sessionId ? `?session_id=${sessionId}` : ''}`);
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal mengecek status WhatsApp.');
        setWhatsAppResult(whatsappStatusRow('Status WhatsApp berhasil dimuat.', 'success'));
        setWhatsAppLoginPanel(renderWhatsAppLoginState(data.data || data));
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Gagal mengecek status WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        showToast(message, 'error');
    }
}

async function submitWhatsAppSettings(event) {
    event.preventDefault();
    const form = event.target;
    const button = form?.querySelector('button[type="submit"]');
    const originalText = button ? button.innerHTML : '';
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
    }
    setWhatsAppResult(whatsappStatusRow('Menyimpan pengaturan WhatsApp...', 'info'));

    try {
        const response = await fetch('/whatsapp/settings', { method: 'POST', body: new FormData(form) });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal menyimpan pengaturan WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(data.message || 'Pengaturan WhatsApp tersimpan.', 'success'));
        showToast(data.message || 'Pengaturan WhatsApp tersimpan.', 'success');
        const activeTab = document.querySelector('.nav-links li.active');
        if (activeTab?.getAttribute('data-tab') === 'settings') {
            await loadTab('settings');
        }
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Gagal menyimpan pengaturan WhatsApp.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        showToast(message, 'error');
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
}

async function testOpenWAHealth() {
    setWhatsAppResult(whatsappStatusRow('Mengecek koneksi OpenWA...', 'info'));
    try {
        const response = await fetch('/whatsapp/health-check', { method: 'POST', body: new FormData() });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Koneksi OpenWA gagal.');
        setWhatsAppResult(whatsappStatusRow('OpenWA tersambung.', 'success'));
        showToast('OpenWA tersambung.', 'success');
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Koneksi OpenWA gagal.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        showToast(message, 'error');
    }
}

async function processWhatsAppQueue() {
    setWhatsAppResult(whatsappStatusRow('Mengirim follow-up tertunda...', 'info'));
    try {
        const response = await fetch('/whatsapp/process-queue', { method: 'POST', body: new FormData() });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal mengirim follow-up tertunda.');
        const sent = (data.processed || []).filter(item => item.status === 'sent').length;
        const failed = (data.processed || []).filter(item => item.status !== 'sent').length;
        const message = `Follow-up diproses: ${data.count || 0}. Terkirim: ${sent}. Belum berhasil: ${failed}.`;
        setWhatsAppResult(whatsappStatusRow(message, failed ? 'info' : 'success'));
        showToast(message, failed ? 'info' : 'success');
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Gagal mengirim follow-up tertunda.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        showToast(message, 'error');
    }
}

async function sendWhatsAppTestMessage(event) {
    event.preventDefault();
    const form = event.target;
    const button = form?.querySelector('button[type="submit"]');
    const originalText = button ? button.innerHTML : '';
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Mengirim...';
    }
    setWhatsAppResult(whatsappStatusRow('Mengirim pesan percobaan...', 'info'));
    try {
        const response = await fetch('/whatsapp/send-test', { method: 'POST', body: new FormData(form) });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal mengirim pesan percobaan.');
        setWhatsAppResult(whatsappStatusRow('Pesan percobaan berhasil dikirim.', 'success'));
        showToast('Pesan percobaan berhasil dikirim.', 'success');
    } catch (error) {
        const message = normalizeOpenWAErrorMessage(error.message || 'Gagal mengirim pesan percobaan.');
        setWhatsAppResult(whatsappStatusRow(message, 'error'));
        showToast(message, 'error');
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
}

let discountRulesCache = [];

function setDiscountRuleType(type) {
    const typeSelect = document.getElementById('discount-rule-type');
    if (typeSelect) typeSelect.value = type;
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
    if (condition) condition.required = type === 'visit_count';
    if (voucher) voucher.required = type === 'voucher';
    if (usageLimit) usageLimit.required = false;
    if (perPatientLimit) perPatientLimit.required = false;
    if (start) start.required = type === 'period' && !end?.value;
    if (end) end.required = type === 'period' && !start?.value;

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
    if (title) title.textContent = active ? 'Aktif' : 'Nonaktif';
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
    if (title) title.textContent = active ? 'Harga manual aktif' : 'Harga normal';
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
    if (result) result.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menghitung simulasi...';

    try {
        const response = await fetch(`/discount_rules/simulate?${params.toString()}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Gagal menjalankan simulasi.');
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
    } catch (error) {
        result.innerHTML = `<div class="settings-error-row">${escapeHtml(error.message)}</div>`;
    }
}

function formatBackupSize(bytes) {
    const value = Number(bytes || 0);
    if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
    if (value >= 1024) return `${(value / 1024).toFixed(1)} KB`;
    return `${value} B`;
}

function renderBackupManagement(data) {
    const list = document.getElementById('backup-management-list');
    const result = document.getElementById('backup-management-result');
    if (!list) return;

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
            <button type="button" data-settings-action="restore-backup" data-path="${escapeHtml(item.path)}" title="Restore backup">
                <i class="fas fa-undo-alt"></i>
            </button>
        </div>
    `).join('');
}

async function loadBackupManagement() {
    const list = document.getElementById('backup-management-list');
    if (list) list.innerHTML = '<div class="settings-muted-row"><i class="fas fa-spinner fa-spin"></i> Memuat daftar backup...</div>';

    try {
        const data = await apiGetJson<BackupListResponse>('/backups', { timeoutMs: 8000 });
        renderBackupManagement(data);
    } catch (error) {
        if (list) {
            const isOffline = error instanceof TypeError && error.message.includes('Failed to fetch') || error.name === 'AbortError';
            const message = isOffline
                ? 'Tidak dapat terhubung ke server lokal. Periksa apakah backend berjalan.'
                : escapeHtml(error.message);
            list.innerHTML = `
                <div class="settings-error-row">${message}</div>
                <div class="settings-info-row" style="margin-top: 12px;">
                    <i class="fas fa-info-circle"></i>
                    <span>Backup masih dapat diakses melalui folder data aplikasi: <code id="backup-folder-path" style="font-size: 11px;">Memuat...</code></span>
                </div>
                <button type="button" class="btn btn-secondary" style="margin-top: 8px;" data-settings-action="open-backup-folder">
                    <i class="fas fa-folder-open"></i> Buka Folder Backup
                </button>
            `;
            loadBackupFolderPath();
        }
    }
}

async function loadBackupFolderPath() {
    try {
        const data = await apiGetJson<{ backup_dir: string }>('/support/app_info', { timeoutMs: 5000 });
        const pathEl = document.getElementById('backup-folder-path');
        if (pathEl) pathEl.textContent = data.backup_dir || 'Tidak tersedia';
    } catch {
        const pathEl = document.getElementById('backup-folder-path');
        if (pathEl) pathEl.textContent = 'Tidak dapat dimuat';
    }
}

function openBackupFolder() {
    if (window.LancarApi?.openPath) {
        window.LancarApi.openPath('backups').catch(() => {
            showToast('Gagal membuka folder backup.', 'error');
        });
    }
}

async function createWebBackup() {
    const result = document.getElementById('backup-management-result');
    if (result) result.innerHTML = '<div class="settings-info-row"><i class="fas fa-spinner fa-spin"></i><span>Membuat backup database...</span></div>';

    try {
        const data = await apiPostForm<{ status: string; message: string }>('/backups/create', new FormData(), { timeoutMs: 15000 });
        if (data.status !== 'success') throw new Error(data.message || 'Gagal membuat backup.');
        showToast(data.message || 'Backup berhasil dibuat.', 'success');
        await loadBackupManagement();
    } catch (error) {
        const isOffline = error instanceof TypeError && error.message.includes('Failed to fetch') || error.name === 'AbortError';
        const message = isOffline
            ? 'Tidak dapat terhubung ke server lokal. Periksa apakah backend berjalan.'
            : escapeHtml(error.message);
        if (result) result.innerHTML = `<div class="settings-error-row">${message}</div>`;
    }
}

async function restoreWebBackup(path) {
    const ok = await showConfirm('Restore database dari backup ini? Database aktif akan dibuatkan backup pengaman terlebih dahulu.', 'warning');
    if (!ok) return;

    const result = document.getElementById('backup-management-result');
    if (result) result.innerHTML = '<div class="settings-info-row"><i class="fas fa-spinner fa-spin"></i><span>Restore backup...</span></div>';

    try {
        const formData = new FormData();
        formData.set('relative_path', path);
        const data = await apiPostForm<{ status: string; message: string }>('/backups/restore', formData, { timeoutMs: 30000 });
        if (data.status !== 'success') throw new Error(data.message || 'Gagal restore backup.');
        showToast(data.message || 'Restore backup berhasil.', 'success');
        await loadBackupManagement();
    } catch (error) {
        const isOffline = error instanceof TypeError && error.message.includes('Failed to fetch') || error.name === 'AbortError';
        const message = isOffline
            ? 'Tidak dapat terhubung ke server lokal. Periksa apakah backend berjalan.'
            : escapeHtml(error.message);
        if (result) result.innerHTML = `<div class="settings-error-row">${message}</div>`;
    }
}

function renderLicenseSettingsStatus(data) {
    const box = document.getElementById('license-settings-status');
    const clinicInput = document.getElementById('license-clinic-id');
    if (!box) return;

    const isValid = data && data.valid === true && data.status !== 'expired';
    const keyText = data && data.license_key ? data.license_key : 'Belum tersedia';
    const clinicId = data && data.clinic_id ? data.clinic_id : '';
    const expiredAt = data && data.expired_at ? formatLicenseSettingsDate(data.expired_at) : '-';
    const message = data && data.message ? data.message : '';

    if (clinicInput && !clinicInput.value) clinicInput.value = clinicId;

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
    if (!text) return '-';

    if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
        const [year, month, day] = text.split('-').map(Number);
        return new Date(year, month - 1, day).toLocaleDateString('id-ID', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    }

    const date = new Date(text);
    if (Number.isNaN(date.getTime())) return text;

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
        if (!response.ok) throw new Error(data.detail || 'Gagal memuat status lisensi.');
        renderLicenseSettingsStatus(data);
    } catch (error) {
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
        result.innerHTML = '<div style="color:#4f46e5;font-size:13px;"><i class="fas fa-spinner fa-spin"></i> Menghubungi pusat lisensi...</div>';
    }

    try {
        const response = await fetch('/activate_license', {
            method: 'POST',
            body: new FormData(form),
        });
        const data = await response.json();
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Aktivasi lisensi gagal.');

        if (result) {
            result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#ecfdf5; color:#065f46; font-size:13px;">${escapeHtml(data.message)}</div>`;
        }
        document.getElementById('license-key-input').value = '';
        renderLicenseSettingsStatus(data.license || {});
        if (typeof loadLicenseStatus === 'function') await loadLicenseStatus();
    } catch (error) {
        if (result) {
            result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#fef2f2; color:#dc2626; font-size:13px;">${escapeHtml(error.message)}</div>`;
        }
        await loadLicenseSettingsStatus();
    } finally {
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
        if (!result) return;
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
    } catch (error) {
        showPinResult(error.message || 'Gagal mengubah PIN admin.');
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
}

function renderAdminPinResetResult(message, type = 'error') {
    const result = document.getElementById('admin-pin-reset-result');
    if (!result) return;
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
    renderAdminPinResetResult('Menghubungi pusat lisensi untuk membuat permintaan reset...', 'success');

    try {
        const response = await fetch('/admin_pin/reset/request', { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') {
            throw new Error(data.detail || 'Gagal meminta kode reset PIN ke pusat lisensi.');
        }
        const suffix = data.reset_request_id ? ` ID permintaan: ${data.reset_request_id}` : '';
        const form = document.getElementById('admin-pin-reset-form');
        if (form) form.dataset.resetReady = 'true';
        renderAdminPinResetResult(`${data.message || 'Permintaan reset PIN dikirim.'}${suffix}`, 'success');
        showToast('Permintaan reset PIN dikirim ke pusat lisensi.', 'success');
    } catch (error) {
        renderAdminPinResetResult(error.message || 'Gagal meminta reset PIN.');
    } finally {
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
    const resetReady = form.dataset.resetReady === 'true';
    const resetPin = document.getElementById('admin-reset-token')?.value.trim() || '';
    const newPin = document.getElementById('admin-reset-new-pin')?.value.trim() || '';
    const confirmPin = document.getElementById('admin-reset-confirm-pin')?.value.trim() || '';

    if (!resetPin) {
        renderAdminPinResetResult('Kode reset lisensi wajib diisi.');
        return;
    }
    if (!resetReady) {
        renderAdminPinResetResult('Kode reset belum siap. Klik Minta Kode Reset ulang.');
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
    } catch (error) {
        renderAdminPinResetResult(error.message || 'Gagal reset PIN admin.');
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
}

async function seedDemoData() {
    const result = document.getElementById('demo-data-result');
    const ok = await showConfirm('Data contoh akan bercampur dengan data asli jika database sudah berisi data. Lanjutkan?', 'warning');
    if (!ok) return;
    if (result) result.innerHTML = '<div class="settings-info-row"><i class="fas fa-spinner fa-spin"></i><span>Mengisi data contoh...</span></div>';
    try {
        const response = await fetch('/demo_data/seed', { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal mengisi data contoh.');
        if (result) result.innerHTML = `<div class="settings-info-row success"><i class="fas fa-check-circle"></i><span>${escapeHtml(data.message || 'Data contoh berhasil ditambahkan.')}</span></div>`;
        showToast(data.message || 'Data contoh berhasil ditambahkan.', 'success');
    } catch (error) {
        if (result) result.innerHTML = `<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>${escapeHtml(error.message)}</span></div>`;
    }
}

async function clearDemoData() {
    const result = document.getElementById('demo-data-result');
    const ok = await showConfirm('Hapus/nonaktifkan data demo yang dikenali sistem? Data asli tidak akan disentuh.', 'warning');
    if (!ok) return;
    if (result) result.innerHTML = '<div class="settings-info-row"><i class="fas fa-spinner fa-spin"></i><span>Menghapus data demo...</span></div>';
    try {
        const response = await fetch('/demo_data/clear', { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal menghapus data demo.');
        if (result) result.innerHTML = `<div class="settings-info-row success"><i class="fas fa-check-circle"></i><span>${escapeHtml(data.message || 'Data demo dihapus.')}</span></div>`;
        showToast(data.message || 'Data demo dihapus.', 'success');
    } catch (error) {
        if (result) result.innerHTML = `<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>${escapeHtml(error.message)}</span></div>`;
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
                        <button type="button" class="btn btn-secondary" data-settings-action="open-export-folder" style="width:auto;margin-top:8px;">
                            <i class="fas fa-folder-open"></i> Buka Folder
                        </button>
                    </span>
                </div>
            `;
        }
        showToast(message, 'success');
    } catch (error) {
        const message = sanitizeAppErrorMessage(error.message, 'Gagal export data.');
        if (result) {
            result.innerHTML = `<div class="settings-error-row"><i class="fas fa-exclamation-circle"></i><span>${escapeHtml(message)}</span></div>`;
        }
        showToast(message, 'error');
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = original;
        }
    }
}

async function loadSettingsExportFolder() {
    const box = document.getElementById('settings-export-folder');
    if (!box) return;
    try {
        const response = await fetch('/support/app_info');
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || 'Gagal memuat folder export.');
        box.innerHTML = `
            <i class="fas fa-folder"></i>
            <span>Folder export:<br><small>${escapeHtml(data.exports_dir || '-')}</small></span>
        `;
    } catch (error) {
        box.innerHTML = `<i class="fas fa-exclamation-circle"></i><span>${escapeHtml(sanitizeAppErrorMessage(error.message, 'Gagal memuat folder export.'))}</span>`;
        box.classList.add('settings-error-row');
    }
}

async function openSettingsExportFolder() {
    try {
        const data = await window.LancarApi!.openPath<ApiResponse>('exports');
        if (data.status && data.status !== 'success') {
            throw new Error(window.LancarApi!.getErrorMessage(data, 'Gagal membuka folder export.'));
        }
        showToast('Folder export dibuka.', 'success');
    } catch (error) {
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
    if (rule.discount_type === 'percent') return `${Number(rule.discount_value || 0)}%`;
    return formatRupiah(Number(rule.discount_value || 0));
}

function formatDiscountRuleCondition(rule) {
    if (rule.type === 'visit_count') return rule.condition_value ? `Mulai kunjungan ke-${Number(rule.condition_value)} dan seterusnya` : '-';
    if (rule.type === 'voucher') {
        const used = Number(rule.usage_count || 0);
        const total = rule.usage_limit ? `${used}/${Number(rule.usage_limit)} kali` : `${used} kali`;
        const patient = rule.per_patient_limit ? `, max ${Number(rule.per_patient_limit)}x/pasien` : '';
        const targets = Array.isArray(rule.target_patient_names) && rule.target_patient_names.length
            ? ` - khusus: ${rule.target_patient_names.slice(0, 3).join(', ')}${rule.target_patient_names.length > 3 ? ' +' + (rule.target_patient_names.length - 3) : ''}`
            : '';
        return `${rule.voucher_code || '-'} - terpakai ${total}${patient}${targets}`;
    }
    if (rule.type === 'manual') return 'Harga manual';
    return 'Tanggal aktif';
}

function formatDiscountRulePeriod(rule) {
    const start = rule.start_date || '-';
    const end = rule.end_date || '-';
    if (start === '-' && end === '-') return '-';
    return `${start} s/d ${end}`;
}

async function loadDiscountRules() {
    const body = document.getElementById('discount-rules-body');
    if (!body) return;

    try {
        const response = await fetch('/discount_rules');
        if (!response.ok) throw new Error('Gagal memuat aturan diskon');
        discountRulesCache = await response.json();

        if (!discountRulesCache.length) {
            body.innerHTML = '<tr><td colspan="7" style="padding:14px; color:var(--text-muted);">Belum ada aturan diskon dinamis.</td></tr>';
            return;
        }

        body.innerHTML = discountRulesCache.map(rule => `
            <tr style="border-top:1px solid var(--color-border); font-size:13px;">
                <td style="padding:10px;"><strong>${escapeHtml(rule.name)}</strong><br><span style="color:var(--text-muted);">Prioritas ${rule.priority}</span></td>
                <td style="padding:10px;">${formatDiscountRuleType(rule.type)}</td>
                <td style="padding:10px;">${formatDiscountRuleValue(rule)}</td>
                <td style="padding:10px;">${escapeHtml(formatDiscountRuleCondition(rule))}</td>
                <td style="padding:10px;">${escapeHtml(formatDiscountRulePeriod(rule))}</td>
                <td style="padding:10px;">
                    <button type="button" data-settings-action="toggle-discount-rule" data-rule-id="${Number(rule.id)}" data-next-active="${!rule.is_active}"
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
                    <button type="button" class="discount-rule-action edit" data-settings-action="edit-discount-rule" data-rule-id="${Number(rule.id)}" title="Edit"><i class="fas fa-edit"></i></button>
                    <button type="button" class="discount-rule-action delete" data-settings-action="delete-discount-rule" data-rule-id="${Number(rule.id)}" title="Hapus"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        body.innerHTML = `<tr><td colspan="7" style="padding:14px; color:#dc2626;">${escapeHtml(error.message)}</td></tr>`;
    }
}

function resetDiscountRuleForm() {
    const form = document.getElementById('discount-rule-form');
    if (!form) return;
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
    if (!rule) return;

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
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Gagal menyimpan aturan diskon.');
        result.innerHTML = `<div style="padding:10px; border-radius:8px; background:#ecfdf5; color:#065f46; font-size:13px;">${escapeHtml(data.message)}</div>`;
        resetDiscountRuleForm();
        await loadDiscountRules();
    } catch (error) {
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
    if (!ok) return;

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
    if (!fileInput.files[0]) return;

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
    } catch (e) {
        resultDiv.innerHTML = `<div style="padding:12px;border-radius:8px;background:#fef2f2;border:1px solid #fecaca;color:#dc2626;font-size:13px;"><i class="fas fa-times-circle"></i> Error: ${e.message}</div>`;
    }
}



