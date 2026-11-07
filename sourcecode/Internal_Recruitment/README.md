# Hệ Thống Tuyển Dụng & Điều Chuyển Nội Bộ Doanh Nghiệp (Internal Recruitment Portal)

> **Chủ đề 6:** Số hóa quy trình tuyển dụng nội bộ tại công ty — Chuyển đổi từ email broadcast sang nền tảng thời gian thực minh bạch, nộp hồ sơ 1-click bảo mật và quản lý luồng tuyển chọn HR Kanban.

---

## 1. Giới Thiệu & Bối Cảnh Bài Toán (Context & Motivation)

### Hiện trạng bất cập (As-Is):
* **Bị trôi tin tuyển dụng:** Đăng tuyển qua email broadcast khiến nhân viên dễ bỏ lỡ thông tin hoặc không biết tin đã hết hạn hay còn hiệu lực.
* **Mơ hồ về yêu cầu & quyền lợi:** JD qua email thường tóm tắt sơ sài, thiếu tiêu chí đánh giá và bảng lương/cấp bậc cụ thể.
* **E ngại thiếu bảo mật:** Nhân viên muốn nộp đơn nhưng sợ quản lý trực tiếp phát hiện gây ảnh hưởng tâm lý làm việc hiện tại.
* **HR quá tải và thiếu minh bạch:** Hồ sơ nộp rải rác qua email cá nhân HR, dễ thất lạc, không có hệ thống cập nhật tiến độ cho ứng viên.

### Giải pháp đề xuất (To-Be):
* **Cổng Thông Tin Tuyển Dụng Nội Bộ (Internal Mobility Portal):**
  * Tự động tính toán trạng thái tin tuyển thời gian thực (`OPEN`, `CLOSING_SOON` $\le 72\text{h}$, `CLOSED`) kèm đồng hồ đếm ngược.
  * Nộp hồ sơ 1-click bảo mật: Quản lý phòng ban cũ hoàn toàn không nhận thông báo cho đến khi ứng viên nhận Offer chính thức.
  * Tự động kiểm tra điều kiện thâm niên ($\ge 6$ tháng), tình trạng kỷ luật và giới hạn tối đa 3 hồ sơ hoạt động.
* **Bảng Điều Hành Tuyển Dụng HR (HR Kanban Pipeline):**
  * Luồng trạng thái 5 giai đoạn: `APPLIED` $\rightarrow$ `HR_SCREENING` $\rightarrow$ `INTERVIEW` $\rightarrow$ `OFFER` $\rightarrow$ `TRANSFERRED` / `REJECTED`.
  * Động cơ thông báo thời gian thực (In-App Notification Engine) cập nhật ngay lập tức khi HR chuyển bước hoặc phản hồi đánh giá.

---

## 2. Cấu Trúc Thư Mục Chuẩn Hóa (Project Structure)

Dự án được phân tách nghiêm ngặt thành hai khu vực tài liệu nghiệp vụ (`docs/`) và mã nguồn hệ thống (`src/`):

```text
f:\main\Internal_Recruitment\
├── docs\                                      <-- Tài liệu chuẩn BABOK, IEEE 830 & Báo cáo BVA Gốc
│   ├── BRD_Internal_Recruitment.md            # Tài liệu Yêu cầu Nghiệp vụ (BABOK Standard)
│   ├── SRS_Internal_Recruitment.md            # Đặc tả Yêu cầu Phần mềm (IEEE 830 Standard)
│   └── BAO_CAO_KIEM_THU_BVA.md                # BÁO CÁO KIỂM THỬ BVA GỐC (Full 625 4-Way Combinatorial Test Cases)
│
├── src\                                       <-- Mã nguồn kiến trúc Microservices
│   ├── gateway\
│   │   └── gateway_server.py                  # API Gateway & Reverse Proxy (Port 8090)
│   ├── services\
│   │   ├── common\                            # Cấu hình mạng & Client HTTP dùng chung
│   │   │   ├── config.py                      # Định nghĩa cổng mạng 8090 - 8094
│   │   │   └── http_client.py                 # Wrapper HTTP REST chuẩn Python Standard Lib
│   │   ├── job_service\                       # Microservice Tin Tuyển Dụng (Port 8091)
│   │   │   ├── app.py
│   │   │   ├── job_db.py
│   │   │   └── jobs.db                        # SQLite riêng biệt
│   │   ├── application_service\               # Microservice Hồ Sơ & Kanban (Port 8092)
│   │   │   ├── app.py
│   │   │   ├── application_db.py
│   │   │   └── applications.db                # SQLite riêng biệt
│   │   ├── employee_service\                  # Microservice Hồ Sơ Nhân Sự & Thâm Niên (Port 8093)
│   │   │   ├── app.py
│   │   │   ├── employee_db.py
│   │   │   └── employees.db                   # SQLite riêng biệt
│   │   └── notification_service\              # Microservice Thông Báo & Cảnh Báo (Port 8094)
│   │       ├── app.py
│   │       ├── notification_db.py
│   │       └── notifications.db               # SQLite riêng biệt
│   ├── static\                                <-- Giao diện Web SPA Dual-Screen
│   │   ├── css\style.css                      # Giao diện Dark-theme hiện đại
│   │   ├── js\employee_portal.js              # Xử lý phía Ứng viên & Nộp đơn 1-click
│   │   ├── js\hr_dashboard.js                 # Xử lý phía HR & Điều phối Kanban
│   │   └── index.html                         # Trang chủ chia đôi màn hình
│   ├── run_microservices.py                   # Master Orchestrator khởi chạy toàn cụm
│   ├── test_to_hop_4_bva.py                   # Bộ kiểm thử tự động toàn bộ 625 ca tổ hợp 4 biến
│   ├── manual_test_cli.py                     # Công cụ kiểm thử thủ công tương tác theo mã TC (1-625)
│   └── run_demo.bat                           # File batch khởi chạy nhanh từ src
│
├── run_demo.bat                               # File batch khởi chạy nhanh từ thư mục gốc
└── README.md                                  # Hướng dẫn kiến trúc & tài liệu
```

---

## 3. Kiến Trúc Microservices & Cơ Sở Dữ Liệu Độc Lập

Hệ thống hoạt động theo nguyên lý **Database-per-Service**, không chia sẻ bộ nhớ hoặc database giữa các dịch vụ. Mọi giao tiếp liên dịch vụ được điều phối qua HTTP REST API:

| Dịch Vụ | Cổng Mạng (Port) | Cơ Sở Dữ Liệu | Vai Trò Chính |
| :--- | :---: | :--- | :--- |
| **API Gateway** | `8090` | *(Không lưu trữ)* | Reverse Proxy, điều hướng request từ trình duyệt tới 4 microservices |
| **Job Service** | `8091` | `jobs.db` | Quản lý vòng đời tin tuyển dụng, tự động cập nhật trạng thái `OPEN`/`CLOSING_SOON`/`CLOSED` |
| **Application Service** | `8092` | `applications.db` | Tiếp nhận hồ sơ, kiểm soát quota đơn nộp, quản lý Kanban Pipeline 5 giai đoạn |
| **Employee Service** | `8093` | `employees.db` | Quản lý hồ sơ nhân viên, thẩm định thâm niên công tác ($\ge 180$ ngày) và tình trạng kỷ luật |
| **Notification Service** | `8094` | `notifications.db` | Động cơ thông báo thời gian thực cho ứng viên và HR |

---

## 4. Hướng Dẫn Khởi Chạy & Kiểm Thử

### Cách 1: Khởi chạy nhanh bằng File Batch (Khuyến nghị)
Nhấp đúp chuột vào file [run_demo.bat](file:///f:/main/Internal_Recruitment/run_demo.bat) tại thư mục gốc của dự án. File sẽ:
1. Tự động dọn dẹp các tiến trình cổng mạng cũ (nếu có xung đột).
2. Khởi động toàn bộ 4 Microservices và API Gateway.
3. Tự động mở trình duyệt web tại địa chỉ: `http://localhost:8090`.

### Cách 2: Khởi chạy bằng lệnh Python
```powershell
cd "f:\main\Internal_Recruitment\src"
python run_microservices.py
```

### Chạy kiểm thử tự động toàn bộ 625 ca BVA:
```powershell
cd "f:\main\Internal_Recruitment\src"
python test_to_hop_4_bva.py
```
*(Kết quả: 625/625 ca kiểm thử tổ hợp 4 biến PASS 100%)*

### Kiểm thử thủ công tương tác:
```powershell
cd "f:\main\Internal_Recruitment\src"
python manual_test_cli.py
```
*(Tra cứu và kiểm thử nhanh từ TC-4W-001 đến TC-4W-625)*

---

## 5. Danh Mục Tài Liệu Bàn Giao

1. **[BRD_Internal_Recruitment.md](file:///f:/main/Internal_Recruitment/docs/BRD_Internal_Recruitment.md)**:
   * Phân tích quy trình hiện tại (As-Is) và quy trình chuẩn hóa (To-Be).
   * Ma trận phân công trách nhiệm RACI.
   * Bộ chỉ số đo lường hiệu quả SMART KPIs (Giảm 75% thời gian tuyển, tăng 80% tỷ lệ giữ chân nhân tài).
   * Chính sách bảo mật thông tin ứng viên nội bộ.

2. **[SRS_Internal_Recruitment.md](file:///f:/main/Internal_Recruitment/docs/SRS_Internal_Recruitment.md)**:
   * Sơ đồ máy trạng thái hữu hạn (FSM) cho Vị trí tuyển dụng và Hồ sơ ứng viên.
   * Danh mục 12 Yêu cầu chức năng (FR) và 8 Yêu cầu phi chức năng (NFR).
   * Lược đồ cơ sở dữ liệu SQLite độc lập cho từng Microservice.

3. **[BAO_CAO_KIEM_THU_BVA.md](file:///f:/main/Internal_Recruitment/docs/BAO_CAO_KIEM_THU_BVA.md)**:
   * **Tài liệu kiểm thử gốc của dự án:** Trích xuất yêu cầu SRS, bảng 12 biên toàn hệ thống có Nominal, và bộ toàn diện **625 ca kiểm thử tổ hợp 4 biến** (4-Way Combinatorial BVA).
