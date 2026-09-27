# TrafficVision – Nhận dạng biển báo giao thông bằng AI

Hệ thống thị giác máy tính nhận dạng biển báo giao thông trên ảnh và video, tối ưu suy luận ONNX trên CPU (macOS/Windows) và sẵn sàng nâng cấp lên mô hình 82 lớp biển báo Việt Nam.

- **Tài liệu đặc tả thiết kế:** [docs/superpowers/specs/2026-09-27-trafficvision-design.md](docs/superpowers/specs/2026-09-27-trafficvision-design.md)
- **Kế hoạch triển khai baseline:** [docs/superpowers/plans/2026-09-27-trafficvision-baseline-app.md](docs/superpowers/plans/2026-09-27-trafficvision-baseline-app.md)

---

## 1. Yêu cầu hệ thống

- **Hệ điều hành:** macOS (Apple Silicon hoặc Intel) hoặc Windows 10/11 (64-bit).
- **Python:** Python 3.11+ (hỗ trợ 3.11 – 3.13).

---

## 2. Hướng dẫn cài đặt

### macOS / Linux (zsh hoặc bash)

```bash
# 1. Tạo môi trường ảo
python3 -m venv .venv

# 2. Kích hoạt môi trường ảo
source .venv/bin/activate

# 3. Nâng cấp pip và cài đặt gói
pip install --upgrade pip
pip install -e ".[dev]"
```

### Windows (PowerShell / Command Prompt)

```powershell
# 1. Tạo môi trường ảo
python -m venv .venv

# 2. Kích hoạt môi trường ảo
.venv\Scripts\Activate.ps1

# 3. Nâng cấp pip và cài đặt gói
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Hoặc trên Windows, bạn có thể **nhấp đúp chuột vào file `run_app.bat`** (hoặc `run.bat`) để chạy menu quản lý:
- Tự động kiểm tra Python / `.venv`.
- Tự động bootstrap baseline model nếu chưa có.
- Cung cấp lựa chọn khởi chạy Web Dashboard hoặc chạy bộ kiểm thử (pytest / smoke test).

---

## 3. Khởi tạo mô hình Baseline (Bootstrap)

Trước khi chạy ứng dụng lần đầu, chạy lệnh sau để tải YOLO11n pretrained gốc, xuất sang ONNX cố định kích thước (`640x640`, batch 1, CPU) và đăng ký vào Model Registry:

```bash
python scripts/bootstrap_baseline.py --project-root .
```

Sau khi hoàn tất, mô hình sẽ được lưu bất biến tại `artifacts/baseline/` và thiết lập làm mô hình phục vụ tại `artifacts/production/`.

---

## 4. Chạy kiểm thử nhanh (Smoke Test)

Để kiểm tra suy luận trên một tệp ảnh bất kỳ từ dòng lệnh:

```bash
python scripts/smoke_test.py --image path/to/sample.jpg
```

Lệnh sẽ in thông tin mô hình, số đối tượng phát hiện, thời gian xử lý và đường dẫn ảnh kết quả cùng tệp CSV.

---

## 5. Khởi chạy giao diện Web

Khởi chạy ứng dụng Streamlit:

```bash
streamlit run app.py
```

Trình duyệt sẽ tự động mở tại địa chỉ `http://localhost:8501`.

Các tính năng trên giao diện:
- **Phân tích:** Nhận diện ảnh JPG/PNG và xử lý tuần tự video MP4/AVI/MOV, hiển thị trực quan và hỗ trợ tải tệp kết quả kèm CSV.
- **Lịch sử:** Tra cứu các phiên phân tích gần đây đã lưu vào SQLite.
- **Thống kê:** Xem tổng số đối tượng và phân bố theo từng loại biển báo.
- **Huấn luyện AI:** Giai đoạn 2 (hiện đang hiển thị lộ trình 4 bước chuẩn bị).
- **Thông tin mô hình:** Kiểm tra chi tiết manifest, mã băm SHA-256, backend và danh mục lớp.
- **Thiết lập:** Điều chỉnh ngưỡng Confidence, IoU (NMS) và giới hạn dung lượng tải lên.

---

## 6. Cấu trúc thư mục Runtime

```text
artifacts/
├── baseline/            # Mô hình pretrained gốc + manifest bất biến
├── production/          # Mô hình ONNX đang phục vụ suy luận
├── outputs/             # Ảnh/video đã chú thích và bảng CSV kết quả
└── state/               # Cơ sở dữ liệu SQLite lịch sử và tệp settings.json
```

---

## 7. Lưu ý quan trọng về Baseline

> **CẢNH BÁO QUAN TRỌNG:**  
> Phiên bản hiện tại sử dụng mô hình cơ sở YOLO11n gốc (COCO pretrained) nhằm kiểm chứng toàn bộ luồng kỹ thuật end-to-end trên CPU.  
> Mô hình baseline **chưa được fine-tune chuyên biệt cho biển báo Việt Nam**. Do đó, giao diện sẽ luôn hiển thị cảnh báo này và không tự động gán nhãn 82 lớp biển báo cho đến khi hoàn thành kế hoạch huấn luyện ở Giai đoạn 2.
