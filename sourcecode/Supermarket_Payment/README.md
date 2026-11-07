# HỆ THỐNG THANH TOÁN NGOẠI TUYẾN SIÊU THỊ (SOPRCS)
### Supermarket Offline Payment & Resilient Checkout System

> **Chủ đề 7:** Đi siêu thị không mang tiền mặt – Khách hàng không mang ví/tiền mặt, điện thoại mất kết nối mạng (không có 4G/Wi-Fi) tại quầy thanh toán.

---

## 1. Cấu trúc thư mục dự án

Toàn bộ dự án được phân chia rành mạch thành 2 phần: **Tài liệu phân tích & kiểm thử (docs)** và **Mã nguồn hệ thống (src)**.

```
f:\main\Supermarket Payment\
│
├── docs/                                    # TÀI LIỆU PHÂN TÍCH, ĐẶC TẢ & KIỂM THỬ
│   ├── BRD_Offline_Payment_Supermarket.md   # Tài liệu Yêu cầu Nghiệp vụ (Chuẩn BABOK)
│   ├── SRS_Offline_Payment_Supermarket.md   # Đặc tả Yêu cầu Phần mềm (Chuẩn IEEE 830 / ISO 29148)
│   └── BAO_CAO_KIEM_THU_BVA.md              # BÁO CÁO KIỂM THỬ BVA GỐC (Full 625 4-Way Combinatorial Test Cases)
│
├── src/                                     # MÃ NGUỒN CỤM MICROSERVICES & DEMO
│   ├── gateway/
│   │   └── gateway_server.py                # API Gateway & Reverse Proxy (Port 8080)
│   │
│   ├── services/
│   │   ├── common/
│   │   │   ├── config.py                    # Cấu hình Topology mạng & Ports
│   │   │   └── http_client.py               # Tiện ích giao tiếp REST JSON nội bộ
│   │   ├── pos_service/                     # POS & Order Microservice (Port 8081 - pos.db)
│   │   ├── payment_service/                 # Payment & Fraud Microservice (Port 8082 - payment.db)
│   │   ├── token_service/                   # Token Vault Microservice (Port 8083 - tokens.db)
│   │   └── customer_service/                # Customer & BNPL Microservice (Port 8084 - customers.db)
│   │
│   ├── static/                              # Giao diện Web Dual Simulator (POS + Phone)
│   │   ├── index.html
│   │   ├── css/style.css
│   │   └── js/ (pos.js, customer.js, qrcode.min.js)
│   │
│   ├── run_microservices.py                 # Master Orchestrator khởi chạy 5 services
│   ├── test_to_hop_4_bva.py                 # Bộ kiểm thử tự động toàn bộ 625 ca tổ hợp 4 biến
│   ├── manual_test_cli.py                   # Công cụ kiểm thử thủ công tương tác theo mã TC (1-625)
│   └── run_demo.bat                         # File 1-click khởi chạy bên trong src
│
├── run_demo.bat                             # Script 1-click tiện lợi tại thư mục gốc
└── README.md                                # Hướng dẫn tổng quan
```

---

## 2. Thư mục Tài liệu (`docs/`)

- [BRD_Offline_Payment_Supermarket.md](file:///f:/main/Supermarket%20Payment/docs/BRD_Offline_Payment_Supermarket.md):
  - Phân tích nguyên nhân gốc rễ (sóng tầng hầm, Captive Portal, app online-only).
  - Mục tiêu SMART và KPI giảm tỷ lệ hủy đơn từ 5.0% xuống < 0.2%.
  - Mô hình As-Is và To-Be.
  - Ma trận RACI và Quy trình chuẩn thu ngân (SOP).
- [SRS_Offline_Payment_Supermarket.md](file:///f:/main/Supermarket%20Payment/docs/SRS_Offline_Payment_Supermarket.md):
  - Đặc tả kiến trúc kỹ thuật chuẩn IEEE 830 / ISO 29148.
  - Thuật toán TOTP HMAC-SHA256 chu kỳ 60s và giao thức Apple Pay NFC EMV chip Secure Element.
  - Đặc tả yêu cầu chức năng (FR) và phi chức năng (NFR) cho từng phân hệ.
  - Lược đồ cơ sở dữ liệu DDL và tiêu chí nghiệm thu kiểm thử.
- [BAO_CAO_KIEM_THU_BVA.md](file:///f:/main/Supermarket%20Payment/docs/BAO_CAO_KIEM_THU_BVA.md):
  - **Tài liệu kiểm thử gốc của dự án:** Trích xuất yêu cầu SRS, bảng 13 biên toàn hệ thống có Nominal, và bộ toàn diện **625 ca kiểm thử tổ hợp 4 biến** (4-Way Combinatorial BVA).

---

## 3. Thư mục Mã nguồn (`src/`)

### Kiến trúc Microservices (Database-per-Service)
- **API Gateway (Port 8080):** Điểm tiếp nhận duy nhất từ trình duyệt, phục vụ frontend và reverse-proxy traffic tới các services.
- **POS Service (Port 8081 - `pos.db`):** Quản lý sản phẩm, giỏ hàng, Treo đơn `[F8]` và Khôi phục đơn `[F9]`.
- **Payment Service (Port 8082 - `payment.db`):** Xác thực Offline TOTP QR, chống Replay Attack, xử lý Apple Pay NFC.
- **Token Service (Port 8083 - `tokens.db`):** Cấp túi token ngoại tuyến, lưu trữ Secret Keys an toàn.
- **Customer Service (Port 8084 - `customers.db`):** Quản lý số dư ví, điểm tín nhiệm, phê duyệt tạm ứng `[F10]` Pay-Later.

---

## 4. Hướng dẫn khởi chạy & Kiểm thử

### Khởi chạy Demo:
- **Cách 1:** Nhấp đúp vào file `run_demo.bat` tại thư mục gốc `Supermarket Payment/` (hoặc trong `src/`).
- **Cách 2:** Từ terminal:
  ```powershell
  cd "f:\main\Supermarket Payment\src"
  python run_microservices.py
  ```
Sau đó truy cập: `http://localhost:8080`.

### Chạy kiểm thử tự động toàn bộ 625 ca BVA:
```powershell
cd "f:\main\Supermarket Payment\src"
python test_to_hop_4_bva.py
```
*(Kết quả: 625/625 ca kiểm thử tổ hợp 4 biến PASS 100%)*

### Kiểm thử thủ công tương tác:
```powershell
cd "f:\main\Supermarket Payment\src"
python manual_test_cli.py
```
*(Tra cứu và kiểm thử nhanh từ TC-4W-001 đến TC-4W-625)*
