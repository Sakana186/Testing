"""
BLACK-BOX TEST SUITE GENERATED FROM BUSINESS SPECIFICATIONS
File: test_ai_dacta.py
Location: F:\\main\\new_research\\test_ai_dacta.py

Techniques covered:
1. Equivalence Partitioning (Valid & Invalid classes) -> Test_AI_EquivalencePartitioning
2. Boundary Value Analysis (3-value technique: min-, min, min+, max-, max, max+) -> Test_AI_BoundaryValueAnalysis
3. Decision Table Testing (Business logic rules & actions) -> Test_AI_DecisionTable

Systems under test:
- IRTMP: Internal Recruitment & Talent Mobility Platform (15 Parameters)
- SOPRCS: Supermarket Offline Payment Robustness & Checkout System (16 Parameters)
"""

import sys
from pathlib import Path
import pytest

# Ensure local business_logic module is importable
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from business_logic import (
    IRTMP_NOMINAL_PAYLOAD,
    SOPRCS_NOMINAL_PAYLOAD,
    validate_irtmp_parameters,
    process_irtmp_decision,
    validate_soprcs_parameters,
    process_soprcs_decision,
)


# ==============================================================================
# CLASS 1: EQUIVALENCE PARTITIONING (EP / ECP)
# ==============================================================================

class Test_AI_EquivalencePartitioning:
    """
    Equivalence Partitioning Black-Box Test Suite.
    Covers 100% of Valid and Invalid equivalence classes specified in SRS.
    """

    # --------------------------------------------------------------------------
    # 1.1 IRTMP Equivalence Partitioning Tests
    # --------------------------------------------------------------------------

    # 6 Valid Equivalence Flows
    IRTMP_VALID_CASES = [
        ("TC-ECP-IRTMP-VAL-01", "D1", {}, 200, "APPLICATION_ACCEPTED"),
        ("TC-ECP-IRTMP-VAL-02", "D2", {"interview_rating": 4, "match_score_percent": 75}, 200, "INTERVIEW_EVALUATED"),
        ("TC-ECP-IRTMP-VAL-03", "D3", {"kanban_cards_limit": 55}, 200, "KANBAN_STAGE_UPDATED"),
        ("TC-ECP-IRTMP-VAL-04", "D4", {"job_deadline_days": 45, "skills_count": 12}, 200, "JOB_POSTED_SUCCESS"),
        ("TC-ECP-IRTMP-VAL-05", "D5", {"closing_soon_hours": 36, "hr_sla_days": 3, "notification_latency_seconds": 1.2}, 200, "ALERT_TRIGGERED"),
        ("TC-ECP-IRTMP-VAL-06", "D6", {}, 200, "APPROVED_ALL"),
    ]

    @pytest.mark.parametrize("tc_id, flow, overrides, expected_status, expected_code", IRTMP_VALID_CASES)
    def test_irtmp_equivalence_partitioning_valid(self, tc_id, flow, overrides, expected_status, expected_code):
        payload = IRTMP_NOMINAL_PAYLOAD.copy()
        payload.update(overrides)
        res = process_irtmp_decision(flow, payload)
        assert res["status"] == expected_status, f"[{tc_id}] Expected {expected_status}, got {res['status']}"
        assert res["code"] == expected_code, f"[{tc_id}] Expected code {expected_code}, got {res['code']}"
        assert res["success"] is True, f"[{tc_id}] Expected success=True"

    # 34 Invalid Equivalence Classes
    IRTMP_INVALID_CASES = [
        ("TC-ECP-IRTMP-INV-01", "seniority_days", 85, 400, "SENIORITY_REQUIREMENT_NOT_MET"),
        ("TC-ECP-IRTMP-INV-02", "seniority_days", 24500, 400, "RETIREMENT_AGE_EXCEEDED"),
        ("TC-ECP-IRTMP-INV-03", "active_applications", 0, 400, "INVALID_APP_COUNT"),
        ("TC-ECP-IRTMP-INV-04", "active_applications", 6, 400, "MAX_ACTIVE_APPLICATIONS_REACHED"),
        ("TC-ECP-IRTMP-INV-05", "cover_letter_length", 4, 400, "COVER_LETTER_TOO_SHORT"),
        ("TC-ECP-IRTMP-INV-06", "cover_letter_length", 1450, 400, "COVER_LETTER_TOO_LONG"),
        ("TC-ECP-IRTMP-INV-07", "interview_rating", 0, 400, "INVALID_RATING"),
        ("TC-ECP-IRTMP-INV-08", "interview_rating", 7, 400, "RATING_OUT_OF_SCALE"),
        ("TC-ECP-IRTMP-INV-09", "job_deadline_days", 0, 400, "INVALID_DEADLINE"),
        ("TC-ECP-IRTMP-INV-10", "job_deadline_days", 135, 400, "EXCEEDS_DEADLINE"),
        ("TC-ECP-IRTMP-INV-11", "closing_soon_hours", 0, 400, "INVALID_CLOSING_SOON_HOURS"),
        ("TC-ECP-IRTMP-INV-12", "closing_soon_hours", 96, 400, "EXCEEDS_CLOSING_SOON_HOURS"),
        ("TC-ECP-IRTMP-INV-13", "cv_file_size_mb", 0.0, 400, "INVALID_CV_FILE_SIZE"),
        ("TC-ECP-IRTMP-INV-14", "cv_file_size_mb", 7.5, 400, "EXCEEDS_CV_FILE_SIZE"),
        ("TC-ECP-IRTMP-INV-15", "hr_sla_days", 0, 400, "INVALID_HR_SLA"),
        ("TC-ECP-IRTMP-INV-16", "hr_sla_days", 6, 400, "EXCEEDS_HR_SLA"),
        ("TC-ECP-IRTMP-INV-17", "skills_count", 0, 400, "INVALID_SKILLS_COUNT"),
        ("TC-ECP-IRTMP-INV-18", "skills_count", 28, 400, "EXCEEDS_SKILLS_COUNT"),
        ("TC-ECP-IRTMP-INV-19", "match_score_percent", 0, 400, "INVALID_MATCH_SCORE"),
        ("TC-ECP-IRTMP-INV-20", "match_score_percent", 145, 400, "EXCEEDS_MATCH_SCORE"),
        ("TC-ECP-IRTMP-INV-21", "kanban_cards_limit", 0, 400, "INVALID_KANBAN_LIMIT"),
        ("TC-ECP-IRTMP-INV-22", "kanban_cards_limit", 160, 400, "EXCEEDS_KANBAN_LIMIT"),
        ("TC-ECP-IRTMP-INV-23", "notification_latency_seconds", 0.0, 400, "INVALID_NOTIFICATION_LATENCY"),
        ("TC-ECP-IRTMP-INV-24", "notification_latency_seconds", 3.8, 400, "EXCEEDS_NOTIFICATION_LATENCY"),
        ("TC-ECP-IRTMP-INV-25", "candidate_email", "", 400, "INVALID_EMAIL_EMPTY"),
        ("TC-ECP-IRTMP-INV-26", "candidate_email", "employee@", 400, "INVALID_EMAIL_FORMAT"),
        ("TC-ECP-IRTMP-INV-27", "candidate_email", "employee@gmail.com", 400, "INVALID_EMAIL_DOMAIN"),
        ("TC-ECP-IRTMP-INV-28", "candidate_email", "a" * 256 + "@company.com", 400, "EMAIL_TOO_LONG"),
        ("TC-ECP-IRTMP-INV-29", "cv_file_extension", "", 400, "INVALID_EXTENSION_EMPTY"),
        ("TC-ECP-IRTMP-INV-30", "cv_file_extension", ".exe", 400, "INVALID_FILE_EXTENSION"),
        ("TC-ECP-IRTMP-INV-31", "cv_file_extension", ".png", 400, "INVALID_FILE_EXTENSION"),
        ("TC-ECP-IRTMP-INV-32", "has_disciplinary_record", True, 400, "DISCIPLINARY_VIOLATION"),
    ]

    @pytest.mark.parametrize("tc_id, param, invalid_val, expected_status, expected_code", IRTMP_INVALID_CASES)
    def test_irtmp_equivalence_partitioning_invalid(self, tc_id, param, invalid_val, expected_status, expected_code):
        payload = IRTMP_NOMINAL_PAYLOAD.copy()
        payload[param] = invalid_val
        res = process_irtmp_decision("D6", payload)
        assert res["status"] == expected_status, f"[{tc_id}] Expected {expected_status}, got {res['status']}"
        assert res["code"] == expected_code, f"[{tc_id}] Expected code {expected_code}, got {res['code']}"
        assert res["success"] is False, f"[{tc_id}] Expected success=False"

    # --------------------------------------------------------------------------
    # 1.2 SOPRCS Equivalence Partitioning Tests
    # --------------------------------------------------------------------------

    # 6 Valid Equivalence Flows
    SOPRCS_VALID_CASES = [
        ("TC-ECP-SOPRCS-VAL-01", "D1", {}, 200, "APPROVED_OFFLINE_PAYMENT"),
        ("TC-ECP-SOPRCS-VAL-02", "D2", {"cart_items_count": 18, "parked_cart_timeout_minutes": 40}, 200, "CART_PARKED_SUCCESS"),
        ("TC-ECP-SOPRCS-VAL-03", "D3", {"credit_score": 780, "is_ekyc_verified": True}, 200, "PAY_LATER_APPROVED"),
        ("TC-ECP-SOPRCS-VAL-04", "D4", {"token_limit_accumulated": 1800000, "prefetch_tokens_count": 4}, 200, "TOKEN_SYNC_SUCCESS"),
        ("TC-ECP-SOPRCS-VAL-05", "D5", {"wifi_duration_minutes": 10, "wifi_bandwidth_mbps": 1.5}, 200, "WIFI_SESSION_GRANTED"),
        ("TC-ECP-SOPRCS-VAL-06", "D6", {}, 200, "APPROVED_ALL"),
    ]

    @pytest.mark.parametrize("tc_id, flow, overrides, expected_status, expected_code", SOPRCS_VALID_CASES)
    def test_soprcs_equivalence_partitioning_valid(self, tc_id, flow, overrides, expected_status, expected_code):
        payload = SOPRCS_NOMINAL_PAYLOAD.copy()
        payload.update(overrides)
        res = process_soprcs_decision(flow, payload)
        assert res["status"] == expected_status, f"[{tc_id}] Expected {expected_status}, got {res['status']}"
        assert res["code"] == expected_code, f"[{tc_id}] Expected code {expected_code}, got {res['code']}"
        assert res["success"] is True, f"[{tc_id}] Expected success=True"

    # 35 Invalid Equivalence Classes
    SOPRCS_INVALID_CASES = [
        ("TC-ECP-SOPRCS-INV-01", "offline_amount", 450, 400, "INVALID_AMOUNT"),
        ("TC-ECP-SOPRCS-INV-02", "offline_amount", 1850000, 400, "EXCEEDS_OFFLINE_LIMIT"),
        ("TC-ECP-SOPRCS-INV-03", "cart_items_count", 0, 400, "EMPTY_CART"),
        ("TC-ECP-SOPRCS-INV-04", "cart_items_count", 65, 400, "EXCEEDS_CART_LIMIT"),
        ("TC-ECP-SOPRCS-INV-05", "pay_later_advance", 350, 400, "INVALID_AMOUNT"),
        ("TC-ECP-SOPRCS-INV-06", "pay_later_advance", 750000, 400, "EXCEEDS_PAY_LATER_LIMIT"),
        ("TC-ECP-SOPRCS-INV-07", "credit_score", 580, 400, "CREDIT_SCORE_TOO_LOW"),
        ("TC-ECP-SOPRCS-INV-08", "credit_score", 920, 400, "EXCEEDS_CREDIT_SCALE"),
        ("TC-ECP-SOPRCS-INV-09", "qr_totp_period", 0, 400, "INVALID_QR_PERIOD"),
        ("TC-ECP-SOPRCS-INV-10", "qr_totp_period", 85, 400, "EXCEEDS_QR_PERIOD"),
        ("TC-ECP-SOPRCS-INV-11", "clock_drift_seconds", -165, 400, "TIME_DRIFT_TOO_LOW"),
        ("TC-ECP-SOPRCS-INV-12", "clock_drift_seconds", 175, 400, "TIME_DRIFT_EXCEEDED"),
        ("TC-ECP-SOPRCS-INV-13", "nonce_ttl_seconds", 0, 400, "INVALID_NONCE_TTL"),
        ("TC-ECP-SOPRCS-INV-14", "nonce_ttl_seconds", 250, 400, "EXCEEDS_NONCE_TTL"),
        ("TC-ECP-SOPRCS-INV-15", "token_limit_accumulated", 600, 400, "INVALID_TOKEN_LIMIT"),
        ("TC-ECP-SOPRCS-INV-16", "token_limit_accumulated", 4500000, 400, "EXCEEDS_TOKEN_LIMIT"),
        ("TC-ECP-SOPRCS-INV-17", "parked_cart_timeout_minutes", 0, 400, "INVALID_PARKED_TIMEOUT"),
        ("TC-ECP-SOPRCS-INV-18", "parked_cart_timeout_minutes", 80, 400, "EXCEEDS_PARKED_TIMEOUT"),
        ("TC-ECP-SOPRCS-INV-19", "grace_period_hours", 0, 400, "INVALID_GRACE_PERIOD"),
        ("TC-ECP-SOPRCS-INV-20", "grace_period_hours", 36, 400, "EXCEEDS_GRACE_PERIOD"),
        ("TC-ECP-SOPRCS-INV-21", "wifi_duration_minutes", 0, 400, "INVALID_WIFI_DURATION"),
        ("TC-ECP-SOPRCS-INV-22", "wifi_duration_minutes", 25, 400, "EXCEEDS_WIFI_DURATION"),
        ("TC-ECP-SOPRCS-INV-23", "prefetch_tokens_count", 0, 400, "INVALID_PREFETCH_COUNT"),
        ("TC-ECP-SOPRCS-INV-24", "prefetch_tokens_count", 9, 400, "EXCEEDS_PREFETCH_COUNT"),
        ("TC-ECP-SOPRCS-INV-25", "wifi_bandwidth_mbps", 0.0, 400, "INVALID_WIFI_BANDWIDTH"),
        ("TC-ECP-SOPRCS-INV-26", "wifi_bandwidth_mbps", 4.2, 400, "EXCEEDS_WIFI_BANDWIDTH"),
        ("TC-ECP-SOPRCS-INV-27", "customer_phone", "", 400, "INVALID_PHONE_EMPTY"),
        ("TC-ECP-SOPRCS-INV-28", "customer_phone", "0987ab5678", 400, "INVALID_PHONE_FORMAT"),
        ("TC-ECP-SOPRCS-INV-29", "customer_phone", "098765432", 400, "INVALID_PHONE_LENGTH"),
        ("TC-ECP-SOPRCS-INV-30", "customer_phone", "09876543210", 400, "INVALID_PHONE_LENGTH"),
        ("TC-ECP-SOPRCS-INV-31", "currency", "", 400, "INVALID_CURRENCY_EMPTY"),
        ("TC-ECP-SOPRCS-INV-32", "currency", "USD", 400, "UNSUPPORTED_CURRENCY"),
        ("TC-ECP-SOPRCS-INV-33", "is_ekyc_verified", False, 400, "EKYC_REQUIRED"),
    ]

    @pytest.mark.parametrize("tc_id, param, invalid_val, expected_status, expected_code", SOPRCS_INVALID_CASES)
    def test_soprcs_equivalence_partitioning_invalid(self, tc_id, param, invalid_val, expected_status, expected_code):
        payload = SOPRCS_NOMINAL_PAYLOAD.copy()
        payload[param] = invalid_val
        res = process_soprcs_decision("D6", payload)
        assert res["status"] == expected_status, f"[{tc_id}] Expected {expected_status}, got {res['status']}"
        assert res["code"] == expected_code, f"[{tc_id}] Expected code {expected_code}, got {res['code']}"
        assert res["success"] is False, f"[{tc_id}] Expected success=False"


# ==============================================================================
# CLASS 2: BOUNDARY VALUE ANALYSIS (BVA - 3 VALUES TECHNIQUE)
# ==============================================================================

class Test_AI_BoundaryValueAnalysis:
    """
    Boundary Value Analysis Black-Box Test Suite.
    Applies the standard 3-value boundary technique:
    {min-, min, min+} and {max-, max, max+} for all input variables.
    """

    # --------------------------------------------------------------------------
    # 2.1 IRTMP 3-Value Boundary Points (81 Test Cases: 1 Nominal + 72 Numeric + 8 Non-numeric)
    # --------------------------------------------------------------------------
    IRTMP_BVA_CASES = [
        # TC-BVA-01: Điểm danh định chuẩn All-Nominal
        ("TC-BVA-IRTMP-01", "nominal", None, "nominal", 200, "APPROVED_ALL"),

        # P1: [180, 18000]
        ("TC-BVA-IRTMP-02", "seniority_days", 179, "min-", 400, "SENIORITY_REQUIREMENT_NOT_MET"),
        ("TC-BVA-IRTMP-03", "seniority_days", 180, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-04", "seniority_days", 181, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-05", "seniority_days", 17999, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-06", "seniority_days", 18000, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-07", "seniority_days", 18001, "max+", 400, "RETIREMENT_AGE_EXCEEDED"),

        # P2: [1, 3]
        ("TC-BVA-IRTMP-08", "active_applications", 0, "min-", 400, "INVALID_APP_COUNT"),
        ("TC-BVA-IRTMP-09", "active_applications", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-10", "active_applications", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-11", "active_applications", 2, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-12", "active_applications", 3, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-13", "active_applications", 4, "max+", 400, "MAX_ACTIVE_APPLICATIONS_REACHED"),

        # P3: [10, 1000]
        ("TC-BVA-IRTMP-14", "cover_letter_length", 9, "min-", 400, "COVER_LETTER_TOO_SHORT"),
        ("TC-BVA-IRTMP-15", "cover_letter_length", 10, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-16", "cover_letter_length", 11, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-17", "cover_letter_length", 999, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-18", "cover_letter_length", 1000, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-19", "cover_letter_length", 1001, "max+", 400, "COVER_LETTER_TOO_LONG"),

        # P4: [1, 5]
        ("TC-BVA-IRTMP-20", "interview_rating", 0, "min-", 400, "INVALID_RATING"),
        ("TC-BVA-IRTMP-21", "interview_rating", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-22", "interview_rating", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-23", "interview_rating", 4, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-24", "interview_rating", 5, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-25", "interview_rating", 6, "max+", 400, "RATING_OUT_OF_SCALE"),

        # P5: [1, 90]
        ("TC-BVA-IRTMP-26", "job_deadline_days", 0, "min-", 400, "INVALID_DEADLINE"),
        ("TC-BVA-IRTMP-27", "job_deadline_days", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-28", "job_deadline_days", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-29", "job_deadline_days", 89, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-30", "job_deadline_days", 90, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-31", "job_deadline_days", 91, "max+", 400, "EXCEEDS_DEADLINE"),

        # P6: [1, 72]
        ("TC-BVA-IRTMP-32", "closing_soon_hours", 0, "min-", 400, "INVALID_CLOSING_SOON_HOURS"),
        ("TC-BVA-IRTMP-33", "closing_soon_hours", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-34", "closing_soon_hours", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-35", "closing_soon_hours", 71, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-36", "closing_soon_hours", 72, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-37", "closing_soon_hours", 73, "max+", 400, "EXCEEDS_CLOSING_SOON_HOURS"),

        # P7: [0.001, 5.0]
        ("TC-BVA-IRTMP-38", "cv_file_size_mb", 0.000, "min-", 400, "INVALID_CV_FILE_SIZE"),
        ("TC-BVA-IRTMP-39", "cv_file_size_mb", 0.001, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-40", "cv_file_size_mb", 0.002, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-41", "cv_file_size_mb", 4.999, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-42", "cv_file_size_mb", 5.0, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-43", "cv_file_size_mb", 5.001, "max+", 400, "EXCEEDS_CV_FILE_SIZE"),

        # P8: [1, 3]
        ("TC-BVA-IRTMP-44", "hr_sla_days", 0, "min-", 400, "INVALID_HR_SLA"),
        ("TC-BVA-IRTMP-45", "hr_sla_days", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-46", "hr_sla_days", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-47", "hr_sla_days", 2, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-48", "hr_sla_days", 3, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-49", "hr_sla_days", 4, "max+", 400, "EXCEEDS_HR_SLA"),

        # P9: [1, 20]
        ("TC-BVA-IRTMP-50", "skills_count", 0, "min-", 400, "INVALID_SKILLS_COUNT"),
        ("TC-BVA-IRTMP-51", "skills_count", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-52", "skills_count", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-53", "skills_count", 19, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-54", "skills_count", 20, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-55", "skills_count", 21, "max+", 400, "EXCEEDS_SKILLS_COUNT"),

        # P10: [1, 100]
        ("TC-BVA-IRTMP-56", "match_score_percent", 0, "min-", 400, "INVALID_MATCH_SCORE"),
        ("TC-BVA-IRTMP-57", "match_score_percent", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-58", "match_score_percent", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-59", "match_score_percent", 99, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-60", "match_score_percent", 100, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-61", "match_score_percent", 101, "max+", 400, "EXCEEDS_MATCH_SCORE"),

        # P11: [1, 100]
        ("TC-BVA-IRTMP-62", "kanban_cards_limit", 0, "min-", 400, "INVALID_KANBAN_LIMIT"),
        ("TC-BVA-IRTMP-63", "kanban_cards_limit", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-64", "kanban_cards_limit", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-65", "kanban_cards_limit", 99, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-66", "kanban_cards_limit", 100, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-67", "kanban_cards_limit", 101, "max+", 400, "EXCEEDS_KANBAN_LIMIT"),

        # P12: [0.1, 2.0]
        ("TC-BVA-IRTMP-68", "notification_latency_seconds", 0.0, "min-", 400, "INVALID_NOTIFICATION_LATENCY"),
        ("TC-BVA-IRTMP-69", "notification_latency_seconds", 0.1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-70", "notification_latency_seconds", 0.2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-71", "notification_latency_seconds", 1.9, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-72", "notification_latency_seconds", 2.0, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-IRTMP-73", "notification_latency_seconds", 2.1, "max+", 400, "EXCEEDS_NOTIFICATION_LATENCY"),

        # Non-numeric Boundary Cases (P13, P14, P15)
        ("TC-BVA-IRTMP-74", "candidate_email", "", "empty", 400, "INVALID_EMAIL_EMPTY"),
        ("TC-BVA-IRTMP-75", "candidate_email", "employee@", "missing_domain", 400, "INVALID_EMAIL_FORMAT"),
        ("TC-BVA-IRTMP-76", "candidate_email", "employee@gmail.com", "wrong_domain", 400, "INVALID_EMAIL_DOMAIN"),
        ("TC-BVA-IRTMP-77", "candidate_email", "a" * 256 + "@company.com", "too_long", 400, "EMAIL_TOO_LONG"),
        ("TC-BVA-IRTMP-78", "cv_file_extension", "", "empty", 400, "INVALID_EXTENSION_EMPTY"),
        ("TC-BVA-IRTMP-79", "cv_file_extension", ".exe", "prohibited_exe", 400, "INVALID_FILE_EXTENSION"),
        ("TC-BVA-IRTMP-80", "cv_file_extension", ".png", "unsupported_png", 400, "INVALID_FILE_EXTENSION"),
        ("TC-BVA-IRTMP-81", "has_disciplinary_record", True, "disciplinary", 400, "DISCIPLINARY_VIOLATION"),
    ]

    @pytest.mark.parametrize("tc_id, param, val, point_type, expected_status, expected_code", IRTMP_BVA_CASES)
    def test_irtmp_boundary_value_analysis(self, tc_id, param, val, point_type, expected_status, expected_code):
        payload = IRTMP_NOMINAL_PAYLOAD.copy()
        if param != "nominal":
            payload[param] = val
        res = process_irtmp_decision("D6", payload)
        assert res["status"] == expected_status, f"[{tc_id} {point_type}] Expected {expected_status}, got {res['status']}"
        assert res["code"] == expected_code, f"[{tc_id} {point_type}] Expected code {expected_code}, got {res['code']}"

    # --------------------------------------------------------------------------
    # 2.2 SOPRCS 3-Value Boundary Points (86 Test Cases: 1 Nominal + 78 Numeric + 7 Non-numeric)
    # --------------------------------------------------------------------------
    SOPRCS_BVA_CASES = [
        # TC-BVA-01: Điểm danh định chuẩn All-Nominal
        ("TC-BVA-SOPRCS-01", "nominal", None, "nominal", 200, "APPROVED_ALL"),

        # P1: [1000, 1000000]
        ("TC-BVA-SOPRCS-02", "offline_amount", 999, "min-", 400, "INVALID_AMOUNT"),
        ("TC-BVA-SOPRCS-03", "offline_amount", 1000, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-04", "offline_amount", 1001, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-05", "offline_amount", 999999, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-06", "offline_amount", 1000000, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-07", "offline_amount", 1000001, "max+", 400, "EXCEEDS_OFFLINE_LIMIT"),

        # P2: [1, 50]
        ("TC-BVA-SOPRCS-08", "cart_items_count", 0, "min-", 400, "EMPTY_CART"),
        ("TC-BVA-SOPRCS-09", "cart_items_count", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-10", "cart_items_count", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-11", "cart_items_count", 49, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-12", "cart_items_count", 50, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-13", "cart_items_count", 51, "max+", 400, "EXCEEDS_CART_LIMIT"),

        # P3: [1000, 500000]
        ("TC-BVA-SOPRCS-14", "pay_later_advance", 999, "min-", 400, "INVALID_AMOUNT"),
        ("TC-BVA-SOPRCS-15", "pay_later_advance", 1000, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-16", "pay_later_advance", 1001, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-17", "pay_later_advance", 499999, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-18", "pay_later_advance", 500000, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-19", "pay_later_advance", 500001, "max+", 400, "EXCEEDS_PAY_LATER_LIMIT"),

        # P4: [650, 850]
        ("TC-BVA-SOPRCS-20", "credit_score", 649, "min-", 400, "CREDIT_SCORE_TOO_LOW"),
        ("TC-BVA-SOPRCS-21", "credit_score", 650, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-22", "credit_score", 651, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-23", "credit_score", 849, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-24", "credit_score", 850, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-25", "credit_score", 851, "max+", 400, "EXCEEDS_CREDIT_SCALE"),

        # P5: [1, 60]
        ("TC-BVA-SOPRCS-26", "qr_totp_period", 0, "min-", 400, "INVALID_QR_PERIOD"),
        ("TC-BVA-SOPRCS-27", "qr_totp_period", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-28", "qr_totp_period", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-29", "qr_totp_period", 59, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-30", "qr_totp_period", 60, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-31", "qr_totp_period", 61, "max+", 400, "EXCEEDS_QR_PERIOD"),

        # P6: [-120, 120]
        ("TC-BVA-SOPRCS-32", "clock_drift_seconds", -121, "min-", 400, "TIME_DRIFT_TOO_LOW"),
        ("TC-BVA-SOPRCS-33", "clock_drift_seconds", -120, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-34", "clock_drift_seconds", -119, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-35", "clock_drift_seconds", 119, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-36", "clock_drift_seconds", 120, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-37", "clock_drift_seconds", 121, "max+", 400, "TIME_DRIFT_EXCEEDED"),

        # P7: [1, 180]
        ("TC-BVA-SOPRCS-38", "nonce_ttl_seconds", 0, "min-", 400, "INVALID_NONCE_TTL"),
        ("TC-BVA-SOPRCS-39", "nonce_ttl_seconds", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-40", "nonce_ttl_seconds", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-41", "nonce_ttl_seconds", 179, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-42", "nonce_ttl_seconds", 180, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-43", "nonce_ttl_seconds", 181, "max+", 400, "EXCEEDS_NONCE_TTL"),

        # P8: [1000, 3000000]
        ("TC-BVA-SOPRCS-44", "token_limit_accumulated", 999, "min-", 400, "INVALID_TOKEN_LIMIT"),
        ("TC-BVA-SOPRCS-45", "token_limit_accumulated", 1000, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-46", "token_limit_accumulated", 1001, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-47", "token_limit_accumulated", 2999999, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-48", "token_limit_accumulated", 3000000, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-49", "token_limit_accumulated", 3000001, "max+", 400, "EXCEEDS_TOKEN_LIMIT"),

        # P9: [1, 60]
        ("TC-BVA-SOPRCS-50", "parked_cart_timeout_minutes", 0, "min-", 400, "INVALID_PARKED_TIMEOUT"),
        ("TC-BVA-SOPRCS-51", "parked_cart_timeout_minutes", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-52", "parked_cart_timeout_minutes", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-53", "parked_cart_timeout_minutes", 59, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-54", "parked_cart_timeout_minutes", 60, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-55", "parked_cart_timeout_minutes", 61, "max+", 400, "EXCEEDS_PARKED_TIMEOUT"),

        # P10: [1, 24]
        ("TC-BVA-SOPRCS-56", "grace_period_hours", 0, "min-", 400, "INVALID_GRACE_PERIOD"),
        ("TC-BVA-SOPRCS-57", "grace_period_hours", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-58", "grace_period_hours", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-59", "grace_period_hours", 23, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-60", "grace_period_hours", 24, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-61", "grace_period_hours", 25, "max+", 400, "EXCEEDS_GRACE_PERIOD"),

        # P11: [1, 15]
        ("TC-BVA-SOPRCS-62", "wifi_duration_minutes", 0, "min-", 400, "INVALID_WIFI_DURATION"),
        ("TC-BVA-SOPRCS-63", "wifi_duration_minutes", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-64", "wifi_duration_minutes", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-65", "wifi_duration_minutes", 14, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-66", "wifi_duration_minutes", 15, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-67", "wifi_duration_minutes", 16, "max+", 400, "EXCEEDS_WIFI_DURATION"),

        # P12: [1, 5]
        ("TC-BVA-SOPRCS-68", "prefetch_tokens_count", 0, "min-", 400, "INVALID_PREFETCH_COUNT"),
        ("TC-BVA-SOPRCS-69", "prefetch_tokens_count", 1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-70", "prefetch_tokens_count", 2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-71", "prefetch_tokens_count", 4, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-72", "prefetch_tokens_count", 5, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-73", "prefetch_tokens_count", 6, "max+", 400, "EXCEEDS_PREFETCH_COUNT"),

        # P13: [0.1, 2.0]
        ("TC-BVA-SOPRCS-74", "wifi_bandwidth_mbps", 0.0, "min-", 400, "INVALID_WIFI_BANDWIDTH"),
        ("TC-BVA-SOPRCS-75", "wifi_bandwidth_mbps", 0.1, "min", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-76", "wifi_bandwidth_mbps", 0.2, "min+", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-77", "wifi_bandwidth_mbps", 1.9, "max-", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-78", "wifi_bandwidth_mbps", 2.0, "max", 200, "APPROVED_ALL"),
        ("TC-BVA-SOPRCS-79", "wifi_bandwidth_mbps", 2.1, "max+", 400, "EXCEEDS_WIFI_BANDWIDTH"),

        # Non-numeric Boundary Cases (P14, P15, P16)
        ("TC-BVA-SOPRCS-80", "customer_phone", "", "empty", 400, "INVALID_PHONE_EMPTY"),
        ("TC-BVA-SOPRCS-81", "customer_phone", "0987ab5678", "letters", 400, "INVALID_PHONE_FORMAT"),
        ("TC-BVA-SOPRCS-82", "customer_phone", "098765432", "9_digits", 400, "INVALID_PHONE_LENGTH"),
        ("TC-BVA-SOPRCS-83", "customer_phone", "09876543210", "11_digits", 400, "INVALID_PHONE_LENGTH"),
        ("TC-BVA-SOPRCS-84", "currency", "", "empty", 400, "INVALID_CURRENCY_EMPTY"),
        ("TC-BVA-SOPRCS-85", "currency", "USD", "unsupported_usd", 400, "UNSUPPORTED_CURRENCY"),
        ("TC-BVA-SOPRCS-86", "is_ekyc_verified", False, "no_ekyc", 400, "EKYC_REQUIRED"),
    ]

    @pytest.mark.parametrize("tc_id, param, val, point_type, expected_status, expected_code", SOPRCS_BVA_CASES)
    def test_soprcs_boundary_value_analysis(self, tc_id, param, val, point_type, expected_status, expected_code):
        payload = SOPRCS_NOMINAL_PAYLOAD.copy()
        if param != "nominal":
            payload[param] = val
        res = process_soprcs_decision("D6", payload)
        assert res["status"] == expected_status, f"[{tc_id} {point_type}] Expected {expected_status}, got {res['status']}"
        assert res["code"] == expected_code, f"[{tc_id} {point_type}] Expected code {expected_code}, got {res['code']}"


# ==============================================================================
# CLASS 3: DECISION TABLE TESTING
# ==============================================================================

class Test_AI_DecisionTable:
    """
    Decision Table Black-Box Test Suite.
    Executes rules R01 to R28 for both systems to verify multi-condition decision logic.
    """

    # --------------------------------------------------------------------------
    # 3.1 IRTMP Decision Table Rules (R01 - R28)
    # --------------------------------------------------------------------------
    IRTMP_DT_RULES = [
        # D1: Submit application (R01 - R11)
        ("TC-DT-IRTMP-01", "R01", "All valid application", "D1", {}, 200, "APPLICATION_ACCEPTED"),
        ("TC-DT-IRTMP-02", "R02", "P1 < 180", "D1", {"seniority_days": 100}, 400, "SENIORITY_REQUIREMENT_NOT_MET"),
        ("TC-DT-IRTMP-03", "R03", "P1 > 18000", "D1", {"seniority_days": 20000}, 400, "RETIREMENT_AGE_EXCEEDED"),
        ("TC-DT-IRTMP-04", "R04", "P2 < 1", "D1", {"active_applications": 0}, 400, "INVALID_APP_COUNT"),
        ("TC-DT-IRTMP-05", "R05", "P2 > 3", "D1", {"active_applications": 5}, 400, "MAX_ACTIVE_APPLICATIONS_REACHED"),
        ("TC-DT-IRTMP-06", "R06", "P3 < 10", "D1", {"cover_letter_length": 5}, 400, "COVER_LETTER_TOO_SHORT"),
        ("TC-DT-IRTMP-07", "R07", "P3 > 1000", "D1", {"cover_letter_length": 1500}, 400, "COVER_LETTER_TOO_LONG"),
        ("TC-DT-IRTMP-08", "R08", "P7 out of range", "D1", {"cv_file_size_mb": 6.5}, 400, "EXCEEDS_CV_FILE_SIZE"),
        ("TC-DT-IRTMP-09", "R09", "P13 wrong domain", "D1", {"candidate_email": "user@gmail.com"}, 400, "INVALID_EMAIL_DOMAIN"),
        ("TC-DT-IRTMP-10", "R10", "P14 prohibited ext", "D1", {"cv_file_extension": ".exe"}, 400, "INVALID_FILE_EXTENSION"),
        ("TC-DT-IRTMP-11", "R11", "P15 disciplinary", "D1", {"has_disciplinary_record": True}, 400, "DISCIPLINARY_VIOLATION"),

        # D2: Interview evaluation (R12 - R15)
        ("TC-DT-IRTMP-12", "R12", "P4>=4 & P10>=70", "D2", {"interview_rating": 4, "match_score_percent": 80}, 200, "INTERVIEW_EVALUATED"),
        ("TC-DT-IRTMP-13", "R13", "P4 invalid scale", "D2", {"interview_rating": 0}, 400, "INVALID_RATING"),
        ("TC-DT-IRTMP-14", "R14", "P10 invalid scale", "D2", {"match_score_percent": 120}, 400, "EXCEEDS_MATCH_SCORE"),
        ("TC-DT-IRTMP-15", "R15", "P4 < 4 or P10 < 70", "D2", {"interview_rating": 3, "match_score_percent": 65}, 400, "INTERVIEW_NOT_RECOMMENDED"),

        # D3: Kanban transition (R16 - R18)
        ("TC-DT-IRTMP-16", "R16", "20 < P11 <= 100", "D3", {"kanban_cards_limit": 60}, 200, "KANBAN_STAGE_UPDATED"),
        ("TC-DT-IRTMP-17", "R17", "P11 > 100", "D3", {"kanban_cards_limit": 120}, 400, "EXCEEDS_KANBAN_LIMIT"),
        ("TC-DT-IRTMP-18", "R18", "P11 <= 20 locked", "D3", {"kanban_cards_limit": 15}, 400, "KANBAN_COLUMN_LOCKED"),

        # D4: Job posting (R19 - R21)
        ("TC-DT-IRTMP-19", "R19", "Valid deadline and skills", "D4", {"job_deadline_days": 45, "skills_count": 10}, 200, "JOB_POSTED_SUCCESS"),
        ("TC-DT-IRTMP-20", "R20", "P5 out of range", "D4", {"job_deadline_days": 120}, 400, "EXCEEDS_DEADLINE"),
        ("TC-DT-IRTMP-21", "R21", "P9 out of range", "D4", {"skills_count": 25}, 400, "EXCEEDS_SKILLS_COUNT"),

        # D5: Alerts (R22 - R24)
        ("TC-DT-IRTMP-22", "R22", "Valid alert condition", "D5", {"closing_soon_hours": 36, "hr_sla_days": 3, "notification_latency_seconds": 1.0}, 200, "ALERT_TRIGGERED"),
        ("TC-DT-IRTMP-23", "R23", "P6 > 48 threshold", "D5", {"closing_soon_hours": 60, "hr_sla_days": 3, "notification_latency_seconds": 1.0}, 400, "ALERT_CLOSING_SOON_VIOLATION"),
        ("TC-DT-IRTMP-24", "R24", "P8 <= 2 blocked SLA", "D5", {"closing_soon_hours": 24, "hr_sla_days": 2, "notification_latency_seconds": 1.0}, 400, "ALERT_SLA_BLOCKED"),

        # D6: Gateway validation (R25 - R28)
        ("TC-DT-IRTMP-25", "R25", "Gateway valid all", "D6", {}, 200, "APPROVED_ALL"),
        ("TC-DT-IRTMP-26", "R26", "Gateway invalid latency", "D6", {"notification_latency_seconds": 2.5}, 400, "EXCEEDS_NOTIFICATION_LATENCY"),
        ("TC-DT-IRTMP-27", "R27", "Gateway boundary P1 max", "D6", {"seniority_days": 18000}, 200, "APPROVED_ALL"),
        ("TC-DT-IRTMP-28", "R28", "Gateway boundary P2 min", "D6", {"active_applications": 1}, 200, "APPROVED_ALL"),
    ]

    @pytest.mark.parametrize("tc_id, rule_id, desc, flow, overrides, expected_status, expected_code", IRTMP_DT_RULES)
    def test_irtmp_decision_table(self, tc_id, rule_id, desc, flow, overrides, expected_status, expected_code):
        payload = IRTMP_NOMINAL_PAYLOAD.copy()
        payload.update(overrides)
        res = process_irtmp_decision(flow, payload)
        assert res["status"] == expected_status, f"[{tc_id} {rule_id}] Expected {expected_status}, got {res['status']}"
        assert res["code"] == expected_code, f"[{tc_id} {rule_id}] Expected code {expected_code}, got {res['code']}"

    # --------------------------------------------------------------------------
    # 3.2 SOPRCS Decision Table Rules (R01 - R28)
    # --------------------------------------------------------------------------
    SOPRCS_DT_RULES = [
        # D1: Offline payment approval (R01 - R11)
        ("TC-DT-SOPRCS-01", "R01", "All valid offline payment", "D1", {}, 200, "APPROVED_OFFLINE_PAYMENT"),
        ("TC-DT-SOPRCS-02", "R02", "P1 < 1000", "D1", {"offline_amount": 500}, 400, "INVALID_AMOUNT"),
        ("TC-DT-SOPRCS-03", "R03", "P1 > 1000000", "D1", {"offline_amount": 1500000}, 400, "EXCEEDS_OFFLINE_LIMIT"),
        ("TC-DT-SOPRCS-04", "R04", "P2 < 1", "D1", {"cart_items_count": 0}, 400, "EMPTY_CART"),
        ("TC-DT-SOPRCS-05", "R05", "P2 > 50", "D1", {"cart_items_count": 60}, 400, "EXCEEDS_CART_LIMIT"),
        ("TC-DT-SOPRCS-06", "R06", "P5 < 1", "D1", {"qr_totp_period": 0}, 400, "INVALID_QR_PERIOD"),
        ("TC-DT-SOPRCS-07", "R07", "P5 > 60", "D1", {"qr_totp_period": 75}, 400, "EXCEEDS_QR_PERIOD"),
        ("TC-DT-SOPRCS-08", "R08", "P6 clock drift out", "D1", {"clock_drift_seconds": 150}, 400, "TIME_DRIFT_EXCEEDED"),
        ("TC-DT-SOPRCS-09", "R09", "P7 nonce out of range", "D1", {"nonce_ttl_seconds": 200}, 400, "EXCEEDS_NONCE_TTL"),
        ("TC-DT-SOPRCS-10", "R10", "P14 phone format invalid", "D1", {"customer_phone": "09876abcde"}, 400, "INVALID_PHONE_FORMAT"),
        ("TC-DT-SOPRCS-11", "R11", "P15 unsupported currency", "D1", {"currency": "USD"}, 400, "UNSUPPORTED_CURRENCY"),

        # D2: Park cart (R12 - R15)
        ("TC-DT-SOPRCS-12", "R12", "Valid cart parking", "D2", {"cart_items_count": 20, "parked_cart_timeout_minutes": 30}, 200, "CART_PARKED_SUCCESS"),
        ("TC-DT-SOPRCS-13", "R13", "P2 out of range", "D2", {"cart_items_count": 0}, 400, "EMPTY_CART"),
        ("TC-DT-SOPRCS-14", "R14", "P9 out of range", "D2", {"parked_cart_timeout_minutes": 70}, 400, "EXCEEDS_PARKED_TIMEOUT"),
        ("TC-DT-SOPRCS-15", "R15", "P9 > 45 critical threshold", "D2", {"parked_cart_timeout_minutes": 50}, 400, "PARKED_TIME_CRITICAL"),

        # D3: Pay-Later (R16 - R18)
        ("TC-DT-SOPRCS-16", "R16", "Valid Pay-Later approval", "D3", {"credit_score": 750, "is_ekyc_verified": True}, 200, "PAY_LATER_APPROVED"),
        ("TC-DT-SOPRCS-17", "R17", "P3 out of range", "D3", {"pay_later_advance": 600000}, 400, "EXCEEDS_PAY_LATER_LIMIT"),
        ("TC-DT-SOPRCS-18", "R18", "P4 credit insufficient", "D3", {"credit_score": 670}, 400, "CREDIT_INSUFFICIENT"),

        # D4: Token sync (R19 - R21)
        ("TC-DT-SOPRCS-19", "R19", "Valid Token sync", "D4", {"token_limit_accumulated": 2000000, "prefetch_tokens_count": 4}, 200, "TOKEN_SYNC_SUCCESS"),
        ("TC-DT-SOPRCS-20", "R20", "P8 limit exceeded", "D4", {"token_limit_accumulated": 3500000}, 400, "EXCEEDS_TOKEN_LIMIT"),
        ("TC-DT-SOPRCS-21", "R21", "P12 prefetch exceeded", "D4", {"prefetch_tokens_count": 8}, 400, "EXCEEDS_PREFETCH_COUNT"),

        # D5: Wifi emergency session (R22 - R24)
        ("TC-DT-SOPRCS-22", "R22", "Valid Wifi session", "D5", {"wifi_duration_minutes": 10, "wifi_bandwidth_mbps": 1.2}, 200, "WIFI_SESSION_GRANTED"),
        ("TC-DT-SOPRCS-23", "R23", "P11 duration out of range", "D5", {"wifi_duration_minutes": 20}, 400, "EXCEEDS_WIFI_DURATION"),
        ("TC-DT-SOPRCS-24", "R24", "P13 bandwidth exceeded", "D5", {"wifi_bandwidth_mbps": 3.0}, 400, "EXCEEDS_WIFI_BANDWIDTH"),

        # D6: Gateway validation (R25 - R28)
        ("TC-DT-SOPRCS-25", "R25", "Gateway valid all", "D6", {}, 200, "APPROVED_ALL"),
        ("TC-DT-SOPRCS-26", "R26", "Gateway eKYC unverified", "D6", {"is_ekyc_verified": False}, 400, "EKYC_REQUIRED"),
        ("TC-DT-SOPRCS-27", "R27", "Gateway boundary P1 max", "D6", {"offline_amount": 1000000}, 200, "APPROVED_ALL"),
        ("TC-DT-SOPRCS-28", "R28", "Gateway boundary P2 min", "D6", {"cart_items_count": 1}, 200, "APPROVED_ALL"),
    ]

    @pytest.mark.parametrize("tc_id, rule_id, desc, flow, overrides, expected_status, expected_code", SOPRCS_DT_RULES)
    def test_soprcs_decision_table(self, tc_id, rule_id, desc, flow, overrides, expected_status, expected_code):
        payload = SOPRCS_NOMINAL_PAYLOAD.copy()
        payload.update(overrides)
        res = process_soprcs_decision(flow, payload)
        assert res["status"] == expected_status, f"[{tc_id} {rule_id}] Expected {expected_status}, got {res['status']}"
        assert res["code"] == expected_code, f"[{tc_id} {rule_id}] Expected code {expected_code}, got {res['code']}"

