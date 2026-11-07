"""
crypto_engine.py - Cryptographic Verification & Anti-Fraud Engine
Performs TOTP dynamic QR verification, HMAC signature validation, and inter-service calls.
"""

import hmac
import hashlib
import base64
import json
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.common.config import TOKEN_SERVICE_URL, CUSTOMER_SERVICE_URL
from services.common.http_client import http_get_json, http_post_json
from services.payment_service.payment_db import (
    is_nonce_used,
    record_nonce,
    record_transaction
)

TOTP_STEP_SECONDS = 60
MAX_TIME_DRIFT_SECONDS = 120
MAX_SINGLE_OFFLINE_LIMIT = 1000000.0


def calculate_totp(secret_key: str, timestamp: int, step: int = TOTP_STEP_SECONDS) -> str:
    time_counter = int(timestamp) // step
    counter_bytes = time_counter.to_bytes(8, byteorder="big")
    key_bytes = bytes.fromhex(secret_key)

    h = hmac.new(key_bytes, counter_bytes, hashlib.sha256).digest()
    offset = h[-1] & 0x0F
    code_int = ((h[offset] & 0x7F) << 24 |
                (h[offset + 1] & 0xFF) << 16 |
                (h[offset + 2] & 0xFF) << 8 |
                (h[offset + 3] & 0xFF))
    return str(code_int % 1000000).zfill(6)


def generate_offline_qr_payload(user_id: str, token_id: str, secret_key: str, timestamp: int = None) -> str:
    """Client-side payload generation logic."""
    if timestamp is None:
        timestamp = int(time.time())

    totp_code = calculate_totp(secret_key, timestamp)
    message = f"V1:{user_id}:{token_id}:{timestamp}:{totp_code}".encode("utf-8")
    key_bytes = bytes.fromhex(secret_key)
    signature = hmac.new(key_bytes, message, hashlib.sha256).hexdigest()

    payload_dict = {
        "ver": 1,
        "uid": user_id,
        "tid": token_id,
        "ts": timestamp,
        "totp": totp_code,
        "sig": signature
    }

    raw_json = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw_json).decode("utf-8")


def verify_offline_qr_payload(payload_b64: str, bill_amount: float, current_time: int = None):
    """
    Verifies the scanned QR payload on the Payment & Fraud Microservice:
    1. Base64URL decoding and JSON parsing.
    2. Time Drift & Expiration check.
    3. Check offline single transaction limit.
    4. Anti-Replay check via Nonce cache.
    5. Fetch token from Token Microservice via Inter-Service REST API.
    6. Verify HMAC-SHA256 signature and TOTP.
    7. Deduct balance via Customer Microservice.
    8. Update token usage via Token Microservice.
    9. Record transaction and consume nonce.
    """
    if current_time is None:
        current_time = int(time.time())

    # Step 1: Decode Base64URL
    try:
        decoded_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        payload = json.loads(decoded_bytes.decode("utf-8"))
    except Exception as e:
        return {
            "success": False,
            "error_code": "INVALID_QR_FORMAT",
            "message": f"Mã QR không đúng định dạng chuẩn: {str(e)}"
        }

    user_id = payload.get("uid")
    token_id = payload.get("tid")
    timestamp = payload.get("ts")
    totp_code = payload.get("totp")
    signature = payload.get("sig")

    if not all([user_id, token_id, timestamp, totp_code, signature]):
        return {
            "success": False,
            "error_code": "MALFORMED_PAYLOAD",
            "message": "Thiếu trường dữ liệu bắt buộc trong mã QR"
        }

    # Step 2: Time Drift check
    time_diff = abs(current_time - timestamp)
    if time_diff > MAX_TIME_DRIFT_SECONDS:
        return {
            "success": False,
            "error_code": "QR_EXPIRED_TIME_DRIFT",
            "message": f"Mã QR đã hết hạn hiệu lực (Độ trễ thời gian: {time_diff}s > {MAX_TIME_DRIFT_SECONDS}s)"
        }

    # Step 3: Check Offline Single Transaction Limit
    if bill_amount <= 0:
        return {
            "success": False,
            "error_code": "EMPTY_CART",
            "message": "Số tiền đơn hàng không hợp lệ (phải lớn hơn 0 đồng)!"
        }

    if bill_amount > MAX_SINGLE_OFFLINE_LIMIT:
        return {
            "success": False,
            "error_code": "EXCEEDS_OFFLINE_LIMIT",
            "message": f"Giá trị đơn hàng ({bill_amount:,.0f}đ) vượt quá hạn mức tối đa cho phép của 1 lần thanh toán ngoại tuyến ({MAX_SINGLE_OFFLINE_LIMIT:,.0f}đ)"
        }

    # Step 4: Anti-Replay Protection check
    cache_key = f"nonce:{user_id}:{token_id}:{totp_code}"
    if is_nonce_used(cache_key):
        return {
            "success": False,
            "error_code": "DUPLICATE_TRANSACTION_REJECTED",
            "message": "CẢNH BÁO GIAN LẬN: Mã QR này đã được quét và sử dụng trước đó (Replay Attack Detected)"
        }

    # Step 5: Fetch Token Info from Token Microservice (Inter-service REST call)
    status, token_resp = http_get_json(f"{TOKEN_SERVICE_URL}/tokens/{token_id}")
    if status != 200 or not token_resp.get("success"):
        return {
            "success": False,
            "error_code": "TOKEN_NOT_FOUND",
            "message": "Token thanh toán ngoại tuyến không tồn tại trên hệ thống"
        }

    token_data = token_resp["token"]
    if not token_data.get("is_active"):
        return {
            "success": False,
            "error_code": "TOKEN_INACTIVE",
            "message": "Token thanh toán ngoại tuyến đã bị vô hiệu hóa hoặc đã dùng hết hạn mức"
        }

    if token_data.get("used_amount", 0.0) + bill_amount > token_data.get("max_accumulated_limit", 3000000.0):
        return {
            "success": False,
            "error_code": "TOKEN_LIMIT_EXCEEDED",
            "message": f"Giao dịch ({bill_amount:,.0f}đ) vượt quá hạn mức tích lũy tối đa còn lại của Token ({token_data.get('max_accumulated_limit', 3000000.0) - token_data.get('used_amount', 0.0):,.0f}đ)"
        }

    # Step 6: Verify HMAC-SHA256 Signature
    secret_key = token_data["secret_key"]
    message = f"V1:{user_id}:{token_id}:{timestamp}:{totp_code}".encode("utf-8")
    key_bytes = bytes.fromhex(secret_key)
    expected_sig = hmac.new(key_bytes, message, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_sig, signature):
        return {
            "success": False,
            "error_code": "INVALID_SIGNATURE",
            "message": "Chữ ký số không khớp! Mã QR có dấu hiệu bị can thiệp trái phép"
        }

    # Step 7: Verify TOTP Window
    current_window = current_time // TOTP_STEP_SECONDS
    ts_window = timestamp // TOTP_STEP_SECONDS
    if abs(current_window - ts_window) > 1:
        return {
            "success": False,
            "error_code": "TOTP_WINDOW_EXPIRED",
            "message": "Mã OTP dựa trên thời gian đã hết hạn hiệu lực"
        }

    # Step 8: Deduct Customer Balance via Customer Microservice (Inter-service REST call)
    c_status, c_resp = http_post_json(f"{CUSTOMER_SERVICE_URL}/wallet/deduct", {
        "user_id": user_id,
        "amount": bill_amount
    })

    if c_status != 200 or not c_resp.get("success"):
        return {
            "success": False,
            "error_code": "INSUFFICIENT_BALANCE",
            "message": c_resp.get("message", "Số dư tài khoản/ví liên kết không đủ để thanh toán")
        }

    # Step 9: Update Token Usage via Token Microservice
    http_post_json(f"{TOKEN_SERVICE_URL}/tokens/mark-used", {
        "token_id": token_id,
        "amount": bill_amount
    })

    # Step 10: Consume Nonce & Record Transaction in Payment DB
    record_nonce(cache_key, ttl_seconds=180)
    tx_id = record_transaction(
        order_id=f"ORD_{int(time.time())}",
        user_id=user_id,
        amount=bill_amount,
        payment_method="OFFLINE_TOTP_QR",
        status="SUCCESS",
        details=f"Token: {token_id}, AuthCode: AUTH_{totp_code}"
    )

    return {
        "success": True,
        "transaction_id": tx_id,
        "auth_code": f"AUTH_{totp_code}",
        "user_name": "Nguyễn Văn An",
        "amount_paid": bill_amount,
        "remaining_balance": c_resp.get("remaining_balance", 0.0),
        "message": "Thanh toán ngoại tuyến qua mã QR thành công!"
    }


def process_nfc_contactless(device_pan: str, cryptogram: str, bill_amount: float, user_id: str = "USER_001"):
    """
    Apple Pay / Google Wallet NFC processing in Payment Microservice.
    Calls Customer Service to deduct balance and records transaction.
    """
    c_status, c_resp = http_post_json(f"{CUSTOMER_SERVICE_URL}/wallet/deduct", {
        "user_id": user_id,
        "amount": bill_amount
    })

    if c_status != 200 or not c_resp.get("success"):
        return {
            "success": False,
            "error_code": "CARD_DECLINED",
            "message": c_resp.get("message", "Thẻ bị từ chối do không đủ số dư")
        }

    tx_id = record_transaction(
        order_id=f"ORD_NFC_{int(time.time())}",
        user_id=user_id,
        amount=bill_amount,
        payment_method="NFC_EMV_CONTACTLESS",
        status="SUCCESS",
        details=f"DPAN: {device_pan[-4:]}, Cryptogram: {cryptogram[:8]}..."
    )

    return {
        "success": True,
        "transaction_id": tx_id,
        "auth_code": f"EMV_{int(time.time()) % 1000000:06d}",
        "user_name": "Nguyễn Văn An",
        "card_type": "Visa / Apple Pay (Contactless)",
        "amount_paid": bill_amount,
        "remaining_balance": c_resp.get("remaining_balance", 0.0),
        "message": "Giao dịch NFC Contactless (Apple Pay) thành công không cần mạng di động!"
    }

