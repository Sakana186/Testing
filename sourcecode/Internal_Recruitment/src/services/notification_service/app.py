"""
app.py - Notification Engine Microservice (Port 8094)
Dispatches real-time in-app alerts and notifications when application statuses change.
"""

import sys
import os
import http.server
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.common.config import NOTIFICATION_SERVICE_PORT
from services.common.http_client import BaseServiceHandler
from services.notification_service.notification_db import (
    init_db,
    reset_db,
    get_notifications,
    create_notification,
    mark_as_read
)


class NotificationServiceHandler(BaseServiceHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/health":
            return self.send_json({"service": "notification_service", "status": "UP", "port": NOTIFICATION_SERVICE_PORT})

        elif path in ["/notifications", "/api/v1/notifications"]:
            emp_id = qs.get("employee_id", ["EMP-101"])[0]
            notis = get_notifications(emp_id)
            unread = sum(1 for n in notis if n["is_read"] == 0)
            return self.send_json({"success": True, "notifications": notis, "unread_count": unread})

        elif path.startswith("/notifications/") or path.startswith("/api/v1/notifications/"):
            parts = path.strip("/").split("/")
            emp_id = parts[-1]
            notis = get_notifications(emp_id)
            unread = sum(1 for n in notis if n["is_read"] == 0)
            return self.send_json({"success": True, "notifications": notis, "unread_count": unread})

        else:
            return self.send_json({"error": "Endpoint not found in notification_service"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        if path in ["/init-demo", "/api/v1/init-demo"]:
            reset_db()
            notis = get_notifications("EMP-101")
            return self.send_json({"success": True, "message": "Notification database reset", "count": len(notis)})

        elif path in ["/notifications/create", "/api/v1/notifications/create"]:
            emp_id = body.get("employee_id")
            title = body.get("title")
            message = body.get("message")
            noti_type = body.get("type", "STATUS_UPDATE")

            if not emp_id or not title or not message:
                return self.send_json({"success": False, "message": "Thiếu tham số thông báo"}, 400)

            nid = create_notification(emp_id, title, message, noti_type)
            return self.send_json({"success": True, "notification_id": nid, "message": "Đã gửi thông báo thành công"})

        elif path in ["/notifications/mark-read", "/api/v1/notifications/mark-read"]:
            emp_id = body.get("employee_id", "EMP-101")
            noti_id = body.get("notification_id")
            mark_as_read(emp_id, noti_id)
            return self.send_json({"success": True, "message": "Đã đánh dấu đã đọc"})

        else:
            return self.send_json({"error": "Endpoint not found in notification_service"}, 404)


def run_service():
    init_db()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", NOTIFICATION_SERVICE_PORT), NotificationServiceHandler)
    print(f"[Notification Service] Started on port {NOTIFICATION_SERVICE_PORT} (DB: notifications.db)")
    server.serve_forever()


if __name__ == "__main__":
    run_service()

