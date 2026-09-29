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

Hoặc trên macOS, bạn có thể chạy nhanh:
- **Terminal:** `./run_app.sh` (hoặc `./run.sh`)
- **Finder:** Nhấp đúp vào file `run.command` để tự động mở Terminal và chọn tác vụ.

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
- **Phân tích:** Nhận diện ảnh JPG/PNG/WEBP và xử lý tuần tự video MP4/AVI/MOV, hiển thị trực quan và hỗ trợ tải tệp kết quả kèm CSV.
- **Lịch sử:** Tra cứu các phiên phân tích gần đây đã lưu vào SQLite.
- **Thống kê:** Xem tổng số đối tượng và phân bố theo từng loại biển báo.
- **Huấn luyện AI:** Giai đoạn 2 (Quy trình 4 bước: Thu thập dữ liệu -> Kiểm định Quality Gate/EDA -> Huấn luyện nền -> Đóng gói và thăng cấp Candidate).
- **Thông tin mô hình:** Kiểm tra chi tiết manifest, mã băm SHA-256, backend, danh mục 82 lớp biển báo Việt Nam và quản lý sao lưu / hoàn tác (Rollback).
- **Thiết lập:** Điều chỉnh ngưỡng Confidence, IoU (NMS) và giới hạn dung lượng tải lên.

---

## 6. Giai đoạn 2: Quy trình Huấn luyện & Thăng cấp Mô hình Biển báo Việt Nam (Phase 2)

TrafficVision Phase 2 cung cấp quy trình khép kín từ tiền xử lý dữ liệu, kiểm định cổng chất lượng, huấn luyện ngầm, xuất ONNX tối ưu và thăng cấp/hoàn tác nguyên tử (atomic promotion & rollback).

### 6.1. Chuẩn bị bộ dữ liệu (Dataset Ingestion)

Hệ thống hỗ trợ chuẩn dữ liệu YOLO cho 82 lớp biển báo giao thông Việt Nam theo quy chuẩn quốc gia:

1. **Từ Hugging Face:** Tải bộ dữ liệu `star092304/Traffic-sign-detection-VietNam`:
   - Định dạng thư mục yêu cầu:
     ```text
     artifacts/staging/
     ├── train/
     │   ├── images/
     │   └── labels/
     ├── val/
     │   ├── images/
     │   └── labels/
     └── test/
         ├── images/
         └── labels/
     ```
2. **Dữ liệu giả lập (Synthetic Fixture):** Dùng để thử nghiệm nhanh mà không cần tải dữ liệu lớn, có thể tạo qua giao diện Web (tab "Huấn luyện AI") hoặc gọi hàm `create_synthetic_dataset(target_dir, num_samples=100)`.

### 6.2. Kiểm định Quality Gate & Phân tích EDA

Trước khi huấn luyện, toàn bộ dữ liệu phải vượt qua cổng kiểm định nghiêm ngặt nhằm tránh lỗi dữ liệu rác, nhãn hỏng, hoặc rò rỉ dữ liệu giữa các tập:

```bash
python scripts/validate_dataset.py --data-dir artifacts/staging --output-dir artifacts/eda --create-snapshot
```

- **Quy tắc chặn (Blocking Gates):**
  - `CORRUPT_IMAGE`: Ảnh 0 byte hoặc tệp ảnh bị hỏng/không đọc được.
  - `MALFORMED_YOLO_LINE`: Dòng nhãn không đúng 5 giá trị số (`class x y w h`).
  - `CLASS_ID_OUT_OF_RANGE`: Mã lớp nằm ngoài khoảng 0 – 81.
  - `INVALID_COORDINATES`: Tọa độ ngoài `[0, 1]` hoặc chiều rộng/cao `<= 0`.
  - `DATA_LEAKAGE`: Trùng lặp mã băm SHA-256 giữa tập huấn luyện (train) và kiểm định (val/test).
- **Cờ `--output-dir`:** Xuất báo cáo EDA toàn diện `eda_report.json` (phân bố lớp, tỷ lệ khung hình, kích thước bbox COCO small/medium/large).
- **Cờ `--create-snapshot`:** Tạo snapshot bất biến tại `artifacts/snapshots/<snapshot_id>/` kèm file `data.yaml` chuẩn 82 lớp sẵn sàng huấn luyện.

### 6.3. Huấn luyện mô hình YOLO (Training Pipeline)

Bạn có thể chạy huấn luyện qua Web UI hoặc thông qua công cụ dòng lệnh:

```bash
# Huấn luyện thông qua CLI
python scripts/train.py \
  --data-yaml artifacts/snapshots/<snapshot_id>/data.yaml \
  --epochs 50 \
  --batch 4 \
  --imgsz 640 \
  --patience 10 \
  --amp \
  --device cpu
```

- **Tham số hỗ trợ:**
  - `--data-yaml`: Đường dẫn tới tệp `data.yaml` hợp lệ (bắt buộc).
  - `--epochs`: Tổng số epoch huấn luyện (mặc định: 50).
  - `--batch`: Kích thước mini-batch (mặc định: 4).
  - `--imgsz`: Độ phân giải ảnh đầu vào (bội số của 32, mặc định: 640).
  - `--device`: Thiết bị tính toán (`cpu`, `mps`, hoặc chỉ số GPU CUDA).
  - `--no-wait`: Chạy tiến trình nền ngầm và thoát ngay lập tức.
  - Tiến trình ghi nhật ký chi tiết vào `artifacts/runs/<run_id>/train.log` và hỗ trợ phím ngắt `Ctrl+C` dừng an toàn.

### 6.4. Đóng gói Ứng viên & Thăng cấp / Hoàn tác (Promotion & Rollback)

Sau khi huấn luyện thành công:
1. Mô hình được đánh giá độc lập trên tập test (`EvaluationMetrics`).
2. Xuất trọng số sang ONNX (`640x640`, batch 1, CPU), kiểm tra độ sai lệch số học tối đa (`max_abs_diff <= 1e-3`) và đo đạc tốc độ CPU FPS / Latency.
3. Đóng gói ứng viên (Candidate) hoàn chỉnh tại `artifacts/runs/<run_id>/candidate/`.

**Thao tác thăng cấp lên Production:**
```bash
# Thăng cấp candidate lên production (tự động tạo backup an toàn)
python scripts/promote_model.py --candidate-dir artifacts/runs/<run_id>/candidate
```

**Xem lịch sử các bản sao lưu:**
```bash
python scripts/promote_model.py --list-backups
```

**Hoàn tác (Rollback) an toàn:**
```bash
# Hoàn tác về bản sao lưu gần nhất:
python scripts/promote_model.py --rollback

# Hoặc hoàn tác về một bản sao lưu cụ thể:
python scripts/promote_model.py --rollback --backup-id <backup_id>
```

---

## 7. Cấu trúc thư mục Runtime

```text
artifacts/
├── baseline/            # Mô hình pretrained gốc + manifest bất biến
├── production/          # Mô hình ONNX đang phục vụ suy luận hiện tại
├── backups/             # Các bản sao lưu an toàn tự động trước mỗi lần thăng cấp
├── runs/                # Nhật ký, trọng số và ứng viên (candidate) sau mỗi phiên train
├── snapshots/           # Snapshot dữ liệu bất biến kèm data.yaml và manifest
├── staging/             # Thư mục tiếp nhận dữ liệu YOLO đang xử lý
├── outputs/             # Ảnh/video đã chú thích và bảng CSV kết quả
└── state/               # Cơ sở dữ liệu SQLite lịch sử và tệp settings.json
```

---

## 8. Chuyển dịch Trạng thái Mô hình

- **Baseline:** Mô hình ban đầu YOLO11n (COCO 80 lớp), đóng vai trò nền móng kỹ thuật và điểm tựa dự phòng ban đầu.
- **Candidate:** Mô hình sau khi huấn luyện trên tập dữ liệu biển báo Việt Nam 82 lớp, đã qua kiểm tra parity ONNX và benchmark.
- **Production:** Mô hình đang trực tiếp phục vụ các yêu cầu nhận diện ảnh/video trên hệ thống. Khi thăng cấp ứng viên 82 lớp thành công, toàn bộ nhãn nhận dạng trả về tiếng Việt chính xác theo danh mục QCVN.
- **Rollback an toàn:** Bất kỳ sự cố nào xảy ra trong quá trình thăng cấp hoặc vận hành đều có thể được đảo ngược ngay lập tức chỉ với một thao tác CLI hoặc nút bấm trên Web UI.

