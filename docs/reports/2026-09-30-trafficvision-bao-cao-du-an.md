# Báo cáo dự án TrafficVision

**Tên đề tài:** TrafficVision – Nhận dạng biển báo giao thông bằng AI  
**Thời điểm chốt báo cáo:** 30/09/2026  
**Phạm vi báo cáo:** Trạng thái mã nguồn, artifact và kiểm thử đang có trong repository.

> **Lưu ý về tính trung thực của số liệu:** Hệ thống hiện đang phục vụ bằng YOLO11n baseline 80 lớp COCO. Chưa có candidate 82 lớp, checkpoint hoàn chỉnh, metrics test hoặc benchmark CPU của mô hình đã fine-tune. Vì vậy các chỉ số Precision, Recall, F1, mAP và FPS của mô hình biển báo Việt Nam được ghi là **Chưa có số liệu**, không dùng số minh họa.

## 1. Giới thiệu

### 1.1. Thông tin cơ bản

TrafficVision là hệ thống thị giác máy tính nhận ảnh và video, phát hiện đối tượng bằng mô hình YOLO, hiển thị khung bao, nhãn, độ tin cậy, thời gian xử lý và cho tải kết quả đã chú thích cùng tệp CSV. Ứng dụng được xây dựng bằng Python, Streamlit, OpenCV, ONNX Runtime và Ultralytics; mã nguồn yêu cầu Python 3.11–3.13.

Mục tiêu sản phẩm gồm hai pha. Pha baseline xác nhận luồng ứng dụng đầu cuối với YOLO11n ONNX trên CPU. Pha tiếp theo kiểm định dữ liệu biển báo Việt Nam 82 lớp, fine-tune, đánh giá độc lập, xuất ONNX, đóng gói candidate và chỉ thăng cấp khi đạt điều kiện kiểm tra.

### 1.2. Động lực và mục tiêu

Biển báo giao thông xuất hiện với kích thước nhỏ, góc nhìn đa dạng, che khuất và điều kiện ánh sáng khác nhau. Một hệ thống demo đáng tin cậy cần nhiều hơn một lần gọi mô hình: dữ liệu phải được kiểm định, các run cần tái lập, mô hình đang phục vụ không bị ghi đè khi huấn luyện, và kết quả suy luận cần được lưu lại để kiểm tra.

TrafficVision đặt các mục tiêu sau:

- Nhận ảnh JPG/PNG/WEBP và video MP4/AVI/MOV từ giao diện web.
- Xử lý suy luận ONNX trên CPU, tạo ảnh/video chú thích và CSV phát hiện.
- Quản lý vòng đời baseline, candidate và production bằng manifest cùng checksum SHA-256.
- Kiểm định dữ liệu YOLO 82 lớp, lập snapshot bất biến và sinh EDA trước huấn luyện.
- Huấn luyện nền, đánh giá trên tập test, kiểm tra parity ONNX, benchmark CPU và thăng cấp/hoàn tác mô hình an toàn.

### 1.3. Thành viên và phân công vai trò

| Thành viên | Vai trò theo đặc tả |
|---|---|
| Phí Văn Nam | Trưởng nhóm; kiến trúc, tích hợp hệ thống, quản lý tiến độ và điều phối báo cáo. |
| Đỗ Thị Vân Anh | Thu thập/kiểm định dữ liệu, tiền xử lý và EDA. |
| Đỗ Hữu Nghị | Huấn luyện, đánh giá, phân tích lỗi và tối ưu/xuất mô hình. |
| Quản Văn Điệp | Giao diện web, luồng suy luận, kiểm thử và tài liệu sử dụng. |

Các thành viên cùng review dữ liệu, kịch bản demo và báo cáo để tránh phụ thuộc vào một cá nhân ở từng mô-đun.

### 1.4. Lịch trình và các mốc quan trọng

Lộ trình đã đặt ra gồm bốn tuần:

| Tuần | Mốc dự kiến | Trạng thái theo repository hiện tại |
|---|---|---|
| 1 | Ứng dụng ảnh/video end-to-end với YOLO11n baseline trên CPU | Đã có mã nguồn, production manifest baseline và 28 cặp ảnh chú thích/CSV. |
| 2 | Dataset kiểm định, snapshot, EDA và giao diện huấn luyện | Đã có catalog 82 lớp, validator, 3 snapshot và `eda_report.json`. |
| 3 | Fine-tune, đánh giá, export ONNX, candidate và promotion | Pipeline đã có mã nguồn và test; artifact chưa có candidate hay metrics từ run hoàn tất. |
| 4 | Benchmark, kiểm thử hoàn chỉnh, báo cáo và demo | 170 test tự động đã qua; benchmark thực và số liệu mô hình 82 lớp còn thiếu. |

## 2. Triển khai dự án

### 2.1. Thu thập dữ liệu

Đặc tả chọn bộ Traffic-sign-detection-VietNam ở định dạng YOLO, 82 lớp, làm nguồn dữ liệu mục tiêu. Trong repository hiện có dữ liệu staging và snapshot mới nhất `snapshot_20260929_160025`, tạo lúc `2026-09-29T16:00:31Z`, dùng seed 42. Snapshot lưu 20.279 checksum cho 10.139 ảnh và 19.722 nhãn, vì vậy có thể truy vết chính xác tập dữ liệu đã dùng cho lần huấn luyện tương ứng.

Trình kiểm định kiểm tra ảnh hỏng, nhãn YOLO sai cấu trúc, class ID ngoài 0–81, tọa độ không hợp lệ và ảnh trùng giữa các split. Các lỗi này là lỗi chặn. Lớp ít mẫu, mất cân bằng lớp và bounding box rất nhỏ là cảnh báo để người dùng cân nhắc trước khi chạy train.

### 2.2. Phương pháp huấn luyện

Mô hình nền là `yolo11n.pt`; cấu hình hai lần chạy đã lưu gồm ảnh đầu vào 640 px, batch 4, tối đa 50 epoch, patience 10, AMP bật, seed 42 và thiết bị CPU. Training runner chạy ở tiến trình riêng, ghi `run_config.json`, `state.json`, log và checkpoint để giao diện có thể theo dõi/dừng an toàn.

Sau khi run hoàn thành, pipeline dự kiến thực hiện theo thứ tự: đánh giá checkpoint trên test, xuất ONNX tĩnh batch 1, kiểm tra sai khác số học tối đa không vượt `1e-3`, benchmark CPU, đóng gói candidate gồm manifest/benchmark/test metrics, rồi mới promotion. Registry chỉ chấp nhận candidate có checksum hợp lệ, model ONNX hợp lệ và đúng 82 tên lớp; trước promotion, production hiện tại được backup. Nếu bước xác minh sau promotion lỗi, registry khôi phục backup.

### 2.3. Quy trình xử lý hệ thống

```text
QUY TRÌNH NGOẠI TUYẾN
Dataset YOLO 82 lớp
  -> quét dữ liệu + quality gate
  -> EDA + snapshot bất biến
  -> train YOLO11n trong tiến trình nền
  -> đánh giá trên test + export/parity ONNX + benchmark CPU
  -> candidate 82 lớp
  -> backup + promotion nguyên tử hoặc rollback

QUY TRÌNH TRỰC TUYẾN
Ảnh/video tải lên
  -> kiểm tra định dạng và dung lượng
  -> giải mã ảnh / đọc tuần tự từng frame video
  -> production ONNX predictor
  -> lọc theo confidence, IoU/NMS
  -> ảnh/video chú thích + CSV + lịch sử SQLite
```

Trong hai quy trình, ứng dụng chỉ đọc mô hình production. Huấn luyện không thay thế mô hình đang phục vụ; điều này bảo vệ luồng demo trước một run lỗi hoặc một candidate chưa đạt yêu cầu.

### 2.4. Sơ đồ hệ thống

```text
Streamlit UI
├── Phân tích ────────> AnalysisService ───> ModelRegistry ───> ONNX predictor
│                       │                         │                 │
│                       │                         │                 └── detections
│                       │                         └── production manifest + SHA-256
│                       └── SQLite history, ảnh/video chú thích, CSV
│
└── Huấn luyện AI ───> Dataset scanner / Validator / EDA / Snapshot
                         │
                         └── TrainingManager ───> evaluator / exporter / candidate
                                                        │
                                                        └── Registry promotion / backup / rollback
```

## 3. Kết quả

### 3.1. Tiền xử lý dữ liệu

Snapshot mới nhất chia dữ liệu thành 8.131 ảnh train, 1.001 ảnh validation và 1.007 ảnh test. Tổng số ảnh trong artifact thực tế là 10.139, khác với con số nguồn được nêu ban đầu trong đặc tả; báo cáo này dùng số đo từ artifact thay vì số mô tả ban đầu.

| Split | Ảnh | Bounding box |
|---|---:|---:|
| Train | 8.131 | 15.733 |
| Validation | 1.001 | 2.036 |
| Test | 1.007 | 1.953 |
| **Tổng** | **10.139** | **19.722** |

EDA không ghi nhận bất thường khi đọc dữ liệu (`anomalies = 0`). Log của run gần nhất cũng quét được 8.131 ảnh train và 1.001 ảnh validation với 0 ảnh corrupt. Tuy vậy, `ValidationReport` đầy đủ cho dữ liệu staging chưa được lưu thành artifact độc lập, nên không thể từ artifact hiện có khẳng định số lỗi chặn/cảnh báo của lần kiểm định cuối. Cần xuất và lưu báo cáo này ở lần chạy tiếp theo.

### 3.2. Phân tích dữ liệu khám phá (EDA)

EDA bao phủ đủ 82 class ID, với số instance theo lớp dao động từ 32 đến 1.446, tỷ lệ lớn nhất/nhỏ nhất là 45,19:1. Đây là mất cân bằng đáng kể, và theo quy tắc quality gate của dự án phải được xem là cảnh báo thay vì bị bỏ qua.

| Nhóm kích thước box theo ngưỡng COCO | Số lượng | Tỷ lệ |
|---|---:|---:|
| Nhỏ | 9.479 | 48,06% |
| Trung bình | 7.069 | 35,84% |
| Lớn | 3.174 | 16,09% |

Box nhỏ chiếm gần một nửa dữ liệu, phù hợp với khó khăn thực tế khi nhận dạng biển báo từ xa. Kích thước normalized trung vị của box là 0,0483 theo chiều rộng và 0,0563 theo chiều cao; vì vậy cần theo dõi riêng Recall/AP của các lớp ít mẫu và các biển nhỏ khi có model candidate.

### 3.3. Xây dựng mô hình

| Hạng mục | Trạng thái và bằng chứng |
|---|---|
| Baseline | `yolo11n-baseline-2db7a993`, ONNX, input 640, 80 lớp COCO, SHA-256 `2db7a993…1f84e9f7`. |
| Production hiện tại | Trỏ tới chính baseline trên, checksum và kích thước tệp 10.701.976 byte khớp baseline. |
| Candidate 82 lớp | Chưa có thư mục candidate, `test_metrics.json` hay `benchmark.json`. |
| Metrics Precision/Recall/F1/mAP | **Chưa có số liệu** từ run mô hình biển báo Việt Nam hoàn tất. |
| Benchmark CPU macOS/Windows | **Chưa có số liệu**. |

Đã có hai run thực tế. `exp_20260929_221643` có trạng thái `failed` trước epoch đầu tiên, với thông báo “Process terminated unexpectedly”. `exp_20260929_230031` ghi cấu hình đúng 82 lớp và đã khởi động epoch 1, nhưng state vẫn là `running` trong khi PID 63651 không còn tồn tại; log dừng ở batch 43/2.033 của epoch 1. Đây là state cũ, không phải một run đang chạy. Không có checkpoint `best.pt`/`last.pt` hoặc metrics để đánh giá, do đó không đủ điều kiện đóng gói hay promotion.

### 3.4. Giao diện người dùng

Giao diện Streamlit có sáu khu vực: Phân tích, Huấn luyện AI, Lịch sử, Thống kê, Thông tin mô hình và Thiết lập. Trang Phân tích nhận ảnh/video, hiển thị cảnh báo khi production còn là baseline, tạo kết quả chú thích và CSV. Các artifact hiện có gồm 28 ảnh chú thích và 28 CSV phát hiện; chưa có video output thực được lưu trong `artifacts/outputs`.

Trang Huấn luyện AI tổ chức luồng bốn bước: chuẩn bị dữ liệu, kiểm định/EDA, điều khiển train và đánh giá–promotion. Trang Thông tin mô hình đọc manifest động, cho kiểm tra checksum, lịch sử backup và rollback. Thiết lập runtime lưu ngưỡng confidence, IoU/NMS và giới hạn dung lượng tải lên; lịch sử phân tích được lưu bằng SQLite.

### 3.5. Kiểm thử và cải tiến

Tại thời điểm chốt báo cáo, lệnh dưới đây hoàn thành thành công với **170 test**:

```bash
.venv/bin/python -m pytest -q --disable-warnings --maxfail=1
```

Phạm vi test gồm catalog 82 lớp, quét/kiểm định/snapshot/EDA, suy luận ảnh và video, rendering/CSV, registry checksum/promotion/rollback, training state/runner/evaluator/exporter, UI Streamlit và hai luồng integration baseline/Phase 2. Các test integration Phase 2 dùng dữ liệu và ONNX tối thiểu mô phỏng để xác nhận logic của luồng end-to-end; chúng không thay thế đánh giá mô hình thật trên tập test.

Cải tiến ưu tiên trước khi báo cáo kết quả mô hình:

1. Khắc phục nguyên nhân tiến trình train kết thúc và cập nhật state từ `running` sang `failed`/`stopped` khi PID không còn sống.
2. Chạy lại fine-tune đến khi có `best.pt`, đánh giá test độc lập và candidate 82 lớp.
3. Lưu `ValidationReport`, metrics test, parity ONNX, benchmark CPU và version môi trường cùng run.
4. Đánh giá theo lớp, nhất là 32–1.446 instance/lớp và 48,06% box nhỏ; cân nhắc augmentation hoặc chiến lược lấy mẫu phù hợp.
5. Chạy benchmark trên macOS và Windows, đồng thời thử video thực để bổ sung bằng chứng vận hành ngoài unit test.

## 4. Projected Impact

### 4.1. Accomplishments and Benefits

TrafficVision đã có một nền tảng ứng dụng có thể kiểm chứng thay vì chỉ là notebook huấn luyện. Luồng baseline cho phép demo upload ảnh, phát hiện, chú thích, tải CSV và lưu lịch sử. Thiết kế manifest động giúp UI không cần hard-code danh sách lớp, nên có thể chuyển từ baseline COCO sang candidate 82 lớp mà không phải viết lại trang Phân tích.

Về vận hành, snapshot checksum tạo dấu vết tái lập cho dữ liệu; registry có xác minh checksum, backup, promotion nguyên tử và rollback. Những cơ chế này giảm rủi ro một lần huấn luyện lỗi làm gián đoạn mô hình production. Bộ test 170 trường hợp tạo lưới an toàn cho việc tiếp tục hoàn thiện pipeline.

### 4.2. Future Improvements

- Hoàn tất một run 82 lớp có metric test thật và chỉ promotion khi parity, checksum, class count và benchmark đều đạt.
- Bổ sung persistence cho quality-gate report, events theo epoch và trạng thái tiến trình để giao diện không hiển thị run chết là `running`.
- So sánh các cấu hình image size, batch, augmentation và thiết bị CPU/MPS/CUDA bằng cùng snapshot, rồi báo cáo trade-off accuracy–latency.
- Tạo phân tích lỗi FP/FN theo từng biển báo, khoảng cách/kích thước box và điều kiện ánh sáng.
- Bổ sung video thực, kiểm thử codec trên macOS/Windows và kịch bản UAT upload tệp lỗi, video dài, reload trang trong lúc train và rollback production.

## 5. Kết luận

TrafficVision đã hoàn thành phần nền tảng quan trọng: web demo, suy luận ONNX baseline, quản lý model an toàn, quality gate, EDA, snapshot, training pipeline và test tự động. Dự án sẵn sàng trình diễn luồng baseline và tiếp tục fine-tune trên dữ liệu biển báo Việt Nam.

Tuy nhiên, hệ thống **chưa sẵn sàng để tuyên bố hiệu năng nhận dạng 82 lớp biển báo Việt Nam**. Chưa có candidate, metric test, benchmark CPU hay promotion thực tế; một run thất bại và run còn lại có state stale. Mốc tiếp theo cần là hoàn tất một run có artifact đầy đủ, đánh giá bằng tập test độc lập, sau đó cập nhật báo cáo này bằng số liệu và biểu đồ sinh trực tiếp từ run đó.

## Phụ lục: Artifact tham chiếu

- [Đặc tả thiết kế](../superpowers/specs/2026-09-27-trafficvision-design.md)
- [Báo cáo EDA](../../artifacts/eda/eda_report.json)
- [Snapshot mới nhất](../../artifacts/snapshots/snapshot_20260929_160025/snapshot_manifest.json)
- [Manifest baseline](../../artifacts/baseline/yolo11n-baseline-2db7a993/manifest.json)
- [Manifest production](../../artifacts/production/manifest.json)
- [Trạng thái run 1](../../artifacts/runs/exp_20260929_221643/state.json)
- [Trạng thái run 2](../../artifacts/runs/exp_20260929_230031/state.json)
