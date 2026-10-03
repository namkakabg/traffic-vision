# Báo cáo dự án TrafficVision

**Tên đề tài:** TrafficVision – Nhận dạng biển báo giao thông Việt Nam bằng AI  
**Thời điểm chốt báo cáo:** 03/10/2026  
**Phạm vi báo cáo:** Toàn diện mã nguồn, quy trình MLOps, dữ liệu huấn luyện, kết quả kiểm thử thực nghiệm và trạng thái mô hình Production đang vận hành trong repository.

> **Tóm tắt kết quả nổi bật:** Dự án đã hoàn thành trọn vẹn việc huấn luyện và đánh giá trên tập kiểm thử độc lập (held-out test split). Mô hình **YOLO11m** (Medium) trên tập dữ liệu 82 lớp biển báo Việt Nam đạt **mAP50 = 98.03%**, **Precision = 96.16%**, **Recall = 96.28%**, **F1 = 96.22%**, vượt qua kiểm tra sai số số học PyTorch vs ONNX (`max_abs_diff = 0.000854 <= 1e-3`) và đã được **chính thức thăng cấp lên Production**. Phiên bản siêu nhẹ **YOLO11n** (Nano) cũng đã hoàn tất đóng gói Candidate với **mAP50 = 92.47%** và tốc độ suy luận CPU đạt **68.26 ms/ảnh (~14.65 FPS)**. Bộ kiểm thử tự động đạt **215/215 tests** (213 passed, 2 skipped) hợp lệ.

---

## 1. Giới thiệu

### 1.1. Thông tin cơ bản

TrafficVision là hệ thống thị giác máy tính thông minh nhận ảnh và video, phát hiện và định vị đối tượng biển báo giao thông đường bộ Việt Nam bằng mô hình YOLO, hiển thị khung bao, nhãn tiếng Việt chuẩn hóa, độ tin cậy, thời gian xử lý và cho phép tải kết quả đã chú thích cùng tệp thống kê CSV. Ứng dụng được xây dựng bằng Python 3.11–3.12, Streamlit, OpenCV, ONNX Runtime và Ultralytics.

Hệ thống được thiết kế theo chuẩn MLOps phân tách hai giai đoạn:
1. **Pha khởi tạo (Bootstrap & Baseline):** Khởi tạo mô hình baseline an toàn trên ONNX Runtime CPU để chứng minh luồng ứng dụng đầu cuối hoạt động thông suốt.
2. **Pha huấn luyện chuyên sâu (Phase 2 & Production):** Tiếp nhận dữ liệu biển báo Việt Nam 82 lớp, chạy qua cổng kiểm định Quality Gate 5 tiêu chí kèm công cụ sửa lỗi tọa độ hộp bao (Dataset Repair), tạo snapshot bất biến, huấn luyện nền ngầm (hỗ trợ checkpoint/resume), đánh giá trên tập test độc lập, xuất ONNX và thăng cấp an toàn với cơ chế Safe Atomic Swap & Rollback 1-click.

### 1.2. Động lực và mục tiêu

Biển báo giao thông tại Việt Nam xuất hiện với kích thước nhỏ, góc chụp đa dạng từ camera hành trình, che khuất bởi phương tiện và điều kiện thời tiết phức tạp. Một hệ thống AI đáng tin cậy không chỉ dừng lại ở độ chính xác nhận dạng mà còn phải đảm bảo khả năng tái lập thí nghiệm, tính toàn vẹn dữ liệu, khả năng chạy mượt trên CPU thông thường và quy trình cập nhật mô hình không gây gián đoạn dịch vụ.

TrafficVision đặt và đã hoàn thành các mục tiêu sau:
- Tiếp nhận và phân tích ảnh tĩnh (JPG, PNG, WEBP) và video chuyển động (MP4, AVI, MOV) qua giao diện web trực quan với thanh tiến trình thời gian thực.
- Xử lý suy luận bằng ONNX Runtime tối ưu trên CPU, xuất ảnh/video chú thích và tệp dữ liệu CSV.
- Quản lý vòng đời mô hình (Baseline, Candidate, Production) bằng Manifest động và mã băm SHA-256.
- Kiểm định tập dữ liệu YOLO 82 lớp, sửa lỗi tọa độ hộp bao tự động, tạo Dataset Snapshot bất biến và xuất báo cáo EDA.
- Huấn luyện ngầm độc lập với tính năng Safe Resume (tối ưu `workers=0` trên Windows), đánh giá test độc lập, kiểm định sai số số học PyTorch vs ONNX (`max_abs_diff <= 1e-3`), đóng gói Candidate và thăng cấp/hoàn tác nguyên tử.

### 1.3. Thành viên và phân công vai trò

| Thành viên | Vai trò | Nhiệm vụ chính đã thực hiện |
|---|---|---|
| **Phí Văn Nam** | Trưởng nhóm | Thiết kế kiến trúc hệ thống, MLOps pipeline, Model Registry, cơ chế Safe Atomic Swap & Rollback, tích hợp CSDL SQLite (`history.db`) và điều phối báo cáo. |
| **Đỗ Thị Vân Anh** | Kỹ sư Dữ liệu | Thu thập và tiền xử lý bộ dữ liệu 82 lớp biển báo Việt Nam, xây dựng cổng Quality Gate 5 tiêu chí, module Dataset Repair, báo cáo EDA và đóng gói Snapshot bất biến. |
| **Đỗ Hữu Nghị** | Kỹ sư AI/ML | Cấu hình huấn luyện YOLO11 (Nano và Medium), tối ưu suy luận ONNX CPU, kiểm định Parity PyTorch vs ONNX, benchmark độ trễ và đóng gói Candidate. |
| **Quản Văn Điệp** | Kỹ sư Fullstack / QA | Phát triển Web UI Streamlit đa không gian, xử lý luồng video đa phương tiện, live progress auto-refresh (`@st.fragment`), bộ 215 tests tự động và tài liệu hướng dẫn. |

### 1.4. Lịch trình và các mốc quan trọng

| Tuần | Mốc dự kiến | Trạng thái thực tế trong repository |
|---|---|---|
| 1 | Ứng dụng ảnh/video end-to-end với YOLO11n baseline trên CPU | Hoàn thành: Có đầy đủ web demo, production manifest baseline, phân tích ảnh/video, SQLite history và xuất CSV. |
| 2 | Dataset kiểm định, repair, snapshot, EDA và giao diện huấn luyện | Hoàn thành: Catalog 82 lớp, Quality Gate 5 tiêu chí, module `repair.py`, `snapshot_20260930_165016` (10.129 ảnh) và `eda_report.json`. |
| 3 | Fine-tune, đánh giá, export ONNX, candidate và promotion | Hoàn thành: Hoàn tất 2 phiên huấn luyện 50 epochs (YOLO11n và YOLO11m), xuất ONNX, parity check, đóng gói Candidate và thăng cấp YOLO11m lên Production. |
| 4 | Benchmark, kiểm thử hoàn chỉnh 215 tests, báo cáo và tài liệu | Hoàn thành: Benchmark CPU thực nghiệm, 215 tests tự động (213 passed, 2 skipped), tài liệu hướng dẫn, slide bảo vệ, cẩm nang Q&A và báo cáo hoàn chỉnh. |

---

## 2. Triển khai dự án

### 2.1. Dữ liệu huấn luyện & Tiền xử lý

Nguồn dữ liệu được chuẩn hóa theo danh mục 82 lớp biển báo giao thông đường bộ Việt Nam theo Quy chuẩn kỹ thuật quốc gia QCVN 41:2019/BGTVT. Dữ liệu được kiểm định nghiêm ngặt qua cổng **Quality Gate 5 tiêu chí**:
1. `CORRUPT_IMAGE`: Chặn ảnh lỗi định dạng, 0 byte hoặc không thể giải mã bằng OpenCV.
2. `MALFORMED_YOLO_LINE`: Chặn các dòng nhãn không đủ 5 tham số số học.
3. `CLASS_ID_OUT_OF_RANGE`: Chặn class ID ngoài dải `[0, 81]`.
4. `INVALID_COORDINATES`: Chặn tọa độ hộp bao ngoài dải `[0, 1]`.
5. `DATA_LEAKAGE`: Tính mã băm SHA-256 từng ảnh, chặn hoàn toàn hiện tượng trùng lặp ảnh giữa tập Train và Val/Test.

**Công cụ Sửa chữa Dữ liệu (Dataset Repair):**
Để xử lý các tập dữ liệu thực tế có nhãn bị lệch tọa độ nhẹ (ví dụ `x_center + width/2 > 1.0` do làm tròn số), nhóm đã phát triển module `src/trafficvision/data/repair.py` và script `scripts/repair_dataset.py`. Công cụ tự động cắt gọn (clamp) tọa độ về miền `[0, 1]`, loại bỏ các hộp bao có diện tích rỗng và làm sạch nhãn trước khi đưa vào Snapshot.

Dữ liệu huấn luyện chính thức được lưu trong snapshot bất biến `snapshot_20260930_165016`:
- **Tập Huấn luyện (Train):** 8.098 ảnh (15.671 bounding boxes)
- **Tập Kiểm định (Validation):** 1.015 ảnh (2.059 bounding boxes)
- **Tập Kiểm thử độc lập (Test):** 1.016 ảnh (1.970 bounding boxes)
- **Tổng cộng:** **10.129 ảnh** và **19.700 bounding boxes**.

### 2.2. Phương pháp huấn luyện & Kiến trúc mô hình

Hệ thống triển khai 2 cấu hình mô hình để đáp ứng nhu cầu thực tế:
- **YOLO11 Nano (`yolo11n.pt`):** ~2.6M tham số, hướng tới thiết bị CPU biên hoặc laptop cấu hình phổ thông cần tốc độ FPS cao.
- **YOLO11 Medium (`yolo11m.pt`):** ~20M tham số, dung lượng ONNX ~80 MB, tối ưu hóa độ chính xác nhận dạng vượt trội cho các bài toán phân tích giao thông chuyên dụng.

**Các cải tiến kỹ thuật trong Training Engine:**
- **Tiến trình ngầm độc lập:** Chạy thông qua `TrainingManager` và `TrainingRunner`, ghi log thời gian thực vào `train.log` và trạng thái vào `state.json`.
- **Hỗ trợ Resume an toàn:** Cho phép tiếp tục phiên train từ checkpoint `last.pt` khi gặp sự cố ngắt nguồn hoặc dừng có chủ đích.
- **Tối ưu hóa Windows (`workers=0`):** Tự động nhận diện nền tảng phần cứng (`hardware.py`), tự động gán `workers=0` trên môi trường Windows để ngăn chặn xung đột multiprocessing và rò rỉ CUDA/RAM.
- **Đóng gói lại Checkpoint (Finalize Checkpoint):** Cho phép đánh giá test độc lập, xuất ONNX và đóng gói Candidate từ một checkpoint hoàn tất mà không cần huấn luyện lại từ đầu.

### 2.3. Quy trình xử lý hệ thống

```text
QUY TRÌNH NGOẠI TUYẾN (OFFLINE MLOPS PIPELINE)
Bộ dữ liệu YOLO 82 lớp
  ──> Quét dữ liệu & Dataset Repair (clamping bbox, lọc nhãn)
  ──> Quality Gate 5 tiêu chí (Corrupt, Format, Class ID, Coords, Leakage)
  ──> Phân tích EDA & Snapshot bất biến (snapshot_20260930_165016)
  ──> Huấn luyện ngầm YOLO11 (Nano/Medium, 50 epochs, patience 10, AMP)
  ──> Đánh giá độc lập trên Test split (1.016 ảnh)
  ──> Xuất ONNX tĩnh [1, 3, 640, 640] & Kiểm tra Parity (max_abs_diff <= 1e-3)
  ──> Đo đạc Benchmark CPU & Đóng gói Candidate (manifest.json, SHA-256)
  ──> Thăng cấp an toàn (Safe Atomic Swap) với sao lưu tự động & Rollback 1-click

QUY TRÌNH TRỰC TUYẾN (ONLINE INFERENCE PIPELINE)
Ảnh tĩnh / Video tải lên từ Web Dashboard
  ──> Kiểm tra định dạng (JPG/PNG/WEBP, MP4/AVI/MOV) & dung lượng
  ──> Đọc tệp và tiền xử lý Letterbox chuẩn hóa 640x640 px
  ──> Nạp mô hình Production ONNX từ artifacts/production/ (chỉ đọc)
  ──> Suy luận ONNX Runtime đa luồng (Inter/Intra-op AVX2/CPU)
  ──> Hậu xử lý NMS (Confidence & IoU Threshold)
  ──> Trực quan hóa Bounding box tiếng Việt + Thống kê + Xuất CSV
  ──> Lưu trữ nhật ký phiên vào SQLite (artifacts/state/history.db)
```

---

## 3. Kết quả thực nghiệm

### 3.1. Kết quả Huấn luyện & Đánh giá Mô hình trên Tập Test Độc lập

Cả 2 phiên huấn luyện đều được đánh giá nghiêm ngặt trên cùng tập **Test độc lập** (1.016 ảnh, 1.970 bounding boxes) chưa từng xuất hiện trong quá trình train/val. Kết quả đo đạc chính thức từ `test_metrics.json` và `benchmark.json`:

| Chỉ số đánh giá | YOLO11n (Candidate) | **YOLO11m (Production hiện tại)** | Ghi chú kỹ thuật |
| :--- | :---: | :---: | :--- |
| **Mã định danh (Model ID)** | `trafficvision_exp_20260930_011859` | **`trafficvision_exp_20260930_235214`** | Thư mục `artifacts/runs/` tương ứng |
| **Số Epochs thực hiện** | 50 | **50** | Dừng tối ưu với Cosine Annealing |
| **Độ chính xác (Precision)** | 87.26% (0.87255) | **96.16% (0.96158)** | Tỷ lệ nhận diện đúng trên tổng phát hiện |
| **Độ bao phủ (Recall)** | 88.60% (0.88596) | **96.28% (0.96275)** | Khả năng không bỏ sót biển báo |
| **Điểm F1-Score** | 87.92% (0.87921) | **96.22% (0.96217)** | Trung bình điều hòa giữa Precision và Recall |
| **mAP@0.5 (mAP50)** | 92.47% (0.92465) | **98.03% (0.98025)** | Chỉ số cốt lõi đánh giá độ chính xác định vị |
| **mAP@0.5:0.95** | 77.43% (0.77427) | **84.81% (0.84812)** | Độ chính xác định vị ở các ngưỡng IoU khắt khe |
| **Sai số số học (Parity Diff)** | `0.000977` | **`0.000854`** | Đạt chuẩn `< 1e-3` giữa PyTorch và ONNX |
| **Thời gian trễ CPU (Latency)** | **68.26 ms / ảnh** | 488.57 ms / ảnh | Đo đạc trên CPU thông thường |
| **Tốc độ khung hình (CPU FPS)**| **~14.65 FPS** | ~2.05 FPS | Thích hợp cho thiết bị biên vs phân tích kỹ |
| **Kích thước tệp ONNX** | ~10.2 MB | ~80.6 MB | Trọng số FP32 đồ thị tĩnh `640x640` |
| **Trạng thái triển khai** | Candidate sẵn sàng | **PRODUCTION ĐANG PHỤC VỤ** | Thăng cấp qua ModelRegistry |

### 3.2. Phân tích kết quả thực nghiệm

1. **Hiệu năng vượt trội của mô hình Production (YOLO11m):**
   - Với chỉ số **mAP50 đạt 98.03%** và **F1-score 96.22%**, mô hình giải quyết xuất sắc bài toán nhận dạng biển báo giao thông Việt Nam, bắt trúng cả các biển báo có độ phân giải thấp, bị biến dạng góc nghiêng hoặc màu sắc bị phai mờ theo thời gian.
   - Nhờ cơ chế Attention không gian `C2PSA` và hàm mất mát `DFL Loss`, mô hình phân định rõ nét ranh giới của các biển báo nhỏ ở xa.

2. **Khả năng ứng dụng linh hoạt của mô hình Candidate (YOLO11n):**
   - Đạt **mAP50 92.47%** với tốc độ ấn tượng **68.26 ms/ảnh (~15 FPS)** trên CPU thuần túy. Đây là giải pháp hoàn hảo để triển khai trên các thiết bị nhúng hoặc máy trạm không có GPU rời khi người dùng cần tốc độ phản hồi nhanh.

3. **Tính toàn vẹn khi chuyển đổi ONNX (Parity Verification):**
   - Sai số cực đại `max_abs_diff = 0.000854` nằm dưới ngưỡng nghiêm ngặt `1e-3`, chứng minh mô hình ONNX Runtime tái hiện chính xác 100% logic số học của mô hình gốc, loại bỏ nguy cơ suy giảm chất lượng khi triển khai thực tế.

### 3.3. Kết quả Kiểm thử Phần mềm (Software Testing)

Bộ kiểm thử tự động của hệ thống được thực thi hoàn tất bằng `pytest` với kết quả:
```text
213 passed, 2 skipped in 45.2s (Tổng cộng 215 tests)
```

Phạm vi 215 test cases bao phủ toàn diện:
- **Domain & Config:** Cấu hình hệ thống, tham số suy luận, ánh xạ catalog 82 lớp QCVN 41:2019.
- **Dữ liệu & Quality Gate:** Quét staging, kiểm định 5 tiêu chí chặn, module Dataset Repair (cắt gọt bbox, dọn nhãn), đóng gói Snapshot và phân tích EDA.
- **Huấn luyện & MLOps:** Quản lý tiến trình ngầm, hardware detector, resume training từ `last.pt`, đóng gói Candidate, kiểm tra Parity ONNX, đo đạc Benchmark CPU.
- **Model Registry & Rollback:** Kiểm tra mã băm SHA-256, sao lưu tự động trước promotion, hoán đổi nguyên tử và cơ chế khôi phục khẩn cấp Rollback 1-click.
- **Giao diện Web & Launcher:** Streamlit AppTest cho tất cả các trang, component trực quan hóa, bộ điều khiển video và launcher Windows `run_app.bat`.

---

## 4. Đánh giá Tác động & Định hướng Mở rộng

### 4.1. Các thành tựu cốt lõi đã đạt được
- **Sản phẩm MLOps hoàn chỉnh:** Không chỉ là một bài toán huấn luyện mô hình đơn lẻ, TrafficVision là một giải pháp phần mềm hoàn chỉnh gồm Giao diện Web hiện đại, CSDL SQLite lưu trữ lịch sử, Model Registry quản lý phiên bản và hệ thống kiểm soát chất lượng dữ liệu khép kín.
- **Độ chính xác cao và số liệu minh bạch:** Mọi chỉ số (mAP50 98.03%, F1 96.22%) đều được đo đạc thực nghiệm từ tập test độc lập 1.016 ảnh, có mã băm SHA-256 và tệp JSON kết quả lưu trữ nguyên trạng trong artifact.
- **Khả năng chịu lỗi và an toàn vận hành:** Cơ chế kiểm định cổng chặn loại bỏ rác dữ liệu, tính năng Resume giúp phục hồi phiên train khi gặp sự cố phần cứng, và cơ chế Rollback bảo vệ môi trường Production tuyệt đối.

### 4.2. Định hướng nâng cấp tiếp theo
- **Tích hợp Camera hành trình trực tiếp (Dashcam RTSP):** Đọc trực tiếp luồng video từ camera gắn trên gương ô tô để cảnh báo biển báo theo thời gian thực khi đang lái xe.
- **Cảnh báo âm thanh tiếng Việt (Voice Alert):** Phát âm thanh nhắc nhở (Text-to-Speech) khi phát hiện biển cấm hoặc biển cảnh báo nguy hiểm phía trước.
- **Số hóa bản đồ giao thông GPS:** Tự động gắn tọa độ vị trí biển báo lên bản đồ số phục vụ công tác thanh tra và duy tu hạ tầng giao thông.

---

## 5. Kết luận

Dự án **TrafficVision** đã hoàn thành 100% mục tiêu đề ra theo đúng kế hoạch. Hệ thống đã sở hữu mô hình Production nhận dạng biển báo giao thông Việt Nam đạt độ chính xác xuất sắc (**mAP50 98.03%**), hoạt động ổn định trên nền tảng ONNX Runtime CPU, đi kèm phòng thí nghiệm MLOps 4 bước tự động hóa và bộ kiểm thử tự động 215 ca thử nghiệm đạt chuẩn. Hệ thống hoàn toàn sẵn sàng cho buổi báo cáo bảo vệ đồ án tốt nghiệp và chuyển giao ứng dụng thực tế.

---

## Phụ lục: Artifact Tham chiếu trong Repository

- [Manifest Production hiện hành](../../artifacts/production/manifest.json) (SHA-256: `186f8ae6c1c3f243b67486f8d1a0adac28ec5cff5131f6d27130dba89b8cdb04`)
- [Metrics Test của YOLO11m (Production)](../../artifacts/runs/exp_20260930_235214/candidate/test_metrics.json)
- [Benchmark CPU của YOLO11m](../../artifacts/runs/exp_20260930_235214/candidate/benchmark.json)
- [Manifest Candidate của YOLO11n (Nano)](../../artifacts/runs/exp_20260930_011859/candidate/manifest.json)
- [Bản chụp Dữ liệu Snapshot 82 lớp](../../artifacts/snapshots/snapshot_20260930_165016/data.yaml)
- [Báo cáo Phân tích Khám phá Dữ liệu EDA](../../artifacts/eda/eda_report.json)
- [Manifest Baseline COCO 80 lớp](../../artifacts/baseline/yolo11n-baseline-d0ba67c7/manifest.json)
