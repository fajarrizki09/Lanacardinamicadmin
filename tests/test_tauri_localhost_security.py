import unittest

from tests.api_test_utils import client


class TestTauriLocalhostSecurityHeaders(unittest.TestCase):
    def setUp(self):
        self.client = client()

    def test_license_html_cannot_be_framed_or_change_base_uri(self):
        response = self.client.get("/license")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertEqual(
            response.headers["content-security-policy"],
            (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self' data:; "
                "connect-src 'self' http://127.0.0.1:*; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "frame-ancestors 'none'"
            ),
        )


if __name__ == "__main__":
    unittest.main()
