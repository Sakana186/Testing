"""
gateway_server.py - API Gateway & Reverse Proxy (Port 8080)
Single Entry Point for all frontend traffic.
Routes API requests to appropriate microservices and serves static assets.
"""

import sys
import os
import json
import urllib.request
import urllib.error
import http.server
from urllib.parse import urlparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.common.config import (
    GATEWAY_PORT,
    POS_SERVICE_URL,
    PAYMENT_SERVICE_URL,
    TOKEN_SERVICE_URL,
    CUSTOMER_SERVICE_URL
)
from services.common.http_client import http_get_json, http_post_json

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")


class GatewayRequestHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, data: dict, status_code: int = 200):
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _proxy_request(self, target_url: str, method: str = "GET", body_bytes: bytes = None):
        req = urllib.request.Request(
            target_url,
            data=body_bytes if method == "POST" else None,
            method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(resp_body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err_body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            self._send_json({"error": f"Gateway Proxy Error: {str(e)}", "target": target_url}, 503)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. Cluster Healthcheck
        if path == "/api/v1/health":
            _, pos_h = http_get_json(f"{POS_SERVICE_URL}/health", timeout=2)
            _, pay_h = http_get_json(f"{PAYMENT_SERVICE_URL}/health", timeout=2)
            _, tok_h = http_get_json(f"{TOKEN_SERVICE_URL}/health", timeout=2)
            _, cust_h = http_get_json(f"{CUSTOMER_SERVICE_URL}/health", timeout=2)
            return self._send_json({
                "gateway": "UP",
                "cluster_topology": {
                    "pos_service": pos_h,
                    "payment_service": pay_h,
                    "token_service": tok_h,
                    "customer_service": cust_h
                }
            })

        # 2. Route to POS Service
        elif path in ["/api/v1/products"]:
            return self._proxy_request(f"{POS_SERVICE_URL}/products", "GET")
        elif path.startswith("/api/v1/pos/parked-orders"):
            return self._proxy_request(f"{POS_SERVICE_URL}/parked-orders", "GET")

        # 3. Route to Customer Service
        elif path in ["/api/v1/customer"] or path.startswith("/api/v1/customer/"):
            sub_path = path.replace("/api/v1/customer", "/customer")
            return self._proxy_request(f"{CUSTOMER_SERVICE_URL}{sub_path}", "GET")

        # 4. Route to Payment Service (Transactions Audit)
        elif path in ["/api/v1/transactions"]:
            return self._proxy_request(f"{PAYMENT_SERVICE_URL}/transactions", "GET")

        # 5. Static files fallback
        if path in ["/", ""]:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"

        # 0. System-Wide BVA Validation Endpoint (All 13 Parameters)
        if path in ["/api/checkout/validate-all", "/api/v1/checkout/validate-all"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p1 = int(data.get("amount", 500000))
                p2 = int(data.get("cart_quantity", 25))
                p3 = int(data.get("loan_amount", 250000))
                p4 = int(data.get("credit_score", 750))
                p5 = int(data.get("qr_totp_period_sec", 30))
                p6 = int(data.get("time_drift_sec", 0))
                p7 = int(data.get("nonce_ttl_sec", 90))
                p8 = int(data.get("token_spending_limit", 1500000))
                p9 = int(data.get("parked_order_timeout_min", 30))
                p10 = int(data.get("pay_later_grace_period_hr", 12))
                p11 = int(data.get("wifi_session_duration_min", 8))
                p12 = int(data.get("prefetched_tokens_count", 3))
                p13 = float(data.get("wifi_qos_bandwidth_mbps", 1.0))
                p14 = str(data.get("customer_phone", "0912345678"))
                p15 = str(data.get("currency", "VND"))
                p16 = bool(data.get("is_ekyc_verified", True))

                errors = []
                # P1: Số tiền đơn hàng ngoại tuyến [1.000, 1.000.000] VNĐ
                if p1 < 1000:
                    errors.append(("p1", "INVALID_AMOUNT", f"Số tiền đơn ({p1:,}đ) < Min (1.000đ)"))
                elif p1 > 1000000:
                    errors.append(("p1", "EXCEEDS_OFFLINE_LIMIT", f"Số tiền ({p1:,}đ) vượt trần Max (1.000.000đ)"))

                # P2: Số lượng món hàng trong giỏ [1, 50] món
                if p2 < 1:
                    errors.append(("p2", "EMPTY_CART", f"Số lượng món ({p2}) < Min (1)"))
                elif p2 > 50:
                    errors.append(("p2", "EXCEEDS_CART_LIMIT", f"Số lượng món ({p2}) vượt trần Max (50)"))

                # P3: Số tiền tạm ứng nợ Pay-Later [1.000, 500.000] VNĐ
                if p3 < 1000:
                    errors.append(("p3", "INVALID_AMOUNT", f"Số tiền vay ({p3:,}đ) < Min (1.000đ)"))
                elif p3 > 500000:
                    errors.append(("p3", "EXCEEDS_PAY_LATER_LIMIT", f"Số tiền vay ({p3:,}đ) vượt trần Max (500.000đ)"))

                # P4: Điểm tín nhiệm hội viên [650, 850] điểm
                if p4 < 650:
                    errors.append(("p4", "CREDIT_SCORE_TOO_LOW", f"Điểm tín nhiệm ({p4}) < Min (650)"))
                elif p4 > 850:
                    errors.append(("p4", "EXCEEDS_CREDIT_SCALE", f"Điểm tín nhiệm ({p4}) vượt trần Max (850)"))

                # P5: Vòng đời chu kỳ QR TOTP [1, 60] giây
                if p5 < 1:
                    errors.append(("p5", "INVALID_QR_PERIOD", f"Chu kỳ QR ({p5}s) < Min (1s)"))
                elif p5 > 60:
                    errors.append(("p5", "EXCEEDS_QR_PERIOD", f"Chu kỳ QR ({p5}s) vượt trần Max (60s)"))

                # P6: Dung sai lệch đồng hồ [-120, 120] giây
                if p6 < -120:
                    errors.append(("p6", "TIME_DRIFT_TOO_LOW", f"Độ lệch thời gian ({p6}s) < Min (-120s)"))
                elif p6 > 120:
                    errors.append(("p6", "TIME_DRIFT_EXCEEDED", f"Độ lệch thời gian ({p6}s) vượt trần Max (120s)"))

                # P7: Thời gian sống Nonce [1, 180] giây
                if p7 < 1:
                    errors.append(("p7", "INVALID_NONCE_TTL", f"Thời gian sống Nonce ({p7}s) < Min (1s)"))
                elif p7 > 180:
                    errors.append(("p7", "EXCEEDS_NONCE_TTL", f"Thời gian sống Nonce ({p7}s) vượt trần Max (180s)"))

                # P8: Hạn mức chi tiêu Token [1.000, 3.000.000] VNĐ
                if p8 < 1000:
                    errors.append(("p8", "INVALID_TOKEN_LIMIT", f"Hạn mức token ({p8:,}đ) < Min (1.000đ)"))
                elif p8 > 3000000:
                    errors.append(("p8", "EXCEEDS_TOKEN_LIMIT", f"Hạn mức token ({p8:,}đ) vượt trần Max (3.000.000đ)"))

                # P9: Thời hạn lưu giữ đơn hàng treo [1, 60] phút
                if p9 < 1:
                    errors.append(("p9", "INVALID_PARKED_TIMEOUT", f"Thời hạn treo đơn ({p9} phút) < Min (1 phút)"))
                elif p9 > 60:
                    errors.append(("p9", "EXCEEDS_PARKED_TIMEOUT", f"Thời hạn treo đơn ({p9} phút) vượt trần Max (60 phút)"))

                # P10: Thời hạn thanh toán nợ Pay-Later [1, 24] giờ
                if p10 < 1:
                    errors.append(("p10", "INVALID_GRACE_PERIOD", f"Thời hạn trả sau ({p10} giờ) < Min (1 giờ)"))
                elif p10 > 24:
                    errors.append(("p10", "EXCEEDS_GRACE_PERIOD", f"Thời hạn trả sau ({p10} giờ) vượt trần Max (24 giờ)"))

                # P11: Thời lượng phiên Wi-Fi [1, 15] phút
                if p11 < 1:
                    errors.append(("p11", "INVALID_WIFI_DURATION", f"Thời lượng Wi-Fi ({p11} phút) < Min (1 phút)"))
                elif p11 > 15:
                    errors.append(("p11", "EXCEEDS_WIFI_DURATION", f"Thời lượng Wi-Fi ({p11} phút) vượt trần Max (15 phút)"))

                # P12: Số lượng Token trong túi tải sẵn [1, 5] Token
                if p12 < 1:
                    errors.append(("p12", "INVALID_PREFETCH_COUNT", f"Số lượng token ({p12}) < Min (1)"))
                elif p12 > 5:
                    errors.append(("p12", "EXCEEDS_PREFETCH_COUNT", f"Số lượng token ({p12}) vượt trần Max (5)"))

                # P13: Băng thông QoS Wi-Fi [0.1, 2.0] Mbps
                if p13 < 0.1:
                    errors.append(("p13", "INVALID_WIFI_BANDWIDTH", f"Băng thông Wi-Fi ({p13} Mbps) < Min (0.1 Mbps)"))
                elif p13 > 2.0:
                    errors.append(("p13", "EXCEEDS_WIFI_BANDWIDTH", f"Băng thông Wi-Fi ({p13} Mbps) vượt trần Max (2.0 Mbps)"))

                # Thẩm định tham số không phải dạng số (P14, P15, P16)
                if not p14:
                    errors.append(("p14", "INVALID_PHONE_EMPTY", "Số điện thoại hội viên không được để trống"))
                elif not p14.isdigit():
                    errors.append(("p14", "INVALID_PHONE_FORMAT", f"Số điện thoại ({p14}) chứa ký tự không hợp lệ"))
                elif len(p14) != 10:
                    errors.append(("p14", "INVALID_PHONE_LENGTH", f"Độ dài số điện thoại ({len(p14)}) khác chuẩn 10 chữ số"))

                if not p15:
                    errors.append(("p15", "INVALID_CURRENCY_EMPTY", "Đơn vị tiền tệ không được để trống"))
                elif p15 != "VND":
                    errors.append(("p15", "UNSUPPORTED_CURRENCY", f"Đơn vị tiền tệ ({p15}) không được hỗ trợ ngoại tuyến"))

                if not p16:
                    errors.append(("p16", "EKYC_REQUIRED", "Hội viên chưa hoàn tất định danh eKYC điện tử"))

                if not errors:
                    return self._send_json({
                        "status": "APPROVED_ALL",
                        "success": True,
                        "code": 200,
                        "message": "Phê duyệt giao dịch ngoại tuyến và cấp hạn mức Pay-Later thành công."
                    }, 200)
                else:
                    return self._send_json({
                        "status": "REJECTED",
                        "success": False,
                        "error": errors[0][1],
                        "violations": [e[1] for e in errors],
                        "details": [e[2] for e in errors]
                    }, 400)
            except Exception as ex:
                return self._send_json({"error": "BAD_PAYLOAD", "message": str(ex)}, 400)

        # Luồng 1 (OUT-01): Phê duyệt thanh toán ngoại tuyến
        elif path in ["/api/checkout/offline-pay", "/api/v1/checkout/offline-pay"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p1 = int(data.get("amount", 500000))
                p2 = int(data.get("cart_quantity", 25))
                p5 = int(data.get("qr_totp_period_sec", 30))
                p6 = int(data.get("time_drift_sec", 0))
                p7 = int(data.get("nonce_ttl_sec", 90))
                p14 = str(data.get("customer_phone", "0912345678"))
                p15 = str(data.get("currency", "VND"))
                if (1000 <= p1 <= 1000000 and 1 <= p2 <= 50 and 1 <= p5 <= 60 and 
                    -120 <= p6 <= 120 and 1 <= p7 <= 180 and len(p14) == 10 and 
                    p14.isdigit() and p15 == "VND"):
                    return self._send_json({
                        "status": "APPROVED_OFFLINE_PAYMENT",
                        "success": True,
                        "code": 200,
                        "message": "Phê duyệt thanh toán ngoại tuyến thành công."
                    }, 200)
                else:
                    return self._send_json({"status": "REJECTED", "error": "PAYMENT_REJECTED"}, 400)
            except Exception as ex:
                return self._send_json({"error": "BAD_PAYLOAD", "message": str(ex)}, 400)

        # Luồng 2 (OUT-02): Lưu tạm đơn hàng tại quầy POS
        elif path in ["/api/cart/park", "/api/v1/cart/park"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p2 = int(data.get("cart_quantity", 15))
                p9 = int(data.get("parked_order_timeout_min", 30))
                # Mã nguồn chuẩn SRS
                if 1 <= p2 <= 50 and 1 <= p9 <= 60:
                    return self._send_json({
                        "status": "CART_PARKED_SUCCESS",
                        "success": True,
                        "code": 200,
                        "message": "Lưu tạm đơn hàng tại quầy POS (Treo đơn) thành công."
                    }, 200)
                else:
                    return self._send_json({"status": "REJECTED", "error": "INVALID_PARK_PARAMS"}, 400)
            except Exception as ex:
                return self._send_json({"error": "BAD_PAYLOAD", "message": str(ex)}, 400)

        # Luồng 3 (OUT-03): Phê duyệt cấp hạn mức Pay-Later
        elif path in ["/api/pay-later/apply", "/api/v1/pay-later/apply"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p3 = int(data.get("loan_amount", 250000))
                p4 = int(data.get("credit_score", 780))
                p10 = int(data.get("pay_later_grace_period_hr", 12))
                p16 = bool(data.get("is_ekyc_verified", True))
                # Mã nguồn chuẩn SRS
                if 1000 <= p3 <= 500000 and 650 <= p4 <= 850 and 1 <= p10 <= 24 and p16:
                    return self._send_json({
                        "status": "PAY_LATER_APPROVED",
                        "success": True,
                        "code": 200,
                        "message": "Phê duyệt cấp hạn mức tạm ứng Pay-Later thành công."
                    }, 200)
                else:
                    return self._send_json({"status": "REJECTED", "error": "INVALID_LOAN_PARAMS"}, 400)
            except Exception as ex:
                return self._send_json({"error": "BAD_PAYLOAD", "message": str(ex)}, 400)

        # Luồng 4 (OUT-04): Đồng bộ và nạp mới túi Token ngoại tuyến
        elif path in ["/api/tokens/sync", "/api/v1/tokens/sync"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p12 = int(data.get("prefetched_tokens_count", 3))
                p8 = int(data.get("token_spending_limit", 1500000))
                if 1 <= p12 <= 5 and 1000 <= p8 <= 3000000:
                    return self._send_json({
                        "status": "TOKEN_SYNC_SUCCESS",
                        "success": True,
                        "code": 200,
                        "message": "Đồng bộ và nạp mới túi Token ngoại tuyến thành công."
                    }, 200)
                else:
                    return self._send_json({"status": "REJECTED", "error": "INVALID_TOKEN_PARAMS"}, 400)
            except Exception as ex:
                return self._send_json({"error": "BAD_PAYLOAD", "message": str(ex)}, 400)

        # Luồng 5 (OUT-05): Khởi tạo phiên Wi-Fi khẩn cấp tại quầy
        elif path in ["/api/wifi/emergency-session", "/api/v1/wifi/emergency-session"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p11 = int(data.get("wifi_session_duration_min", 8))
                p13 = float(data.get("wifi_qos_bandwidth_mbps", 1.5))
                # Mã nguồn chuẩn SRS
                if 1 <= p11 <= 15 and 0.1 <= p13 <= 2.0:
                    return self._send_json({
                        "status": "WIFI_SESSION_GRANTED",
                        "success": True,
                        "code": 200,
                        "message": "Khởi tạo phiên Wi-Fi khẩn cấp tại quầy thành công."
                    }, 200)
                else:
                    return self._send_json({"status": "REJECTED", "error": "INVALID_WIFI_PARAMS"}, 400)
            except Exception as ex:
                return self._send_json({"error": "BAD_PAYLOAD", "message": str(ex)}, 400)

        # 1. Broadcast Reset / Init Demo to all microservices
        elif path == "/api/v1/init-demo":
            http_post_json(f"{POS_SERVICE_URL}/init-demo", {})
            http_post_json(f"{TOKEN_SERVICE_URL}/init-demo", {})
            http_post_json(f"{CUSTOMER_SERVICE_URL}/init-demo", {})
            http_post_json(f"{PAYMENT_SERVICE_URL}/init-demo", {})
            return self._send_json({
                "success": True,
                "message": "Đã khởi tạo lại toàn bộ cơ sở dữ liệu của cả 4 Microservices thành công!"
            })

        # 2. Route to POS Service
        elif path.startswith("/api/v1/pos/"):
            sub_path = path.replace("/api/v1/pos", "")
            return self._proxy_request(f"{POS_SERVICE_URL}{sub_path}", "POST", body_bytes)

        # 3. Route to Token Service
        elif path.startswith("/api/v1/tokens/"):
            sub_path = path.replace("/api/v1/tokens", "/tokens")
            return self._proxy_request(f"{TOKEN_SERVICE_URL}{sub_path}", "POST", body_bytes)

        # 4. Route to Payment Service
        elif path.startswith("/api/v1/payment/"):
            sub_path = path.replace("/api/v1/payment", "/payment")
            return self._proxy_request(f"{PAYMENT_SERVICE_URL}{sub_path}", "POST", body_bytes)

        # 5. Route to Customer Service
        elif path.startswith("/api/v1/loyalty/") or path.startswith("/api/v1/wallet/"):
            sub_path = path.replace("/api/v1", "")
            return self._proxy_request(f"{CUSTOMER_SERVICE_URL}{sub_path}", "POST", body_bytes)

        else:
            return self._send_json({"error": "Endpoint not routed by API Gateway"}, 404)


def run_gateway():
    server_address = ("0.0.0.0", GATEWAY_PORT)
    httpd = http.server.ThreadingHTTPServer(server_address, GatewayRequestHandler)
    print(f"============================================================")
    print(f" [API Gateway] Running on http://localhost:{GATEWAY_PORT}")
    print(f" Routing traffic to 4 independent microservices")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Gateway...")
        httpd.server_close()


if __name__ == "__main__":
    run_gateway()

