import json
import os
import sys
import unittest


sys.path.insert(0, os.path.dirname(__file__))
from api_test_utils import app_headers, client, db
from database import HerbalTransaction


class TestHerbalApi(unittest.TestCase):
    def setUp(self):
        self.client = client()

    def test_herbal_sale_reduces_stock_without_admin_pin(self):
        herbal_id = db.add_herbal(
            "Herbal API Stock Test",
            "botol",
            25000,
            stock=10,
            cost_price=10000,
            min_stock=2,
        )
        response = self.client.post(
            "/herbals/sale",
            data={
                "buyer_name": "Pembeli Test",
                "items": json.dumps([{"herbal_id": herbal_id, "quantity": 3}]),
            },
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

        herbals = db.get_all_herbals(active_only=False)
        herbal = next(item for item in herbals if item["id"] == herbal_id)
        self.assertEqual(herbal["stock"], 7)

    def test_herbal_sale_valid_manual_payment_is_normalized(self):
        herbal_id = db.add_herbal("Herbal Manual Payment Test", "botol", 25000, stock=5, cost_price=10000)

        response = self.client.post(
            "/herbals/sale",
            data={
                "buyer_name": "Pembeli Manual",
                "items": json.dumps([{"herbal_id": herbal_id, "quantity": 2}]),
                "payment_status": "partial",
                "payment_method": "cash",
                "amount_paid": "25000",
            },
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            tx = (
                session.query(HerbalTransaction)
                .filter(HerbalTransaction.herbal_id == herbal_id, HerbalTransaction.transaction_type == "sale")
                .one()
            )
        self.assertEqual(tx.payment_provider, "manual")
        self.assertEqual(tx.payment_status, "partial")
        self.assertEqual(tx.payment_method, "cash")
        self.assertEqual(tx.amount_paid, 25000)

    def test_herbal_sale_valid_gateway_providers_are_allowed(self):
        for provider in ("gateway_mock", "midtrans"):
            with self.subTest(provider=provider):
                herbal_id = db.add_herbal(f"Herbal Gateway Payment {provider}", "botol", 30000, stock=5, cost_price=10000)
                response = self.client.post(
                    "/herbals/sale",
                    data={
                        "buyer_name": f"Pembeli {provider}",
                        "items": json.dumps([{"herbal_id": herbal_id, "quantity": 1}]),
                        "payment_status": "pending",
                        "payment_method": "qris",
                        "payment_provider": provider,
                    },
                    headers=app_headers(),
                )

                self.assertEqual(response.status_code, 200)
                with db.Session() as session:
                    tx = (
                        session.query(HerbalTransaction)
                        .filter(HerbalTransaction.herbal_id == herbal_id, HerbalTransaction.transaction_type == "sale")
                        .one()
                    )
                self.assertEqual(tx.payment_provider, provider)
                self.assertEqual(tx.payment_status, "pending")
                self.assertEqual(tx.payment_method, "qris")
                self.assertEqual(tx.amount_paid, 0)

    def test_herbal_sale_rejects_coming_soon_provider_without_reducing_stock(self):
        for provider in ("xendit", "duitku", "doku", "tripay"):
            with self.subTest(provider=provider):
                herbal_id = db.add_herbal(f"Herbal Reject {provider}", "botol", 25000, stock=4, cost_price=10000)
                response = self.client.post(
                    "/herbals/sale",
                    data={
                        "buyer_name": f"Pembeli {provider}",
                        "items": json.dumps([{"herbal_id": herbal_id, "quantity": 2}]),
                        "payment_status": "pending",
                        "payment_method": "qris",
                        "payment_provider": provider,
                    },
                    headers=app_headers(),
                )

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["detail"], "Provider pembayaran ini belum tersedia.")
                herbal = next(item for item in db.get_all_herbals(active_only=False) if item["id"] == herbal_id)
                self.assertEqual(herbal["stock"], 4)
                with db.Session() as session:
                    count = (
                        session.query(HerbalTransaction)
                        .filter(HerbalTransaction.herbal_id == herbal_id, HerbalTransaction.transaction_type == "sale")
                        .count()
                    )
                self.assertEqual(count, 0)

    def test_herbal_sale_rejects_invalid_payment_without_reducing_stock(self):
        cases = [
            {"payment_status": "selesai", "payment_method": "cash"},
            {"payment_status": "paid", "payment_method": "barter"},
        ]
        for idx, payload in enumerate(cases):
            with self.subTest(payload=payload):
                herbal_id = db.add_herbal(f"Herbal Invalid Payment {idx}", "botol", 25000, stock=3, cost_price=10000)
                response = self.client.post(
                    "/herbals/sale",
                    data={
                        "buyer_name": "Pembeli Invalid",
                        "items": json.dumps([{"herbal_id": herbal_id, "quantity": 1}]),
                        **payload,
                    },
                    headers=app_headers(),
                )

                self.assertEqual(response.status_code, 400)
                herbal = next(item for item in db.get_all_herbals(active_only=False) if item["id"] == herbal_id)
                self.assertEqual(herbal["stock"], 3)
                with db.Session() as session:
                    count = (
                        session.query(HerbalTransaction)
                        .filter(HerbalTransaction.herbal_id == herbal_id, HerbalTransaction.transaction_type == "sale")
                        .count()
                    )
                self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
