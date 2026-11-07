# -*- coding: utf-8 -*-
"""
manual_test_cli.py - Công cụ Hỗ trợ Kiểm thử Thủ công (Manual Test CLI)
Dự án: Hệ Thống Thanh Toán Ngoại Tuyến Siêu Thị (SOPRCS)
Cho phép tester:
1. Tra cứu và thực thi thủ công theo Mã Test Case (ví dụ: TC-4W-086, TC-4W-313, TC-4W-625).
2. Tự nhập thủ công 4 tham số biên bất kỳ để kiểm tra phản hồi của hệ thống.
3. Chạy duyệt các ca hợp lệ toàn phần (81 Valid Combinations) bao gồm cả điểm tâm Nominal.
"""

import sys
import os
import itertools

# Định nghĩa miền biên chuẩn của 4 biến
Y1_BOUNDS = (1000, 1000000)      # Amount [1.000đ, 1.000.000đ]
Y2_BOUNDS = (1, 50)              # CartQuantity [1, 50 món]
Y3_BOUNDS = (1000, 500000)       # LoanAmount [1.000đ, 500.000đ]
Y4_BOUNDS = (650, 850)           # CreditScore [650, 850 điểm]

# 5 Mức giá trị: Min-1, Min, Nom, Max, Max+1
y1_levels = [
    (0, 'Min-1', False, 'EMPTY_CART'),
    (1000, 'Min', True, 'OK'),
    (500000, 'Nom', True, 'OK'),
    (1000000, 'Max', True, 'OK'),
    (1000001, 'Max+1', False, 'EXCEEDS_OFFLINE_LIMIT')
]
y2_levels = [
    (0, 'Min-1', False, 'EMPTY_CART'),
    (1, 'Min', True, 'OK'),
    (25, 'Nom', True, 'OK'),
    (50, 'Max', True, 'OK'),
    (51, 'Max+1', False, 'EXCEEDS_CART_LIMIT')
]
y3_levels = [
    (0, 'Min-1', False, 'INVALID_AMOUNT'),
    (1000, 'Min', True, 'OK'),
    (250000, 'Nom', True, 'OK'),
    (500000, 'Max', True, 'OK'),
    (500001, 'Max+1', False, 'EXCEEDS_PAY_LATER_LIMIT')
]
y4_levels = [
    (649, 'Min-1', False, 'CREDIT_SCORE_TOO_LOW'),
    (650, 'Min', True, 'OK'),
    (750, 'Nom', True, 'OK'),
    (850, 'Max', True, 'OK'),
    (851, 'Max+1', False, 'EXCEEDS_CREDIT_SCALE')
]

combos = list(itertools.product(y1_levels, y2_levels, y3_levels, y4_levels))


def evaluate_vector(y1, y2, y3, y4):
    """Hàm lõi thẩm định biên của hệ thống thanh toán siêu thị"""
    errors = []
    
    # 1. Kiểm tra giỏ hàng
    if y2 < 1:
        errors.append(("y2 (CartQuantity)", "EMPTY_CART", f"Số lượng món trong giỏ ({y2}) < Min (1)"))
    elif y2 > 50:
        errors.append(("y2 (CartQuantity)", "EXCEEDS_CART_LIMIT", f"Số lượng món ({y2}) vượt trần Max (50 món)"))

    # 2. Kiểm tra số tiền đơn hàng
    if y1 < 1000:
        errors.append(("y1 (Amount)", "EMPTY_CART", f"Số tiền đơn hàng ({y1:,}đ) < Min (1.000đ)"))
    elif y1 > 1000000:
        errors.append(("y1 (Amount)", "EXCEEDS_OFFLINE_LIMIT", f"Số tiền ({y1:,}đ) vượt trần ngoại tuyến Max (1.000.000đ)"))

    # 3. Kiểm tra số tiền tạm ứng nợ
    if y3 < 1000:
        errors.append(("y3 (LoanAmount)", "INVALID_AMOUNT", f"Số tiền vay ({y3:,}đ) < Min (1.000đ)"))
    elif y3 > 500000:
        errors.append(("y3 (LoanAmount)", "EXCEEDS_PAY_LATER_LIMIT", f"Số tiền vay ({y3:,}đ) vượt trần nợ Max (500.000đ)"))

    # 4. Kiểm tra điểm tín nhiệm
    if y4 < 650:
        errors.append(("y4 (CreditScore)", "CREDIT_SCORE_TOO_LOW", f"Điểm ({y4}) dưới chuẩn bảo lãnh Min (650 điểm)"))
    elif y4 > 850:
        errors.append(("y4 (CreditScore)", "EXCEEDS_CREDIT_SCALE", f"Điểm ({y4}) vượt trần thang đo chuẩn FICO Max (850 điểm)"))

    if not errors:
        return {
            "status": "APPROVED_ALL",
            "http_code": 200,
            "success": True,
            "message": "Phê duyệt giao dịch ngoại tuyến và cấp bảo lãnh Pay-Later thành công."
        }
    else:
        return {
            "status": "REJECTED",
            "http_code": 400,
            "success": False,
            "error": errors[0][1],
            "violations": errors,
            "message": f"Từ chối giao dịch do vi phạm biên: {', '.join(e[1] for e in errors)}"
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
    print(f"  + Vector đầu vào:      < y1={y1_val:,}đ, y2={y2_val} món, y3={y3_val:,}đ, y4={y4_val} điểm >")
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
        print(" CÔNG CỤ KIỂM THỬ THỦ CÔNG - SOPRCS (625 TEST CASES)")
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
                y1 = int(input(" - y1 (Số tiền đơn hàng: 1.000đ - 1.000.000đ): ").strip())
                y2 = int(input(" - y2 (Số lượng sản phẩm giỏ: 1 - 50 món): ").strip())
                y3 = int(input(" - y3 (Số tiền vay Pay-Later: 1.000đ - 500.000đ): ").strip())
                y4 = int(input(" - y4 (Điểm tín nhiệm: 650 - 850 điểm): ").strip())

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
