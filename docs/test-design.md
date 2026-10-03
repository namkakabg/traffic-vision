# Tài liệu Thiết kế Kiểm thử — TrafficVision

**Dự án:** TrafficVision – Nhận dạng biển báo giao thông bằng AI  
**Phiên bản tài liệu:** 1.0  
**Ngày:** 03/10/2026  
**Tham chiếu Spec:** `docs/superpowers/specs/2026-09-27-trafficvision-design.md`  
**Tham chiếu Plan 1:** `docs/superpowers/plans/2026-09-27-trafficvision-baseline-app.md`  
**Tham chiếu Plan 2:** `docs/superpowers/plans/2026-09-28-trafficvision-phase2-training-pipeline.md`

---

## Mục lục

1. [Phạm vi kiểm thử](#1-phạm-vi-kiểm-thử)
2. [Chiến lược kiểm thử](#2-chiến-lược-kiểm-thử)
3. [Module A — Cấu hình & Domain](#3-module-a--cấu-hình--domain)
4. [Module B — Model Registry & Bootstrap](#4-module-b--model-registry--bootstrap)
5. [Module C — ONNX Predictor Adapter](#5-module-c--onnx-predictor-adapter)
6. [Module D — Xử lý ảnh & Rendering](#6-module-d--xử-lý-ảnh--rendering)
7. [Module E — Xử lý video](#7-module-e--xử-lý-video)
8. [Module F — Lịch sử, Thống kê & Settings](#8-module-f--lịch-sử-thống-kê--settings)
9. [Module G — Giao diện Web](#9-module-g--giao-diện-web)
10. [Module H — Danh mục 82 lớp & Dataset Scanner](#10-module-h--danh-mục-82-lớp--dataset-scanner)
11. [Module I — Quality Gate Validator & Snapshot](#11-module-i--quality-gate-validator--snapshot)
12. [Module J — EDA Engine](#12-module-j--eda-engine)
13. [Module K — Training Engine](#13-module-k--training-engine)
14. [Module L — Evaluation, ONNX Export & Candidate](#14-module-l--evaluation-onnx-export--candidate)
15. [Module M — Promotion, Backup & Rollback](#15-module-m--promotion-backup--rollback)
16. [Module N — Giao diện Huấn luyện AI](#16-module-n--giao-diện-huấn-luyện-ai)
17. [Integration Tests](#17-integration-tests)
18. [UAT & Hiệu năng](#18-uat--hiệu-năng)
19. [Acceptance Criteria Checklist](#19-acceptance-criteria-checklist)

---

## 1. Phạm vi kiểm thử

| Loại | Phạm vi | Ngoài phạm vi |
|------|---------|---------------|
| Unit test | Mọi module trong `src/trafficvision/` | Camera trực tiếp, cloud deploy |
| Integration | Luồng ảnh/video end-to-end; luồng training→promotion | Nhiều người dùng đồng thời |
| UI (Streamlit) | `AppTest` cho mọi trang | Kiểm thử trình duyệt thực |
| UAT thủ công | Ảnh/video thực trên macOS và Windows | Điều khiển phương tiện tự hành |
| Hiệu năng | CPU macOS/Windows; CUDA GTX 1050 Ti (training) | GPU cloud |

---

## 2. Chiến lược kiểm thử

```
Pyramid kiểm thử TrafficVision
─────────────────────────────
         [UAT thủ công]          ← hiếm, chậm
       [Integration tests]        ← mỗi task 1 test
     [UI tests (AppTest)]         ← mỗi trang 1+ test
   [Unit tests (pytest, mock)]    ← đa số, nhanh, TDD
```

**Nguyên tắc:**
- TDD: viết test thất bại trước, rồi implement.
- Mọi test dùng `tmp_path` fixture; không đọc/ghi dữ liệu thật.
- Fixture ảnh/video tổng hợp (synthetic); không commit dữ liệu huấn luyện thật.
- Mỗi task kết thúc bằng: `.venv/bin/pytest -q` → toàn xanh → commit.

---

## 3. Module A — Cấu hình & Domain

> **Files:** `src/trafficvision/config.py`, `src/trafficvision/domain.py`  
> **Test files:** `tests/test_config.py`, `tests/test_domain.py`

### TC-A-01: Giá trị mặc định cấu hình

| Trường | Kỳ vọng |
|--------|---------|
| `confidence` | `0.25` |
| `iou` | `0.70` |
| `imgsz` | `640` |
| `max_image_bytes` | `20 * 1024 * 1024` (20 MB) |
| `max_video_bytes` | `500 * 1024 * 1024` (500 MB) |

**Điều kiện:** `AppConfig.load(project_root=tmp_path)`  
**Kết quả mong đợi:** Tất cả giá trị mặc định khớp bảng trên  
**Mức độ:** P0

---

### TC-A-02: Ghi đè cấu hình qua biến môi trường

**Input:** `TRAFFICVISION_CONFIDENCE=0.5`, `TRAFFICVISION_IOU=0.6`  
**Kết quả mong đợi:** `config.confidence == 0.5`, `config.iou == 0.6`  
**Mức độ:** P1

---

### TC-A-03: Từ chối giá trị cấu hình không hợp lệ

**Input:** `confidence=1.5` (> 1.0)  
**Kết quả mong đợi:** Raise `ValidationError`  
**Mức độ:** P1

---

### TC-A-04: AppPaths — đường dẫn con của project root

**Input:** `AppPaths.from_root(tmp_path)`  
**Kết quả mong đợi:** `paths.baseline`, `paths.production`, `paths.backups`, `paths.runs`, `paths.outputs`, `paths.staging`, `paths.state` đều là con của `tmp_path`  
**Mức độ:** P0

---

### TC-A-05: ModelManifest — class map động

**Input:** manifest với `class_names={0: "person", 1: "bicycle"}`  
**Kết quả mong đợi:** `len(manifest.class_names) == 2`; không hard-code 82  
**Mức độ:** P0

---

### TC-A-06: ModelManifest — từ chối SHA-256 không hợp lệ

**Input:** `sha256=""` hoặc `sha256="abc"` (không đủ 64 ký tự hex)  
**Kết quả mong đợi:** Raise `ValidationError`  
**Mức độ:** P1

---

### TC-A-07: ModelManifest — từ chối class map rỗng

**Input:** `class_names={}`  
**Kết quả mong đợi:** Raise `ValidationError`  
**Mức độ:** P1

---

### TC-A-08: Detection — từ chối confidence ngoài [0, 1]

**Input:** `Detection(confidence=1.5, ...)`  
**Kết quả mong đợi:** Raise `ValidationError`  
**Mức độ:** P1

---

### TC-A-09: Detection — từ chối tọa độ đảo ngược

**Input:** `xyxy=(100, 10, 50, 200)` (x2 < x1)  
**Kết quả mong đợi:** Raise `ValidationError`  
**Mức độ:** P1

---

### TC-A-10: ModelManifest — round-trip JSON

**Input:** Tạo manifest → `model_dump_json()` → `model_validate_json()`  
**Kết quả mong đợi:** Manifest sau round-trip bằng manifest gốc  
**Mức độ:** P1

---

## 4. Module B — Model Registry & Bootstrap

> **Files:** `src/trafficvision/registry.py`, `src/trafficvision/bootstrap.py`  
> **Test files:** `tests/test_registry.py`, `tests/test_bootstrap.py`

### TC-B-01: SHA-256 checksum file

**Input:** File với nội dung cố định  
**Kết quả mong đợi:** `sha256_file(path)` trả về hex string 64 ký tự, khớp giá trị tính tay  
**Mức độ:** P0

---

### TC-B-02: install_baseline → production được giải quyết ngay

**Input:** ONNX bytes + manifest hợp lệ  
**Kết quả mong đợi:**
- `artifacts/baseline/<model_id>/model.onnx` tồn tại
- `registry.get_production().manifest.sha256 == sha256_file(onnx_path)`
- `model.manifest.stage == "production"`

**Mức độ:** P0

---

### TC-B-03: get_production() — phát hiện tampering

**Điều kiện:** Sửa 1 byte trong file ONNX sau khi đăng ký  
**Kết quả mong đợi:** `get_production()` raise `ModelIntegrityError`  
**Mức độ:** P0 *(Review Focus Plan 1)*

---

### TC-B-04: get_production() — từ chối path traversal

**Input:** `artifact_filename = "../../../etc/passwd"`  
**Kết quả mong đợi:** Raise `ModelSecurityError`  
**Mức độ:** P0 *(Security)*

---

### TC-B-05: get_production() — chưa có model

**Điều kiện:** Chưa install baseline  
**Kết quả mong đợi:** Raise `ModelNotFoundError`  
**Mức độ:** P1

---

### TC-B-06: bootstrap_baseline — export đúng tham số

**Input:** Monkeypatch Ultralytics factory  
**Kết quả mong đợi:** `format="onnx"`, `imgsz=640`, `batch=1`, `dynamic=False`, `device="cpu"`  
**Mức độ:** P1

---

### TC-B-07: bootstrap_baseline — class names từ model metadata

**Điều kiện:** Model có `names={0: "car", 1: "truck"}`  
**Kết quả mong đợi:** `production.manifest.class_names == {0: "car", 1: "truck"}`; không hard-code  
**Mức độ:** P0

---

## 5. Module C — ONNX Predictor Adapter

> **Files:** `src/trafficvision/inference/ultralytics.py`  
> **Test files:** `tests/inference/test_ultralytics_predictor.py`

### TC-C-01: Chuyển đổi kết quả sang Detection

**Input:** `xyxy=[10,20,100,200]`, `conf=0.85`, `cls=1`  
**Kết quả mong đợi:** `Detection(class_id=1, class_name="<từ manifest>", confidence=0.85, xyxy=(10,20,100,200))`  
**Mức độ:** P0

---

### TC-C-02: Class name từ manifest, không phải result.names

**Input:** `result.names={1:"car"}` nhưng manifest có `{1:"bien_cam"}`  
**Kết quả mong đợi:** `detection.class_name == "bien_cam"`  
**Mức độ:** P0

---

### TC-C-03: Không có detection

**Input:** 0 bounding boxes  
**Kết quả mong đợi:** `predict()` trả về `()`  
**Mức độ:** P1

---

### TC-C-04: Tham số inference đúng

**Input:** `confidence=0.35`, `iou=0.55`  
**Kết quả mong đợi:** Ultralytics gọi với `imgsz=manifest.imgsz`, `device="cpu"`, `verbose=False`, `conf=0.35`, `iou=0.55`  
**Mức độ:** P1

---

### TC-C-05: Phát hiện tampering trước khi load

**Điều kiện:** Tạo predictor → sửa ONNX file → gọi predict  
**Kết quả mong đợi:** Raise `ModelIntegrityError` trước khi Ultralytics factory được gọi  
**Mức độ:** P0 *(Review Focus Plan 1)*

---

### TC-C-06: Class ID không có trong manifest

**Input:** Model trả về class_id=99; manifest chỉ có 0,1  
**Kết quả mong đợi:** Raise `PredictionContractError`  
**Mức độ:** P1

---

## 6. Module D — Xử lý ảnh & Rendering

> **Files:** `src/trafficvision/media.py`, `src/trafficvision/inference/image.py`, `src/trafficvision/rendering.py`  
> **Test files:** `tests/test_media.py`, `tests/inference/test_image.py`, `tests/test_rendering.py`

### TC-D-01: stage_upload — cô lập tên file nguy hiểm

**Input:** `../secret.jpg`, `C:\Windows\secret.jpg`  
**Kết quả mong đợi:** File staging dùng UUID; không thoát ra ngoài `paths.staging`  
**Mức độ:** P0 *(Security)*

---

### TC-D-02: stage_upload — từ chối file quá kích thước

**Input:** `21 * 1024 * 1024` bytes  
**Kết quả mong đợi:** Raise `MediaValidationError`  
**Mức độ:** P1

---

### TC-D-03: stage_upload — từ chối ảnh hỏng (kiểm tra nội dung)

**Input:** `b"plain text"` với filename `fake.jpg`  
**Kết quả mong đợi:** Raise `MediaValidationError` — kiểm tra nội dung, không tin tưởng extension  
**Mức độ:** P0 *(Review Focus Plan 1)*

---

### TC-D-04: stage_upload — từ chối video hỏng

**Input:** `b"plain text"` với filename `fake.mp4`  
**Kết quả mong đợi:** Raise `MediaValidationError`  
**Mức độ:** P0

---

### TC-D-05: decode_image — trả về numpy array BGR

**Input:** JPEG bytes 64×48  
**Kết quả mong đợi:** `shape == (48, 64, 3)`, `dtype == uint8`  
**Mức độ:** P1

---

### TC-D-06: analyze_image — thresholds truyền đúng

**Input:** `confidence=0.35`, `iou=0.55`, fake predictor  
**Kết quả mong đợi:** Predictor nhận đúng `confidence=0.35`, `iou=0.55`  
**Mức độ:** P1

---

### TC-D-07: analyze_image — không có detection

**Input:** Predictor trả về `()`  
**Kết quả mong đợi:** `analysis.detections == ()`; ảnh annotate hợp lệ; CSV chỉ có header  
**Mức độ:** P1 *(Review Focus Plan 1)*

---

### TC-D-08: annotate_image — nhãn tiếng Việt không raise

**Input:** `class_name="Cấm đi ngược chiều"`  
**Kết quả mong đợi:** JPEG/PNG bytes hợp lệ, decode được bằng Pillow  
**Mức độ:** P0

---

### TC-D-09: annotate_image — output đúng kích thước gốc

**Input:** Ảnh 640×480  
**Kết quả mong đợi:** Output PNG/JPEG kích thước 640×480  
**Mức độ:** P1

---

### TC-D-10: detections_csv — đủ cột bắt buộc

**Kết quả mong đợi:** Header: `source,frame_index,timestamp_s,class_id,class_name,confidence,x1,y1,x2,y2`  
**Mức độ:** P0

---

### TC-D-11: detections_csv — không có detection → chỉ header

**Input:** `detections=[]`  
**Kết quả mong đợi:** 1 dòng header, không có data row  
**Mức độ:** P1

---

### TC-D-12: detections_csv — UTF-8 BOM

**Kết quả mong đợi:** `csv_bytes[:3] == b"\xef\xbb\xbf"`  
**Mức độ:** P1

---

### TC-D-13: analyze_image — thời gian inference >= 0

**Kết quả mong đợi:** `analysis.inference_ms >= 0.0`  
**Mức độ:** P1

---

## 7. Module E — Xử lý video

> **Files:** `src/trafficvision/inference/video.py`  
> **Test files:** `tests/inference/test_video.py`

### TC-E-01: process_video — output hợp lệ

**Input:** Video 6 frame, 64×48 px, 10 FPS; fake predictor  
**Kết quả mong đợi:**
- `analysis.width == 64`, `analysis.height == 48`, `analysis.fps == 10.0`
- `analysis.total_frames == 6`
- Output file tồn tại; không có `.partial` file

**Mức độ:** P0

---

### TC-E-02: process_video — callback tiến độ đơn điệu

**Kết quả mong đợi:** `progress.fraction` tăng từ 0 → 1.0; gọi callback >= 1 lần  
**Mức độ:** P1

---

### TC-E-03: process_video — CSV ghi đúng frame_index và timestamp_s

**Kết quả mong đợi:** CSV tồn tại; `frame_index` và `timestamp_s` được điền đúng  
**Mức độ:** P1

---

### TC-E-04: process_video — từ chối video hỏng

**Input:** `b"plain text"` rename thành `.mp4`  
**Kết quả mong đợi:** Raise `VideoProcessingError`  
**Mức độ:** P0

---

### TC-E-05: process_video — lỗi giữa chừng → message rõ ràng + không partial file

**Điều kiện:** Predictor raise exception tại frame 3  
**Kết quả mong đợi:**
- Raise `VideoProcessingError` chứa thông tin frame lỗi
- Không có `.partial` file còn lại

**Mức độ:** P0 *(Review Focus Plan 1)*

---

### TC-E-06: process_video — codec fallback

**Điều kiện:** H.264 init thất bại  
**Kết quả mong đợi:** Tự động thử MP4V; output vẫn được tạo  
**Mức độ:** P2

---

## 8. Module F — Lịch sử, Thống kê & Settings

> **Files:** `src/trafficvision/history.py`, `src/trafficvision/settings.py`, `src/trafficvision/service.py`  
> **Test files:** `tests/test_history.py`, `tests/test_settings.py`, `tests/test_service.py`

### TC-F-01: AnalysisRepository — mới nhất trước

**Input:** 3 records thêm lần lượt  
**Kết quả mong đợi:** `list_recent()[0]` là record thêm cuối  
**Mức độ:** P1

---

### TC-F-02: AnalysisRepository — limit

**Input:** 50 records; `list_recent(limit=10)`  
**Kết quả mong đợi:** `len(result) == 10`  
**Mức độ:** P1

---

### TC-F-03: AnalysisRepository — class_totals aggregate

**Input:** 3 records có class_counts khác nhau  
**Kết quả mong đợi:** `class_totals()` trả về tổng cộng dồn theo từng lớp  
**Mức độ:** P1

---

### TC-F-04: AnalysisRepository — tên file Unicode

**Input:** `original_filename = "ảnh_giao_thông_2026.jpg"`  
**Kết quả mong đợi:** Giá trị lưu và đọc lại khớp chính xác  
**Mức độ:** P1

---

### TC-F-05: RuntimeSettingsStore — mặc định khi file không tồn tại

**Kết quả mong đợi:** `store.load()` trả về `confidence=0.25`, `iou=0.70`  
**Mức độ:** P1

---

### TC-F-06: RuntimeSettingsStore — round-trip JSON

**Input:** `save(confidence=0.5)` → `load()`  
**Kết quả mong đợi:** `0.5` được đọc lại chính xác  
**Mức độ:** P1

---

### TC-F-07: RuntimeSettingsStore — từ chối giá trị không hợp lệ

**Input:** `confidence=2.0`  
**Kết quả mong đợi:** Raise exception; không ghi file  
**Mức độ:** P1

---

### TC-F-08: RuntimeSettingsStore — atomic save

**Điều kiện:** Inject lỗi write ở lần save thứ hai  
**Kết quả mong đợi:** File gốc giữ nguyên giá trị cũ  
**Mức độ:** P1

---

### TC-F-09: AnalysisService — history ghi sau khi file tồn tại

**Kết quả mong đợi:** `repo.list_recent()` có 1 record sau khi phân tích ảnh hợp lệ; `annotated_path.is_file()`  
**Mức độ:** P0

---

### TC-F-10: AnalysisService — video lỗi → không ghi history, không partial file

**Input:** Video corrupt  
**Kết quả mong đợi:** `repo.list_recent() == []`; không có `.partial*` file  
**Mức độ:** P0 *(Review Focus Plan 1)*

---

## 9. Module G — Giao diện Web

> **Test files:** `tests/ui/test_app_smoke.py`, `tests/ui/test_analysis_page.py`, `tests/ui/test_secondary_pages.py`, `tests/ui/test_theme.py`

### TC-G-01: App smoke — không crash khi chưa có model

**Kết quả mong đợi:**
- `at.exception` là None
- Tiêu đề chứa "TrafficVision"
- Không hiển thị "82 lớp"
- Có hướng dẫn setup

**Mức độ:** P0

---

### TC-G-02: Trang Phân tích — cảnh báo baseline

**Điều kiện:** Baseline model (chưa fine-tune)  
**Kết quả mong đợi:** Warning chứa "baseline" AND "chưa fine-tune"  
**Mức độ:** P0

---

### TC-G-03: Trang Phân tích — định dạng uploader đúng

**Kết quả mong đợi:** Image: `{jpg, jpeg, png, webp}`; Video: `{mp4, avi, mov}`  
**Mức độ:** P1

---

### TC-G-04: Trang Phân tích — số lớp từ manifest

**Điều kiện:** Model 2 lớp  
**Kết quả mong đợi:** UI hiển thị "2", không hiển thị "82 lớp"  
**Mức độ:** P0

---

### TC-G-05: Trang Phân tích — không hiển thị metrics giả

**Điều kiện:** `metrics=None`  
**Kết quả mong đợi:** Không có "mAP", "82 lớp" hay số liệu giả  
**Mức độ:** P0

---

### TC-G-06: Trang Lịch sử — trạng thái rỗng

**Kết quả mong đợi:** Thông báo "chưa có" hoặc "không có"  
**Mức độ:** P1

---

### TC-G-07: Trang Lịch sử — hiển thị records

**Điều kiện:** 2 records trong DB  
**Kết quả mong đợi:** `at.dataframe` có dữ liệu  
**Mức độ:** P1

---

### TC-G-08: Trang Thống kê — metric cards

**Điều kiện:** 1 record trong DB với 4 detections  
**Kết quả mong đợi:** `len(at.metric) >= 2`  
**Mức độ:** P1

---

### TC-G-09: Trang Thông tin mô hình — metadata

**Kết quả mong đợi:** Model ID, backend, SHA-256 prefix (8 ký tự) hiển thị  
**Mức độ:** P1

---

### TC-G-10: Trang Thông tin mô hình — cảnh báo baseline

**Kết quả mong đợi:** Warning có text "baseline"  
**Mức độ:** P0

---

### TC-G-11: Trang Thông tin mô hình — rollback UI

**Điều kiện:** Có backup sau promotion  
**Kết quả mong đợi:** `at.selectbox` có >= 1 phần tử; button rollback tồn tại  
**Mức độ:** P1

---

### TC-G-12: Trang Thiết lập — sliders và nút lưu

**Kết quả mong đợi:** `len(at.slider) >= 2`; `len(at.button) >= 1`  
**Mức độ:** P1

---

### TC-G-13: Theme CSS — contrast rules cho input

**Kết quả mong đợi:** CSS chứa `div[data-testid="stTextInput"] input`, `background-color: #ffffff !important`, `caret-color: #2563eb !important`  
**Mức độ:** P2

---

### TC-G-14: Streamlit config.toml — màu sắc theme

**Kết quả mong đợi:** `primaryColor="#2563eb"`, `backgroundColor="#f8fafc"`, `textColor="#0f172a"`  
**Mức độ:** P2

---

### TC-G-15: Trang Huấn luyện placeholder — hiển thị sequence 4 bước

**Điều kiện:** Plan 1 training placeholder (giai đoạn 1)  
**Kết quả mong đợi:** Chứa text "Dữ liệu → Kiểm định → Huấn luyện → Đánh giá"; không có nút Start  
**Mức độ:** P1

---

## 10. Module H — Danh mục 82 lớp & Dataset Scanner

> **Files:** `src/trafficvision/data/catalog.py`, `src/trafficvision/data/dataset.py`  
> **Test files:** `tests/data/test_catalog.py`, `tests/data/test_dataset.py`

### TC-H-01: Catalog — đúng 82 phần tử

**Kết quả mong đợi:** `len(VIETNAM_TRAFFIC_SIGN_CATALOG) == 82`  
**Mức độ:** P0

---

### TC-H-02: Catalog — ID liên tục 0→81

**Kết quả mong đợi:** `[c.id for c in catalog] == list(range(82))`  
**Mức độ:** P0

---

### TC-H-03: Catalog — tên không rỗng, mã không trùng

**Kết quả mong đợi:** `all(c.name_vi != "" for c in catalog)`; `len({c.code for c in catalog}) == 82`  
**Mức độ:** P1

---

### TC-H-04: scan_yolo_dataset — quét cấu trúc train/val/test

**Input:** Thư mục YOLO chuẩn  
**Kết quả mong đợi:** List `DatasetItem` với đúng `split` cho mỗi ảnh  
**Mức độ:** P0

---

### TC-H-05: scan_yolo_dataset — ảnh không có nhãn → label_path=None

**Kết quả mong đợi:** `item.label_path is None` cho ảnh không có `.txt`  
**Mức độ:** P1

---

### TC-H-06: get_class_names — 82 tên tiếng Việt theo thứ tự

**Kết quả mong đợi:** `len(get_class_names()) == 82`; mỗi phần tử không rỗng  
**Mức độ:** P1

---

## 11. Module I — Quality Gate Validator & Snapshot

> **Files:** `src/trafficvision/data/validator.py`, `src/trafficvision/data/snapshot.py`  
> **Test files:** `tests/data/test_validator.py`, `tests/data/test_snapshot.py`

### TC-I-01: Dataset sạch → is_valid=True

**Input:** Synthetic dataset 10 ảnh hợp lệ  
**Kết quả mong đợi:** `report.is_valid == True`, `report.has_blocking == False`  
**Mức độ:** P0

---

### TC-I-02: Ảnh 0 byte → CORRUPT_IMAGE (blocking)

**Kết quả mong đợi:** `code="CORRUPT_IMAGE"`, `level="blocking"`, `has_blocking==True`  
**Mức độ:** P0

---

### TC-I-03: Ảnh giả mạo đuôi → CORRUPT_IMAGE (blocking)

**Input:** Text file đổi tên thành `.jpg`  
**Kết quả mong đợi:** `code="CORRUPT_IMAGE"`, `has_blocking==True`  
**Mức độ:** P0

---

### TC-I-04: Nhãn sai cấu trúc → MALFORMED_YOLO_LINE (blocking)

**Input:** Dòng nhãn có != 5 giá trị  
**Kết quả mong đợi:** `code="MALFORMED_YOLO_LINE"`, `level="blocking"`  
**Mức độ:** P0

---

### TC-I-05: Class ID ngoài [0, 81] → CLASS_ID_OUT_OF_RANGE (blocking)

**Input a:** `class_id=82` / **Input b:** `class_id=-1`  
**Kết quả mong đợi:** `code="CLASS_ID_OUT_OF_RANGE"`, `has_blocking==True`  
**Mức độ:** P0 *(Review Focus Plan 2)*

---

### TC-I-06: Tọa độ không hợp lệ → INVALID_COORDINATES (blocking)

**Input:** `x_center=-0.1`, `width=0`, `y_center=1.5`  
**Kết quả mong đợi:** `code="INVALID_COORDINATES"`, `has_blocking==True`  
**Mức độ:** P0

---

### TC-I-07: NaN/Inf trong tọa độ → blocking

**Input:** `0 0.5 nan 0.2 0.2`  
**Kết quả mong đợi:** `report.has_blocking == True`  
**Mức độ:** P0

---

### TC-I-08: Ảnh trùng exact (SHA-256) giữa train/val → DATA_LEAKAGE (blocking)

**Kết quả mong đợi:** `code="DATA_LEAKAGE"`, `level="blocking"`  
**Mức độ:** P0 *(Review Focus Plan 2)*

---

### TC-I-09: Mất cân bằng lớp > 10:1 → warning, không blocking

**Điều kiện:** Lớp A: 100 mẫu; lớp B: 5 mẫu  
**Kết quả mong đợi:** `has_blocking==False`; `warnings` chứa `"CLASS_IMBALANCE"`  
**Mức độ:** P1

---

### TC-I-10: Lớp ít mẫu < 5 → LOW_SAMPLE_COUNT (warning)

**Kết quả mong đợi:** `has_blocking==False`; `warnings` chứa `"LOW_SAMPLE_COUNT"`  
**Mức độ:** P1

---

### TC-I-11: Box quá nhỏ → SMALL_BBOX (warning, không blocking)

**Input:** Normalized area < 0.0001  
**Kết quả mong đợi:** `has_blocking==False`; `warnings` chứa `"SMALL_BBOX"`  
**Mức độ:** P1

---

### TC-I-12: Nhãn rỗng = ảnh nền → không blocking

**Input:** File `.txt` tồn tại nhưng rỗng  
**Kết quả mong đợi:** Không có `"CORRUPT_IMAGE"` trong blocking errors  
**Mức độ:** P1

---

### TC-I-13: create_snapshot — từ chối khi has_blocking=True

**Kết quả mong đợi:** Raise exception hoặc trả về None; không tạo snapshot  
**Mức độ:** P0

---

### TC-I-14: create_snapshot — data.yaml có 82 tên tiếng Việt

**Kết quả mong đợi:**
- `snapshot_dir/data.yaml` tồn tại
- `names:` list có 82 phần tử tiếng Việt
- `snapshot_manifest.json` có checksum

**Mức độ:** P0

---

### TC-I-15: create_snapshot — bất biến

**Điều kiện:** Tạo snapshot → sửa file gốc  
**Kết quả mong đợi:** File trong snapshot_dir không thay đổi  
**Mức độ:** P1

---

## 12. Module J — EDA Engine

> **Files:** `src/trafficvision/data/eda.py`  
> **Test files:** `tests/data/test_eda.py`

### TC-J-01: Đếm đúng số ảnh theo split

**Input:** 8 train, 2 val, 2 test  
**Kết quả mong đợi:** `eda.split_summary["train"]["images"] == 8`  
**Mức độ:** P1

---

### TC-J-02: Phân loại kích thước box theo COCO

| Loại | Diện tích |
|------|-----------|
| Nhỏ | < 1024 px² |
| Vừa | 1024–9216 px² |
| Lớn | > 9216 px² |

**Kết quả mong đợi:** `eda.size_distribution` có keys `"small"`, `"medium"`, `"large"` đúng  
**Mức độ:** P1

---

### TC-J-03: save_eda_summary → eda_report.json parse được

**Kết quả mong đợi:** File tồn tại; `json.loads()` không lỗi  
**Mức độ:** P1

---

### TC-J-04: Phân bố tâm box x, y trong khoảng [0, 1]

**Kết quả mong đợi:** `eda.bbox_stats` chứa giá trị mean x, y hợp lệ  
**Mức độ:** P2

---

## 13. Module K — Training Engine

> **Files:** `src/trafficvision/training/config.py`, `src/trafficvision/training/state.py`, `src/trafficvision/training/manager.py`  
> **Test files:** `tests/training/test_training_config.py`, `tests/training/test_training_state.py`, `tests/training/test_training_manager.py`

### TC-K-01: TrainingConfig — validation giá trị

| Tham số | Rule | Input lỗi | Kết quả |
|---------|------|-----------|---------|
| `batch` | >= 1 | batch=0 | Raise |
| `epochs` | >= 1 | epochs=-1 | Raise |
| `imgsz` | bội số 32 | imgsz=100 | Raise |
| `imgsz` | bội số 32 | imgsz=640 | OK |

**Mức độ:** P1

---

### TC-K-02: TrainingConfig — round-trip JSON

**Kết quả mong đợi:** Config sau round-trip bằng config gốc  
**Mức độ:** P1

---

### TC-K-03: TrainingState — default values

**Kết quả mong đợi:** `status="idle"`, `current_epoch=0`, `best_map50=0.0`  
**Mức độ:** P1

---

### TC-K-04: TrainingState — serialize từ disk

**Kết quả mong đợi:** state.json → đọc lại → giá trị khớp  
**Mức độ:** P1

---

### TC-K-05: TrainingManager — khởi chạy subprocess và ghi PID

**Kết quả mong đợi:** `run.pid` tồn tại; PID là số nguyên dương  
**Mức độ:** P0

---

### TC-K-06: TrainingManager — get_state đọc từ disk

**Điều kiện:** Ghi `state.json` thủ công  
**Kết quả mong đợi:** `manager.get_state(run_id).status` khớp  
**Mức độ:** P1

---

### TC-K-07: TrainingManager — stop_training tạo stop.signal

**Kết quả mong đợi:** File `stop.signal` tồn tại trong run directory  
**Mức độ:** P1

---

### TC-K-08: TrainingManager — crash recovery *(Review Focus Plan 2)*

**Điều kiện:** `state.json` có `status="running"` nhưng PID không còn  
**Kết quả mong đợi:** `get_state()` tự cập nhật sang `status="failed"` với message rõ ràng  
**Mức độ:** P0

---

### TC-K-09: TrainingManager — list_runs

**Input:** 2 runs  
**Kết quả mong đợi:** `manager.list_runs()` trả về 2 phần tử  
**Mức độ:** P1

---

## 14. Module L — Evaluation, ONNX Export & Candidate

> **Test files:** `tests/training/test_evaluator.py`, `tests/training/test_exporter.py`, `tests/training/test_candidate.py`

### TC-L-01: EvaluationMetrics — validate fields

**Kết quả mong đợi:** `0 <= precision <= 1`, `0 <= map50 <= 1`  
**Mức độ:** P1

---

### TC-L-02: evaluate_checkpoint — trích xuất chỉ số

**Điều kiện:** Fake YOLO result với map50=0.85  
**Kết quả mong đợi:** `metrics.map50 == 0.85`; các chỉ số khác không null  
**Mức độ:** P1

---

### TC-L-03: export_and_verify_onnx — parity pass

**Input:** `max_abs_diff=0.001` (<= tolerance 1e-3)  
**Kết quả mong đợi:** `result.is_parity_valid == True`  
**Mức độ:** P0

---

### TC-L-04: export_and_verify_onnx — parity fail *(Review Focus Plan 2)*

**Input:** `max_abs_diff=0.1` (> tolerance)  
**Kết quả mong đợi:** `result.is_parity_valid == False`; không cho promotion  
**Mức độ:** P0

---

### TC-L-05: export_and_verify_onnx — file không tồn tại → raise

**Kết quả mong đợi:** Raise exception rõ ràng  
**Mức độ:** P1

---

### TC-L-06: package_candidate — cấu trúc thư mục

**Kết quả mong đợi:**
- `candidate/model.onnx` ✓
- `candidate/manifest.json` có `stage="candidate"`, 82 lớp, SHA-256 chính xác ✓
- `candidate/benchmark.json` có `cpu_latency_ms`, `cpu_fps`, `is_parity_valid` ✓
- `candidate/test_metrics.json` có `map50`, `precision`, `recall`, `confusion_matrix` ✓

**Mức độ:** P0

---

### TC-L-07: package_candidate — parity failure ghi vào manifest

**Input:** `is_parity_valid=False`, `max_abs_diff=0.045`  
**Kết quả mong đợi:** `manifest.metrics["is_parity_valid"] == False`  
**Mức độ:** P1

---

## 15. Module M — Promotion, Backup & Rollback

> **Test files:** `tests/test_promotion_rollback.py`

### TC-M-01: promote_candidate — tạo backup trước khi thay thế

**Kết quả mong đợi:**
- `artifacts/backups/<timestamp>_<model_id>/manifest.json` tồn tại
- Tên thư mục chứa timestamp
- Backup SHA-256 khớp model production cũ

**Mức độ:** P0

---

### TC-M-02: promote_candidate — production mới có 82 lớp

**Kết quả mong đợi:** `registry.get_production().manifest.class_names` có 82 phần tử  
**Mức độ:** P0

---

### TC-M-03: promote_candidate — từ chối thiếu manifest

**Kết quả mong đợi:** Raise exception; production không thay đổi  
**Mức độ:** P0

---

### TC-M-04: promote_candidate — từ chối checksum sai

**Kết quả mong đợi:** Raise `ModelIntegrityError`  
**Mức độ:** P0

---

### TC-M-05: promote_candidate — từ chối số lớp không phải 82

**Input a:** 80 lớp / **Input b:** 1 lớp  
**Kết quả mong đợi:** Raise `ModelPromotionError`; production không thay đổi  
**Mức độ:** P0

---

### TC-M-06: promote_candidate — từ chối ONNX smoke test thất bại

**Kết quả mong đợi:** Raise `ModelIntegrityError`  
**Mức độ:** P0

---

### TC-M-07: promote_candidate — rollback tự động khi verify sau thất bại *(Review Focus Plan 2)*

**Điều kiện:** Verify raise exception sau khi đã thay thế  
**Kết quả mong đợi:** Production khôi phục về model trước; không trạng thái hỏng  
**Mức độ:** P0

---

### TC-M-08: rollback_to_backup — khôi phục về bản mới nhất

**Input:** 2 backups theo thứ tự thời gian  
**Kết quả mong đợi:** `rollback_to_backup()` → production = backup mới nhất  
**Mức độ:** P0

---

### TC-M-09: rollback_to_backup — không có backup → raise

**Kết quả mong đợi:** Raise `ModelNotFoundError`  
**Mức độ:** P1

---

### TC-M-10: rollback_to_backup — backup_id cụ thể

**Kết quả mong đợi:** `rollback_to_backup("id_A")` → production = model-A  
**Mức độ:** P1

---

### TC-M-11: list_backups — sắp xếp giảm dần theo timestamp

**Input:** 3 backups với timestamps khác nhau  
**Kết quả mong đợi:** `list_backups()[0]` là backup mới nhất  
**Mức độ:** P1

---

### TC-M-12: rollback — backup bị corrupt → raise

**Kết quả mong đợi:** Raise `ModelIntegrityError`  
**Mức độ:** P1

---

### TC-M-13: baseline bất biến sau promotion

**Kết quả mong đợi:** `artifacts/baseline/<id>/model.onnx` không thay đổi  
**Mức độ:** P0

---

## 16. Module N — Giao diện Huấn luyện AI

> **Test files:** `tests/ui/test_training_page.py`

### TC-N-01: Hiển thị đúng 4 bước

**Kết quả mong đợi:** UI chứa "Dữ liệu", "Kiểm định", "Huấn luyện", "Đánh giá"  
**Mức độ:** P0

---

### TC-N-02: Bước 1 — ô nhập thư mục + nút quét

**Kết quả mong đợi:** `at.text_input >= 1`; button "quét" hoặc "mẫu" tồn tại  
**Mức độ:** P1

---

### TC-N-03: Bước 2 — lỗi blocking khóa nút bắt đầu

**Điều kiện:** Ảnh corrupt → validate  
**Kết quả mong đợi:**
- `at.error` chứa thông báo lỗi
- Button "bắt đầu" bị `disabled=True`

**Mức độ:** P0

---

### TC-N-04: Bước 2 — dataset hợp lệ hiển thị EDA

**Điều kiện:** Dataset sạch → validate  
**Kết quả mong đợi:** Thông tin EDA hiển thị; button "snapshot" tồn tại  
**Mức độ:** P1

---

### TC-N-05: Bước 3 — controls cấu hình

**Kết quả mong đợi:** `at.number_input >= 2`; `at.checkbox >= 1`; buttons "bắt đầu" + "dừng"  
**Mức độ:** P1

---

### TC-N-06: Bước 3 — vùng metrics thời gian thực

**Kết quả mong đợi:** UI chứa "epoch", "mAP", "loss"  
**Mức độ:** P1

---

### TC-N-07: Bước 4 — promotion button

**Điều kiện:** Candidate 82 lớp hợp lệ  
**Kết quả mong đợi:** Button "production" hoặc "thăng cấp" tồn tại và hoạt động  
**Mức độ:** P0

---

## 17. Integration Tests

> **Test files:** `tests/integration/test_baseline_flow.py`, `tests/integration/test_phase2_flow.py`

### TC-INT-01: Baseline flow — ảnh → annotated + CSV + history

**Flow:** install baseline → `analyze_image_upload("cam.jpg", jpeg_bytes)`  
**Kết quả mong đợi:** annotated file tồn tại; CSV tồn tại; `repo.list_recent()` có 1 record  
**Mức độ:** P0

---

### TC-INT-02: Phase 2 flow — dataset→validate→snapshot→candidate→promote→inference→rollback

**Kết quả mong đợi:** Mọi bước không raise; nhãn inference thuộc danh mục 82 lớp tiếng Việt  
**Mức độ:** P0

---

### TC-INT-03: CLI validate_dataset — exit 0 + eda_report.json

**Command:** `python scripts/validate_dataset.py --data-dir <valid>`  
**Kết quả mong đợi:** `returncode == 0`; `eda_report.json` tồn tại  
**Mức độ:** P1

---

### TC-INT-04: CLI validate_dataset — exit 1 khi có blocking error

**Command:** `python scripts/validate_dataset.py --data-dir <invalid>`  
**Kết quả mong đợi:** `returncode == 1`; "blocking" hoặc "Error" trong output  
**Mức độ:** P1

---

### TC-INT-05: CLI promote_model — promote → rollback

**Commands:** promote → list-backups → rollback  
**Kết quả mong đợi:** Mỗi command `returncode == 0`; production thay đổi đúng chiều  
**Mức độ:** P1

---

### TC-INT-06: CLI train — help + validation

**Kết quả mong đợi:** `--help` in ra các flags; `--batch 0` → `returncode == 1`  
**Mức độ:** P1

---

## 18. UAT & Hiệu năng

> Thực hiện thủ công. Tham chiếu Spec §10.3

| ID | Kịch bản | Input | Kết quả mong đợi | Thiết bị |
|----|----------|-------|-----------------|---------|
| UAT-01 | Ảnh không có biển báo | Cảnh quan trống | count=0; CSV chỉ header; không crash | CPU |
| UAT-02 | Ảnh nhiều biển báo | Giao lộ ≥ 5 biển | Phát hiện ≥ 1; bbox hiển thị đúng | CPU |
| UAT-03 | Ảnh biển rất nhỏ | Biển < 1% diện tích | Không crash; thông báo hạn chế | CPU |
| UAT-04 | Ảnh thiếu sáng | Chụp đêm / mờ | Không crash; thông báo hỗ trợ | CPU |
| UAT-05 | File sai định dạng | PDF đổi tên `.jpg` | Lỗi tiếng Việt rõ ràng; không crash | CPU |
| UAT-06 | Video dài > 5 phút | MP4 300 giây | Thanh tiến độ cập nhật; không OOM | CPU macOS |
| UAT-07 | Video codec lỗi | Codec không phổ biến | Lỗi rõ ràng hoặc codec fallback | CPU |
| UAT-08 | Reload tab khi training | Tab reload giữa chừng | Job vẫn chạy; UI hiển thị đúng trạng thái | macOS |
| UAT-09 | Rollback sau promotion lỗi | Candidate lỗi sau promote | Auto rollback; không mất production | CPU |
| UAT-10 | Benchmark CPU | Ảnh 1080p | Ghi nhận inference ms và FPS | macOS + Windows |

---

## 19. Acceptance Criteria Checklist

> Tham chiếu Spec §15

| AC | Tiêu chí | Test case liên quan | ✓ |
|----|---------|-------------------|---|
| AC-1 | Cài đặt được trên Python hỗ trợ (macOS + Windows) | TC-A-01, UAT-01 | ☐ |
| AC-2 | Xử lý ảnh + video baseline, tạo output + CSV trên CPU | TC-INT-01, TC-E-01 | ☐ |
| AC-3 | Đọc manifest động; không hard-code 82 lớp hay metrics giả | TC-G-02, TC-G-04, TC-A-05 | ☐ |
| AC-4 | Validation khóa training khi có lỗi chặn | TC-I-01→TC-I-08, TC-N-03 | ☐ |
| AC-5 | Training chạy nền; checkpoint riêng; không ảnh hưởng production | TC-K-05→TC-K-08 | ☐ |
| AC-6 | ONNX 82 lớp; CPU benchmark tái tạo; parity <= 1e-3 | TC-L-03, TC-L-06 | ☐ |
| AC-7 | Promotion luôn tạo backup; rollback về production cũ | TC-M-01, TC-M-08, TC-M-13 | ☐ |
| AC-8 | Test tự động trọng yếu PASS; demo tái hiện được | TC-INT-01, TC-INT-02 | ☐ |
| AC-9 | Báo cáo cuối chứa số liệu từ artifact thật | Manual review | ☐ |

---

## Phụ lục A — Mapping Test Case → File pytest

| Module | File test | Nội dung kiểm thử | Số TC |
|--------|-----------|-------------------|-------|
| A | `tests/test_config.py`, `tests/test_domain.py` | Cấu hình app, schema, inference params | 10 |
| B | `tests/test_registry.py`, `tests/test_bootstrap.py` | Registry, SHA-256, baseline bootstrap | 8 |
| C | `tests/inference/test_ultralytics_predictor.py` | Adapter ONNX Runtime, NMS, output parsing | 6 |
| D | `tests/test_media.py`, `test_image.py`, `test_rendering.py` | Staging ảnh, letterbox, annotation BBox, CSV | 14 |
| E | `tests/inference/test_video.py` | Đọc frame tuần tự, callback progress, xuất video | 6 |
| F | `tests/test_history.py`, `test_settings.py`, `test_service.py` | SQLite history.db, settings JSON, AppServices | 12 |
| G | `tests/ui/test_analysis_page.py`, `test_secondary_pages.py`, `test_theme.py`, `test_components.py` | Streamlit AppTest, theme CSS, KPI cards, badges | 24 |
| H | `tests/data/test_catalog.py`, `tests/data/test_dataset.py` | Catalog 82 lớp QCVN 41:2019, staging scanner | 6 |
| I | `tests/data/test_validator.py`, `test_snapshot.py`, `test_repair.py` | Quality Gate 5 quy tắc, snapshot bất biến, Dataset Repair clamp BBox | 22 |
| J | `tests/data/test_eda.py` | Thống kê phân bố lớp, aspect ratio, bbox size | 4 |
| K | `tests/training/test_training_config.py`, `test_training_state.py`, `test_hardware.py`, `test_training_runner.py`, `test_training_manager.py` | Runner, manager, hardware detection, workers config, safe resume | 27 |
| L | `tests/training/test_evaluator.py`, `test_exporter.py`, `test_candidate.py` | Đánh giá test, export ONNX, parity check, finalize checkpoint | 18 |
| M | `tests/test_promotion_rollback.py` | Atomic copy, auto backup, verify SHA-256, rollback 1-click | 13 |
| N | `tests/ui/test_training_page.py` | Giao diện Lab 4 bước, live polling `@st.fragment`, nút resume & finalize | 18 |
| O | `tests/test_windows_launcher.py`, `tests/test_spec_gaps.py`, `tests/ui/test_app_smoke.py` | Launcher Windows batch, app smoke test, edge cases | 21 |
| Integration | `tests/integration/test_baseline_flow.py`, `test_phase2_flow.py` | Luồng ảnh/video end-to-end, luồng training → candidate → promotion | 6 |
| **Tổng cộng** | **37 files kiểm thử tự động** | **Tất cả các module của hệ thống** | **215 tests** |

---

## Phụ lục B — Priority Matrix

| Priority | Mô tả | Action khi fail |
|----------|-------|----------------|
| **P0 — Critical** | Bảo mật, toàn vẹn dữ liệu, luồng chính | Fix ngay trước mọi commit |
| **P1 — High** | Feature quan trọng, correctness | Fix trong sprint hiện tại |
| **P2 — Medium** | Edge case ít gặp, quality | Fix trước demo cuối kỳ |

---

*Tài liệu tạo từ spec `2026-09-27-trafficvision-design.md` và 2 implementation plans. Cập nhật mỗi khi spec thay đổi.*
