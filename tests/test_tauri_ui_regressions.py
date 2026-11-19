import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def css_block(source, selector):
    match = re.search(re.escape(selector) + r"\s*\{(?P<body>[^}]*)\}", source, flags=re.S)
    if not match:
        raise AssertionError(f"Selector tidak ditemukan: {selector}")
    return match.group("body")


def last_css_block(source, selector):
    matches = re.findall(re.escape(selector) + r"\s*\{(?P<body>[^}]*)\}", source, flags=re.S)
    if not matches:
        raise AssertionError(f"Selector tidak ditemukan: {selector}")
    return matches[-1]


class TestTauriUiRegressionGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.style = (ROOT / "api" / "static" / "style.css").read_text(encoding="utf-8")
        cls.input_css = (ROOT / "api" / "static" / "src" / "input.css").read_text(encoding="utf-8")
        cls.patients = (ROOT / "api" / "static" / "ts" / "patients.ts").read_text(encoding="utf-8")
        cls.settings = (ROOT / "api" / "static" / "ts" / "settings.ts").read_text(encoding="utf-8")
        cls.whatsapp_gateway = (ROOT / "api" / "static" / "ts" / "whatsapp_gateway.ts").read_text(encoding="utf-8")
        cls.crm = (ROOT / "api" / "static" / "ts" / "crm.ts").read_text(encoding="utf-8")
        cls.modal = (ROOT / "api" / "static" / "ts" / "modal.ts").read_text(encoding="utf-8")
        cls.api = (ROOT / "api" / "static" / "ts" / "api.ts").read_text(encoding="utf-8")
        cls.app = (ROOT / "api" / "static" / "ts" / "app.ts").read_text(encoding="utf-8")
        cls.utils = (ROOT / "api" / "static" / "ts" / "utils.ts").read_text(encoding="utf-8")
        cls.therapists = (ROOT / "api" / "static" / "ts" / "therapists.ts").read_text(encoding="utf-8")
        cls.services = (ROOT / "api" / "static" / "ts" / "services.ts").read_text(encoding="utf-8")
        cls.analytics = (ROOT / "api" / "static" / "ts" / "analytics.ts").read_text(encoding="utf-8")
        cls.invoices = (ROOT / "api" / "static" / "ts" / "invoices.ts").read_text(encoding="utf-8")
        cls.help = (ROOT / "api" / "static" / "ts" / "help.ts").read_text(encoding="utf-8")
        cls.herbals = (ROOT / "api" / "static" / "ts" / "herbals.ts").read_text(encoding="utf-8")
        cls.inventory = (ROOT / "api" / "static" / "ts" / "inventory.ts").read_text(encoding="utf-8")
        cls.tauri_capability = json.loads((ROOT / "src-tauri" / "capabilities" / "default.json").read_text(encoding="utf-8"))

    def test_visit_patient_picker_is_not_sticky_and_closes_when_input_blurs(self):
        picker_block = css_block(self.style, ".visit-quick-picker,\n.visit-form-card")

        self.assertIn("position: static", picker_block)
        self.assertNotIn("position: sticky", picker_block)
        self.assertIn("input.addEventListener('blur'", self.patients)
        self.assertIn("closeVisitPatientResults()", self.patients)
        self.assertIn("results.addEventListener('pointerdown'", self.patients)
        self.assertIn("e.preventDefault()", self.patients)
        self.assertIn("const selectVisitPatientResult", self.patients)
        self.assertIn("selectVisitPatientResult(btn)", self.patients)
        self.assertIn('data-ui-revision="phase3d-r3-reopened"', self.patients)

    def test_payment_dynamic_content_has_wrapping_and_no_narrow_button_clamp(self):
        action_block = css_block(self.style, ".invoice-action-btn-text")
        meta_block = css_block(self.style, ".invoice-payment-meta")

        self.assertIn("max-width: 100%", action_block)
        self.assertIn("white-space: normal", action_block)
        self.assertIn("overflow-wrap: anywhere", action_block)
        self.assertIn("min-width: 0", meta_block)
        self.assertIn("line-height: 1.45", meta_block)
        self.assertIn("min-w-0", self.input_css)
        self.assertNotIn("max-width: 128px", action_block)

    def test_visit_payment_quick_actions_wrap_icon_and_text_in_narrow_card(self):
        actions_block = css_block(self.style, ".visit-payment-quick-actions")
        button_block = css_block(self.style, ".visit-payment-quick-actions button")

        self.assertIn("display: flex", actions_block)
        self.assertIn("flex-wrap: wrap", actions_block)
        self.assertIn("flex: 1 1 142px", button_block)
        self.assertIn("white-space: normal", button_block)
        self.assertIn("overflow-wrap: anywhere", button_block)
        self.assertNotIn("white-space: nowrap", button_block)

    def test_therapist_and_service_counts_are_rendered_only_in_filter_tabs(self):
        self.assertNotIn('class="therapist-stats-badges"', self.therapists)
        self.assertNotIn('class="service-header-stats"', self.services)
        self.assertIn("therapist-filter-btn", self.therapists)
        self.assertIn("service-filter-btn", self.services)

    def test_analytics_and_dark_mode_provide_responsive_readable_guards(self):
        monitor_grid = css_block(self.input_css, ".analytics-monitor-grid")
        monitor_value = css_block(self.input_css, ".analytics-monitor-item strong")
        insight_grid = css_block(self.input_css, ".analytics-insight-grid")

        self.assertIn("auto-fit", monitor_grid)
        self.assertIn("minmax(220px,1fr)", monitor_grid)
        self.assertIn("whitespace-normal", monitor_value)
        self.assertNotIn("text-ellipsis", monitor_value)
        self.assertIn("auto-fit", insight_grid)
        self.assertNotIn("grid-template-columns: repeat(4, minmax(0, 1fr));", self.input_css)
        self.assertNotIn("grid-template-columns: repeat(5, minmax(0, 1fr));", self.input_css)
        self.assertIn("--theme-surface", self.style)
        self.assertIn("body.theme-dark .visit-payment-quick-actions button", self.style)
        self.assertIn("body.theme-dark .therapist-card", self.style)
        self.assertIn("body.theme-dark .service-card", self.style)
        self.assertIn('data-ui-revision="phase3d-r3-reopened"', self.analytics)

    def test_r3_service_card_is_compact_left_aligned_with_labeled_actions(self):
        card_block = last_css_block(self.style, ".service-card")
        icon_block = last_css_block(self.style, ".service-card-icon")
        action_block = last_css_block(self.style, ".service-card-action")

        self.assertIn("min-height: 0", card_block)
        self.assertIn("width: 38px", icon_block)
        self.assertIn("width: auto", action_block)
        self.assertIn("<span>Edit</span>", self.services)
        self.assertIn("Nonaktifkan", self.services)
        self.assertIn("<span>Hapus</span>", self.services)
        self.assertIn("service-card-title-group", self.services)

    def test_r3_patient_and_invoice_actions_are_readable_buttons_that_wrap(self):
        patient_block = last_css_block(self.style, ".patient-edit-btn,\n.visit-edit-btn")
        invoice_block = last_css_block(self.style, ".invoice-action-btn,\n.invoice-action-btn-text")

        self.assertIn("min-height: 44px", patient_block)
        self.assertIn("min-width: 76px", patient_block)
        self.assertIn("flex: 0 0 auto", patient_block)
        self.assertIn("font-size: 13px", patient_block)
        self.assertIn("<span>Edit</span>", self.patients)
        self.assertIn("patient-action-buttons-compact", self.patients)
        self.assertIn('data-patient-action="edit"', self.patients)
        self.assertIn('data-patient-action="visits"', self.patients)
        self.assertIn("<span>Edit Pasien</span>", self.patients)
        self.assertIn("width: auto", invoice_block)
        self.assertIn("white-space: normal", invoice_block)
        self.assertIn("<span>Lihat</span>", self.invoices)
        self.assertIn("<span>Print</span>", self.invoices)
        self.assertIn("<span>Cek Status</span>", self.invoices)

    def test_phase4a_native_path_helpers_use_tauri_wrapper_with_safe_fallbacks(self):
        self.assertIn('invoke<T>("native_open_path"', self.api)
        self.assertIn('invoke<T>("native_reveal_path"', self.api)
        self.assertIn("openPath: openDesktopPath", self.api)
        self.assertIn("revealPath: revealDesktopPath", self.api)
        self.assertIn("/support/open_folder?kind=", self.api)
        self.assertIn("'/open_invoice?path=' + encodeURIComponent(path)", self.api)
        self.assertIn("isNativeCommandUnavailable(error)", self.api)
        self.assertIn("window.LancarApi!.openPath<SupportOpenFolderResponse>", self.help)
        self.assertIn("window.LancarApi!.openPath<ApiResponse>('exports')", self.settings)
        self.assertNotIn("window.__TAURI__.shell", self.api)
        self.assertNotIn("window.__TAURI__.fs", self.api)

    def test_phase4a_native_invoice_file_helper_uses_tauri_wrapper_with_safe_fallback(self):
        self.assertIn('invoke<T>("native_open_invoice_file"', self.api)
        self.assertIn("openInvoiceFileFallback<T>(path, action)", self.api)
        self.assertIn("'/open_invoice?path=' + encodeURIComponent(path)", self.api)
        self.assertIn("Fitur reveal invoice native belum tersedia.", self.api)
        self.assertIn("openInvoiceFile: openDesktopInvoiceFile", self.api)
        self.assertIn("window.openDesktopInvoiceFile = openDesktopInvoiceFile", self.api)
        self.assertIn("window.LancarApi!.openInvoiceFile<ApiResponse>(path, 'open')", self.invoices)
        self.assertIn("window.LancarApi!.openInvoiceFile<ApiResponse>(path, 'reveal')", self.invoices)
        self.assertIn("function generateInvoiceForVisit", self.invoices)
        self.assertIn("fetch('/generate_invoice'", self.invoices)
        self.assertIn("function generateInvoiceForHerbal", self.invoices)
        self.assertIn("fetch('/generate_herbal_invoice'", self.invoices)

        for source in [self.api, self.invoices]:
            self.assertNotIn("window.open(", source)
            self.assertNotIn("window.__TAURI__.shell", source)
            self.assertNotIn("window.__TAURI__.fs", source)

    def test_phase4a_native_invoice_commands_are_allowed_for_loopback_webview_only(self):
        permissions = self.tauri_capability["permissions"]
        self.assertIn("allow-native-open-invoice-file", permissions)
        self.assertIn("allow-native-print-file", permissions)
        self.assertIn("allow-native-reveal-path", permissions)
        self.assertEqual(["http://127.0.0.1:*"], self.tauri_capability.get("remote", {}).get("urls"))
        self.assertNotIn("http://localhost:*", self.tauri_capability.get("remote", {}).get("urls", []))
        self.assertNotIn("https://*", self.tauri_capability.get("remote", {}).get("urls", []))

    def test_phase4a_native_print_file_helper_uses_tauri_wrapper_with_safe_fallback(self):
        self.assertIn('invoke<T>("native_print_file"', self.api)
        self.assertIn("printFileFallback<T>(path)", self.api)
        self.assertIn("'/print_invoice?path=' + encodeURIComponent(path)", self.api)
        self.assertIn("printFile: printDesktopFile", self.api)
        self.assertIn("window.printDesktopFile = printDesktopFile", self.api)
        self.assertIn("type NativePrintFileSource = \"invoice\" | \"herbal_invoice\" | \"export\" | \"receipt\"", self.api)
        self.assertIn("window.LancarApi!.printFile<ApiResponse & { message?: string }>(path, source)", self.invoices)
        self.assertIn("status === 'printed' || status === 'success'", self.invoices)
        self.assertIn("status === 'open_fallback'", self.invoices)
        self.assertIn("case 'print-invoice':", self.invoices)
        self.assertIn('data-invoice-action="print-invoice"', self.invoices)
        self.assertIn('data-print-source="herbal_invoice"', self.invoices)
        self.assertIn('data-print-source="invoice"', self.invoices)
        self.assertIn("function generateInvoiceForVisit", self.invoices)
        self.assertIn("fetch('/generate_invoice'", self.invoices)
        self.assertIn("function generateInvoiceForHerbal", self.invoices)
        self.assertIn("fetch('/generate_herbal_invoice'", self.invoices)

        for source in [self.api, self.invoices]:
            self.assertNotIn("window.open(", source)
            self.assertNotIn("window.__TAURI__.shell", source)
            self.assertNotIn("window.__TAURI__.fs", source)

    def test_phase4a_native_external_url_helper_uses_tauri_wrapper_with_safe_fallback(self):
        self.assertIn('invoke<T>("native_open_external_url"', self.api)
        self.assertIn("openExternalUrlFallback<T>(url)", self.api)
        self.assertIn("isNativeCommandUnavailable(error)", self.api)
        self.assertIn('type NativeExternalUrlSource = "payment" | "whatsapp_help" | "gateway_dashboard" | "support" | "unknown"', self.api)
        self.assertIn("openExternalUrl: openDesktopExternalUrl", self.api)
        self.assertIn("await openDesktopExternalUrl(paymentUrl, 'payment')", self.invoices)
        self.assertIn("await openDesktopExternalUrl(url, 'payment')", self.invoices)
        self.assertIn("await openDesktopExternalUrl(button.dataset.url || '', 'whatsapp_help')", self.help)
        self.assertIn("await openDesktopExternalUrl('http://127.0.0.1:3000', 'gateway_dashboard')", self.settings)

        for source in [self.api, self.invoices, self.help, self.settings]:
            self.assertNotIn("window.open(", source)
            self.assertNotIn('target="_blank"', source)
            self.assertNotIn("window.__TAURI__.shell", source)
            self.assertNotIn("window.__TAURI__.opener", source)

        self.assertNotIn("app.midtrans.com", self.api)

    def test_r3_reopened_analytics_filters_do_not_orphan_the_last_period(self):
        premium_filter = css_block(self.input_css, ".analytics-period-filter-premium")
        premium_button = last_css_block(self.input_css, ".analytics-period-filter-premium button")
        hero = last_css_block(self.input_css, ".analytics-hero")

        self.assertIn("flex-nowrap", premium_filter)
        self.assertIn("overflow-x-auto", premium_filter)
        self.assertNotIn("flex-wrap", premium_filter)
        self.assertIn("whitespace-nowrap", premium_button)
        self.assertIn("shrink-0", premium_button)
        self.assertIn("minmax(390px, 460px)", hero)

    def test_r3_voucher_and_dark_mode_overrides_target_active_runtime_stylesheet(self):
        voucher_tabs = last_css_block(self.style, ".discount-type-picker button")

        self.assertIn("grid-template-columns: minmax(0, 1fr) minmax(250px, 300px);", self.style)
        self.assertIn("flex: 1 1 112px", voucher_tabs)
        self.assertIn("body.theme-dark .discount-admin-card", self.style)
        self.assertIn("body.theme-dark .invoice-card-wrapper", self.style)

    def test_whatsapp_ui_accepts_proxy_qr_string_without_calling_gateway_directly(self):
        self.assertIn("typeof data === 'string' ? data : ''", self.settings)
        self.assertIn("data?.qr?.qr", self.settings)
        self.assertIn("const qr = extractOpenWAQR(data);", self.settings)
        self.assertIn("Menunggu QR WhatsApp", self.settings)
        self.assertNotIn("`data:image/png;base64,${qr}`", self.settings)
        self.assertNotIn("fetch('http://127.0.0.1:3000", self.settings)
        self.assertNotIn('fetch("http://127.0.0.1:3000', self.settings)

    def test_whatsapp_profile_card_and_actions_have_structured_dark_mode_layout(self):
        actions = css_block(self.style, ".wa-actions-row .btn")
        profile_grid = css_block(self.style, ".wa-profile-grid")

        self.assertIn("wa-profile-card is-connected", self.settings)
        self.assertIn("Nama akun", self.settings)
        self.assertIn("Nomor WhatsApp", self.settings)
        self.assertIn("Status koneksi", self.settings)
        self.assertIn("wa-profile-card is-idle", self.whatsapp_gateway)
        self.assertIn("min-height: 44px", actions)
        self.assertIn("inline-flex", actions)
        self.assertIn("repeat(3, minmax(0, 1fr))", profile_grid)
        self.assertIn("body.theme-dark .wa-profile-card", self.style)

    def test_followup_contacted_action_posts_json_and_handles_non_json_failure(self):
        self.assertIn("/mark-whatsapp-contacted", self.crm)
        self.assertIn("'Content-Type': 'application/json'", self.crm)
        self.assertIn("JSON.stringify({ follow_up_date: followUpDate })", self.crm)
        self.assertIn("readCRMActionPayload", self.crm)
        self.assertIn("Gagal memperbarui status follow-up. Periksa log aplikasi.", self.crm)
        self.assertNotIn("fetch(`/crm/patient/${patientId}/whatsapp-confirm`", self.crm)

    def test_r3_reopen_dark_mode_tokens_and_runtime_dialog_surfaces_are_guarded(self):
        self.assertIn("--color-surface: var(--card-bg)", self.style)
        self.assertIn("body.theme-dark .dashboard-panel", self.style)
        self.assertIn("body.theme-dark .runtime-modal-panel", self.style)
        self.assertIn("body.theme-dark .system-dialog-panel", self.style)
        self.assertIn("body.theme-dark .analytics-period-filter-premium button", self.style)
        self.assertIn('class="runtime-modal-panel full-edit-panel"', self.modal)
        self.assertIn('class="runtime-modal-panel"', self.modal)
        self.assertIn('class="runtime-modal-close"', self.modal)
        self.assertNotIn("background:white", self.modal)
        self.assertNotIn("background:#fff", self.modal)
        self.assertIn('class="runtime-modal-panel"', self.app)
        self.assertNotIn("background:#fff", self.app)
        self.assertIn('class="system-dialog-panel"', self.utils)
        self.assertNotIn("background:#fff", self.utils)

    def test_r3_reopen_dark_mode_has_complete_semantic_token_contract(self):
        for token in [
            "--color-bg",
            "--color-bg-soft",
            "--color-surface",
            "--color-surface-2",
            "--color-surface-muted",
            "--color-surface-elevated",
            "--color-border",
            "--color-border-strong",
            "--color-text",
            "--color-text-muted",
            "--color-text-soft",
            "--color-primary",
            "--color-primary-soft",
            "--color-success",
            "--color-success-soft",
            "--color-warning",
            "--color-warning-soft",
            "--color-danger",
            "--color-danger-soft",
            "--color-info",
            "--color-input-bg",
            "--color-input-border",
            "--color-table-header",
            "--color-table-row",
            "--color-table-row-hover",
            "--color-modal-bg",
            "--color-toast-bg",
        ]:
            self.assertIn(token, self.style)

        self.assertIn("document.body.classList.toggle('theme-dark'", self.app)

    def test_r3_reopen_dark_mode_audit_covers_primary_page_surfaces(self):
        audit = self.style.split(
            "/* === Phase 3D-R3 Reopen: audited global dark surface coverage ============= */",
            1,
        )[1]

        for selector in [
            ".card-stats",
            ".patient-form-card",
            ".visit-form-card",
            ".therapist-card",
            ".service-card",
            ".herbal-table-card",
            ".inventory-table-card",
            ".invoice-card-wrapper",
            ".wa-profile-card",
            ".crm-followup-card",
            ".owner-kpi-card",
            ".analytics-kpi-card",
            ".discount-admin-card",
            ".settings-compact-grid .card",
            ".help-card",
        ]:
            self.assertIn(selector, audit)

        self.assertIn("var(--color-surface)", audit)
        self.assertIn("var(--color-surface-muted)", audit)

    def test_r3_reopen_dark_mode_guards_tables_forms_modals_without_light_surfaces(self):
        audit = self.style.split(
            "/* === Phase 3D-R3 Reopen: audited global dark surface coverage ============= */",
            1,
        )[1].lower()

        for selector in [
            ".datatables_wrapper .dt-top",
            ".patient-dt-table",
            ".herbal-table",
            ".inventory-table",
            ".runtime-modal-panel",
            ".system-dialog-panel",
            ".crm-modal",
            ".toast",
        ]:
            self.assertIn(selector, audit)

        self.assertIn("var(--color-input-bg)", audit)
        self.assertIn("var(--color-table-header)", audit)
        self.assertIn("var(--color-modal-bg)", audit)
        self.assertIn("var(--color-toast-bg)", audit)

        for hardcoded_light_surface in [
            "background: white",
            "background:white",
            "background: #fff",
            "background:#fff",
            "background: #ffffff",
            "background:#ffffff",
            "background-color: white",
            "background-color:white",
            "background-color: #fff",
            "background-color:#fff",
            "background: #f8fafc",
            "background: #f9fafb",
            "background: #f1f5f9",
            "background: #f3f4f6",
        ]:
            self.assertNotIn(hardcoded_light_surface, audit)

    def test_r3_reopen_settings_uses_searchable_category_workspace(self):
        self.assertIn('class="settings-workspace"', self.settings)
        self.assertIn('id="settings-search-input"', self.settings)
        self.assertIn("filterSettingsSections", self.settings)
        self.assertIn("setSettingsCategory", self.settings)
        self.assertIn("openSettingsWhatsAppTab", self.settings)
        self.assertIn(".settings-category-nav", self.style)
        self.assertIn("body.theme-dark .settings-workspace-head", self.style)
        self.assertIn('type="password" name="midtrans_server_key"', self.settings)
        self.assertNotIn('value="${escapeHtml(s.midtrans_server_key', self.settings)

    def test_r3_reopen_therapist_capability_ui_filters_visit_services(self):
        self.assertIn("therapistCapabilityPicker", self.therapists)
        self.assertIn('name="service_ids"', self.therapists)
        self.assertIn("if (action === 'capability-sync') return;", self.therapists)
        self.assertIn("therapist-capability-check", self.therapists)
        self.assertIn("option.classList.toggle('is-selected'", self.therapists)
        self.assertIn("service_capabilities", self.therapists)
        self.assertIn("Terapis belum memiliki layanan yang ditangani.", self.therapists)
        self.assertIn("service_capabilities", self.patients)
        self.assertIn("onVisitTherapistChange", self.patients)
        self.assertIn("Layanan otomatis dipilih sesuai terapis.", self.patients)
        self.assertIn("Terapis belum dikaitkan dengan layanan. Semua layanan masih ditampilkan.", self.patients)
        self.assertIn("Layanan direset karena tidak sesuai dengan terapis yang dipilih.", self.patients)
        self.assertIn(".therapist-capability-field", self.style)
        self.assertIn(".therapist-capability-check", self.style)
        self.assertIn(".therapist-capability-option.is-selected", self.style)
        self.assertIn(".visit-capability-helper.is-warning", self.style)

    def test_r3_reopen_stock_tabs_use_action_modals_instead_of_permanent_forms(self):
        herbal_render = self.herbals.split("function renderHerbals", 1)[1].split("function selectHerbal", 1)[0]
        inventory_render = self.inventory.split("function renderInventory", 1)[1].split("function selectInventory", 1)[0]

        self.assertNotIn('<form action="/add_herbal"', herbal_render)
        self.assertNotIn('<form action="/update_herbal"', herbal_render)
        self.assertNotIn("Tambah Produk Baru", herbal_render)
        self.assertIn('data-herbal-action="open-add"', herbal_render)
        self.assertIn('data-herbal-action="open-stock"', herbal_render)
        self.assertIn('data-herbal-action="open-sale"', herbal_render)
        self.assertIn('data-herbal-action="open-return"', herbal_render)

        self.assertNotIn('<form action="/add_inventory"', inventory_render)
        self.assertNotIn('<form action="/update_inventory"', inventory_render)
        self.assertIn('data-inventory-action="open-add"', inventory_render)
        self.assertIn('data-inventory-action="open-stock"', inventory_render)

    def test_r3_reopen_stock_actions_provide_search_selection_and_dark_mode_guards(self):
        self.assertIn('type="search" id="${context}-search"', self.herbals)
        self.assertIn("filterHerbalPicker", self.herbals)
        self.assertIn("selectHerbalPickerItem", self.herbals)
        self.assertIn("window._selectedHerbalId", self.herbals)
        self.assertIn("row-selected", self.herbals)
        self.assertIn('id="herbal-return-search"', self.herbals)

        self.assertIn('type="search" id="inventory-correction-search"', self.inventory)
        self.assertIn("filterInventoryPicker", self.inventory)
        self.assertIn("selectInventoryPickerItem", self.inventory)
        self.assertIn("window._selectedInventoryId", self.inventory)
        self.assertIn("row-selected", self.inventory)

        self.assertIn("body.theme-dark .action-picker", self.style)
        self.assertIn("background: var(--color-surface-muted)", self.style)
        self.assertIn("body.theme-dark .inventory-table tbody tr.row-selected", self.style)
        self.assertIn("body.theme-dark .herbal-table tbody tr.row-selected", self.style)


if __name__ == "__main__":
    unittest.main()
