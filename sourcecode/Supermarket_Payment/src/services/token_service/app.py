"""
app.py - Token Vault Microservice (Port 8083)
Manages pre-fetched offline payment tokens, cryptographic keys, and token limits.
"""

import sys
import os
import http.server
from urllib.parse import urlparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.common.config import TOKEN_SERVICE_PORT
from services.common.http_client import BaseServiceHandler
from services.token_service.token_db import (
    init_db,
    reset_db,
    prefetch_tokens,
    get_token,
    mark_token_used
)


class TokenServiceHandler(BaseServiceHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            return self.send_json({"service": "token_service", "status": "UP", "port": TOKEN_SERVICE_PORT})

        # GET /tokens/<token_id>
        elif path.startswith("/tokens/") or path.startswith("/api/v1/tokens/"):
            parts = path.strip("/").split("/")
            token_id = parts[-1]
            token = get_token(token_id)
            if not token:
                return self.send_json({"success": False, "error": "Token not found"}, 404)
            return self.send_json({"success": True, "token": token})

        else:
            return self.send_json({"error": "Endpoint not found in token_service"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        if path in ["/init-demo", "/api/v1/init-demo"]:
            reset_db()
            tokens = prefetch_tokens("USER_001", count=5)
            return self.send_json({"success": True, "message": "Tokens initialized", "count": len(tokens)})

        elif path in ["/tokens/prefetch", "/api/v1/tokens/prefetch"]:
            user_id = body.get("user_id", "USER_001")
            count = int(body.get("count", 5))
            tokens = prefetch_tokens(user_id, count)
            return self.send_json({"success": True, "tokens": tokens})

        elif path in ["/tokens/mark-used", "/api/v1/tokens/mark-used"]:
            token_id = body.get("token_id")
            amount = float(body.get("amount", 0))
            if not token_id:
                return self.send_json({"success": False, "error": "Missing token_id"}, 400)
            mark_token_used(token_id, amount)
            return self.send_json({"success": True, "message": "Token usage updated"})

        else:
            return self.send_json({"error": "Endpoint not found in token_service"}, 404)


def run_service():
    init_db()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", TOKEN_SERVICE_PORT), TokenServiceHandler)
    print(f"[Token Service] Started on port {TOKEN_SERVICE_PORT} (DB: tokens.db)")
    server.serve_forever()


if __name__ == "__main__":
    run_service()

