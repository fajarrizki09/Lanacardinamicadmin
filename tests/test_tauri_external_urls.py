import unittest
from unittest.mock import patch

from helpers.support_helper import open_external_url, validate_external_url
from tests.api_test_utils import app_headers, client


class TestTauriExternalUrlAllowlist(unittest.TestCase):
    def test_known_desktop_external_targets_are_allowed(self):
        self.assertEqual(
            validate_external_url("https://app.sandbox.midtrans.com/snap/v2/vtweb/token"),
            "https://app.sandbox.midtrans.com/snap/v2/vtweb/token",
        )
        self.assertEqual(
            validate_external_url("https://wa.me/628111111111?text=Halo"),
            "https://wa.me/628111111111?text=Halo",
        )
        self.assertEqual(
            validate_external_url("http://127.0.0.1:3000"),
            "http://127.0.0.1:3000",
        )

    def test_dangerous_or_unknown_external_targets_are_rejected(self):
        for value in (
            "javascript:alert(1)",
            "file:///C:/Windows/System32/cmd.exe",
            "https://evil.example/",
            "https://app.sandbox.midtrans.com.evil.example/pay",
            "https://user:password@wa.me/628111111111",
            "https://wa.me:444/628111111111",
            "http://127.0.0.1:4000",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_external_url(value)

    def test_allowed_external_url_is_opened_through_operating_system(self):
        with patch("helpers.support_helper.platform.system", return_value="windows"), patch(
            "helpers.support_helper.os.startfile", create=True
        ) as startfile:
            opened = open_external_url("https://wa.me/628111111111")

        self.assertEqual(opened, "https://wa.me/628111111111")
        startfile.assert_called_once_with("https://wa.me/628111111111")

    def test_api_rejects_disallowed_target(self):
        response = client().post(
            "/support/open_external_url",
            data={"url": "file:///C:/Windows/System32/cmd.exe"},
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 400)

    def test_api_allows_safe_target_without_admin_pin(self):
        with patch("api.routes.support.open_external_url", return_value="https://wa.me/628111111111"):
            response = client().post(
                "/support/open_external_url",
                data={"url": "https://wa.me/628111111111"},
                headers=app_headers(),
            )

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
