"""
run_microservices.py - Master Orchestrator for Microservices Mesh
Launches all 4 microservices + API Gateway concurrently, monitors cluster health,
and provides graceful shutdown on Ctrl+C.
"""

import sys
import os
import time
import threading
import http.server

# Ensure root directory is in python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.common.config import (
    GATEWAY_PORT,
    POS_SERVICE_PORT,
    PAYMENT_SERVICE_PORT,
    TOKEN_SERVICE_PORT,
    CUSTOMER_SERVICE_PORT,
    GATEWAY_URL,
    POS_SERVICE_URL,
    PAYMENT_SERVICE_URL,
    TOKEN_SERVICE_URL,
    CUSTOMER_SERVICE_URL
)
from services.common.http_client import http_get_json

# Import service handlers and initializers
from services.pos_service.app import POSServiceHandler, init_db as init_pos_db
from services.token_service.app import TokenServiceHandler, init_db as init_token_db
from services.customer_service.app import CustomerServiceHandler, init_db as init_customer_db
from services.payment_service.app import PaymentServiceHandler, init_db as init_payment_db
from gateway.gateway_server import GatewayRequestHandler

servers = []


def start_service(name: str, port: int, handler_cls, init_func=None):
    if init_func:
        init_func()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), handler_cls)
    servers.append(server)
    print(f"  [+] {name:<26} running on http://127.0.0.1:{port}")
    server.serve_forever()


def main():
    print("=" * 66)
    print(" SUPERMARKET OFFLINE PAYMENT & RESILIENT CHECKOUT (SOPRCS)")
    print(" MICROSERVICES ARCHITECTURE CLUSTER LAUNCHER")
    print("=" * 66)
    print("Starting microservices mesh...")

    services = [
        ("POS & Order Service", POS_SERVICE_PORT, POSServiceHandler, init_pos_db),
        ("Token Vault Service", TOKEN_SERVICE_PORT, TokenServiceHandler, init_token_db),
        ("Customer & BNPL Service", CUSTOMER_SERVICE_PORT, CustomerServiceHandler, init_customer_db),
        ("Payment & Fraud Service", PAYMENT_SERVICE_PORT, PaymentServiceHandler, init_payment_db),
        ("API Gateway & Reverse Proxy", GATEWAY_PORT, GatewayRequestHandler, None),
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
        ("POS Service", f"{POS_SERVICE_URL}/health"),
        ("Token Service", f"{TOKEN_SERVICE_URL}/health"),
        ("Customer Service", f"{CUSTOMER_SERVICE_URL}/health"),
        ("Payment Service", f"{PAYMENT_SERVICE_URL}/health"),
    ]:
        status, resp = http_get_json(url, timeout=2)
        if status == 200 and resp.get("status") == "UP":
            print(f"  [*] {svc_name:<20} [HEALTHY] -> {resp}")
        else:
            print(f"  [!] {svc_name:<20} [FAILED]")
            all_healthy = False

    if all_healthy:
        print("\n" + "=" * 66)
        print(f" CLUSTER READY! Access the Web Application at:")
        print(f" >>> {GATEWAY_URL} <<<")
        print(" Press Ctrl+C to stop all services.")
        print("=" * 66 + "\n")
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

