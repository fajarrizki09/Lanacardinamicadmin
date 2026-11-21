import unittest
import os
from tests.api_test_utils import client, app_headers

class TestInvoicePathTraversal(unittest.TestCase):
    def setUp(self):
        self.client = client()

    def test_open_invoice_path_traversal_blocked(self):
        # Attempt to access a file outside the allowed directories using ../
        malicious_path = "../../../../../../../../../../../../../Windows/System32/drivers/etc/hosts"
        response = self.client.get(f"/invoices/open_invoice?path={malicious_path}", headers=app_headers())
        
        # Should be forbidden/not found, not 200/success
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, [403, 404])
