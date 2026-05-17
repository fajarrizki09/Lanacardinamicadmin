#!/usr/bin/env python3
"""
Manual test: parallel duplicate herbal sale idempotency.
Generates two parallel POSTs with same X-Idempotency-Key and asserts DB state.

Usage: run while the server is running (http://127.0.0.1:8000)
"""
import requests
import sqlite3
import time
import uuid
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "http://127.0.0.1:8000/herbals/sale"
DB_PATH = "data.db"  # adjust if needed
HERBAL_ID = 1
TIMEOUT = 10

PAYLOAD = {
    "buyer_name": "QA_IDEMPOTENCY",
    "items": json.dumps([{"herbal_id": HERBAL_ID, "quantity": 1}]),
    "payment_status": "paid",
    "amount_paid": "10000",
}


def read_stock(conn, herbal_id=HERBAL_ID):
    cur = conn.cursor()
    cur.execute("SELECT stock FROM herbals WHERE id=?", (herbal_id,))
    r = cur.fetchone()
    return int(r[0]) if r and r[0] is not None else None


def count_transactions_by_sale_group(conn, sale_group_id):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM herbal_transactions WHERE sale_group_id=?", (sale_group_id,))
    r = cur.fetchone()
    return int(r[0]) if r else 0


def find_transactions_by_note(conn, buyer_name):
    cur = conn.cursor()
    like = f"%{buyer_name}%"
    cur.execute(
        "SELECT sale_group_id, COUNT(*) as cnt FROM herbal_transactions WHERE note LIKE ? GROUP BY sale_group_id ORDER BY cnt DESC",
        (like,)
    )
    return cur.fetchall()


def send_request(session, key):
    headers = {"X-Idempotency-Key": key}
    try:
        r = session.post(URL, headers=headers, data=PAYLOAD, timeout=TIMEOUT)
        try:
            body = r.json()
        except Exception:
            body = {"text": r.text}
        return {"status_code": r.status_code, "body": body}
    except Exception as e:
        return {"status_code": None, "body": {"error": str(e)}}


def main():
    key = f"test-{uuid.uuid4().hex}"
    print("Idempotency key:", key)

    conn = sqlite3.connect(DB_PATH)
    try:
        stock_before = read_stock(conn)
    except Exception as e:
        print("ERROR: cannot read DB. Is data.db path correct and server stopped?", e)
        return

    print("stok_awal:", stock_before)

    session = requests.Session()
    results = []

    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(send_request, session, key) for _ in range(2)]
        for fut in as_completed(futures):
            results.append(fut.result())

    # small delay to ensure DB commit
    time.sleep(0.5)

    conn = sqlite3.connect(DB_PATH)
    stock_after = read_stock(conn)

    # find sale_group_id from responses
    sale_group_id = None
    for res in results:
        body = res.get("body") or {}
        # body may contain 'sale' dict
        sale = None
        if isinstance(body, dict):
            sale = body.get("sale")
        if isinstance(sale, dict):
            sale_group_id = sale.get("sale_group_id")
            if sale_group_id:
                break

    transactions_count = 0
    if sale_group_id:
        transactions_count = count_transactions_by_sale_group(conn, sale_group_id)
    else:
        rows = find_transactions_by_note(conn, PAYLOAD["buyer_name"])
        transactions_count = sum(r[1] for r in rows) if rows else 0

    # Evaluate expectations
    expected_stock_after = None if stock_before is None else stock_before - 1
    pass_conditions = (
        (stock_after is not None and expected_stock_after == stock_after)
        and transactions_count == 1
    )

    print("\n--- RESULTS ---")
    print("PASS" if pass_conditions else "FAIL")
    print("stok_awal:", stock_before)
    print("stok_akhir:", stock_after)
    print("response_1:", results[0])
    print("response_2:", results[1])
    print("detected_transactions_count:", transactions_count)
    if sale_group_id:
        print("sale_group_id:", sale_group_id)

    if not pass_conditions:
        print("\nNotes:")
        if stock_after is None:
            print("- Could not read stock from DB. Check DB path and schema.")
        else:
            print("- Expected stock to decrease by 1 but did not.")
        if transactions_count != 1:
            print(f"- Expected 1 transaction for this sale, found {transactions_count}.")


if __name__ == '__main__':
    main()
