"""
run_microservices.py - Master Orchestrator for Internal Recruitment Microservices Mesh
Launches all 4 microservices + API Gateway concurrently (Ports 8090-8094),
monitors cluster health, and provides graceful shutdown on Ctrl+C.
"""

import sys
import os
import time
import threading
import http.server

# Ensure src root directory is in python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.common.config import (
    GATEWAY_PORT,
    JOB_SERVICE_PORT,
    APPLICATION_SERVICE_PORT,
    EMPLOYEE_SERVICE_PORT,
    NOTIFICATION_SERVICE_PORT,
    GATEWAY_URL,
    JOB_SERVICE_URL,
    APPLICATION_SERVICE_URL,
    EMPLOYEE_SERVICE_URL,
    NOTIFICATION_SERVICE_URL
)
from services.common.http_client import http_get_json

# Import service handlers and initializers
from services.job_service.app import JobServiceHandler, init_db as init_job_db
from services.application_service.app import ApplicationServiceHandler, init_db as init_app_db
from services.employee_service.app import EmployeeServiceHandler, init_db as init_emp_db
from services.notification_service.app import NotificationServiceHandler, init_db as init_noti_db
from gateway.gateway_server import GatewayRequestHandler

servers = []


def start_service(name: str, port: int, handler_cls, init_func=None):
    if init_func:
        init_func()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), handler_cls)
    servers.append(server)
    print(f"  [+] {name:<32} running on http://127.0.0.1:{port}")
    server.serve_forever()


def main():
    print("=" * 70)
    print(" INTERNAL RECRUITMENT & MOBILITY PORTAL (TUYỂN DỤNG NỘI BỘ)")
    print(" MICROSERVICES ARCHITECTURE CLUSTER LAUNCHER")
    print("=" * 70)
    print("Starting microservices mesh...")

    services = [
        ("Job Service (8091)", JOB_SERVICE_PORT, JobServiceHandler, init_job_db),
        ("Application Service (8092)", APPLICATION_SERVICE_PORT, ApplicationServiceHandler, init_app_db),
        ("Employee Service (8093)", EMPLOYEE_SERVICE_PORT, EmployeeServiceHandler, init_emp_db),
        ("Notification Service (8094)", NOTIFICATION_SERVICE_PORT, NotificationServiceHandler, init_noti_db),
        ("API Gateway & Static Proxy (8090)", GATEWAY_PORT, GatewayRequestHandler, None),
    ]

    threads = []
    for name, port, handler, init_fn in services:
        t = threading.Thread(target=start_service, args=(name, port, handler, init_fn), daemon=True)
        t.start()
        threads.append(t)

    # Allow servers to bind
    time.sleep(0.8)

    print("\nVerifying cluster health...")
    all_healthy = True
    for svc_name, url in [
        ("Job Service", f"{JOB_SERVICE_URL}/health"),
        ("Application Service", f"{APPLICATION_SERVICE_URL}/health"),
        ("Employee Service", f"{EMPLOYEE_SERVICE_URL}/health"),
        ("Notification Service", f"{NOTIFICATION_SERVICE_URL}/health"),
        ("API Gateway", f"{GATEWAY_URL}/api/v1/health"),
    ]:
        status, resp = http_get_json(url, timeout=2)
        if status == 200 and (resp.get("status") == "UP" or resp.get("gateway") == "UP"):
            print(f"  [*] {svc_name:<24} [HEALTHY] -> {resp.get('status') or resp.get('gateway')}")
        else:
            print(f"  [!] {svc_name:<24} [FAILED]")
            all_healthy = False

    if all_healthy:
        print("\n" + "=" * 70)
        print(f" CLUSTER READY! Access the Web Application at:")
        print(f" >>> {GATEWAY_URL} <<<")
        print(" Press Ctrl+C to stop all services.")
        print("=" * 70 + "\n")
    else:
        print("\n[WARNING] Some services reported non-200 status.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Shutdown] Stopping all microservices gracefully...")
        for s in servers:
            try:
                s.shutdown()
            except Exception:
                pass
        print("[Shutdown] All microservices stopped.")


if __name__ == "__main__":
    main()

