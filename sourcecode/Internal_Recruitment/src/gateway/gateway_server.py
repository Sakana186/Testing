"""
gateway_server.py - API Gateway & Reverse Proxy (Port 8090)
Single Entry Point for Internal Recruitment System frontend traffic.
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
    JOB_SERVICE_URL,
    APPLICATION_SERVICE_URL,
    EMPLOYEE_SERVICE_URL,
    NOTIFICATION_SERVICE_URL
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
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json; charset=utf-8"))
                self.send_header("Content-Length", str(len(resp_body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(err_body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            self._send_json({"error": f"Gateway Proxy Error: {str(e)}", "target": target_url}, 503)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        raw_query = parsed.query
        query_suffix = f"?{raw_query}" if raw_query else ""

        # 1. Cluster Healthcheck
        if path == "/api/v1/health":
            _, job_h = http_get_json(f"{JOB_SERVICE_URL}/health", timeout=2)
            _, app_h = http_get_json(f"{APPLICATION_SERVICE_URL}/health", timeout=2)
            _, emp_h = http_get_json(f"{EMPLOYEE_SERVICE_URL}/health", timeout=2)
            _, noti_h = http_get_json(f"{NOTIFICATION_SERVICE_URL}/health", timeout=2)
            return self._send_json({
                "gateway": "UP",
                "cluster_topology": {
                    "job_service": job_h,
                    "application_service": app_h,
                    "employee_service": emp_h,
                    "notification_service": noti_h
                }
            })

        # 2. Route to Job Service
        elif path.startswith("/api/v1/jobs"):
            sub_path = path.replace("/api/v1", "")
            return self._proxy_request(f"{JOB_SERVICE_URL}{sub_path}{query_suffix}", "GET")

        # 3. Route to Application Service
        elif path.startswith("/api/v1/applications"):
            sub_path = path.replace("/api/v1", "")
            return self._proxy_request(f"{APPLICATION_SERVICE_URL}{sub_path}{query_suffix}", "GET")

        # 4. Route to Employee Service
        elif path.startswith("/api/v1/employees"):
            sub_path = path.replace("/api/v1", "")
            return self._proxy_request(f"{EMPLOYEE_SERVICE_URL}{sub_path}{query_suffix}", "GET")

        # 5. Route to Notification Service
        elif path.startswith("/api/v1/notifications"):
            sub_path = path.replace("/api/v1", "")
            return self._proxy_request(f"{NOTIFICATION_SERVICE_URL}{sub_path}{query_suffix}", "GET")

        # 6. Static files fallback
        if path in ["/", ""]:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"

        # 0. System-Wide BVA Validation Endpoint (All 12 Parameters)
        if path in ["/api/applications/validate-all", "/api/v1/applications/validate-all"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p1 = int(data.get("seniority_days", 730))
                p2 = int(data.get("active_applications", 2))
                p3 = int(data.get("cover_letter_length", 500))
                p4 = int(data.get("interview_rating", 3))
                p5 = int(data.get("job_deadline_days", 30))
                p6 = int(data.get("closing_soon_hours", 24))
                p7 = float(data.get("cv_file_size_mb", 2.5))
                p8 = int(data.get("hr_sla_days", 2))
                p9 = int(data.get("skills_count", 5))
                p10 = int(data.get("match_score_percent", 50))
                p11 = int(data.get("kanban_cards_limit", 20))
                p12 = float(data.get("notification_latency_seconds", 0.5))
                p13 = str(data.get("candidate_email", "employee@company.com"))
                p14 = str(data.get("cv_file_extension", ".pdf"))
                p15 = bool(data.get("has_disciplinary_record", False))

                errors = []
                if p1 < 180:
                    errors.append(("p1", "SENIORITY_REQUIREMENT_NOT_MET", f"Thâm niên ({p1} ngày) < Min (180 ngày)"))
                elif p1 > 18000:
                    errors.append(("p1", "RETIREMENT_AGE_EXCEEDED", f"Thâm niên ({p1:,} ngày) vượt trần Max (18.000 ngày)"))

                if p2 < 1:
                    errors.append(("p2", "INVALID_APP_COUNT", f"Số lượng đơn ({p2}) < Min (1 đơn)"))
                elif p2 > 3:
                    errors.append(("p2", "MAX_ACTIVE_APPLICATIONS_REACHED", f"Số lượng đơn ({p2}) vượt trần Max (3 đơn)"))

                if p3 < 10:
                    errors.append(("p3", "COVER_LETTER_TOO_SHORT", f"Độ dài thư ({p3} ký tự) < Min (10 ký tự)"))
                elif p3 > 1000:
                    errors.append(("p3", "COVER_LETTER_TOO_LONG", f"Độ dài thư ({p3} ký tự) vượt trần Max (1000 ký tự)"))

                if p4 < 1:
                    errors.append(("p4", "INVALID_RATING", f"Điểm đánh giá ({p4}) < Min (1 sao)"))
                elif p4 > 5:
                    errors.append(("p4", "RATING_OUT_OF_SCALE", f"Điểm đánh giá ({p4}) vượt trần Max (5 sao)"))

                if p5 < 1:
                    errors.append(("p5", "INVALID_DEADLINE", f"Hạn nộp hồ sơ ({p5} ngày) < Min (1 ngày)"))
                elif p5 > 90:
                    errors.append(("p5", "EXCEEDS_DEADLINE", f"Hạn nộp hồ sơ ({p5} ngày) vượt trần Max (90 ngày)"))

                if p6 < 1:
                    errors.append(("p6", "INVALID_CLOSING_SOON_HOURS", f"Ngưỡng Closing Soon ({p6} giờ) < Min (1 giờ)"))
                elif p6 > 72:
                    errors.append(("p6", "EXCEEDS_CLOSING_SOON_HOURS", f"Ngưỡng Closing Soon ({p6} giờ) vượt trần Max (72 giờ)"))

                if p7 < 0.001:
                    errors.append(("p7", "INVALID_CV_FILE_SIZE", f"Dung lượng CV ({p7} MB) < Min (0.001 MB)"))
                elif p7 > 5.0:
                    errors.append(("p7", "EXCEEDS_CV_FILE_SIZE", f"Dung lượng CV ({p7} MB) vượt trần Max (5.0 MB)"))

                if p8 < 1:
                    errors.append(("p8", "INVALID_HR_SLA", f"Thời hạn phản hồi HR SLA ({p8} ngày) < Min (1 ngày)"))
                elif p8 > 3:
                    errors.append(("p8", "EXCEEDS_HR_SLA", f"Thời hạn phản hồi HR SLA ({p8} ngày) vượt trần Max (3 ngày)"))

                if p9 < 1:
                    errors.append(("p9", "INVALID_SKILLS_COUNT", f"Số lượng kỹ năng ({p9}) < Min (1)"))
                elif p9 > 20:
                    errors.append(("p9", "EXCEEDS_SKILLS_COUNT", f"Số lượng kỹ năng ({p9}) vượt trần Max (20)"))

                if p10 < 1:
                    errors.append(("p10", "INVALID_MATCH_SCORE", f"Độ khớp kỹ năng ({p10}%) < Min (1%)"))
                elif p10 > 100:
                    errors.append(("p10", "EXCEEDS_MATCH_SCORE", f"Độ khớp kỹ năng ({p10}%) vượt trần Max (100%)"))

                if p11 < 1:
                    errors.append(("p11", "INVALID_KANBAN_LIMIT", f"Số thẻ trên cột ({p11}) < Min (1)"))
                elif p11 > 100:
                    errors.append(("p11", "EXCEEDS_KANBAN_LIMIT", f"Số thẻ trên cột ({p11}) vượt trần Max (100)"))

                if p12 < 0.1:
                    errors.append(("p12", "INVALID_NOTIFICATION_LATENCY", f"Độ trễ thông báo ({p12}s) < Min (0.1s)"))
                elif p12 > 2.0:
                    errors.append(("p12", "EXCEEDS_NOTIFICATION_LATENCY", f"Độ trễ thông báo ({p12}s) vượt trần Max (2.0s)"))

                # Thẩm định tham số không phải dạng số (P13, P14, P15)
                if not p13:
                    errors.append(("p13", "INVALID_EMAIL_EMPTY", "Email ứng viên không được để trống"))
                elif len(p13) > 255:
                    errors.append(("p13", "EMAIL_TOO_LONG", "Độ dài địa chỉ email vượt quá giới hạn 255 ký tự"))
                elif "@" not in p13 or p13.endswith("@"):
                    errors.append(("p13", "INVALID_EMAIL_FORMAT", f"Email ({p13}) sai định dạng cú pháp"))
                elif not p13.endswith("@company.com"):
                    errors.append(("p13", "INVALID_EMAIL_DOMAIN", f"Email ({p13}) không thuộc tên miền nội bộ @company.com"))

                if not p14:
                    errors.append(("p14", "INVALID_EXTENSION_EMPTY", "Định dạng tệp CV không được để trống"))
                elif p14.lower() not in [".pdf", ".docx"]:
                    errors.append(("p14", "INVALID_FILE_EXTENSION", f"Định dạng ({p14}) không được hỗ trợ (chỉ nhận .pdf, .docx)"))

                if p15:
                    errors.append(("p15", "DISCIPLINARY_VIOLATION", "Ứng viên đang trong thời gian chấp hành kỷ luật nội bộ"))

                if not errors:
                    return self._send_json({
                        "status": "APPROVED_ALL",
                        "success": True,
                        "code": 200,
                        "message": "Hồ sơ hợp lệ toàn phần. Đã tiếp nhận và chuyển tiếp vào luồng đánh giá Kanban."
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

        # Luồng 1 (OUT-01): Tiếp nhận hồ sơ ứng tuyển nội bộ
        elif path in ["/api/applications/apply", "/api/v1/applications/apply"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p1 = int(data.get("seniority_days", 730))
                p2 = int(data.get("active_applications", 2))
                p3 = int(data.get("cover_letter_length", 500))
                p7 = float(data.get("cv_file_size_mb", 2.5))
                p13 = str(data.get("candidate_email", "employee@company.com"))
                p14 = str(data.get("cv_file_extension", ".pdf"))
                p15 = bool(data.get("has_disciplinary_record", False))
                if (180 <= p1 <= 18000 and 1 <= p2 <= 3 and 10 <= p3 <= 1000 and 
                    0.001 <= p7 <= 5.0 and p13.endswith("@company.com") and 
                    p14.lower() in [".pdf", ".docx"] and not p15):
                    return self._send_json({
                        "status": "APPLICATION_ACCEPTED",
                        "success": True,
                        "code": 200,
                        "message": "Tiếp nhận hồ sơ ứng tuyển nội bộ thành công."
                    }, 200)
                else:
                    return self._send_json({"status": "REJECTED", "error": "APPLICATION_CRITERIA_UNMET"}, 400)
            except Exception as ex:
                return self._send_json({"error": "BAD_PAYLOAD", "message": str(ex)}, 400)

        # Luồng 2 (OUT-02): Ghi nhận điểm và hoàn tất phỏng vấn
        elif path in ["/api/interviews/evaluate", "/api/v1/interviews/evaluate"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p4 = int(data.get("interview_rating", 3))
                p10 = int(data.get("match_score_percent", 50))
                # Mã nguồn chuẩn SRS
                if 1 <= p4 <= 5 and 1 <= p10 <= 100:
                    return self._send_json({
                        "status": "INTERVIEW_EVALUATED",
                        "success": True,
                        "code": 200,
                        "message": "Ghi nhận điểm và hoàn tất phỏng vấn thành công."
                    }, 200)
                else:
                    return self._send_json({"status": "REJECTED", "error": "INVALID_PARAMS"}, 400)
            except Exception as ex:
                return self._send_json({"error": "BAD_PAYLOAD", "message": str(ex)}, 400)

        # Luồng 3 (OUT-03): Điều chuyển trạng thái thẻ ứng viên trên Kanban
        elif path in ["/api/kanban/move-card", "/api/v1/kanban/move-card"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p11 = int(data.get("kanban_cards_limit", 20))
                # Mã nguồn chuẩn SRS
                if 1 <= p11 <= 100:
                    return self._send_json({
                        "status": "KANBAN_STAGE_UPDATED",
                        "success": True,
                        "code": 200,
                        "message": "Điều chuyển trạng thái thẻ ứng viên trên Kanban thành công."
                    }, 200)
                else:
                    return self._send_json({"status": "REJECTED", "error": "INVALID_KANBAN_LIMIT"}, 400)
            except Exception as ex:
                return self._send_json({"error": "BAD_PAYLOAD", "message": str(ex)}, 400)

        # Luồng 4 (OUT-04): Đăng tải và kích hoạt tin tuyển dụng mới
        elif path in ["/api/jobs/create", "/api/v1/jobs/create"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p5 = int(data.get("job_deadline_days", 30))
                p9 = int(data.get("skills_count", 5))
                if 1 <= p5 <= 90 and 1 <= p9 <= 20:
                    return self._send_json({
                        "status": "JOB_POSTED_SUCCESS",
                        "success": True,
                        "code": 200,
                        "message": "Đăng tải và kích hoạt tin tuyển dụng mới thành công."
                    }, 200)
                else:
                    return self._send_json({"status": "REJECTED", "error": "INVALID_JOB_PARAMS"}, 400)
            except Exception as ex:
                return self._send_json({"error": "BAD_PAYLOAD", "message": str(ex)}, 400)

        # Luồng 5 (OUT-05): Gửi cảnh báo Closing Soon và SLA
        elif path in ["/api/alerts/trigger", "/api/v1/notifications/trigger"]:
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                p6 = int(data.get("closing_soon_hours", 24))
                p8 = int(data.get("hr_sla_days", 2))
                p12 = float(data.get("notification_latency_seconds", 0.5))
                # Mã nguồn chuẩn SRS
                if 1 <= p6 <= 72 and 1 <= p8 <= 3 and 0.1 <= p12 <= 2.0:
                    return self._send_json({
                        "status": "ALERT_TRIGGERED",
                        "success": True,
                        "code": 200,
                        "message": "Gửi cảnh báo Closing Soon và vi phạm SLA thành công."
                    }, 200)
                else:
                    return self._send_json({"status": "REJECTED", "error": "INVALID_ALERT_PARAMS"}, 400)
            except Exception as ex:
                return self._send_json({"error": "BAD_PAYLOAD", "message": str(ex)}, 400)

        # 1. Broadcast Reset / Init Demo to all microservices
        elif path == "/api/v1/init-demo":
            http_post_json(f"{JOB_SERVICE_URL}/init-demo", {})
            http_post_json(f"{APPLICATION_SERVICE_URL}/init-demo", {})
            http_post_json(f"{EMPLOYEE_SERVICE_URL}/init-demo", {})
            http_post_json(f"{NOTIFICATION_SERVICE_URL}/init-demo", {})
            return self._send_json({
                "success": True,
                "message": "Đã khởi tạo lại toàn bộ cơ sở dữ liệu của cả 4 Microservices Tuyển dụng nội bộ thành công!"
            })

        # 2. Route to Job Service
        elif path.startswith("/api/v1/jobs"):
            sub_path = path.replace("/api/v1", "")
            return self._proxy_request(f"{JOB_SERVICE_URL}{sub_path}", "POST", body_bytes)

        # 3. Route to Application Service
        elif path.startswith("/api/v1/applications"):
            sub_path = path.replace("/api/v1", "")
            return self._proxy_request(f"{APPLICATION_SERVICE_URL}{sub_path}", "POST", body_bytes)

        # 4. Route to Employee Service
        elif path.startswith("/api/v1/employees"):
            sub_path = path.replace("/api/v1", "")
            return self._proxy_request(f"{EMPLOYEE_SERVICE_URL}{sub_path}", "POST", body_bytes)

        # 5. Route to Notification Service
        elif path.startswith("/api/v1/notifications"):
            sub_path = path.replace("/api/v1", "")
            return self._proxy_request(f"{NOTIFICATION_SERVICE_URL}{sub_path}", "POST", body_bytes)

        else:
            return self._send_json({"error": "Endpoint not routed by API Gateway"}, 404)


def run_gateway():
    os.makedirs(STATIC_DIR, exist_ok=True)
    server_address = ("0.0.0.0", GATEWAY_PORT)
    httpd = http.server.ThreadingHTTPServer(server_address, GatewayRequestHandler)
    print(f"============================================================")
    print(f" [API Gateway - Tuyển Dụng Nội Bộ] Running on http://localhost:{GATEWAY_PORT}")
    print(f" Routing traffic to 4 independent microservices (8091-8094)")
    print(f" Serving static assets from: {STATIC_DIR}")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Gateway...")
        httpd.server_close()


if __name__ == "__main__":
    run_gateway()

