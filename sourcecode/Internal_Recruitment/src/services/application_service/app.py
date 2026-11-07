"""
app.py - Application & Kanban Pipeline Microservice (Port 8092)
Coordinates application submissions, eligibility verification, Kanban board movements,
and inter-service notification triggers.
"""

import sys
import os
import http.server
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.common.config import (
    APPLICATION_SERVICE_PORT,
    JOB_SERVICE_URL,
    EMPLOYEE_SERVICE_URL,
    NOTIFICATION_SERVICE_URL
)
from services.common.http_client import BaseServiceHandler, http_get_json, http_post_json
from services.application_service.application_db import (
    init_db,
    reset_db,
    get_all_applications,
    get_applications_by_employee,
    get_active_count,
    has_applied_for_job,
    create_application_record,
    update_status
)


class ApplicationServiceHandler(BaseServiceHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/health":
            return self.send_json({"service": "application_service", "status": "UP", "port": APPLICATION_SERVICE_PORT})

        elif path in ["/applications", "/api/v1/applications"]:
            apps = get_all_applications()
            return self.send_json({"success": True, "applications": apps, "total": len(apps)})

        elif path in ["/applications/my-applications", "/api/v1/applications/my-applications"]:
            emp_id = qs.get("employee_id", ["EMP-101"])[0]
            apps = get_applications_by_employee(emp_id)
            active_count = get_active_count(emp_id)
            return self.send_json({"success": True, "applications": apps, "active_count": active_count})

        else:
            return self.send_json({"error": "Endpoint not found in application_service"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        if path in ["/init-demo", "/api/v1/init-demo"]:
            reset_db()
            apps = get_all_applications()
            return self.send_json({"success": True, "message": "Application database reset", "count": len(apps)})

        # 1. Submit Application
        elif path in ["/applications/apply", "/api/v1/applications/apply"]:
            job_id = body.get("job_id")
            employee_id = body.get("employee_id", "EMP-101")
            cover_letter = body.get("cover_letter", "").strip()
            resume_file = body.get("resume_file", "Internal_Profile.pdf")

            if not job_id:
                return self.send_json({"success": False, "message": "Thiếu mã vị trí tuyển dụng (job_id)"}, 400)

            if len(cover_letter) < 10:
                return self.send_json({
                    "success": False,
                    "error_code": "COVER_LETTER_TOO_SHORT",
                    "message": "Thư nguyện vọng phải có độ dài tối thiểu 10 ký tự!"
                }, 400)

            # Step A: Check Job Status via Job Microservice
            j_status, j_resp = http_get_json(f"{JOB_SERVICE_URL}/jobs/{job_id}")
            if j_status != 200 or not j_resp.get("success"):
                return self.send_json({"success": False, "message": "Vị trí tuyển dụng không tồn tại"}, 404)

            job = j_resp["job"]
            if job.get("computed_status") == "CLOSED":
                return self.send_json({
                    "success": False,
                    "error_code": "JOB_EXPIRED",
                    "message": "Tin tuyển dụng này đã hết hạn nộp hồ sơ!"
                }, 400)

            # Step B: Check Employee Seniority & Disciplinary Status via Employee Microservice
            e_status, e_resp = http_post_json(f"{EMPLOYEE_SERVICE_URL}/employees/check-eligibility", {
                "employee_id": employee_id
            })
            if e_status != 200 or not e_resp.get("eligible"):
                return self.send_json({
                    "success": False,
                    "error_code": "SENIORITY_REQUIREMENT_NOT_MET",
                    "message": e_resp.get("message", "Chưa đủ điều kiện thâm niên 6 tháng để ứng tuyển")
                }, 400)

            employee = e_resp["employee"]

            # Step C: Check Duplicate Application
            if has_applied_for_job(job_id, employee_id):
                return self.send_json({
                    "success": False,
                    "error_code": "ALREADY_APPLIED",
                    "message": "Bạn đã nộp hồ sơ cho vị trí này rồi! Vui lòng theo dõi tiến trình."
                }, 400)

            # Step D: Check Active Applications Limit (Max 3)
            active_cnt = get_active_count(employee_id)
            if active_cnt >= 3:
                return self.send_json({
                    "success": False,
                    "error_code": "MAX_ACTIVE_APPLICATIONS_REACHED",
                    "message": "Bạn đã đạt giới hạn tối đa 3 đơn ứng tuyển đang hoạt động! Hãy đợi kết quả các đơn cũ."
                }, 400)

            # Step E: Insert Record
            app_id = create_application_record(
                job_id=job_id,
                job_title=job["title"],
                employee_id=employee_id,
                employee_name=employee["name"],
                department=employee["current_department"],
                cover_letter=cover_letter,
                resume_file=resume_file
            )

            # Step F: Dispatch Notification via Notification Microservice
            http_post_json(f"{NOTIFICATION_SERVICE_URL}/notifications/create", {
                "employee_id": employee_id,
                "title": f"🎉 Ứng tuyển thành công: {job['title']}",
                "message": f"Hồ sơ mã {app_id} đã được gửi bảo mật đến bộ phận Tuyển dụng nội bộ. HR sẽ phản hồi trong 3 ngày làm việc.",
                "type": "APPLICATION_SUBMITTED"
            })

            return self.send_json({
                "success": True,
                "application_id": app_id,
                "status": "APPLIED",
                "message": "Đã nộp hồ sơ ứng tuyển bảo mật thành công! HR đã tiếp nhận trên bảng Kanban."
            })

        # 2. Update Application Status (Kanban Transition by HR)
        elif path in ["/applications/update-status", "/api/v1/applications/update-status"]:
            app_id = body.get("application_id")
            new_status = body.get("new_status")
            notes = body.get("hr_notes", "")
            score = body.get("interview_score")

            if not app_id or not new_status:
                return self.send_json({"success": False, "message": "Thiếu application_id hoặc new_status"}, 400)

            updated_app = update_status(app_id, new_status, notes, score)
            if not updated_app:
                return self.send_json({"success": False, "message": "Không tìm thấy hồ sơ ứng tuyển"}, 404)

            # Notify Candidate
            status_labels = {
                "HR_SCREENING": "HR đã tiếp nhận và đang sàng lọc hồ sơ",
                "INTERVIEW": "Đã xếp lịch Phỏng vấn chuyên môn với Hiring Manager",
                "OFFER": "Chúc mừng! Bạn đã nhận được Đề nghị điều chuyển (Offer)",
                "TRANSFERRED": "Hoàn tất thủ tục chuyển phòng ban thành công",
                "REJECTED": "Hồ sơ của bạn chưa phù hợp cho đợt tuyển này"
            }
            desc = status_labels.get(new_status, new_status)
            http_post_json(f"{NOTIFICATION_SERVICE_URL}/notifications/create", {
                "employee_id": updated_app["employee_id"],
                "title": f"🔔 Cập nhật hồ sơ {updated_app['job_title']}",
                "message": f"Trạng thái mới: {new_status} ({desc}). Ghi chú HR: {notes if notes else 'Đang tiến hành'}.",
                "type": "STATUS_UPDATE"
            })

            return self.send_json({
                "success": True,
                "application": updated_app,
                "message": f"Đã cập nhật trạng thái hồ sơ thành {new_status}!"
            })

        else:
            return self.send_json({"error": "Endpoint not found in application_service"}, 404)


def run_service():
    init_db()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", APPLICATION_SERVICE_PORT), ApplicationServiceHandler)
    print(f"[Application Service] Started on port {APPLICATION_SERVICE_PORT} (DB: applications.db)")
    server.serve_forever()


if __name__ == "__main__":
    run_service()

