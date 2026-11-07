"""
app.py - Employee Profile & Talent Service (Port 8093)
Provides employee profile data, authenticated user context, and career mobility eligibility checks.
"""

import sys
import os
import http.server
from urllib.parse import urlparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.common.config import EMPLOYEE_SERVICE_PORT
from services.common.http_client import BaseServiceHandler
from services.employee_service.employee_db import (
    init_db,
    reset_db,
    get_all_employees,
    get_employee,
    check_eligibility
)


class EmployeeServiceHandler(BaseServiceHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            return self.send_json({"service": "employee_service", "status": "UP", "port": EMPLOYEE_SERVICE_PORT})

        elif path in ["/employees", "/api/v1/employees"]:
            employees = get_all_employees()
            return self.send_json({"success": True, "employees": employees})

        elif path.startswith("/employees/") or path.startswith("/api/v1/employees/"):
            parts = path.strip("/").split("/")
            emp_id = parts[-1]
            emp = get_employee(emp_id)
            if not emp:
                return self.send_json({"success": False, "error": "Employee not found"}, 404)
            return self.send_json({"success": True, "employee": emp})

        else:
            return self.send_json({"error": "Endpoint not found in employee_service"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        if path in ["/init-demo", "/api/v1/init-demo"]:
            reset_db()
            employees = get_all_employees()
            return self.send_json({"success": True, "message": "Employee database reset", "count": len(employees)})

        elif path in ["/employees/check-eligibility", "/api/v1/employees/check-eligibility"]:
            emp_id = body.get("employee_id", "EMP-101")
            eligible, msg, emp = check_eligibility(emp_id)
            return self.send_json({
                "success": True,
                "eligible": eligible,
                "message": msg,
                "employee": emp
            })

        else:
            return self.send_json({"error": "Endpoint not found in employee_service"}, 404)


def run_service():
    init_db()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", EMPLOYEE_SERVICE_PORT), EmployeeServiceHandler)
    print(f"[Employee Service] Started on port {EMPLOYEE_SERVICE_PORT} (DB: employees.db)")
    server.serve_forever()


if __name__ == "__main__":
    run_service()

