"""
crypto_engine.py - Cryptographic and Offline Token Engine
Implements TOTP (Time-based One-Time Password), HMAC-SHA256 signatures,
anti-replay protection, time drift tolerance, and Apple Pay NFC simulation.
"""

import hmac
import hashlib
import base64
import json
import time
from database import (
    get_token,
    get_customer,
    update_customer_balance,
    mark_token_used,
    is_nonce_used,
    record_nonce,
    record_transaction
)

TOTP_STEP_SECONDS = 60
MAX_TIME_DRIFT_SECONDS = 120  # Tolerance for client/server clock difference
MAX_SINGLE_OFFLINE_LIMIT = 1000000.0  # 1,000,000 VND max per offline QR transaction


def calculate_totp(secret_key: str, timestamp: int, step: int = TOTP_STEP_SECONDS) -> str:
    """
    Computes a 6-digit TOTP code using HMAC-SHA256 based on the secret key and time window.
    """
    time_counter = int(timestamp) // step
    counter_bytes = time_counter.to_bytes(8, byteorder="big")
    key_bytes = bytes.fromhex(secret_key)

    h = hmac.new(key_bytes, counter_bytes, hashlib.sha256).digest()
    # Dynamic truncation (RFC 6238)
    offset = h[-1] & 0x0F
    code_int = ((h[offset] & 0x7F) << 24 |
                (h[offset + 1] & 0xFF) << 16 |
                (h[offset + 2] & 0xFF) << 8 |
                (h[offset + 3] & 0xFF))
    totp = str(code_int % 1000000).zfill(6)
    return totp


def generate_offline_qr_payload(user_id: str, token_id: str, secret_key: str, timestamp: int = None) -> str:
    """
    Generates an encrypted, signed Offline QR Payload on the mobile device (Offline Mode).
    Payload format: Base64URL-encoded JSON structure with HMAC-SHA256 signature.
    """
    if timestamp is None:
        timestamp = int(time.time())

    totp_code = calculate_totp(secret_key, timestamp)

    # Core message to sign
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
    Verifies the scanned QR payload on the Cloud Payment Gateway via the POS:
    1. Base64URL decoding and JSON parsing.
    2. Time Drift & Expiration check.
    3. Anti-Replay check via Nonce cache.
    4. Token validity and offline spending ceiling limit check.
    5. Signature & TOTP verification against the customer's shared secret.
    6. Balance deduction and transaction confirmation.
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

    # Step 2: Time Drift check (|T_client - T_server| <= MAX_TIME_DRIFT_SECONDS)
    time_diff = abs(current_time - timestamp)
    if time_diff > MAX_TIME_DRIFT_SECONDS:
        return {
            "success": False,
            "error_code": "QR_EXPIRED_TIME_DRIFT",
            "message": f"Mã QR đã hết hạn hiệu lực (Độ trễ thời gian: {time_diff}s > {MAX_TIME_DRIFT_SECONDS}s)"
        }

    # Step 3: Check Offline Single Transaction Limit
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

    # Step 5: Verify Token Existence & Validity in DB
    token_data = get_token(token_id)
    if not token_data:
        return {
            "success": False,
            "error_code": "TOKEN_NOT_FOUND",
            "message": "Token thanh toán ngoại tuyến không tồn tại trên hệ thống"
        }

    if not token_data["is_active"]:
        return {
            "success": False,
            "error_code": "TOKEN_INACTIVE",
            "message": "Token thanh toán ngoại tuyến đã bị vô hiệu hóa hoặc đã dùng hết hạn mức"
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

    # Step 7: Verify TOTP Calculation for current or adjacent time window
    # Allow current window and +/- 1 window
    current_window = current_time // TOTP_STEP_SECONDS
    ts_window = timestamp // TOTP_STEP_SECONDS
    if abs(current_window - ts_window) > 1:
        return {
            "success": False,
            "error_code": "TOTP_WINDOW_EXPIRED",
            "message": "Mã OTP dựa trên thời gian đã hết hạn hiệu lực"
        }

    # Step 8: Verify Customer Balance
    customer = get_customer(user_id)
    if not customer or customer["wallet_balance"] < bill_amount:
        return {
            "success": False,
            "error_code": "INSUFFICIENT_BALANCE",
            "message": f"Số dư tài khoản/ví liên kết không đủ ({customer['wallet_balance'] if customer else 0:,.0f}đ < {bill_amount:,.0f}đ)"
        }

    # SUCCESS: Consume Nonce to prevent replay
    record_nonce(cache_key, ttl_seconds=180)

    # Deduct customer balance & record usage
    new_balance = customer["wallet_balance"] - bill_amount
    update_customer_balance(user_id, new_balance)
    mark_token_used(token_id, bill_amount)

    # Record transaction log
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
        "user_name": customer["name"],
        "amount_paid": bill_amount,
        "remaining_balance": new_balance,
        "message": "Thanh toán ngoại tuyến qua mã QR thành công!"
    }


def process_nfc_contactless(device_pan: str, cryptogram: str, bill_amount: float, user_id: str = "USER_001"):
    """
    Simulates Apple Pay / Google Wallet NFC Contactless EMV processing.
    The customer's phone does NOT need internet connection because the Device PAN (DPAN)
    and ARQC Cryptogram are stored and generated directly by the hardware Secure Element (SE).
    The POS transmits this packet over its in-store wired LAN to the Bank/Card Scheme Switch.
    """
    customer = get_customer(user_id)
    if not customer:
        return {"success": False, "error_code": "CUSTOMER_NOT_FOUND", "message": "Không tìm thấy thông tin chủ thẻ"}

    if customer["wallet_balance"] < bill_amount:
        return {
            "success": False,
            "error_code": "CARD_DECLINED",
            "message": f"Thẻ bị từ chối: Số dư khả dụng không đủ ({customer['wallet_balance']:,.0f}đ < {bill_amount:,.0f}đ)"
        }

    # Simulate bank approval
    new_balance = customer["wallet_balance"] - bill_amount
    update_customer_balance(user_id, new_balance)

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
        "user_name": customer["name"],
        "card_type": "Visa / Apple Pay (Contactless)",
        "amount_paid": bill_amount,
        "remaining_balance": new_balance,
        "message": "Giao dịch NFC Contactless (Apple Pay) thành công không cần mạng di động!"
    }
