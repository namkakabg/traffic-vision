# TrafficVision Phase 2: Dataset, Training and 82-Class Promotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Triển khai toàn bộ Giai đoạn 2 của TrafficVision: danh mục 82 lớp biển báo Việt Nam, nạp và kiểm định dữ liệu (Quality Gate), phân tích EDA, tiến trình huấn luyện YOLO11n ngầm độc lập với web, đánh giá tập test và xuất ONNX, quản lý candidate/promotion/rollback an toàn, và giao diện Web Huấn luyện AI 4 bước hoàn chỉnh.

**Architecture:** Tách biệt hoàn toàn giữa luồng Dữ liệu (`trafficvision.data`), Huấn luyện (`trafficvision.training`), Registry (`trafficvision.registry`) và Web UI (`trafficvision.ui.pages.training`). Tiến trình huấn luyện chạy dưới dạng subprocess riêng biệt ghi trạng thái ra đĩa (`events.jsonl`, `state.json`) để reload/đóng tab web không làm gián đoạn job. Quá trình thăng cấp (promotion) mô hình 82 lớp lên production luôn tự động sao lưu production cũ, thực hiện thay thế nguyên tử và hỗ trợ rollback.

**Tech Stack:** Python 3.11, Ultralytics YOLO11n, PyTorch, ONNX, ONNX Runtime CPU, Streamlit, OpenCV, Pillow, Pydantic 2, pandas, PyYAML, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-09-27-trafficvision-design.md`

## Global Constraints

- Mô-đun dữ liệu và huấn luyện không được phụ thuộc trực tiếp vào trạng thái giao diện Streamlit; toàn bộ có thể chạy độc lập qua CLI hoặc Web.
- Bộ danh mục 82 lớp biển báo Việt Nam (ID 0–81) phải có tên tiếng Việt chuẩn hóa, mã biển và nhóm biển báo theo quy chuẩn QCVN 41:2019/BGTVT.
- Quality Gate phải phân định rõ ràng giữa Lỗi chặn (blocking errors: ảnh hỏng, nhãn sai cấu trúc, class ID ngoài 0–81, box sai tọa độ, rò rỉ trùng lặp giữa các tập) và Cảnh báo (warnings: mất cân bằng lớp, box nhỏ, lớp ít mẫu). Lỗi chặn bắt buộc phải khóa nút huấn luyện.
- Mỗi lần huấn luyện gắn với một Snapshot bất biến lưu manifest, checksum, class mapping, seed, cấu hình chia tập và tệp `data.yaml`.
- Huấn luyện chạy ở tiến trình nền (subprocess) độc lập với vòng đời render của Streamlit.
- Cấu hình mặc định: kích thước ảnh 640 px, batch 4 cho máy GTX 1050 Ti 4 GB hoặc CPU, tối đa 50 epoch, patience 10, mixed precision (AMP) khi có CUDA.
- Checkpoint `best.pt` được xuất sang ONNX với backend CPU, batch 1, `imgsz=640`. Đầu ra ONNX phải vượt qua parity test so sánh với PyTorch trong dung sai sai số <= 1e-3.
- Quá trình Promotion candidate thành production phải: kiểm tra checksum, smoke test, kiểm tra 82 lớp, tự động sao lưu production hiện tại vào `artifacts/backups/<timestamp>_<model_id>/`, và thay thế nguyên tử. Hỗ trợ rollback về backup gần nhất khi cần.
- Tất cả unit test và integration test phải chạy nhanh bằng fixture dữ liệu mẫu tổng hợp (synthetic fixtures) mà không đòi hỏi tải trước hàng chục nghìn ảnh thực tế.
- Mỗi task thực hiện theo TDD (Test-Driven Development) và kết thúc bằng một commit độc lập.

## Review Focus

1. **Dataset format tampering:** Tệp nhãn chứa tọa độ âm, tọa độ > 1, NaN/Inf, hoặc class ID = 82 (ngoài miền 0-81) phải bị Quality Gate chặn ngay lập tức; Task 2 có test tương ứng.
2. **Train/val/test data leakage:** Ảnh trùng lặp chính xác (hoặc gần trùng lặp) giữa tập train và tập val/test phải bị phát hiện và xếp vào lỗi chặn; Task 2 có test tương ứng.
3. **Training process crash recovery:** Nếu tiến trình huấn luyện nền bị kill đột ngột hoặc mất điện, `state.json` và checkpoint `last.pt` phải cho phép phát hiện trạng thái thất bại và tiếp tục huấn luyện (resume); Task 4 có test tương ứng.
4. **ONNX parity divergence:** Candidate ONNX sau khi export có kết quả suy luận sai lệch lớn hơn tolerance cho phép so với checkpoint PyTorch gốc phải bị từ chối trước promotion; Task 5 có test tương ứng.
5. **Promotion failure rollback:** Nếu quá trình thay thế production gặp lỗi ở bước xác minh cuối, hệ thống phải tự động phục hồi về backup trước đó và không để production ở trạng thái hỏng; Task 6 có test tương ứng.

---

## File Map

### Data Pipeline and Catalog
- `src/trafficvision/data/__init__.py`: Package export cho data module.
- `src/trafficvision/data/catalog.py`: Danh mục 82 lớp biển báo giao thông Việt Nam (ID, mã, tên tiếng Việt, nhóm).
- `src/trafficvision/data/dataset.py`: Đọc cấu trúc dataset YOLO, quét các tập train/val/test, hỗ trợ tải từ Hugging Face hoặc đọc thư mục cục bộ.
- `src/trafficvision/data/validator.py`: Quality Gate kiểm định dữ liệu (blocking errors vs warnings).
- `src/trafficvision/data/snapshot.py`: Tạo snapshot bất biến kèm manifest, checksum và sinh `data.yaml`.
- `src/trafficvision/data/eda.py`: Phân tích thống kê khám phá dữ liệu (EDA), phân bố lớp, kích thước box, sinh báo cáo JSON và biểu đồ.
- `tests/fixtures/dataset_fixture.py`: Helper sinh fixture dataset nhỏ hợp lệ và không hợp lệ phục vụ kiểm thử.
- `tests/data/test_catalog.py`: Kiểm thử danh mục 82 lớp.
- `tests/data/test_dataset.py`: Kiểm thử đọc và quét dataset.
- `tests/data/test_validator.py`: Kiểm thử các quy tắc kiểm định Quality Gate.
- `tests/data/test_snapshot.py`: Kiểm thử tạo snapshot và `data.yaml`.
- `tests/data/test_eda.py`: Kiểm thử sinh báo cáo EDA.

### Training Engine and Evaluation
- `src/trafficvision/training/__init__.py`: Package export cho training module.
- `src/trafficvision/training/config.py`: Pydantic model cho cấu hình huấn luyện `TrainingConfig`.
- `src/trafficvision/training/state.py`: Model trạng thái `TrainingState` và nhật ký sự kiện `TrainingEvent`.
- `src/trafficvision/training/runner.py`: Subprocess entrypoint cho huấn luyện YOLO11n với callback cập nhật `state.json` và `events.jsonl`.
- `src/trafficvision/training/manager.py`: Điều phối khởi chạy, theo dõi tiến độ, tạm dừng/dừng job nền trong `artifacts/runs/<run_id>/`.
- `src/trafficvision/training/evaluator.py`: Đánh giá checkpoint trên test set (mAP50, mAP50-95, P, R, F1, confusion matrix).
- `src/trafficvision/training/exporter.py`: Xuất ONNX CPU, kiểm tra dung sai (parity check) so với PyTorch, benchmark độ trễ CPU.
- `src/trafficvision/training/candidate.py`: Đóng gói candidate model kèm manifest 82 lớp và số liệu đánh giá.
- `tests/training/test_training_config.py`: Kiểm thử cấu hình huấn luyện.
- `tests/training/test_training_state.py`: Kiểm thử chuyển đổi trạng thái và serialization.
- `tests/training/test_training_manager.py`: Kiểm thử quản lý tiến trình nền.
- `tests/training/test_evaluator.py`: Kiểm thử đánh giá mô hình.
- `tests/training/test_exporter.py`: Kiểm thử xuất ONNX và parity check.

### Model Registry Enhancements
- `src/trafficvision/registry.py`: Bổ sung `promote_candidate`, `rollback_to_backup`, `list_backups`.
- `tests/test_promotion_rollback.py`: Kiểm thử promotion nguyên tử, tạo backup và rollback.

### Web Interface & Integration
- `src/trafficvision/ui/pages/training.py`: Giao diện 4 bước (Dữ liệu -> Kiểm định -> Huấn luyện -> Đánh giá & xuất) thay thế placeholder.
- `src/trafficvision/ui/app.py`: Cập nhật routing sang trang training thực tế.
- `src/trafficvision/ui/pages/model_info.py`: Cập nhật hiển thị lịch sử backup và danh sách 82 lớp tiếng Việt khi đã promotion.
- `scripts/validate_dataset.py`: CLI kiểm định dữ liệu và sinh EDA.
- `scripts/train.py`: CLI huấn luyện mô hình.
- `scripts/promote_model.py`: CLI thăng cấp và rollback mô hình.
- `tests/ui/test_training_page.py`: Kiểm thử giao diện huấn luyện.
- `tests/integration/test_phase2_flow.py`: Integration test trọn vẹn luồng Giai đoạn 2.

---

## Task 1: Vietnamese 82-Class Catalogue, Dataset Ingestion & Synthetic Fixtures

**Files:**
- Create: `src/trafficvision/data/__init__.py`
- Create: `src/trafficvision/data/catalog.py`
- Create: `src/trafficvision/data/dataset.py`
- Create: `tests/fixtures/dataset_fixture.py`
- Create: `tests/data/__init__.py`
- Create: `tests/data/test_catalog.py`
- Create: `tests/data/test_dataset.py`

**Interfaces:**
- Consumes: `AppPaths` from `trafficvision.config`.
- Produces:
  - `SignClass(id: int, code: str, name_vi: str, category: str)`
  - `VIETNAM_TRAFFIC_SIGN_CATALOG: list[SignClass]` (chính xác 82 lớp, ID từ 0 đến 81)
  - `get_class_names() -> list[str]` (danh sách 82 tên tiếng Việt có thứ tự index)
  - `DatasetItem(image_path: Path, label_path: Path | None, split: str)`
  - `DatasetSummary(total_images: int, split_counts: dict[str, int], classes_present: set[int])`
  - `scan_yolo_dataset(root_dir: Path) -> list[DatasetItem]`
  - `create_synthetic_dataset(target_dir: Path, num_samples: int = 10, invalid_case: str | None = None) -> Path`

- [ ] **Step 1: Write failing catalog and dataset tests**
Thêm `tests/data/test_catalog.py` kiểm tra danh mục gồm đúng 82 phần tử, ID liên tục từ 0 đến 81, tên tiếng Việt không rỗng, và không trùng lặp mã. Thêm `tests/data/test_dataset.py` kiểm tra quét thư mục YOLO (chứa `train/images`, `train/labels`, `val/images`, `val/labels`, `test/images`, `test/labels`) trả về đúng danh sách item và phát hiện ảnh không có nhãn (ảnh nền hợp lệ hoặc thiếu nhãn).

- [ ] **Step 2: Run Task 1 tests and confirm expected failure**
Run: `.venv/bin/python -m pytest tests/data/test_catalog.py tests/data/test_dataset.py -q`
Expected: FAIL do chưa có file mã nguồn trong `src/trafficvision/data/`.

- [ ] **Step 3: Implement catalog and synthetic fixture generator**
Viết `src/trafficvision/data/catalog.py` với đầy đủ 82 lớp biển báo Việt Nam theo chuẩn bộ dữ liệu HF `star092304/Traffic-sign-detection-VietNam`. Viết `tests/fixtures/dataset_fixture.py` sinh các ảnh PNG nhỏ (32x32) và file nhãn TXT tương ứng theo định dạng YOLO chuẩn `class_id x_center y_center width height`.

- [ ] **Step 4: Implement dataset scanner and indexer**
Viết `src/trafficvision/data/dataset.py` quét cấu trúc thư mục YOLO linh hoạt (hỗ trợ cả cấu trúc phẳng `images/train` hoặc cấu trúc nhóm `train/images`), ghép cặp tệp ảnh và nhãn dựa trên phần thân tên tệp.

- [ ] **Step 5: Verify Task 1**
Run: `.venv/bin/python -m pytest tests/data/test_catalog.py tests/data/test_dataset.py -q`
Expected: all Task 1 tests PASS.
Run: `.venv/bin/ruff check src/trafficvision/data tests/data`
Expected: exit code 0.

- [ ] **Step 6: Commit Task 1**
```bash
git add src/trafficvision/data/catalog.py src/trafficvision/data/dataset.py tests/fixtures/dataset_fixture.py tests/data
git commit -m "feat: add Vietnamese 82-class traffic sign catalog and dataset scanner"
```

---

## Task 2: Quality Gate Validator & Immutable Dataset Snapshot

**Files:**
- Create: `src/trafficvision/data/validator.py`
- Create: `src/trafficvision/data/snapshot.py`
- Create: `tests/data/test_validator.py`
- Create: `tests/data/test_snapshot.py`

**Interfaces:**
- Consumes: `DatasetItem`, `VIETNAM_TRAFFIC_SIGN_CATALOG` from Task 1.
- Produces:
  - `ValidationErrorItem(level: Literal["blocking", "warning"], code: str, message: str, file_path: Path | None = None)`
  - `ValidationReport(is_valid: bool, has_blocking: bool, blocking_errors: list[ValidationErrorItem], warnings: list[ValidationErrorItem], total_images: int, total_labels: int, class_distribution: dict[int, int])`
  - `validate_dataset(items: list[DatasetItem], catalog: list[SignClass]) -> ValidationReport`
  - `DatasetSnapshot(snapshot_id: str, snapshot_dir: Path, data_yaml_path: Path, manifest: dict)`
  - `create_dataset_snapshot(items: list[DatasetItem], output_dir: Path, validation_report: ValidationReport, seed: int = 42) -> DatasetSnapshot`

- [ ] **Step 1: Write failing validation tests (Review Focus: format tampering & data leakage)**
Test các trường hợp:
1. File ảnh dung lượng 0 byte hoặc đuôi giả mạo bị báo lỗi blocking `CORRUPT_IMAGE`.
2. Nhãn chứa số lượng giá trị khác 5 trên một dòng bị báo lỗi blocking `MALFORMED_YOLO_LINE`.
3. Class ID = 82 hoặc -1 bị báo lỗi blocking `CLASS_ID_OUT_OF_RANGE`.
4. Tọa độ box < 0 hoặc > 1 hoặc width <= 0 bị báo lỗi blocking `INVALID_COORDINATES`.
5. Ảnh giống hệt nhau (trùng SHA-256) xuất hiện ở cả `train` và `val/test` bị báo lỗi blocking `DATA_LEAKAGE`.
6. Lớp có ít hơn 5 mẫu hoặc tỷ lệ mất cân bằng > 10:1 chỉ bị báo `warning` (không làm `has_blocking=True`).

- [ ] **Step 2: Write failing snapshot tests**
Test việc tạo snapshot: từ chối tạo snapshot nếu `validation_report.has_blocking` là `True`; khi hợp lệ, sao chép hoặc liên kết dữ liệu vào `snapshots/<snapshot_id>`, sinh file `data.yaml` với đường dẫn tuyệt đối/chuẩn hóa, ghi danh sách `names` 82 lớp tiếng Việt, và xuất `manifest.json` chứa checksum của tất cả các file.

- [ ] **Step 3: Run Task 2 tests and confirm failure**
Run: `.venv/bin/python -m pytest tests/data/test_validator.py tests/data/test_snapshot.py -q`
Expected: FAIL do chưa có `validator.py` và `snapshot.py`.

- [ ] **Step 4: Implement Quality Gate Validator**
Cài đặt `validate_dataset` kiểm tra toàn diện cấu trúc ảnh, nội dung nhãn, phạm vi giá trị và phát hiện rò rỉ dữ liệu qua checksum SHA-256 giữa các tập chia.

- [ ] **Step 5: Implement Immutable Dataset Snapshot**
Cài đặt `create_dataset_snapshot` lưu cấu hình bất biến, ghi file cấu hình `data.yaml` phục vụ Ultralytics huấn luyện và xuất nhật ký biến đổi `snapshot_manifest.json`.

- [ ] **Step 6: Verify Task 2**
Run: `.venv/bin/python -m pytest tests/data/test_validator.py tests/data/test_snapshot.py -q`
Expected: all Task 2 tests PASS.

- [ ] **Step 7: Commit Task 2**
```bash
git add src/trafficvision/data/validator.py src/trafficvision/data/snapshot.py tests/data/test_validator.py tests/data/test_snapshot.py
git commit -m "feat: implement dataset quality gate validator and immutable snapshot"
```

---

## Task 3: Automated EDA (Exploratory Data Analysis) Engine

**Files:**
- Create: `src/trafficvision/data/eda.py`
- Create: `tests/data/test_eda.py`

**Interfaces:**
- Consumes: `DatasetItem`, `ValidationReport`, `SignClass`.
- Produces:
  - `EDAMetrics(split_summary: dict, class_counts: dict[int, int], size_distribution: dict[str, int], aspect_ratios: list[float], bbox_stats: dict, sample_image_manifest: list[dict])`
  - `generate_eda_report(items: list[DatasetItem], output_dir: Path) -> EDAMetrics`
  - `save_eda_summary(eda: EDAMetrics, output_path: Path) -> None`

- [ ] **Step 1: Write failing EDA tests**
Viết test kiểm tra:
1. Thống kê đúng số lượng ảnh, số lượng bounding box theo từng tập `train`, `val`, `test`.
2. Phân loại kích thước bounding box theo tiêu chuẩn COCO (nhỏ: diện tích < 32^2, vừa: 32^2 - 96^2, lớn: > 96^2).
3. Tính toán phân bố tâm box (x, y) và tỷ lệ khung hình (width / height).
4. Xuất file `eda_report.json` và cấu trúc dữ liệu để sẵn sàng vẽ biểu đồ trên giao diện.

- [ ] **Step 2: Run Task 3 tests and confirm failure**
Run: `.venv/bin/python -m pytest tests/data/test_eda.py -q`
Expected: FAIL do chưa có `src/trafficvision/data/eda.py`.

- [ ] **Step 3: Implement EDA calculation engine**
Viết `generate_eda_report` đọc ảnh và nhãn (sử dụng Pillow/OpenCV để lấy kích thước thật của ảnh), tính toán các phân bố thống kê, phát hiện mẫu bất thường và xuất báo cáo có thể tuần tự hóa JSON.

- [ ] **Step 4: Verify Task 3**
Run: `.venv/bin/python -m pytest tests/data/test_eda.py -q`
Expected: all Task 3 tests PASS.

- [ ] **Step 5: Commit Task 3**
```bash
git add src/trafficvision/data/eda.py tests/data/test_eda.py
git commit -m "feat: add automated dataset EDA analysis engine"
```

---

## Task 4: Background Training Engine & Subprocess Runner

**Files:**
- Create: `src/trafficvision/training/__init__.py`
- Create: `src/trafficvision/training/config.py`
- Create: `src/trafficvision/training/state.py`
- Create: `src/trafficvision/training/runner.py`
- Create: `src/trafficvision/training/manager.py`
- Create: `tests/training/__init__.py`
- Create: `tests/training/test_training_config.py`
- Create: `tests/training/test_training_state.py`
- Create: `tests/training/test_training_manager.py`

**Interfaces:**
- Consumes: `AppPaths`, `DatasetSnapshot`.
- Produces:
  - `TrainingConfig(run_id: str, data_yaml: Path, base_model: str = "yolo11n.pt", epochs: int = 50, batch: int = 4, imgsz: int = 640, patience: int = 10, amp: bool = True, device: str = "cpu", seed: int = 42)`
  - `TrainingState(run_id: str, status: Literal["idle", "running", "paused", "completed", "failed", "stopped"], current_epoch: int, total_epochs: int, best_map50: float, metrics: dict, elapsed_s: float, error_message: str | None = None)`
  - `TrainingManager.start_training(config: TrainingConfig) -> TrainingState`
  - `TrainingManager.get_state(run_id: str) -> TrainingState`
  - `TrainingManager.stop_training(run_id: str) -> None`
  - `TrainingManager.list_runs() -> list[TrainingState]`

- [ ] **Step 1: Write failing training config and state tests**
Test validation giá trị: batch >= 1, epochs >= 1, imgsz là bội số của 32, và round-trip JSON của `TrainingState`.

- [ ] **Step 2: Write failing training manager tests (Review Focus: crash recovery & background isolation)**
Test:
1. `TrainingManager` khởi chạy tiến trình huấn luyện ở chế độ nền (subprocess), ghi PID vào file `run.pid`.
2. Kiểm tra `get_state` đọc đúng dữ liệu cập nhật từ `state.json` và `events.jsonl`.
3. Kiểm tra cơ chế `stop_training` tạo file cờ `stop.signal` hoặc gửi tín hiệu ngắt để tiến trình dừng an toàn sau epoch hiện tại.
4. Kiểm tra phát hiện tiến trình bị kill đột ngột (PID không còn chạy nhưng status trong file vẫn là `running`) -> tự động cập nhật status thành `failed` kèm thông báo rõ ràng.

- [ ] **Step 3: Run Task 4 tests and confirm failure**
Run: `.venv/bin/python -m pytest tests/training/test_training_config.py tests/training/test_training_state.py tests/training/test_training_manager.py -q`
Expected: FAIL do các module training chưa được tạo.

- [ ] **Step 4: Implement training config, state and runner subprocess**
Cài đặt `runner.py`:
- Nhận tham số qua CLI hoặc file cấu hình `run_config.json`.
- Sử dụng callback của Ultralytics (`on_train_epoch_end`, `on_fit_epoch_end`) để cập nhật `state.json` và append vào `events.jsonl` sau mỗi epoch.
- Kiểm tra file cờ `stop.signal` ở cuối mỗi epoch để dừng sớm an toàn khi người dùng yêu cầu.
- Lưu checkpoint `last.pt` và `best.pt` trong thư mục `artifacts/runs/<run_id>/weights/`.

- [ ] **Step 5: Implement TrainingManager service**
Cài đặt `manager.py` quản lý vòng đời subprocess bằng `subprocess.Popen`, kiểm tra tiến trình sống bằng `poll()`, đọc và cập nhật file trạng thái mà không block ứng dụng web.

- [ ] **Step 6: Verify Task 4**
Run: `.venv/bin/python -m pytest tests/training/ -q`
Expected: all Task 4 tests PASS.

- [ ] **Step 7: Commit Task 4**
```bash
git add src/trafficvision/training tests/training
git commit -m "feat: add background training runner and manager"
```

---

## Task 5: Independent Evaluation, ONNX Export & Parity Verification

**Files:**
- Create: `src/trafficvision/training/evaluator.py`
- Create: `src/trafficvision/training/exporter.py`
- Create: `src/trafficvision/training/candidate.py`
- Create: `tests/training/test_evaluator.py`
- Create: `tests/training/test_exporter.py`
- Create: `tests/training/test_candidate.py`

**Interfaces:**
- Consumes: checkpoint `best.pt`, `ModelManifest`, test split from `DatasetSnapshot`.
- Produces:
  - `EvaluationMetrics(precision: float, recall: float, f1: float, map50: float, map50_95: float, per_class_ap: dict[str, float], confusion_matrix: list[list[int]])`
  - `evaluate_checkpoint(model_path: Path, data_yaml: Path, split: str = "test") -> EvaluationMetrics`
  - `ExportResult(onnx_path: Path, max_abs_diff: float, is_parity_valid: bool, cpu_latency_ms: float, cpu_fps: float)`
  - `export_and_verify_onnx(model_path: Path, imgsz: int = 640, tolerance: float = 1e-3) -> ExportResult`
  - `package_candidate(run_id: str, weights_path: Path, onnx_result: ExportResult, eval_metrics: EvaluationMetrics, class_names: list[str], runs_dir: Path) -> Path`

- [ ] **Step 1: Write failing evaluation and ONNX parity tests (Review Focus: parity divergence)**
Test:
1. `evaluate_checkpoint` gọi validator trên test split và trích xuất đúng các chỉ số mAP50, mAP50-95, P, R, F1 và confusion matrix.
2. `export_and_verify_onnx` xuất file ONNX với `batch=1, imgsz=640, device="cpu"`, chạy suy luận thử trên ảnh mẫu bằng cả PyTorch và ONNX Runtime, tính toán sai số tuyệt đối lớn nhất `max_abs_diff`.
3. Nếu sai số > 1e-3, hàm trả về `is_parity_valid=False` và cảnh báo không cho promotion.
4. `package_candidate` tạo thư mục `artifacts/runs/<run_id>/candidate/` chứa `model.onnx`, `manifest.json` (có `stage="candidate"`, 82 lớp biển báo, checksum SHA-256), `benchmark.json` và `test_metrics.json`.

- [ ] **Step 2: Run Task 5 tests and confirm failure**
Run: `.venv/bin/python -m pytest tests/training/test_evaluator.py tests/training/test_exporter.py tests/training/test_candidate.py -q`
Expected: FAIL do chưa có file evaluator/exporter/candidate.

- [ ] **Step 3: Implement model evaluation and ONNX exporter**
Cài đặt `evaluator.py` và `exporter.py`. Tích hợp đo benchmark CPU thời gian suy luận (chạy 10 vòng warmup và 30 vòng đo lường để tính FPS và latency trung bình).

- [ ] **Step 4: Implement candidate packager**
Cài đặt `package_candidate` tổng hợp toàn bộ artifact thẩm định vào thư mục `candidate/` theo đúng cấu trúc thư mục quy định trong Spec Mục 6.

- [ ] **Step 5: Verify Task 5**
Run: `.venv/bin/python -m pytest tests/training/test_evaluator.py tests/training/test_exporter.py tests/training/test_candidate.py -q`
Expected: all Task 5 tests PASS.

- [ ] **Step 6: Commit Task 5**
```bash
git add src/trafficvision/training/evaluator.py src/trafficvision/training/exporter.py src/trafficvision/training/candidate.py tests/training/test_evaluator.py tests/training/test_exporter.py tests/training/test_candidate.py
git commit -m "feat: add test evaluation, ONNX parity verification and candidate packager"
```

---

## Task 6: Model Promotion, Automatic Backup & Rollback in Registry

**Files:**
- Modify: `src/trafficvision/registry.py`
- Create: `tests/test_promotion_rollback.py`

**Interfaces:**
- Consumes: candidate artifacts from Task 5, existing `ModelRegistry`.
- Produces:
  - `BackupInfo(backup_id: str, timestamp: str, model_id: str, backup_dir: Path, manifest: ModelManifest)`
  - `ModelRegistry.promote_candidate(candidate_dir: Path) -> RegisteredModel`
  - `ModelRegistry.list_backups() -> list[BackupInfo]`
  - `ModelRegistry.rollback_to_backup(backup_id: str | None = None) -> RegisteredModel`

- [ ] **Step 1: Write failing promotion and rollback tests (Review Focus: promotion failure rollback)**
Test:
1. Thăng cấp candidate hợp lệ: tự động sao lưu model production hiện tại vào `artifacts/backups/<timestamp>_<model_id>`, chuyển candidate thành production mới có `stage="production"` và 82 lớp biển báo.
2. Từ chối candidate nếu thiếu manifest, checksum sai, hoặc số lớp không khớp 82.
3. Kịch bản mô phỏng lỗi khi thăng cấp: nếu xảy ra lỗi sau khi đã backup nhưng trước khi hoàn tất thay thế, hệ thống tự động khôi phục (rollback) về bản backup gần nhất mà không làm mất production.
4. Gọi `rollback_to_backup` khôi phục chính xác phiên bản model production trước đó.

- [ ] **Step 2: Run Task 6 tests and confirm failure**
Run: `.venv/bin/python -m pytest tests/test_promotion_rollback.py -q`
Expected: FAIL do `promote_candidate` và `rollback_to_backup` chưa có trên `ModelRegistry`.

- [ ] **Step 3: Implement promotion, backup, and rollback in ModelRegistry**
Mở rộng `ModelRegistry` trong `src/trafficvision/registry.py`:
- Thực hiện kiểm tra tính toàn vẹn của candidate trước khi chạm vào production.
- Sao lưu nguyên tử production cũ kèm timestamp `YYYYMMDD_HHMMSS`.
- Thay thế file và manifest nguyên tử sử dụng file tạm và `os.replace`.
- Thêm cơ chế rollback an toàn khôi phục từ thư mục backup.

- [ ] **Step 4: Verify Task 6**
Run: `.venv/bin/python -m pytest tests/test_promotion_rollback.py tests/test_registry.py -q`
Expected: all tests PASS.

- [ ] **Step 5: Commit Task 6**
```bash
git add src/trafficvision/registry.py tests/test_promotion_rollback.py
git commit -m "feat: implement atomic model promotion, automated backup and rollback"
```

---

## Task 7: Full AI Experiment Lab Web Interface (`pages/training.py`)

**Files:**
- Create: `src/trafficvision/ui/pages/training.py`
- Modify: `src/trafficvision/ui/app.py`
- Modify: `src/trafficvision/ui/pages/model_info.py`
- Delete: `src/trafficvision/ui/pages/training_placeholder.py`
- Create: `tests/ui/test_training_page.py`
- Modify: `tests/ui/test_secondary_pages.py`

**Interfaces:**
- Consumes: `AppServices`, `TrainingManager`, `validate_dataset`, `create_dataset_snapshot`, `generate_eda_report`, `ModelRegistry`.
- Produces:
  - `render_training_page(services: AppServices) -> None`

- [ ] **Step 1: Write failing UI tests for the 4-step AI Experiment Lab**
Test:
1. Trang render đầy đủ 4 bước (Dữ liệu -> Kiểm định -> Huấn luyện -> Đánh giá & xuất) bám sát cấu trúc mockup HTML.
2. Bước 1 Dữ liệu: hiển thị ô chọn thư mục / nạp dữ liệu, nút quét và thông tin số lượng ảnh.
3. Bước 2 Kiểm định: khi dữ liệu có lỗi blocking, nút bắt đầu huấn luyện bị vô hiệu hóa kèm bảng thông báo lỗi đỏ; khi dữ liệu hợp lệ, hiển thị thông số EDA.
4. Bước 3 Huấn luyện: cho phép cấu hình tham số, hiển thị nút Bắt đầu / Tạm dừng / Dừng, thanh tiến độ, các thẻ số liệu thời gian thực (Epoch, Best mAP50, Loss, Time) và log terminal console.
5. Bước 4 Đánh giá & xuất: hiển thị chỉ số test set, nút "Thăng cấp lên Production" và hiển thị thông báo thành công sau promotion.

- [ ] **Step 2: Run UI tests and confirm failure**
Run: `.venv/bin/python -m pytest tests/ui/test_training_page.py -q`
Expected: FAIL do chưa có `training.py`.

- [ ] **Step 3: Implement active 4-step Training UI page**
Viết `src/trafficvision/ui/pages/training.py`:
- Tích hợp trạng thái các bước với `st.session_state`.
- Hiển thị đầy đủ thông tin phần cứng (nhận diện GPU NVIDIA CUDA khả dụng hoặc Chế độ CPU).
- Kết nối `TrainingManager` để polling cập nhật biểu đồ và thanh tiến độ khi job đang chạy.
- Kết nối `ModelRegistry.promote_candidate` cho phép thăng cấp mô hình 82 lớp trực tiếp từ web với một cú click chuột.

- [ ] **Step 4: Update navigation and model info page**
Cập nhật `src/trafficvision/ui/app.py` trỏ trang Huấn luyện AI vào `render_training_page`. Cập nhật `src/trafficvision/ui/pages/model_info.py` hiển thị lịch sử sao lưu (backups) và nút phục hồi (Rollback) cho phép người quản trị hoàn tác khi cần. Xóa bỏ `training_placeholder.py`.

- [ ] **Step 5: Verify Task 7**
Run: `.venv/bin/python -m pytest tests/ui/ -q`
Expected: all UI tests PASS.

- [ ] **Step 6: Commit Task 7**
```bash
git add src/trafficvision/ui/ tests/ui/
git rm src/trafficvision/ui/pages/training_placeholder.py
git commit -m "feat: complete active 4-step AI Experiment Lab web interface"
```

---

## Task 8: End-to-End Integration, CLI Scripts & Smoke Verification

**Files:**
- Create: `scripts/validate_dataset.py`
- Create: `scripts/train.py`
- Create: `scripts/promote_model.py`
- Create: `tests/integration/test_phase2_flow.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: toàn bộ interface công khai từ Tasks 1–7.
- Produces:
  - `python scripts/validate_dataset.py --data-dir <path>`
  - `python scripts/train.py --data-yaml <path> --epochs <N> --batch <B>`
  - `python scripts/promote_model.py --candidate-dir <path>`
  - `python scripts/promote_model.py --rollback`
  - Integration test chứng minh luồng hoàn chỉnh từ dataset -> kiểm định -> huấn luyện 1 epoch mock -> export ONNX -> promotion -> suy luận nhận dạng biển báo tiếng Việt!

- [ ] **Step 1: Write full end-to-end integration test**
Viết `tests/integration/test_phase2_flow.py`:
1. Sinh synthetic dataset có 82 lớp biển báo.
2. Chạy `validate_dataset` xác nhận không có lỗi blocking.
3. Tạo `DatasetSnapshot` bất biến.
4. Chạy huấn luyện thử nghiệm (mock hoặc 1 epoch nhỏ).
5. Tạo candidate model 82 lớp kèm ONNX và manifest.
6. Thăng cấp candidate lên production, tự động lưu backup baseline cũ.
7. Gọi `AnalysisService.analyze_image_upload` trên ảnh test, xác nhận nhãn trả về thuộc danh mục 82 lớp tiếng Việt và trạng thái manifest chuyển sang mô hình biển báo Việt Nam!

- [ ] **Step 2: Run integration test and confirm failure**
Run: `.venv/bin/python -m pytest tests/integration/test_phase2_flow.py -q`
Expected: FAIL trước khi kết nối hoàn chỉnh CLI và scripts.

- [ ] **Step 3: Implement CLI operator scripts**
Cài đặt `scripts/validate_dataset.py`, `scripts/train.py`, `scripts/promote_model.py` với đầy đủ cờ `--project-root`, `--help`, định dạng in ấn màu sắc và mã thoát chuẩn.

- [ ] **Step 4: Update README.md with Phase 2 documentation**
Cập nhật tài liệu hướng dẫn sử dụng:
- Cách tải/chuẩn bị bộ dữ liệu biển báo Việt Nam (từ Hugging Face hoặc thư mục cục bộ).
- Quy trình kiểm định Quality Gate và xem báo cáo EDA.
- Hướng dẫn huấn luyện qua giao diện web hoặc CLI.
- Hướng dẫn thăng cấp mô hình candidate lên production và cách hoàn tác (rollback).

- [ ] **Step 5: Run the complete test suite and code quality gate**
Run: `.venv/bin/python -m pytest -q`
Expected: all tests PASS (100%).
Run: `.venv/bin/ruff check .`
Expected: exit code 0.
Run: `.venv/bin/ruff format --check .`
Expected: exit code 0.

- [ ] **Step 6: Commit Task 8**
```bash
git add scripts/ tests/integration/test_phase2_flow.py README.md
git commit -m "docs: finalize Phase 2 dataset, training, and promotion workflows"
```

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-28-trafficvision-phase2-training-pipeline.md`.
