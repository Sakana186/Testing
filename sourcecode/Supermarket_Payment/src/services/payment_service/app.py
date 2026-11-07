"""
app.py - Payment & Fraud Gateway Microservice (Port 8082)
Validates offline dynamic QR codes, checks Anti-Replay nonces, and coordinates inter-service settlement.
"""

import sys
import os
import http.server
from urllib.parse import urlparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.common.config import PAYMENT_SERVICE_PORT
from services.common.http_client import BaseServiceHandler
from services.payment_service.payment_db import (
    init_db,
    reset_db,
    get_recent_transactions
)
from services.payment_service.crypto_engine import (
    verify_offline_qr_payload,
    process_nfc_contactless
)


class PaymentServiceHandler(BaseServiceHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            return self.send_json({"service": "payment_service", "status": "UP", "port": PAYMENT_SERVICE_PORT})

        elif path in ["/transactions", "/api/v1/transactions"]:
            txs = get_recent_transactions(15)
            return self.send_json({"success": True, "transactions": txs})

        else:
            return self.send_json({"error": "Endpoint not found in payment_service"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        if path in ["/init-demo", "/api/v1/init-demo"]:
            reset_db()
            return self.send_json({"success": True, "message": "Payment database reset"})

        elif path in ["/payment/offline-qr", "/api/v1/payment/offline-qr"]:
            qr_data = body.get("qr_data", "")
            amount_raw = body.get("amount") if body.get("amount") is not None else body.get("bill_amount", 0)
            amount = float(amount_raw)
            result = verify_offline_qr_payload(qr_data, amount)
            status_code = 200 if result.get("success") else 400
            return self.send_json(result, status_code)

        elif path in ["/payment/nfc-contactless", "/api/v1/payment/nfc-contactless"]:
            device_pan = body.get("device_pan", "9876-XXXX-XXXX-1024")
            cryptogram = body.get("cryptogram", "ARQC_A89F9B0212")
            amount = float(body.get("amount", 0))
            user_id = body.get("user_id", "USER_001")
            result = process_nfc_contactless(device_pan, cryptogram, amount, user_id)
            status_code = 200 if result.get("success") else 400
            return self.send_json(result, status_code)

        else:
            return self.send_json({"error": "Endpoint not found in payment_service"}, 404)


def run_service():
    init_db()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PAYMENT_SERVICE_PORT), PaymentServiceHandler)
    print(f"[Payment Service] Started on port {PAYMENT_SERVICE_PORT} (DB: payment.db)")
    server.serve_forever()


if __name__ == "__main__":
    run_service()

