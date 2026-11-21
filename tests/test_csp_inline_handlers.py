import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULES_DIR = ROOT / "api" / "static" / "modules"
TEMPLATES_DIR = ROOT / "api" / "templates"

INLINE_HANDLER_PATTERNS = [
    "onclick=",
    "onsubmit=",
    "onchange=",
    "oninput=",
    "onkeydown=",
    "onkeyup=",
    "onblur=",
    "onfocus=",
    'href="javascript:',
]

LEGACY_INLINE_HANDLER_ALLOWLIST = {}


class ScriptTagParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.executable_inline_scripts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "script":
            return
        attr_map = {name.lower(): value or "" for name, value in attrs}
        if "src" in attr_map:
            return
        script_type = attr_map.get("type", "").strip().lower()
        if script_type == "application/json":
            return
        self.executable_inline_scripts.append(attr_map)


class CspInlineHandlerGuardTest(unittest.TestCase):
    def test_generated_modules_do_not_add_inline_handlers(self):
        failures = []
        for path in sorted(MODULES_DIR.glob("*.js")):
            text = path.read_text(encoding="utf-8")
            allowed = LEGACY_INLINE_HANDLER_ALLOWLIST.get(path.name, {})
            for pattern in INLINE_HANDLER_PATTERNS:
                count = len(re.findall(re.escape(pattern), text))
                limit = allowed.get(pattern, 0)
                if count > limit:
                    failures.append(f"{path.name}: {pattern} count {count} exceeds allowlist {limit}")

        self.assertEqual([], failures)

    def test_templates_have_no_inline_handlers_or_executable_inline_scripts(self):
        failures = []
        for path in sorted(TEMPLATES_DIR.glob("*.html")):
            text = path.read_text(encoding="utf-8")
            for pattern in INLINE_HANDLER_PATTERNS:
                count = len(re.findall(re.escape(pattern), text))
                if count:
                    failures.append(f"{path.name}: {pattern} count {count}")

            parser = ScriptTagParser()
            parser.feed(text)
            if parser.executable_inline_scripts:
                failures.append(
                    f"{path.name}: executable inline <script> count {len(parser.executable_inline_scripts)}"
                )

        self.assertEqual([], failures)

    def test_refactored_modules_expose_delegation_guards(self):
        invoices = (ROOT / "api" / "static" / "ts" / "invoices.ts").read_text(encoding="utf-8")
        settings = (ROOT / "api" / "static" / "ts" / "settings.ts").read_text(encoding="utf-8")
        herbals = (ROOT / "api" / "static" / "ts" / "herbals.ts").read_text(encoding="utf-8")
        inventory = (ROOT / "api" / "static" / "ts" / "inventory.ts").read_text(encoding="utf-8")
        patients = (ROOT / "api" / "static" / "ts" / "patients.ts").read_text(encoding="utf-8")
        services = (ROOT / "api" / "static" / "ts" / "services.ts").read_text(encoding="utf-8")
        therapists = (ROOT / "api" / "static" / "ts" / "therapists.ts").read_text(encoding="utf-8")
        modal = (ROOT / "api" / "static" / "ts" / "modal.ts").read_text(encoding="utf-8")
        crm = (ROOT / "api" / "static" / "ts" / "crm.ts").read_text(encoding="utf-8")
        whatsapp = (ROOT / "api" / "static" / "ts" / "whatsapp_gateway.ts").read_text(encoding="utf-8")
        analytics = (ROOT / "api" / "static" / "ts" / "analytics.ts").read_text(encoding="utf-8")
        help_ts = (ROOT / "api" / "static" / "ts" / "help.ts").read_text(encoding="utf-8")
        audit = (ROOT / "api" / "static" / "ts" / "audit.ts").read_text(encoding="utf-8")
        owner_report = (ROOT / "api" / "static" / "ts" / "owner_report.ts").read_text(encoding="utf-8")
        self.assertIn("invoiceDelegationReady", invoices)
        self.assertIn("ensureInvoiceEventDelegation", invoices)
        self.assertIn("settingsDelegationReady", settings)
        self.assertIn("ensureSettingsEventDelegation", settings)
        self.assertIn("herbalDelegationReady", herbals)
        self.assertIn("ensureHerbalEventDelegation", herbals)
        self.assertIn("inventoryDelegationReady", inventory)
        self.assertIn("ensureInventoryEventDelegation", inventory)
        self.assertIn("patientsDelegationReady", patients)
        self.assertIn("ensurePatientsEventDelegation", patients)
        self.assertIn("serviceDelegationReady", services)
        self.assertIn("ensureServiceEventDelegation", services)
        self.assertIn("therapistDelegationReady", therapists)
        self.assertIn("ensureTherapistEventDelegation", therapists)
        self.assertIn("runtimeModalDelegationReady", modal)
        self.assertIn("ensureRuntimeModalEventDelegation", modal)
        self.assertIn("crmDelegationReady", crm)
        self.assertIn("ensureCRMEventDelegation", crm)
        self.assertIn("whatsappGatewayDelegationReady", whatsapp)
        self.assertIn("ensureWhatsAppGatewayEventDelegation", whatsapp)
        self.assertIn("analyticsDelegationReady", analytics)
        self.assertIn("ensureAnalyticsEventDelegation", analytics)
        self.assertIn("helpDelegationReady", help_ts)
        self.assertIn("ensureHelpEventDelegation", help_ts)
        self.assertIn("auditDelegationReady", audit)
        self.assertIn("ensureAuditEventDelegation", audit)
        self.assertIn("ownerReportDelegationReady", owner_report)
        self.assertIn("ensureOwnerReportEventDelegation", owner_report)


if __name__ == "__main__":
    unittest.main()
