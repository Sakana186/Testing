# -*- coding: utf-8 -*-
"""
test_ai_code.py - Bộ Kiểm Thử Hộp Trắng Sinh Tự Động Từ Mã Nguồn (White-box Automation Test Suite)
Mục tiêu bao phủ:
1. 100% Statement Coverage (Bao phủ câu lệnh)
2. 100% Branch Coverage (Bao phủ nhánh rẽ, bao gồm tất cả các nhánh True/False của biểu thức phức hợp)
3. 100% All-Uses Data Flow Coverage (Bao phủ tất cả các đường đi Def-Use không bị tái định nghĩa)

Framework: pytest
Chạy trực tiếp: pytest test_ai_code.py
"""

import sys
import os
import pytest

# Thêm đường dẫn hiện tại để import module logic mã nguồn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from source_logic import (
    validate_all_irtmp,
    process_irtmp_decision,
    validate_all_soprcs,
    process_soprcs_decision
)


# ==============================================================================
# BASELINE DỮ LIỆU DANH ĐỊNH CHO TỪNG HỆ THỐNG
# ==============================================================================

IRTMP_NOMINAL = {
    "seniority_days": 730,
    "active_applications": 2,
    "cover_letter_length": 500,
    "interview_rating": 3,
    "job_deadline_days": 30,
    "closing_soon_hours": 24,
    "cv_file_size_mb": 2.5,
    "hr_sla_days": 2,
    "skills_count": 5,
    "match_score_percent": 50,
    "kanban_cards_limit": 20,
    "notification_latency_seconds": 0.5,
    "candidate_email": "employee@company.com",
    "cv_file_extension": ".pdf",
    "has_disciplinary_record": False
}

SOPRCS_NOMINAL = {
    "amount": 500000,
    "cart_quantity": 25,
    "loan_amount": 250000,
    "credit_score": 750,
    "qr_totp_period_sec": 30,
    "time_drift_sec": 0,
    "nonce_ttl_sec": 90,
    "token_spending_limit": 1500000,
    "parked_order_timeout_min": 30,
    "pay_later_grace_period_hr": 12,
    "wifi_session_duration_min": 8,
    "prefetched_tokens_count": 3,
    "wifi_qos_bandwidth_mbps": 1.0,
    "customer_phone": "0912345678",
    "currency": "VND",
    "is_ekyc_verified": True
}


def make_irtmp(**kwargs):
    d = IRTMP_NOMINAL.copy()
    d.update(kwargs)
    return d


def make_soprcs(**kwargs):
    d = SOPRCS_NOMINAL.copy()
    d.update(kwargs)
    return d


# ==============================================================================
# CLASS 1: KIỂM THỬ LUỒNG ĐIỀU KHIỂN (CONTROL FLOW TESTING)
# Bao phủ 100% Statement Coverage & 100% Branch Coverage
# ==============================================================================

class Test_AI_ControlFlow:
    """
    Kiểm thử luồng điều khiển (Control Flow Testing) trên đồ thị CFG:
    - Bao phủ 100% tất cả các câu lệnh thực thi (Statement Coverage)
    - Bao phủ 100% các nhánh rẽ điều kiện đơn và điều kiện phức hợp (Branch Coverage)
    """

    # --------------------------------------------------------------------------
    # 1. IRTMP Gateway - Statement & Branch Coverage (Validate-All)
    # --------------------------------------------------------------------------
    @pytest.mark.parametrize("tc_id, override, exp_code, exp_status, exp_error", [
        # Nhánh True toàn phần (if not errors -> APPROVED_ALL)
        ("TC-CFG-IR-GW-00", {}, 200, "APPROVED_ALL", None),

        # 32 Nhánh False kích hoạt từng câu lệnh errors.append(...)
        ("TC-CFG-IR-GW-01", {"seniority_days": 179}, 400, "REJECTED", "SENIORITY_REQUIREMENT_NOT_MET"),
        ("TC-CFG-IR-GW-02", {"seniority_days": 18001}, 400, "REJECTED", "RETIREMENT_AGE_EXCEEDED"),
        ("TC-CFG-IR-GW-03", {"active_applications": 0}, 400, "REJECTED", "INVALID_APP_COUNT"),
        ("TC-CFG-IR-GW-04", {"active_applications": 4}, 400, "REJECTED", "MAX_ACTIVE_APPLICATIONS_REACHED"),
        ("TC-CFG-IR-GW-05", {"cover_letter_length": 9}, 400, "REJECTED", "COVER_LETTER_TOO_SHORT"),
        ("TC-CFG-IR-GW-06", {"cover_letter_length": 1001}, 400, "REJECTED", "COVER_LETTER_TOO_LONG"),
        ("TC-CFG-IR-GW-07", {"interview_rating": 0}, 400, "REJECTED", "INVALID_RATING"),
        ("TC-CFG-IR-GW-08", {"interview_rating": 6}, 400, "REJECTED", "RATING_OUT_OF_SCALE"),
        ("TC-CFG-IR-GW-09", {"job_deadline_days": 0}, 400, "REJECTED", "INVALID_DEADLINE"),
        ("TC-CFG-IR-GW-10", {"job_deadline_days": 91}, 400, "REJECTED", "EXCEEDS_DEADLINE"),
        ("TC-CFG-IR-GW-11", {"closing_soon_hours": 0}, 400, "REJECTED", "INVALID_CLOSING_SOON_HOURS"),
        ("TC-CFG-IR-GW-12", {"closing_soon_hours": 73}, 400, "REJECTED", "EXCEEDS_CLOSING_SOON_HOURS"),
        ("TC-CFG-IR-GW-13", {"cv_file_size_mb": 0.0}, 400, "REJECTED", "INVALID_CV_FILE_SIZE"),
        ("TC-CFG-IR-GW-14", {"cv_file_size_mb": 5.1}, 400, "REJECTED", "EXCEEDS_CV_FILE_SIZE"),
        ("TC-CFG-IR-GW-15", {"hr_sla_days": 0}, 400, "REJECTED", "INVALID_HR_SLA"),
        ("TC-CFG-IR-GW-16", {"hr_sla_days": 4}, 400, "REJECTED", "EXCEEDS_HR_SLA"),
        ("TC-CFG-IR-GW-17", {"skills_count": 0}, 400, "REJECTED", "INVALID_SKILLS_COUNT"),
        ("TC-CFG-IR-GW-18", {"skills_count": 21}, 400, "REJECTED", "EXCEEDS_SKILLS_COUNT"),
        ("TC-CFG-IR-GW-19", {"match_score_percent": 0}, 400, "REJECTED", "INVALID_MATCH_SCORE"),
        ("TC-CFG-IR-GW-20", {"match_score_percent": 101}, 400, "REJECTED", "EXCEEDS_MATCH_SCORE"),
        ("TC-CFG-IR-GW-21", {"kanban_cards_limit": 0}, 400, "REJECTED", "INVALID_KANBAN_LIMIT"),
        ("TC-CFG-IR-GW-22", {"kanban_cards_limit": 101}, 400, "REJECTED", "EXCEEDS_KANBAN_LIMIT"),
        ("TC-CFG-IR-GW-23", {"notification_latency_seconds": 0.0}, 400, "REJECTED", "INVALID_NOTIFICATION_LATENCY"),
        ("TC-CFG-IR-GW-24", {"notification_latency_seconds": 2.1}, 400, "REJECTED", "EXCEEDS_NOTIFICATION_LATENCY"),
        ("TC-CFG-IR-GW-25", {"candidate_email": ""}, 400, "REJECTED", "INVALID_EMAIL_EMPTY"),
        ("TC-CFG-IR-GW-26", {"candidate_email": "user@" + "a" * 255}, 400, "REJECTED", "EMAIL_TOO_LONG"),
        ("TC-CFG-IR-GW-27", {"candidate_email": "invalid_email_format"}, 400, "REJECTED", "INVALID_EMAIL_FORMAT"),
        ("TC-CFG-IR-GW-28", {"candidate_email": "user@gmail.com"}, 400, "REJECTED", "INVALID_EMAIL_DOMAIN"),
        ("TC-CFG-IR-GW-29", {"cv_file_extension": ""}, 400, "REJECTED", "INVALID_EXTENSION_EMPTY"),
        ("TC-CFG-IR-GW-30", {"cv_file_extension": ".exe"}, 400, "REJECTED", "INVALID_FILE_EXTENSION"),
        ("TC-CFG-IR-GW-31", {"cv_file_extension": ".png"}, 400, "REJECTED", "INVALID_FILE_EXTENSION"),
        ("TC-CFG-IR-GW-32", {"has_disciplinary_record": True}, 400, "REJECTED", "DISCIPLINARY_VIOLATION"),
    ])
    def test_irtmp_gateway_control_flow(self, tc_id, override, exp_code, exp_status, exp_error):
        payload = make_irtmp(**override)
        res = validate_all_irtmp(payload)
        assert res["code"] == exp_code, f"{tc_id}: HTTP code mismatch"
        assert res["status"] == exp_status, f"{tc_id}: Status mismatch"
        if exp_error:
            assert res["error"] == exp_error, f"{tc_id}: Error code mismatch"

    # --------------------------------------------------------------------------
    # 2. IRTMP Quyết định D1 -> D5: Branch Coverage cho biểu thức điều kiện phức hợp
    # --------------------------------------------------------------------------
    @pytest.mark.parametrize("tc_id, dec_id, override, exp_code, exp_status", [
        # D1: Biểu thức compound 7 điều kiện atomic
        ("TC-CFG-IR-D1-TRUE", "D1", {}, 200, "APPLICATION_ACCEPTED"),
        ("TC-CFG-IR-D1-F1", "D1", {"seniority_days": 179}, 400, "REJECTED"),
        ("TC-CFG-IR-D1-F2", "D1", {"active_applications": 4}, 400, "REJECTED"),
        ("TC-CFG-IR-D1-F3", "D1", {"cover_letter_length": 5}, 400, "REJECTED"),
        ("TC-CFG-IR-D1-F4", "D1", {"cv_file_size_mb": 6.0}, 400, "REJECTED"),
        ("TC-CFG-IR-D1-F5", "D1", {"candidate_email": "user@other.com"}, 400, "REJECTED"),
        ("TC-CFG-IR-D1-F6", "D1", {"cv_file_extension": ".exe"}, 400, "REJECTED"),
        ("TC-CFG-IR-D1-F7", "D1", {"has_disciplinary_record": True}, 400, "REJECTED"),

        # D2: Biểu thức compound (1 <= p4 <= 5 and 1 <= p10 <= 100)
        ("TC-CFG-IR-D2-TRUE", "D2", {"interview_rating": 4, "match_score_percent": 80}, 200, "INTERVIEW_EVALUATED"),
        ("TC-CFG-IR-D2-F1", "D2", {"interview_rating": 0}, 400, "REJECTED"),
        ("TC-CFG-IR-D2-F2", "D2", {"match_score_percent": 105}, 400, "REJECTED"),

        # D3: Biểu thức đơn (1 <= p11 <= 100)
        ("TC-CFG-IR-D3-TRUE", "D3", {"kanban_cards_limit": 50}, 200, "KANBAN_STAGE_UPDATED"),
        ("TC-CFG-IR-D3-FALSE", "D3", {"kanban_cards_limit": 0}, 400, "REJECTED"),

        # D4: Biểu thức compound (1 <= p5 <= 90 and 1 <= p9 <= 20)
        ("TC-CFG-IR-D4-TRUE", "D4", {"job_deadline_days": 30, "skills_count": 5}, 200, "JOB_POSTED_SUCCESS"),
        ("TC-CFG-IR-D4-F1", "D4", {"job_deadline_days": 0}, 400, "REJECTED"),
        ("TC-CFG-IR-D4-F2", "D4", {"skills_count": 25}, 400, "REJECTED"),

        # D5: Biểu thức compound (1 <= p6 <= 72 and 1 <= p8 <= 3 and 0.1 <= p12 <= 2.0)
        ("TC-CFG-IR-D5-TRUE", "D5", {"closing_soon_hours": 24, "hr_sla_days": 2, "notification_latency_seconds": 0.5}, 200, "ALERT_TRIGGERED"),
        ("TC-CFG-IR-D5-F1", "D5", {"closing_soon_hours": 0}, 400, "REJECTED"),
        ("TC-CFG-IR-D5-F2", "D5", {"hr_sla_days": 5}, 400, "REJECTED"),
        ("TC-CFG-IR-D5-F3", "D5", {"notification_latency_seconds": 2.5}, 400, "REJECTED"),
    ])
    def test_irtmp_decisions_branch_coverage(self, tc_id, dec_id, override, exp_code, exp_status):
        payload = make_irtmp(**override)
        res = process_irtmp_decision(dec_id, payload)
        assert res["code"] == exp_code, f"{tc_id}: HTTP code mismatch"
        assert res["status"] == exp_status, f"{tc_id}: Status mismatch"

    # --------------------------------------------------------------------------
    # 3. SOPRCS Gateway - Statement & Branch Coverage (Validate-All)
    # --------------------------------------------------------------------------
    @pytest.mark.parametrize("tc_id, override, exp_code, exp_status, exp_error", [
        # Nhánh True toàn phần (if not errors -> APPROVED_ALL)
        ("TC-CFG-SO-GW-00", {}, 200, "APPROVED_ALL", None),

        # 33 Nhánh False kích hoạt từng câu lệnh errors.append(...)
        ("TC-CFG-SO-GW-01", {"amount": 999}, 400, "REJECTED", "INVALID_AMOUNT"),
        ("TC-CFG-SO-GW-02", {"amount": 1000001}, 400, "REJECTED", "EXCEEDS_OFFLINE_LIMIT"),
        ("TC-CFG-SO-GW-03", {"cart_quantity": 0}, 400, "REJECTED", "EMPTY_CART"),
        ("TC-CFG-SO-GW-04", {"cart_quantity": 51}, 400, "REJECTED", "EXCEEDS_CART_LIMIT"),
        ("TC-CFG-SO-GW-05", {"loan_amount": 999}, 400, "REJECTED", "INVALID_AMOUNT"),
        ("TC-CFG-SO-GW-06", {"loan_amount": 500001}, 400, "REJECTED", "EXCEEDS_PAY_LATER_LIMIT"),
        ("TC-CFG-SO-GW-07", {"credit_score": 649}, 400, "REJECTED", "CREDIT_SCORE_TOO_LOW"),
        ("TC-CFG-SO-GW-08", {"credit_score": 851}, 400, "REJECTED", "EXCEEDS_CREDIT_SCALE"),
        ("TC-CFG-SO-GW-09", {"qr_totp_period_sec": 0}, 400, "REJECTED", "INVALID_QR_PERIOD"),
        ("TC-CFG-SO-GW-10", {"qr_totp_period_sec": 61}, 400, "REJECTED", "EXCEEDS_QR_PERIOD"),
        ("TC-CFG-SO-GW-11", {"time_drift_sec": -121}, 400, "REJECTED", "TIME_DRIFT_TOO_LOW"),
        ("TC-CFG-SO-GW-12", {"time_drift_sec": 121}, 400, "REJECTED", "TIME_DRIFT_EXCEEDED"),
        ("TC-CFG-SO-GW-13", {"nonce_ttl_sec": 0}, 400, "REJECTED", "INVALID_NONCE_TTL"),
        ("TC-CFG-SO-GW-14", {"nonce_ttl_sec": 181}, 400, "REJECTED", "EXCEEDS_NONCE_TTL"),
        ("TC-CFG-SO-GW-15", {"token_spending_limit": 999}, 400, "REJECTED", "INVALID_TOKEN_LIMIT"),
        ("TC-CFG-SO-GW-16", {"token_spending_limit": 3000001}, 400, "REJECTED", "EXCEEDS_TOKEN_LIMIT"),
        ("TC-CFG-SO-GW-17", {"parked_order_timeout_min": 0}, 400, "REJECTED", "INVALID_PARKED_TIMEOUT"),
        ("TC-CFG-SO-GW-18", {"parked_order_timeout_min": 61}, 400, "REJECTED", "EXCEEDS_PARKED_TIMEOUT"),
        ("TC-CFG-SO-GW-19", {"pay_later_grace_period_hr": 0}, 400, "REJECTED", "INVALID_GRACE_PERIOD"),
        ("TC-CFG-SO-GW-20", {"pay_later_grace_period_hr": 25}, 400, "REJECTED", "EXCEEDS_GRACE_PERIOD"),
        ("TC-CFG-SO-GW-21", {"wifi_session_duration_min": 0}, 400, "REJECTED", "INVALID_WIFI_DURATION"),
        ("TC-CFG-SO-GW-22", {"wifi_session_duration_min": 16}, 400, "REJECTED", "EXCEEDS_WIFI_DURATION"),
        ("TC-CFG-SO-GW-23", {"prefetched_tokens_count": 0}, 400, "REJECTED", "INVALID_PREFETCH_COUNT"),
        ("TC-CFG-SO-GW-24", {"prefetched_tokens_count": 6}, 400, "REJECTED", "EXCEEDS_PREFETCH_COUNT"),
        ("TC-CFG-SO-GW-25", {"wifi_qos_bandwidth_mbps": 0.05}, 400, "REJECTED", "INVALID_WIFI_BANDWIDTH"),
        ("TC-CFG-SO-GW-26", {"wifi_qos_bandwidth_mbps": 2.5}, 400, "REJECTED", "EXCEEDS_WIFI_BANDWIDTH"),
        ("TC-CFG-SO-GW-27", {"customer_phone": ""}, 400, "REJECTED", "INVALID_PHONE_EMPTY"),
        ("TC-CFG-SO-GW-28", {"customer_phone": "091234567a"}, 400, "REJECTED", "INVALID_PHONE_FORMAT"),
        ("TC-CFG-SO-GW-29", {"customer_phone": "091234567"}, 400, "REJECTED", "INVALID_PHONE_LENGTH"),
        ("TC-CFG-SO-GW-30", {"customer_phone": "09123456789"}, 400, "REJECTED", "INVALID_PHONE_LENGTH"),
        ("TC-CFG-SO-GW-31", {"currency": ""}, 400, "REJECTED", "INVALID_CURRENCY_EMPTY"),
        ("TC-CFG-SO-GW-32", {"currency": "USD"}, 400, "REJECTED", "UNSUPPORTED_CURRENCY"),
        ("TC-CFG-SO-GW-33", {"is_ekyc_verified": False}, 400, "REJECTED", "EKYC_REQUIRED"),
    ])
    def test_soprcs_gateway_control_flow(self, tc_id, override, exp_code, exp_status, exp_error):
        payload = make_soprcs(**override)
        res = validate_all_soprcs(payload)
        assert res["code"] == exp_code, f"{tc_id}: HTTP code mismatch"
        assert res["status"] == exp_status, f"{tc_id}: Status mismatch"
        if exp_error:
            assert res["error"] == exp_error, f"{tc_id}: Error code mismatch"

    # --------------------------------------------------------------------------
    # 4. SOPRCS Quyết định D1 -> D5: Branch Coverage cho biểu thức điều kiện phức hợp
    # --------------------------------------------------------------------------
    @pytest.mark.parametrize("tc_id, dec_id, override, exp_code, exp_status", [
        # D1: Biểu thức compound 8 điều kiện atomic
        ("TC-CFG-SO-D1-TRUE", "D1", {}, 200, "APPROVED_OFFLINE_PAYMENT"),
        ("TC-CFG-SO-D1-F1", "D1", {"amount": 500}, 400, "REJECTED"),
        ("TC-CFG-SO-D1-F2", "D1", {"cart_quantity": 60}, 400, "REJECTED"),
        ("TC-CFG-SO-D1-F3", "D1", {"qr_totp_period_sec": 70}, 400, "REJECTED"),
        ("TC-CFG-SO-D1-F4", "D1", {"time_drift_sec": -150}, 400, "REJECTED"),
        ("TC-CFG-SO-D1-F5", "D1", {"nonce_ttl_sec": 200}, 400, "REJECTED"),
        ("TC-CFG-SO-D1-F6", "D1", {"customer_phone": "09123"}, 400, "REJECTED"),
        ("TC-CFG-SO-D1-F7", "D1", {"currency": "EUR"}, 400, "REJECTED"),

        # D2: Biểu thức compound (1 <= p2 <= 50 and 1 <= p9 <= 60)
        ("TC-CFG-SO-D2-TRUE", "D2", {"cart_quantity": 20, "parked_order_timeout_min": 30}, 200, "CART_PARKED_SUCCESS"),
        ("TC-CFG-SO-D2-F1", "D2", {"cart_quantity": 0}, 400, "REJECTED"),
        ("TC-CFG-SO-D2-F2", "D2", {"parked_order_timeout_min": 70}, 400, "REJECTED"),

        # D3: Biểu thức compound (1000 <= p3 <= 500000 and 650 <= p4 <= 850 and 1 <= p10 <= 24 and p16)
        ("TC-CFG-SO-D3-TRUE", "D3", {"loan_amount": 200000, "credit_score": 750, "pay_later_grace_period_hr": 12, "is_ekyc_verified": True}, 200, "PAY_LATER_APPROVED"),
        ("TC-CFG-SO-D3-F1", "D3", {"loan_amount": 100}, 400, "REJECTED"),
        ("TC-CFG-SO-D3-F2", "D3", {"credit_score": 500}, 400, "REJECTED"),
        ("TC-CFG-SO-D3-F3", "D3", {"pay_later_grace_period_hr": 30}, 400, "REJECTED"),
        ("TC-CFG-SO-D3-F4", "D3", {"is_ekyc_verified": False}, 400, "REJECTED"),

        # D4: Biểu thức compound (1 <= p12 <= 5 and 1000 <= p8 <= 3000000)
        ("TC-CFG-SO-D4-TRUE", "D4", {"prefetched_tokens_count": 3, "token_spending_limit": 1500000}, 200, "TOKEN_SYNC_SUCCESS"),
        ("TC-CFG-SO-D4-F1", "D4", {"prefetched_tokens_count": 0}, 400, "REJECTED"),
        ("TC-CFG-SO-D4-F2", "D4", {"token_spending_limit": 5000000}, 400, "REJECTED"),

        # D5: Biểu thức compound (1 <= p11 <= 15 and 0.1 <= p13 <= 2.0)
        ("TC-CFG-SO-D5-TRUE", "D5", {"wifi_session_duration_min": 10, "wifi_qos_bandwidth_mbps": 1.5}, 200, "WIFI_SESSION_GRANTED"),
        ("TC-CFG-SO-D5-F1", "D5", {"wifi_session_duration_min": 0}, 400, "REJECTED"),
        ("TC-CFG-SO-D5-F2", "D5", {"wifi_qos_bandwidth_mbps": 3.0}, 400, "REJECTED"),
    ])
    def test_soprcs_decisions_branch_coverage(self, tc_id, dec_id, override, exp_code, exp_status):
        payload = make_soprcs(**override)
        res = process_soprcs_decision(dec_id, payload)
        assert res["code"] == exp_code, f"{tc_id}: HTTP code mismatch"
        assert res["status"] == exp_status, f"{tc_id}: Status mismatch"


# ==============================================================================
# CLASS 2: KIỂM THỬ LUỒNG DỮ LIỆU ALL-USES (DATA FLOW TESTING)
# Bao phủ tất cả các cặp Def-Use không bị tái định nghĩa (Definition-Clear DU-paths)
# ==============================================================================

class Test_AI_DataFlow_AllUses:
    """
    Kiểm thử luồng dữ liệu theo tiêu chuẩn All-Uses (Data Flow Testing):
    - Phân tích chu trình sống của biến: Def(x) -> Use(x) (p-use vị từ & c-use tính toán).
    - Đảm bảo thực thi tất cả các đường đi Def-Clear từ điểm gán giá trị đến mọi điểm sử dụng.
    """

    # --------------------------------------------------------------------------
    # 1. DU-Chains của biến errors và biến đầu vào IRTMP (32 Ca kiểm thử DU)
    # --------------------------------------------------------------------------
    @pytest.mark.parametrize("du_id, var_name, def_line, use_type, override, exp_status, exp_error", [
        # Biến errors: Def(errors=[]) -> p-use(if not errors -> True) -> c-use(return APPROVED_ALL)
        ("DU-IR-ERR-01", "errors", "def:errors=[]", "p-use(empty)", {}, "APPROVED_ALL", None),
        # Biến errors: Def(errors=[]) -> c-use(errors.append) -> p-use(if not errors -> False) -> c-use(errors[0][1])
        ("DU-IR-ERR-02", "errors", "def:errors=[]", "c-use(append+return)", {"seniority_days": 100}, "REJECTED", "SENIORITY_REQUIREMENT_NOT_MET"),

        # p1: Def -> p-use(p1 < 180 True) -> c-use(str formatting)
        ("DU-IR-P1-01", "p1", "def:p1", "p-use(p1<180)+c-use", {"seniority_days": 150}, "REJECTED", "SENIORITY_REQUIREMENT_NOT_MET"),
        # p1: Def -> p-use(p1 > 18000 True) -> c-use(str formatting)
        ("DU-IR-P1-02", "p1", "def:p1", "p-use(p1>18000)+c-use", {"seniority_days": 20000}, "REJECTED", "RETIREMENT_AGE_EXCEEDED"),

        # p2: Def -> p-use(p2 < 1) / p-use(p2 > 3)
        ("DU-IR-P2-01", "p2", "def:p2", "p-use(p2<1)+c-use", {"active_applications": -1}, "REJECTED", "INVALID_APP_COUNT"),
        ("DU-IR-P2-02", "p2", "def:p2", "p-use(p2>3)+c-use", {"active_applications": 5}, "REJECTED", "MAX_ACTIVE_APPLICATIONS_REACHED"),

        # p3: Def -> p-use(p3 < 10) / p-use(p3 > 1000)
        ("DU-IR-P3-01", "p3", "def:p3", "p-use(p3<10)+c-use", {"cover_letter_length": 8}, "REJECTED", "COVER_LETTER_TOO_SHORT"),
        ("DU-IR-P3-02", "p3", "def:p3", "p-use(p3>1000)+c-use", {"cover_letter_length": 1200}, "REJECTED", "COVER_LETTER_TOO_LONG"),

        # p4: Def -> p-use(p4 < 1) / p-use(p4 > 5)
        ("DU-IR-P4-01", "p4", "def:p4", "p-use(p4<1)+c-use", {"interview_rating": -1}, "REJECTED", "INVALID_RATING"),
        ("DU-IR-P4-02", "p4", "def:p4", "p-use(p4>5)+c-use", {"interview_rating": 8}, "REJECTED", "RATING_OUT_OF_SCALE"),

        # p5: Def -> p-use(p5 < 1) / p-use(p5 > 90)
        ("DU-IR-P5-01", "p5", "def:p5", "p-use(p5<1)+c-use", {"job_deadline_days": -5}, "REJECTED", "INVALID_DEADLINE"),
        ("DU-IR-P5-02", "p5", "def:p5", "p-use(p5>90)+c-use", {"job_deadline_days": 120}, "REJECTED", "EXCEEDS_DEADLINE"),

        # p6: Def -> p-use(p6 < 1) / p-use(p6 > 72)
        ("DU-IR-P6-01", "p6", "def:p6", "p-use(p6<1)+c-use", {"closing_soon_hours": -2}, "REJECTED", "INVALID_CLOSING_SOON_HOURS"),
        ("DU-IR-P6-02", "p6", "def:p6", "p-use(p6>72)+c-use", {"closing_soon_hours": 100}, "REJECTED", "EXCEEDS_CLOSING_SOON_HOURS"),

        # p7: Def -> p-use(p7 < 0.001) / p-use(p7 > 5.0)
        ("DU-IR-P7-01", "p7", "def:p7", "p-use(p7<0.001)+c-use", {"cv_file_size_mb": -0.5}, "REJECTED", "INVALID_CV_FILE_SIZE"),
        ("DU-IR-P7-02", "p7", "def:p7", "p-use(p7>5.0)+c-use", {"cv_file_size_mb": 8.0}, "REJECTED", "EXCEEDS_CV_FILE_SIZE"),

        # p8: Def -> p-use(p8 < 1) / p-use(p8 > 3)
        ("DU-IR-P8-01", "p8", "def:p8", "p-use(p8<1)+c-use", {"hr_sla_days": -1}, "REJECTED", "INVALID_HR_SLA"),
        ("DU-IR-P8-02", "p8", "def:p8", "p-use(p8>3)+c-use", {"hr_sla_days": 6}, "REJECTED", "EXCEEDS_HR_SLA"),

        # p9: Def -> p-use(p9 < 1) / p-use(p9 > 20)
        ("DU-IR-P9-01", "p9", "def:p9", "p-use(p9<1)+c-use", {"skills_count": -3}, "REJECTED", "INVALID_SKILLS_COUNT"),
        ("DU-IR-P9-02", "p9", "def:p9", "p-use(p9>20)+c-use", {"skills_count": 30}, "REJECTED", "EXCEEDS_SKILLS_COUNT"),

        # p10: Def -> p-use(p10 < 1) / p-use(p10 > 100)
        ("DU-IR-P10-01", "p10", "def:p10", "p-use(p10<1)+c-use", {"match_score_percent": -10}, "REJECTED", "INVALID_MATCH_SCORE"),
        ("DU-IR-P10-02", "p10", "def:p10", "p-use(p10>100)+c-use", {"match_score_percent": 150}, "REJECTED", "EXCEEDS_MATCH_SCORE"),

        # p11: Def -> p-use(p11 < 1) / p-use(p11 > 100)
        ("DU-IR-P11-01", "p11", "def:p11", "p-use(p11<1)+c-use", {"kanban_cards_limit": -2}, "REJECTED", "INVALID_KANBAN_LIMIT"),
        ("DU-IR-P11-02", "p11", "def:p11", "p-use(p11>100)+c-use", {"kanban_cards_limit": 120}, "REJECTED", "EXCEEDS_KANBAN_LIMIT"),

        # p12: Def -> p-use(p12 < 0.1) / p-use(p12 > 2.0)
        ("DU-IR-P12-01", "p12", "def:p12", "p-use(p12<0.1)+c-use", {"notification_latency_seconds": 0.05}, "REJECTED", "INVALID_NOTIFICATION_LATENCY"),
        ("DU-IR-P12-02", "p12", "def:p12", "p-use(p12>2.0)+c-use", {"notification_latency_seconds": 3.5}, "REJECTED", "EXCEEDS_NOTIFICATION_LATENCY"),

        # p13: Def -> p-use(not p13) / p-use(len > 255) / p-use(@ not in) / p-use(not endswith)
        ("DU-IR-P13-01", "p13", "def:p13", "p-use(empty)", {"candidate_email": ""}, "REJECTED", "INVALID_EMAIL_EMPTY"),
        ("DU-IR-P13-02", "p13", "def:p13", "p-use(len>255)", {"candidate_email": "x" * 256}, "REJECTED", "EMAIL_TOO_LONG"),
        ("DU-IR-P13-03", "p13", "def:p13", "p-use(no_at)", {"candidate_email": "bademailformat"}, "REJECTED", "INVALID_EMAIL_FORMAT"),
        ("DU-IR-P13-04", "p13", "def:p13", "p-use(not_domain)", {"candidate_email": "user@external.org"}, "REJECTED", "INVALID_EMAIL_DOMAIN"),

        # p14: Def -> p-use(not p14) / p-use(not in allowed)
        ("DU-IR-P14-01", "p14", "def:p14", "p-use(empty)", {"cv_file_extension": ""}, "REJECTED", "INVALID_EXTENSION_EMPTY"),
        ("DU-IR-P14-02", "p14", "def:p14", "p-use(disallowed)", {"cv_file_extension": ".zip"}, "REJECTED", "INVALID_FILE_EXTENSION"),

        # p15: Def -> p-use(if p15)
        ("DU-IR-P15-01", "p15", "def:p15", "p-use(flag_true)", {"has_disciplinary_record": True}, "REJECTED", "DISCIPLINARY_VIOLATION"),
    ])
    def test_irtmp_dataflow_all_uses(self, du_id, var_name, def_line, use_type, override, exp_status, exp_error):
        payload = make_irtmp(**override)
        res = validate_all_irtmp(payload)
        assert res["status"] == exp_status, f"{du_id}: Status mismatch for variable {var_name}"
        if exp_error:
            assert res["error"] == exp_error, f"{du_id}: Error code mismatch for {var_name}"

    # --------------------------------------------------------------------------
    # 2. DU-Chains của biến errors và biến đầu vào SOPRCS (32 Ca kiểm thử DU)
    # --------------------------------------------------------------------------
    @pytest.mark.parametrize("du_id, var_name, def_line, use_type, override, exp_status, exp_error", [
        # Biến errors: Def(errors=[]) -> p-use(if not errors -> True) -> c-use(return APPROVED_ALL)
        ("DU-SO-ERR-01", "errors", "def:errors=[]", "p-use(empty)", {}, "APPROVED_ALL", None),
        # Biến errors: Def(errors=[]) -> c-use(errors.append) -> p-use(if not errors -> False) -> c-use(errors[0][1])
        ("DU-SO-ERR-02", "errors", "def:errors=[]", "c-use(append+return)", {"amount": 500}, "REJECTED", "INVALID_AMOUNT"),

        # p1: Def -> p-use(p1 < 1000) / p-use(p1 > 1000000)
        ("DU-SO-P1-01", "p1", "def:p1", "p-use(p1<1000)+c-use", {"amount": 800}, "REJECTED", "INVALID_AMOUNT"),
        ("DU-SO-P1-02", "p1", "def:p1", "p-use(p1>1000000)+c-use", {"amount": 2000000}, "REJECTED", "EXCEEDS_OFFLINE_LIMIT"),

        # p2: Def -> p-use(p2 < 1) / p-use(p2 > 50)
        ("DU-SO-P2-01", "p2", "def:p2", "p-use(p2<1)+c-use", {"cart_quantity": -1}, "REJECTED", "EMPTY_CART"),
        ("DU-SO-P2-02", "p2", "def:p2", "p-use(p2>50)+c-use", {"cart_quantity": 80}, "REJECTED", "EXCEEDS_CART_LIMIT"),

        # p3: Def -> p-use(p3 < 1000) / p-use(p3 > 500000)
        ("DU-SO-P3-01", "p3", "def:p3", "p-use(p3<1000)+c-use", {"loan_amount": 500}, "REJECTED", "INVALID_AMOUNT"),
        ("DU-SO-P3-02", "p3", "def:p3", "p-use(p3>500000)+c-use", {"loan_amount": 800000}, "REJECTED", "EXCEEDS_PAY_LATER_LIMIT"),

        # p4: Def -> p-use(p4 < 650) / p-use(p4 > 850)
        ("DU-SO-P4-01", "p4", "def:p4", "p-use(p4<650)+c-use", {"credit_score": 600}, "REJECTED", "CREDIT_SCORE_TOO_LOW"),
        ("DU-SO-P4-02", "p4", "def:p4", "p-use(p4>850)+c-use", {"credit_score": 900}, "REJECTED", "EXCEEDS_CREDIT_SCALE"),

        # p5: Def -> p-use(p5 < 1) / p-use(p5 > 60)
        ("DU-SO-P5-01", "p5", "def:p5", "p-use(p5<1)+c-use", {"qr_totp_period_sec": -2}, "REJECTED", "INVALID_QR_PERIOD"),
        ("DU-SO-P5-02", "p5", "def:p5", "p-use(p5>60)+c-use", {"qr_totp_period_sec": 90}, "REJECTED", "EXCEEDS_QR_PERIOD"),

        # p6: Def -> p-use(p6 < -120) / p-use(p6 > 120)
        ("DU-SO-P6-01", "p6", "def:p6", "p-use(p6<-120)+c-use", {"time_drift_sec": -200}, "REJECTED", "TIME_DRIFT_TOO_LOW"),
        ("DU-SO-P6-02", "p6", "def:p6", "p-use(p6>120)+c-use", {"time_drift_sec": 200}, "REJECTED", "TIME_DRIFT_EXCEEDED"),

        # p7: Def -> p-use(p7 < 1) / p-use(p7 > 180)
        ("DU-SO-P7-01", "p7", "def:p7", "p-use(p7<1)+c-use", {"nonce_ttl_sec": -5}, "REJECTED", "INVALID_NONCE_TTL"),
        ("DU-SO-P7-02", "p7", "def:p7", "p-use(p7>180)+c-use", {"nonce_ttl_sec": 250}, "REJECTED", "EXCEEDS_NONCE_TTL"),

        # p8: Def -> p-use(p8 < 1000) / p-use(p8 > 3000000)
        ("DU-SO-P8-01", "p8", "def:p8", "p-use(p8<1000)+c-use", {"token_spending_limit": 500}, "REJECTED", "INVALID_TOKEN_LIMIT"),
        ("DU-SO-P8-02", "p8", "def:p8", "p-use(p8>3000000)+c-use", {"token_spending_limit": 4000000}, "REJECTED", "EXCEEDS_TOKEN_LIMIT"),

        # p9: Def -> p-use(p9 < 1) / p-use(p9 > 60)
        ("DU-SO-P9-01", "p9", "def:p9", "p-use(p9<1)+c-use", {"parked_order_timeout_min": -1}, "REJECTED", "INVALID_PARKED_TIMEOUT"),
        ("DU-SO-P9-02", "p9", "def:p9", "p-use(p9>60)+c-use", {"parked_order_timeout_min": 80}, "REJECTED", "EXCEEDS_PARKED_TIMEOUT"),

        # p10: Def -> p-use(p10 < 1) / p-use(p10 > 24)
        ("DU-SO-P10-01", "p10", "def:p10", "p-use(p10<1)+c-use", {"pay_later_grace_period_hr": -2}, "REJECTED", "INVALID_GRACE_PERIOD"),
        ("DU-SO-P10-02", "p10", "def:p10", "p-use(p10>24)+c-use", {"pay_later_grace_period_hr": 48}, "REJECTED", "EXCEEDS_GRACE_PERIOD"),

        # p11: Def -> p-use(p11 < 1) / p-use(p11 > 15)
        ("DU-SO-P11-01", "p11", "def:p11", "p-use(p11<1)+c-use", {"wifi_session_duration_min": -1}, "REJECTED", "INVALID_WIFI_DURATION"),
        ("DU-SO-P11-02", "p11", "def:p11", "p-use(p11>15)+c-use", {"wifi_session_duration_min": 25}, "REJECTED", "EXCEEDS_WIFI_DURATION"),

        # p12: Def -> p-use(p12 < 1) / p-use(p12 > 5)
        ("DU-SO-P12-01", "p12", "def:p12", "p-use(p12<1)+c-use", {"prefetched_tokens_count": -1}, "REJECTED", "INVALID_PREFETCH_COUNT"),
        ("DU-SO-P12-02", "p12", "def:p12", "p-use(p12>5)+c-use", {"prefetched_tokens_count": 8}, "REJECTED", "EXCEEDS_PREFETCH_COUNT"),

        # p13: Def -> p-use(p13 < 0.1) / p-use(p13 > 2.0)
        ("DU-SO-P13-01", "p13", "def:p13", "p-use(p13<0.1)+c-use", {"wifi_qos_bandwidth_mbps": 0.02}, "REJECTED", "INVALID_WIFI_BANDWIDTH"),
        ("DU-SO-P13-02", "p13", "def:p13", "p-use(p13>2.0)+c-use", {"wifi_qos_bandwidth_mbps": 5.0}, "REJECTED", "EXCEEDS_WIFI_BANDWIDTH"),

        # p14: Def -> p-use(not p14) / p-use(not isdigit) / p-use(len != 10)
        ("DU-SO-P14-01", "p14", "def:p14", "p-use(empty)", {"customer_phone": ""}, "REJECTED", "INVALID_PHONE_EMPTY"),
        ("DU-SO-P14-02", "p14", "def:p14", "p-use(not_digit)", {"customer_phone": "09876abcde"}, "REJECTED", "INVALID_PHONE_FORMAT"),
        ("DU-SO-P14-03", "p14", "def:p14", "p-use(length!=10)", {"customer_phone": "09876"}, "REJECTED", "INVALID_PHONE_LENGTH"),

        # p15: Def -> p-use(not p15) / p-use(p15 != 'VND')
        ("DU-SO-P15-01", "p15", "def:p15", "p-use(empty)", {"currency": ""}, "REJECTED", "INVALID_CURRENCY_EMPTY"),
        ("DU-SO-P15-02", "p15", "def:p15", "p-use(not_vnd)", {"currency": "JPY"}, "REJECTED", "UNSUPPORTED_CURRENCY"),

        # p16: Def -> p-use(not p16)
        ("DU-SO-P16-01", "p16", "def:p16", "p-use(not_ekyc)", {"is_ekyc_verified": False}, "REJECTED", "EKYC_REQUIRED"),
    ])
    def test_soprcs_dataflow_all_uses(self, du_id, var_name, def_line, use_type, override, exp_status, exp_error):
        payload = make_soprcs(**override)
        res = validate_all_soprcs(payload)
        assert res["status"] == exp_status, f"{du_id}: Status mismatch for variable {var_name}"
        if exp_error:
            assert res["error"] == exp_error, f"{du_id}: Error code mismatch for {var_name}"

