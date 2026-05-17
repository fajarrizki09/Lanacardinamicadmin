import os
import sys
import unittest


sys.path.insert(0, os.path.dirname(__file__))
from api_test_utils import app_headers, client


class TestSecurityTokenMiddleware(unittest.TestCase):
    def setUp(self):
        self.client = client()

    def test_api_without_app_token_is_rejected(self):
        response = self.client.get("/patients")

        self.assertEqual(response.status_code, 403)

    def test_operator_endpoint_accepts_valid_app_token_without_admin_pin(self):
        response = self.client.get("/patients", headers=app_headers())

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
