"""
server.py - Supermarket Offline Payment REST API & Web Server
Uses Python's built-in http.server.ThreadingHTTPServer with Zero External Dependencies.
Serves static frontend assets and provides REST API endpoints for POS and Mobile Simulator.
"""

import http.server
import json
import os
import sys
import mimetypes
import time
from urllib.parse import urlparse, parse_qs
from database import (
    init_db,
    get_customer,
    get_products,
    prefetch_tokens,
    park_order,
    resume_order,
    get_all_parked_orders,
    update_customer_pay_later,
    record_transaction,
    get_recent_transactions
)
from crypto_engine import (
    generate_offline_qr_payload,
    verify_offline_qr_payload,
    process_nfc_contactless
)

HOST = "0.0.0.0"
PORT = 8080
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class SOPRCSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, data, status_code=200):
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API Routes
        if path == "/api/v1/products":
            products = get_products()
            return self._send_json({"success": True, "products": products})

        elif path == "/api/v1/customer":
            customer = get_customer("USER_001")
            return self._send_json({"success": True, "customer": customer})

        elif path == "/api/v1/pos/parked-orders":
            orders = get_all_parked_orders()
            return self._send_json({"success": True, "parked_orders": orders})

        elif path == "/api/v1/transactions":
            txs = get_recent_transactions(15)
            return self._send_json({"success": True, "transactions": txs})

        elif path == "/api/v1/health":
            return self._send_json({"status": "OK", "timestamp": int(time.time())})

        # Static file fallback
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        # 1. Reset / Init Demo
        if path == "/api/v1/init-demo":
            init_db()
            tokens = prefetch_tokens("USER_001", count=5)
            customer = get_customer("USER_001")
            return self._send_json({
                "success": True,
                "message": "Cơ sở dữ liệu và token đã được khởi tạo thành công!",
                "customer": customer,
                "token_count": len(tokens)
            })

        # 2. Pre-fetch Tokens for Mobile App
        elif path == "/api/v1/tokens/prefetch":
            user_id = payload.get("user_id", "USER_001")
            tokens = prefetch_tokens(user_id, count=5)
            return self._send_json({"success": True, "tokens": tokens})

        # 3. Process Scanned Offline QR at POS Terminal
        elif path == "/api/v1/payment/offline-qr":
            qr_data = payload.get("qr_data", "")
            amount = float(payload.get("amount", 0))
            result = verify_offline_qr_payload(qr_data, amount)
            status_code = 200 if result["success"] else 400
            return self._send_json(result, status_code)

        # 4. Process NFC Contactless (Apple Pay / Google Wallet)
        elif path == "/api/v1/payment/nfc-contactless":
            device_pan = payload.get("device_pan", "9876-XXXX-XXXX-1024")
            cryptogram = payload.get("cryptogram", "ARQC_A89F9B0212")
            amount = float(payload.get("amount", 0))
            user_id = payload.get("user_id", "USER_001")
            result = process_nfc_contactless(device_pan, cryptogram, amount, user_id)
            status_code = 200 if result["success"] else 400
            return self._send_json(result, status_code)

        # 5. Suspend / Park Current Cart (F8)
        elif path == "/api/v1/pos/park-order":
            store_id = payload.get("store_id", "SUPERMARKET_01")
            terminal_id = payload.get("terminal_id", "POS_LINE_01")
            cashier_id = payload.get("cashier_id", "CASHIER_LINH")
            customer_id = payload.get("customer_id", "USER_001")
            total_amount = float(payload.get("total_amount", 0))
            order_items = payload.get("order_items", [])

            if not order_items or total_amount <= 0:
                return self._send_json({"success": False, "message": "Giỏ hàng trống, không thể treo đơn!"}, 400)

            park_id, expires_at = park_order(
                store_id, terminal_id, cashier_id, customer_id, total_amount, order_items
            )
            return self._send_json({
                "success": True,
                "park_id": park_id,
                "total_amount": total_amount,
                "item_count": len(order_items),
                "expires_at": expires_at,
                "message": f"Đơn hàng đã được lưu tạm thành công với mã: {park_id}"
            })

        # 6. Resume Suspended Cart (F9)
        elif path == "/api/v1/pos/resume-order":
            park_id = payload.get("park_id", "").strip()
            order = resume_order(park_id)
            if not order:
                return self._send_json({
                    "success": False,
                    "message": f"Không tìm thấy đơn hàng treo có mã '{park_id}' hoặc đơn đã được thanh toán!"
                }, 404)

            return self._send_json({
                "success": True,
                "order": order,
                "message": f"Đã khôi phục thành công đơn hàng {park_id} gồm {len(order['items'])} sản phẩm!"
            })

        # 7. Check Member Trust Credit
        elif path == "/api/v1/loyalty/credit-check":
            user_id = payload.get("user_id", "USER_001")
            customer = get_customer(user_id)
            if not customer:
                return self._send_json({"success": False, "message": "Không tìm thấy thông tin hội viên"}, 404)

            available_credit = customer["pay_later_limit"] - customer["pay_later_used"]
            eligible = customer["credit_score"] >= 650 and available_credit > 0

            return self._send_json({
                "success": True,
                "customer_name": customer["name"],
                "loyalty_tier": customer["loyalty_tier"],
                "credit_score": customer["credit_score"],
                "pay_later_limit": customer["pay_later_limit"],
                "available_credit": max(0, available_credit),
                "eligible": eligible
            })

        # 8. Issue In-Store Pay Later
        elif path == "/api/v1/loyalty/pay-later":
            user_id = payload.get("user_id", "USER_001")
            amount = float(payload.get("amount", 0))
            customer = get_customer(user_id)

            if not customer:
                return self._send_json({"success": False, "message": "Hội viên không tồn tại"}, 404)

            available_credit = customer["pay_later_limit"] - customer["pay_later_used"]
            if amount > available_credit:
                return self._send_json({
                    "success": False,
                    "message": f"Số tiền đơn hàng ({amount:,.0f}đ) vượt quá hạn mức nợ cho phép ({available_credit:,.0f}đ)"
                }, 400)

            update_customer_pay_later(user_id, amount)
            tx_id = record_transaction(
                order_id=f"ORD_BNPL_{int(time.time())}",
                user_id=user_id,
                amount=amount,
                payment_method="LOYALTY_PAY_LATER",
                status="DEFERRED_PAYMENT",
                details=f"Hạn mức còn lại: {available_credit - amount:,.0f}đ. Hạn thanh toán: 24 giờ."
            )

            return self._send_json({
                "success": True,
                "transaction_id": tx_id,
                "amount": amount,
                "customer_name": customer["name"],
                "due_hours": 24,
                "message": "Đã phê duyệt xuất hàng tạm ứng! Hóa đơn điện tử kèm mã VietQR đã được gửi tới số điện thoại của quý khách."
            })

        else:
            return self._send_json({"error": "Endpoint không tồn tại"}, 404)


def run_server():
    init_db()
    server_address = (HOST, PORT)
    httpd = http.server.ThreadingHTTPServer(server_address, SOPRCSRequestHandler)
    print(f"============================================================")
    print(f" Supermarket Offline Payment Simulator (SOPRCS) Running")
    print(f" Server URL: http://localhost:{PORT}")
    print(f" API Ready: Zero external dependencies (Python 3.11 Standard Library)")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nĐang dừng server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()

