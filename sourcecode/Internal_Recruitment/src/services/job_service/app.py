"""
app.py - Job Posting & Lifecycle Microservice (Port 8091)
Manages internal job catalog, real-time status calculation (OPEN, CLOSING_SOON, CLOSED),
and deadline extension.
"""

import sys
import os
import http.server
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.common.config import JOB_SERVICE_PORT
from services.common.http_client import BaseServiceHandler
from services.job_service.job_db import (
    init_db,
    reset_db,
    get_all_jobs,
    get_job_by_id,
    create_job,
    extend_job_deadline,
    close_job
)


class JobServiceHandler(BaseServiceHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/health":
            return self.send_json({"service": "job_service", "status": "UP", "port": JOB_SERVICE_PORT})

        elif path in ["/jobs", "/api/v1/jobs"]:
            keyword = qs.get("keyword", [""])[0]
            dept = qs.get("department", [""])[0]
            lvl = qs.get("level", [""])[0]
            only_active = qs.get("only_active", ["false"])[0].lower() == "true"
            jobs = get_all_jobs(keyword, dept, lvl, only_active)
            return self.send_json({"success": True, "jobs": jobs, "total": len(jobs)})

        elif path.startswith("/jobs/") or path.startswith("/api/v1/jobs/"):
            parts = path.strip("/").split("/")
            job_id = parts[-1]
            job = get_job_by_id(job_id)
            if not job:
                return self.send_json({"success": False, "error": "Job not found"}, 404)
            return self.send_json({"success": True, "job": job})

        else:
            return self.send_json({"error": "Endpoint not found in job_service"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        if path in ["/init-demo", "/api/v1/init-demo"]:
            reset_db()
            jobs = get_all_jobs()
            return self.send_json({"success": True, "message": "Job database reset", "count": len(jobs)})

        elif path in ["/jobs/create", "/api/v1/jobs/create"]:
            if not body.get("title") or not body.get("deadline_date"):
                return self.send_json({"success": False, "message": "Tiêu đề và Hạn chót không được để trống!"}, 400)
            new_job = create_job(body)
            return self.send_json({"success": True, "job": new_job, "message": "Đã đăng tin tuyển dụng nội bộ mới!"})

        elif path in ["/jobs/extend", "/api/v1/jobs/extend"]:
            job_id = body.get("job_id")
            new_deadline = body.get("new_deadline")
            if not job_id or not new_deadline:
                return self.send_json({"success": False, "message": "Thiếu job_id hoặc new_deadline"}, 400)
            updated = extend_job_deadline(job_id, new_deadline)
            return self.send_json({"success": True, "job": updated, "message": f"Đã gia hạn tin đến {new_deadline}!"})

        elif path in ["/jobs/close", "/api/v1/jobs/close"]:
            job_id = body.get("job_id")
            if not job_id:
                return self.send_json({"success": False, "message": "Thiếu job_id"}, 400)
            closed = close_job(job_id)
            return self.send_json({"success": True, "job": closed, "message": "Đã đóng tin tuyển dụng thành công!"})

        else:
            return self.send_json({"error": "Endpoint not found in job_service"}, 404)


def run_service():
    init_db()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", JOB_SERVICE_PORT), JobServiceHandler)
    print(f"[Job Service] Started on port {JOB_SERVICE_PORT} (DB: jobs.db)")
    server.serve_forever()


if __name__ == "__main__":
    run_service()

