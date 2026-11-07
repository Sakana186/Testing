"""
app.py - Customer & Loyalty Microservice (Port 8084)
Handles customer profiles, wallet balances, credit scoring, and in-store Pay-Later loans.
"""

import sys
import os
import http.server
import time
from urllib.parse import urlparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.common.config import CUSTOMER_SERVICE_PORT
from services.common.http_client import BaseServiceHandler
from services.customer_service.customer_db import (
    init_db,
    reset_db,
    get_customer,
    deduct_balance,
    update_pay_later
)


class CustomerServiceHandler(BaseServiceHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            return self.send_json({"service": "customer_service", "status": "UP", "port": CUSTOMER_SERVICE_PORT})

        elif path in ["/customer", "/api/v1/customer"]:
            customer = get_customer("USER_001")
            return self.send_json({"success": True, "customer": customer})

        elif path.startswith("/customer/") or path.startswith("/api/v1/customer/"):
            parts = path.strip("/").split("/")
            user_id = parts[-1]
            customer = get_customer(user_id)
            if not customer:
                return self.send_json({"success": False, "error": "Customer not found"}, 404)
            return self.send_json({"success": True, "customer": customer})

        else:
            return self.send_json({"error": "Endpoint not found in customer_service"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        if path in ["/init-demo", "/api/v1/init-demo"]:
            reset_db()
            cust = get_customer("USER_001")
            return self.send_json({"success": True, "message": "Customer database reset", "customer": cust})

        elif path in ["/wallet/deduct", "/api/v1/wallet/deduct"]:
            user_id = body.get("user_id", "USER_001")
            amount = float(body.get("amount", 0))
            success, msg, new_bal = deduct_balance(user_id, amount)
            status_code = 200 if success else 400
            return self.send_json({
                "success": success,
                "message": msg,
                "remaining_balance": new_bal
            }, status_code)

        elif path in ["/loyalty/credit-check", "/api/v1/loyalty/credit-check"]:
            user_id = body.get("user_id", "USER_001")
            customer = get_customer(user_id)
            if not customer:
                return self.send_json({"success": False, "message": "Không tìm thấy thông tin hội viên"}, 404)

            available_credit = customer["pay_later_limit"] - customer["pay_later_used"]
            eligible = customer["credit_score"] >= 650 and available_credit > 0

            return self.send_json({
                "success": True,
                "customer_name": customer["name"],
                "loyalty_tier": customer["loyalty_tier"],
                "credit_score": customer["credit_score"],
                "pay_later_limit": customer["pay_later_limit"],
                "available_credit": max(0, available_credit),
                "eligible": eligible
            })

        elif path in ["/loyalty/pay-later", "/api/v1/loyalty/pay-later"]:
            user_id = body.get("user_id", "USER_001")
            amount = float(body.get("amount", 0))
            customer = get_customer(user_id)

            if amount <= 0:
                return self.send_json({
                    "success": False,
                    "error": "INVALID_AMOUNT",
                    "message": "Số tiền tạm ứng không hợp lệ (phải lớn hơn 0 đồng)!"
                }, 400)

            available_credit = customer["pay_later_limit"] - customer["pay_later_used"]
            if amount > available_credit:
                return self.send_json({
                    "success": False,
                    "message": f"Số tiền đơn hàng ({amount:,.0f}đ) vượt quá hạn mức nợ cho phép ({available_credit:,.0f}đ)"
                }, 400)

            update_pay_later(user_id, amount)
            tx_id = f"TX_BNPL_{int(time.time())}"
            return self.send_json({
                "success": True,
                "transaction_id": tx_id,
                "amount": amount,
                "customer_name": customer["name"],
                "due_hours": 24,
                "message": "Đã phê duyệt xuất hàng tạm ứng! Hóa đơn điện tử kèm mã VietQR đã được gửi tới số điện thoại của quý khách."
            })

        else:
            return self.send_json({"error": "Endpoint not found in customer_service"}, 404)


def run_service():
    init_db()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", CUSTOMER_SERVICE_PORT), CustomerServiceHandler)
    print(f"[Customer Service] Started on port {CUSTOMER_SERVICE_PORT} (DB: customers.db)")
    server.serve_forever()


if __name__ == "__main__":
    run_service()

