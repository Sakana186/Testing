# -*- coding: utf-8 -*-
"""
manual_test_cli.py - Công cụ Hỗ trợ Kiểm thử Thủ công (Manual Test CLI)
Dự án: Cổng Tuyển Dụng & Điều Chuyển Nhân Tài Nội Bộ (IRTMP)
Cho phép tester:
1. Tra cứu và thực thi thủ công theo Mã Test Case (ví dụ: TC-4W-086, TC-4W-313, TC-4W-625).
2. Tự nhập thủ công 4 tham số biên bất kỳ để kiểm tra phản hồi của hệ thống.
3. Chạy duyệt các ca hợp lệ toàn phần (81 Valid Combinations) bao gồm cả điểm tâm Nominal.
"""

import sys
import os
import itertools

# Định nghĩa miền biên chuẩn của 4 biến
# y1: Seniority [180, 18.000 ngày]
# y2: ActiveApplications [1, 3 đơn]
# y3: CoverLetterLength [10, 1000 ký tự]
# y4: InterviewRating [1, 5 sao]

# 5 Mức giá trị: Min-1, Min, Nom, Max, Max+1
y1_levels = [
    (179, 'Min-1', False, 'SENIORITY_REQUIREMENT_NOT_MET'),
    (180, 'Min', True, 'OK'),
    (730, 'Nom', True, 'OK'),
    (18000, 'Max', True, 'OK'),
    (18001, 'Max+1', False, 'RETIREMENT_AGE_EXCEEDED')
]
y2_levels = [
    (0, 'Min-1', False, 'INVALID_APP_COUNT'),
    (1, 'Min', True, 'OK'),
    (2, 'Nom', True, 'OK'),
    (3, 'Max', True, 'OK'),
    (4, 'Max+1', False, 'MAX_ACTIVE_APPLICATIONS_REACHED')
]
y3_levels = [
    (9, 'Min-1', False, 'COVER_LETTER_TOO_SHORT'),
    (10, 'Min', True, 'OK'),
    (500, 'Nom', True, 'OK'),
    (1000, 'Max', True, 'OK'),
    (1001, 'Max+1', False, 'COVER_LETTER_TOO_LONG')
]
y4_levels = [
    (0, 'Min-1', False, 'INVALID_RATING'),
    (1, 'Min', True, 'OK'),
    (3, 'Nom', True, 'OK'),
    (5, 'Max', True, 'OK'),
    (6, 'Max+1', False, 'RATING_OUT_OF_SCALE')
]

combos = list(itertools.product(y1_levels, y2_levels, y3_levels, y4_levels))


def evaluate_vector(y1, y2, y3, y4):
    """Hàm lõi thẩm định biên của hệ thống tuyển dụng nội bộ"""
    errors = []

    # 1. Kiểm tra thâm niên
    if y1 < 180:
        errors.append(("y1 (Seniority)", "SENIORITY_REQUIREMENT_NOT_MET", f"Thâm niên ({y1} ngày) < Min (180 ngày / 6 tháng)"))
    elif y1 > 18000:
        errors.append(("y1 (Seniority)", "RETIREMENT_AGE_EXCEEDED", f"Thâm niên ({y1:,} ngày) vượt trần công tác Max (18.000 ngày)"))

    # 2. Kiểm tra số đơn đồng thời
    if y2 < 1:
        errors.append(("y2 (ActiveApps)", "INVALID_APP_COUNT", f"Số lượng đơn ({y2}) < Min (1 đơn)"))
    elif y2 > 3:
        errors.append(("y2 (ActiveApps)", "MAX_ACTIVE_APPLICATIONS_REACHED", f"Số lượng đơn ({y2}) vượt trần Max (3 đơn)"))

    # 3. Kiểm tra độ dài thư nguyện vọng
    if y3 < 10:
        errors.append(("y3 (CoverLetter)", "COVER_LETTER_TOO_SHORT", f"Độ dài thư ({y3} ký tự) < Min (10 ký tự)"))
    elif y3 > 1000:
        errors.append(("y3 (CoverLetter)", "COVER_LETTER_TOO_LONG", f"Độ dài thư ({y3} ký tự) vượt trần Max (1000 ký tự)"))

    # 4. Kiểm tra điểm đánh giá phỏng vấn
    if y4 < 1:
        errors.append(("y4 (Rating)", "INVALID_RATING", f"Điểm đánh giá ({y4}) < Min (1 sao)"))
    elif y4 > 5:
        errors.append(("y4 (Rating)", "RATING_OUT_OF_SCALE", f"Điểm đánh giá ({y4}) vượt thang đo chuẩn Max (5 sao)"))

    if not errors:
        return {
            "status": "APPROVED_ALL",
            "http_code": 200,
            "success": True,
            "message": "Hồ sơ hợp lệ toàn phần. Đã tiếp nhận và chuyển tiếp vào luồng đánh giá Kanban."
        }
    else:
        return {
            "status": "REJECTED",
            "http_code": 400,
            "success": False,
            "error": errors[0][1],
            "violations": errors,
            "message": f"Từ chối nộp đơn do vi phạm biên: {', '.join(e[1] for e in errors)}"
        }


def print_test_case_detail(tc_idx):
    if tc_idx < 1 or tc_idx > 625:
        print(f"[!] Mã test case không hợp lệ! Vui lòng nhập từ 1 đến 625.")
        return

    c1, c2, c3, c4 = combos[tc_idx - 1]
    y1_val, y1_tag, y1_ok, _ = c1
    y2_val, y2_tag, y2_ok, _ = c2
    y3_val, y3_tag, y3_ok, _ = c3
    y4_val, y4_tag, y4_ok, _ = c4

    print("=" * 68)
    print(f" THÔNG TIN TEST CASE: TC-4W-{tc_idx:03d}")
    print("=" * 68)
    print(f"  + Đặc trưng biên:      ({y1_tag}, {y2_tag}, {y3_tag}, {y4_tag})")
    print(f"  + Vector đầu vào:      < y1={y1_val:,} ngày, y2={y2_val} đơn, y3={y3_val:,} ký tự, y4={y4_val} sao >")
    print("-" * 68)

    res = evaluate_vector(y1_val, y2_val, y3_val, y4_val)
    print(f"  [>] Phản hồi HTTP:     HTTP {res['http_code']}")
    print(f"  [>] Trạng thái hệ thống: {res['status']}")
    print(f"  [>] Thông điệp:        {res['message']}")
    if not res['success']:
        print("  [>] Chi tiết các lỗi vi phạm:")
        for v in res['violations']:
            print(f"      - {v[0]}: {v[1]} -> {v[2]}")
    print("=" * 68)


def main():
    while True:
        print("\n" + "=" * 60)
        print(" CÔNG CỤ KIỂM THỬ THỦ CÔNG - IRTMP (625 TEST CASES)")
        print("=" * 60)
        print(" [1] Kiểm thử theo Mã Test Case (Nhập từ 1 đến 625)")
        print(" [2] Nhập thủ công 4 tham số biên tùy ý <y1, y2, y3, y4>")
        print(" [3] Chạy thử các ca Hợp lệ toàn phần (81 Valid Combinations)")
        print(" [0] Quay lại / Thoát")
        print("=" * 60)
        choice = input("Lựa chọn của bạn: ").strip()

        if choice == '1':
            inp = input("Nhập số thứ tự Test Case (1-625) hoặc mã (ví dụ TC-4W-086): ").strip()
            inp = inp.upper().replace('TC-4W-', '').replace('TC-', '')
            try:
                num = int(inp)
                print_test_case_detail(num)
            except ValueError:
                print("[!] Số nhập vào không hợp lệ.")

        elif choice == '2':
            try:
                print("\nNhập 4 tham số kiểm thử:")
                y1 = int(input(" - y1 (Thâm niên công tác: 180 - 18.000 ngày): ").strip())
                y2 = int(input(" - y2 (Số lượng đơn đang nộp: 1 - 3 đơn): ").strip())
                y3 = int(input(" - y3 (Độ dài thư nguyện vọng: 10 - 1000 ký tự): ").strip())
                y4 = int(input(" - y4 (Điểm đánh giá phỏng vấn: 1 - 5 sao): ").strip())

                print("\n[ĐANG XỬ LÝ KIỂM THỬ THỦ CÔNG...]")
                res = evaluate_vector(y1, y2, y3, y4)
                print("-" * 60)
                print(f" Kết quả: HTTP {res['http_code']} - {res['status']}")
                print(f" Phản hồi: {res['message']}")
                if not res['success']:
                    for v in res['violations']:
                        print(f"  * {v[0]}: {v[1]} ({v[2]})")
                print("-" * 60)
            except ValueError:
                print("[!] Giá trị nhập vào phải là số nguyên!")

        elif choice == '3':
            print("\nDANH SÁCH 81 TỔ HỢP HỢP LỆ TOÀN PHẦN (81 VALID COMBINATIONS):")
            valid_indices = [idx for idx, (c1, c2, c3, c4) in enumerate(combos, 1) if c1[2] and c2[2] and c3[2] and c4[2]]
            for v_idx in valid_indices:
                c1, c2, c3, c4 = combos[v_idx - 1]
                print(f" * TC-4W-{v_idx:03d}: <y1={c1[0]}, y2={c2[0]}, y3={c3[0]}, y4={c4[0]}> ({c1[1]},{c2[1]},{c3[1]},{c4[1]}) - HTTP 200 OK")

        elif choice == '0':
            break


if __name__ == '__main__':
    main()
