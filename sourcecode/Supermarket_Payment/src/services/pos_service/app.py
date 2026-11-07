"""
app.py - POS & Order Microservice (Port 8081)
Handles product catalog, cart suspension (F8 Park Cart) and resumption (F9 Resume Cart).
"""

import sys
import os
import http.server
from urllib.parse import urlparse

# Add parent directories to sys.path for common imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.common.config import POS_SERVICE_PORT
from services.common.http_client import BaseServiceHandler
from services.pos_service.pos_db import (
    init_db,
    reset_db,
    get_products,
    park_order,
    resume_order,
    get_all_parked_orders
)


class POSServiceHandler(BaseServiceHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            return self.send_json({"service": "pos_service", "status": "UP", "port": POS_SERVICE_PORT})

        elif path in ["/products", "/api/v1/products"]:
            products = get_products()
            return self.send_json({"success": True, "products": products})

        elif path in ["/parked-orders", "/api/v1/pos/parked-orders"]:
            orders = get_all_parked_orders()
            return self.send_json({"success": True, "parked_orders": orders})

        else:
            return self.send_json({"error": "Endpoint not found in pos_service"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        if path in ["/init-demo", "/api/v1/init-demo"]:
            reset_db()
            return self.send_json({"success": True, "message": "POS database initialized successfully"})

        elif path in ["/park-order", "/api/v1/pos/park-order"]:
            store_id = body.get("store_id", "SUPERMARKET_01")
            terminal_id = body.get("terminal_id", "POS_LINE_01")
            cashier_id = body.get("cashier_id", "CASHIER_LINH")
            customer_id = body.get("customer_id", "USER_001")
            total_amount = float(body.get("total_amount", 0))
            order_items = body.get("order_items", [])

            if not order_items or total_amount <= 0:
                return self.send_json({"success": False, "error": "EMPTY_CART", "message": "Giỏ hàng trống, không thể treo đơn!"}, 400)

            if len(order_items) > 50:
                return self.send_json({
                    "success": False,
                    "error": "EXCEEDS_CART_LIMIT",
                    "message": f"Số lượng sản phẩm ({len(order_items)}) vượt quá hạn mức tối đa cho phép của 1 lần treo đơn (50 sản phẩm)!"
                }, 400)

            park_id, expires_at = park_order(store_id, terminal_id, cashier_id, customer_id, total_amount, order_items)
            return self.send_json({
                "success": True,
                "park_id": park_id,
                "total_amount": total_amount,
                "item_count": len(order_items),
                "expires_at": expires_at,
                "message": f"Đơn hàng đã được lưu tạm thành công với mã: {park_id}"
            })

        elif path in ["/resume-order", "/api/v1/pos/resume-order"]:
            park_id = body.get("park_id", "").strip()
            order = resume_order(park_id)
            if not order:
                return self.send_json({
                    "success": False,
                    "message": f"Không tìm thấy đơn hàng treo có mã '{park_id}' hoặc đơn đã được thanh toán!"
                }, 404)

            return self.send_json({
                "success": True,
                "order": order,
                "message": f"Đã khôi phục thành công đơn hàng {park_id} gồm {len(order['items'])} sản phẩm!"
            })

        else:
            return self.send_json({"error": "Endpoint not found in pos_service"}, 404)


def run_service():
    init_db()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", POS_SERVICE_PORT), POSServiceHandler)
    print(f"[POS Service] Started on port {POS_SERVICE_PORT} (DB: pos.db)")
    server.serve_forever()


if __name__ == "__main__":
    run_service()

