# TrafficVision Baseline Application Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng ứng dụng web TrafficVision hoàn chỉnh cho ảnh và video bằng YOLO11n pretrained gốc, chạy ONNX trên CPU và sẵn sàng thay bằng mô hình biển báo Việt Nam ở kế hoạch huấn luyện sau.

**Architecture:** Streamlit chỉ đảm nhiệm trình bày và gọi các service thuần Python. Model registry cung cấp model + manifest động; inference adapter dùng Ultralytics với backend ONNX; pipeline ảnh/video trả về domain object trung lập để UI, CSV và kho lịch sử cùng sử dụng. Video được xử lý tuần tự để giới hạn RAM, còn mọi tệp người dùng đều được ghi vào đường dẫn do ứng dụng sinh ra thay vì dùng trực tiếp tên tải lên.

**Tech Stack:** Python 3.11, Streamlit, Ultralytics YOLO11n, ONNX Runtime CPU, OpenCV, Pillow, Pydantic 2, pandas, PyYAML, SQLite, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-09-27-trafficvision-design.md`

## Global Constraints

- Giai đoạn này phải hoàn thành ứng dụng end-to-end với YOLO11n pretrained gốc trước khi thêm dữ liệu hoặc code huấn luyện.
- Mô hình baseline chưa chuyên biệt cho biển báo Việt Nam; giao diện phải luôn hiển thị cảnh báo này và không hiển thị metrics/82 lớp giả.
- Inference và UI không được hard-code số lớp hoặc tên lớp; toàn bộ metadata đến từ `ModelManifest`.
- Production inference dùng ONNX, batch 1, `imgsz=640`, `device="cpu"`; checkpoint `.pt` chỉ dùng cho bootstrap/export.
- Ứng dụng hỗ trợ ảnh JPG/PNG và video MP4/AVI/MOV; mặc định giới hạn ảnh 20 MB, video 500 MB và các giới hạn phải cấu hình được.
- Hệ thống chạy trên macOS và Windows với Python 3.11; không dùng shell path hoặc symlink phụ thuộc hệ điều hành.
- Không commit dữ liệu tải lên, model, kết quả, database runtime hoặc artifact sinh tự động.
- Không dùng webcam, tài khoản, cloud deployment, dữ liệu huấn luyện hoặc giao diện chạy training trong kế hoạch này.
- Mỗi task thực hiện theo TDD và kết thúc bằng một commit độc lập.

## Review Focus

- Tệp đổi đuôi hoặc ảnh/video hỏng phải bị từ chối theo nội dung, không chỉ theo tên/MIME; Task 4 và Task 5 có test tương ứng.
- Tên tệp tải lên có `../`, đường dẫn Windows hoặc Unicode không được thoát khỏi thư mục staging; Task 4 có test path traversal.
- Ảnh không có detection vẫn phải tạo ảnh kết quả hợp lệ và CSV chỉ có header; Task 4 có test tương ứng.
- Model ONNX bị sửa sau khi đăng ký phải thất bại trước inference do checksum không khớp; Task 2 và Task 3 có test tương ứng.
- Video lỗi giữa chừng phải đóng reader/writer, giữ trạng thái lỗi rõ ràng và không đưa output dở vào lịch sử; Task 5 và Task 6 có test tương ứng.

---

## File Map

### Project and configuration

- `pyproject.toml`: package metadata, runtime/dev dependencies and tool configuration.
- `.streamlit/config.toml`: upload ceiling, theme and headless server defaults.
- `configs/app.yaml`: checked-in application defaults.
- `app.py`: minimal Streamlit entry point.
- `src/trafficvision/config.py`: typed configuration loading and runtime paths.
- `src/trafficvision/domain.py`: shared immutable domain models.

### Model lifecycle and inference

- `src/trafficvision/registry.py`: manifest verification and production model resolution.
- `src/trafficvision/bootstrap.py`: download/export/register baseline model.
- `scripts/bootstrap_baseline.py`: CLI for first-time baseline installation.
- `src/trafficvision/inference/base.py`: predictor protocol.
- `src/trafficvision/inference/ultralytics.py`: ONNX predictor adapter.
- `src/trafficvision/inference/image.py`: image analysis orchestration.
- `src/trafficvision/inference/video.py`: bounded-memory video processing.

### Media, output and persistence

- `src/trafficvision/media.py`: content validation and safe staging.
- `src/trafficvision/rendering.py`: annotation and CSV serialization.
- `src/trafficvision/history.py`: SQLite analysis history and aggregate queries.
- `src/trafficvision/settings.py`: atomic local settings persistence.
- `src/trafficvision/service.py`: application-level image/video orchestration and history transaction boundary.

### Web UI

- `src/trafficvision/ui/app.py`: navigation, dependency wiring and page setup.
- `src/trafficvision/ui/theme.py`: approved navy/blue/teal visual contract.
- `src/trafficvision/ui/components.py`: reusable status, metric and download components.
- `src/trafficvision/ui/pages/analysis.py`: image/video upload and results.
- `src/trafficvision/ui/pages/history.py`: recent analyses.
- `src/trafficvision/ui/pages/statistics.py`: aggregate cards and charts.
- `src/trafficvision/ui/pages/model_info.py`: manifest/checksum/baseline status.
- `src/trafficvision/ui/pages/settings.py`: confidence, IoU and media limits.

### Tests and operator docs

- `tests/`: unit and integration tests mirroring the modules above.
- `tests/fixtures/`: small generated image/video/manifest fixtures only.
- `scripts/smoke_test.py`: non-interactive baseline inference smoke test.
- `README.md`: installation, bootstrap and run instructions for macOS/Windows.

## Task 1: Project foundation, configuration and domain contracts

**Files:**
- Create: `pyproject.toml`
- Create: `.streamlit/config.toml`
- Create: `configs/app.yaml`
- Create: `src/trafficvision/__init__.py`
- Create: `src/trafficvision/config.py`
- Create: `src/trafficvision/domain.py`
- Create: `tests/test_config.py`
- Create: `tests/test_domain.py`

**Interfaces:**
- Consumes: none.
- Produces: `AppConfig.load(path: Path, env: Mapping[str, str] | None = None) -> AppConfig`; `AppPaths.from_root(root: Path) -> AppPaths`; `ModelManifest`, `RegisteredModel`, `Detection`, `StagedMedia`, `InferenceOptions`, `VideoProgress`, `ImageAnalysis`, `VideoAnalysis`, `AnalysisRecord`, and `AnalysisArtifacts` Pydantic models.

- [ ] **Step 1: Write failing configuration tests**

Add `test_load_defaults_are_cross_platform`, `test_environment_overrides_thresholds`, and `test_invalid_threshold_is_rejected`. Assert defaults `confidence=0.25`, `iou=0.70`, `imgsz=640`, image limit `20 MiB`, video limit `500 MiB`, and that all runtime paths are children of the injected project root.

- [ ] **Step 2: Write failing domain contract tests**

Add tests asserting that `ModelManifest` accepts dynamic contiguous class maps, rejects an invalid SHA-256 or empty class map, and round-trips JSON; assert that `Detection` rejects confidence outside `[0,1]` and inverted `xyxy` coordinates.

- [ ] **Step 3: Run the focused tests and confirm the expected failure**

Run: `python -m pytest tests/test_config.py tests/test_domain.py -q`  
Expected: FAIL during import because `trafficvision.config` and `trafficvision.domain` do not exist.

- [ ] **Step 4: Add package/tool configuration**

Declare Python `>=3.11,<3.13`; runtime dependencies for Streamlit, Ultralytics, ONNX, ONNX Runtime, OpenCV, Pillow, Pydantic, pandas and PyYAML; dev dependencies for pytest, pytest-cov and Ruff. Configure a `src` package, pytest paths and Ruff target `py311`.

- [ ] **Step 5: Implement the typed configuration and domain models**

Use `pathlib.Path` throughout. `ModelManifest` fields are `schema_version`, `model_id`, `stage`, optional `source_model_id`, `artifact_filename`, `backend`, `task`, `class_names`, `imgsz`, `sha256`, `source`, `created_at`, and optional `metrics`; it must not assume 80 or 82 classes. `InferenceOptions` owns confidence/IoU, while `StagedMedia` and `VideoProgress` are the cross-module media contracts. `AnalysisArtifacts` owns the committed `AnalysisRecord`, final annotated-media path and final CSV path; pure image inference does not know output paths.

- [ ] **Step 6: Verify Task 1**

Run: `python -m pytest tests/test_config.py tests/test_domain.py -q`  
Expected: all Task 1 tests PASS.  
Run: `python -m ruff check src tests`  
Expected: exit code 0.

- [ ] **Step 7: Commit Task 1**

```bash
git add pyproject.toml .streamlit/config.toml configs src/trafficvision tests/test_config.py tests/test_domain.py
git commit -m "chore: scaffold TrafficVision domain"
```

## Task 2: Model registry and baseline bootstrap

**Files:**
- Create: `src/trafficvision/registry.py`
- Create: `src/trafficvision/bootstrap.py`
- Create: `scripts/bootstrap_baseline.py`
- Create: `tests/test_registry.py`
- Create: `tests/test_bootstrap.py`

**Interfaces:**
- Consumes: `AppPaths`, `ModelManifest`, `RegisteredModel` from Task 1.
- Produces: `sha256_file(path: Path) -> str`; `ModelRegistry.install_baseline(model_file: Path, manifest: ModelManifest) -> RegisteredModel`; `ModelRegistry.get_production() -> RegisteredModel`; `ModelRegistry.verify(model: RegisteredModel) -> None`; `bootstrap_baseline(registry: ModelRegistry, model_name: str = "yolo11n.pt") -> RegisteredModel`.

- [ ] **Step 1: Write failing registry tests**

Test atomic installation into `artifacts/baseline/<model_id>` and `artifacts/production`; production resolution after install; refusal when manifest filename escapes its directory; and `ModelIntegrityError` after one byte of the ONNX file changes.

- [ ] **Step 2: Write a failing isolated bootstrap test**

Monkeypatch the Ultralytics model factory so no network/model runtime is used. Assert export is called with `format="onnx"`, `imgsz=640`, `batch=1`, `dynamic=False`, `simplify=False`, `device="cpu"`; assert class names come from the model metadata and the production manifest stage is `production` with `source_model_id` pointing to the immutable baseline.

- [ ] **Step 3: Run Task 2 tests and confirm failure**

Run: `python -m pytest tests/test_registry.py tests/test_bootstrap.py -q`  
Expected: FAIL because registry/bootstrap interfaces do not exist.

- [ ] **Step 4: Implement checksum-verified registry operations**

Use temporary sibling files plus `os.replace` for atomic writes. Copy files rather than symlinking so behavior matches Windows. `get_production()` must validate manifest schema, keep the resolved path within `production`, and verify checksum before returning.

- [ ] **Step 5: Implement baseline bootstrap and CLI**

Set `YOLO_AUTOINSTALL=False`; load `yolo11n.pt`; export fixed-shape ONNX without simplification-time dependency installation; build manifests from actual model metadata; install baseline and production through `ModelRegistry`. The CLI accepts `--project-root` and `--model-name`, prints the final model ID/path, and returns nonzero with an actionable message on download/export failure.

- [ ] **Step 6: Verify Task 2**

Run: `python -m pytest tests/test_registry.py tests/test_bootstrap.py -q`  
Expected: all Task 2 tests PASS.

- [ ] **Step 7: Commit Task 2**

```bash
git add src/trafficvision/registry.py src/trafficvision/bootstrap.py scripts/bootstrap_baseline.py tests/test_registry.py tests/test_bootstrap.py
git commit -m "feat: add baseline model registry"
```

## Task 3: Dynamic ONNX predictor adapter

**Files:**
- Create: `src/trafficvision/inference/__init__.py`
- Create: `src/trafficvision/inference/base.py`
- Create: `src/trafficvision/inference/ultralytics.py`
- Create: `tests/inference/test_ultralytics_predictor.py`

**Interfaces:**
- Consumes: checksum-verified `RegisteredModel`, `Detection` and `AppConfig` from Tasks 1–2.
- Produces: `Predictor` protocol with `predict(image_bgr: NDArray[np.uint8], *, confidence: float, iou: float) -> tuple[Detection, ...]`; `UltralyticsOnnxPredictor.from_registered(model: RegisteredModel) -> UltralyticsOnnxPredictor`.

- [ ] **Step 1: Write failing predictor adapter tests**

With a fake Ultralytics result, assert conversion of `xyxy`, confidence and class ID; class name must come from the manifest, not `result.names`. Add cases for no boxes, class ID absent from manifest, and arguments `imgsz=manifest.imgsz`, `device="cpu"`, `verbose=False`.

- [ ] **Step 2: Add the checksum review-focus test**

Create the predictor from a registered model, mutate the model before lazy load and assert `ModelIntegrityError` occurs before the Ultralytics factory is invoked.

- [ ] **Step 3: Run focused tests and confirm failure**

Run: `python -m pytest tests/inference/test_ultralytics_predictor.py -q`  
Expected: FAIL because predictor modules do not exist.

- [ ] **Step 4: Implement the predictor protocol and lazy ONNX adapter**

Keep Ultralytics imports inside the factory/load boundary so domain tests stay lightweight. Convert tensors with `.cpu().tolist()`. Raise `PredictionContractError` when the model returns a class not declared by the manifest; do not invent names.

- [ ] **Step 5: Verify Task 3**

Run: `python -m pytest tests/inference/test_ultralytics_predictor.py -q`  
Expected: all predictor tests PASS.

- [ ] **Step 6: Commit Task 3**

```bash
git add src/trafficvision/inference tests/inference/test_ultralytics_predictor.py
git commit -m "feat: add ONNX inference adapter"
```

## Task 4: Safe image intake, analysis, annotation and CSV

**Files:**
- Create: `src/trafficvision/media.py`
- Create: `src/trafficvision/inference/image.py`
- Create: `src/trafficvision/rendering.py`
- Create: `tests/test_media.py`
- Create: `tests/inference/test_image.py`
- Create: `tests/test_rendering.py`

**Interfaces:**
- Consumes: `Predictor`, `Detection`, `ImageAnalysis`, `AppConfig`.
- Produces: `stage_upload(filename: str, data: bytes, media_type: Literal["image", "video"], paths: AppPaths, config: AppConfig) -> StagedMedia`; `decode_image(media: StagedMedia) -> NDArray[np.uint8]`; `analyze_image(image_bgr: NDArray[np.uint8], predictor: Predictor, confidence: float, iou: float) -> ImageAnalysis`; `annotate_image(image_bgr, detections, font_resolver) -> bytes`; `detections_csv(detections, source_name: str) -> bytes`.

- [ ] **Step 1: Write failing safe-staging tests**

Assert `../secret.jpg`, `C:\\secret.jpg` and a Unicode filename all produce an application-generated UUID filename under `paths.staging`; original names remain metadata only. Assert oversize data and bytes that do not decode as the declared image type raise `MediaValidationError`.

- [ ] **Step 2: Write failing image-analysis tests**

Use a fake predictor to assert thresholds are passed through, elapsed time is nonnegative, dimensions are recorded and detections remain immutable. Add the no-detection case.

- [ ] **Step 3: Write failing rendering/export tests**

Assert annotation returns decodable PNG/JPEG bytes at original dimensions; a Vietnamese label such as `Cấm đi ngược chiều` does not raise; CSV columns are exactly `source,frame_index,timestamp_s,class_id,class_name,confidence,x1,y1,x2,y2`; no detections produces a header-only CSV.

- [ ] **Step 4: Run Task 4 tests and confirm failure**

Run: `python -m pytest tests/test_media.py tests/inference/test_image.py tests/test_rendering.py -q`  
Expected: FAIL because media/image/rendering modules do not exist.

- [ ] **Step 5: Implement safe media staging and decoding**

Inspect image content with Pillow/OpenCV rather than trusting extension or browser MIME. Never join runtime paths with the submitted filename. Preserve original filename only as sanitized display metadata.

- [ ] **Step 6: Implement image orchestration and rendering**

Use Pillow drawing over an RGB copy for Unicode-capable labels; resolve fonts in this order: configured project font, macOS Arial, Windows Arial, Linux DejaVu Sans, Pillow fallback. Clamp drawing coordinates to image bounds. Serialize tabular output deterministically with UTF-8 BOM for Excel compatibility on Windows.

- [ ] **Step 7: Verify Task 4**

Run: `python -m pytest tests/test_media.py tests/inference/test_image.py tests/test_rendering.py -q`  
Expected: all Task 4 tests PASS.

- [ ] **Step 8: Commit Task 4**

```bash
git add src/trafficvision/media.py src/trafficvision/inference/image.py src/trafficvision/rendering.py tests/test_media.py tests/inference/test_image.py tests/test_rendering.py
git commit -m "feat: analyze and export uploaded images"
```

## Task 5: Bounded-memory video pipeline

**Files:**
- Create: `src/trafficvision/inference/video.py`
- Create: `tests/inference/test_video.py`
- Create: `tests/fixtures/README.md`

**Interfaces:**
- Consumes: staged video, `Predictor`, rendering and CSV row serialization from Tasks 3–4.
- Produces: `process_video(input_path: Path, output_path: Path, csv_path: Path, predictor: Predictor, options: InferenceOptions, on_progress: Callable[[VideoProgress], None] | None = None) -> VideoAnalysis`; `VideoProcessingError`.

- [ ] **Step 1: Write failing video success tests**

Generate a tiny synthetic video during the test. Assert output dimensions/FPS/frame count match input, `on_progress` is monotonic and ends at `1.0`, detections are written incrementally to CSV, and the summary aggregates counts by class without storing annotated frames.

- [ ] **Step 2: Write failing invalid/corrupt video tests**

Assert renamed text bytes are rejected before processing. Use fake capture/writer objects to simulate failure in the middle; assert both are released, `VideoProcessingError` includes the failed frame, and the final output filename is absent because only a `.partial` file was written. Add a codec negotiation case where H.264 initialization fails and MP4V succeeds with an explicit fallback note in the result.

- [ ] **Step 3: Run Task 5 tests and confirm failure**

Run: `python -m pytest tests/inference/test_video.py -q`  
Expected: FAIL because video pipeline does not exist.

- [ ] **Step 4: Implement streaming video processing**

Read, infer, annotate and write one frame at a time. Write CSV rows as frames complete and retain only counters/timings in memory. Use a sibling partial output and `os.replace` only after successful close and re-open verification. Raise a clear error when FPS, dimensions or writer initialization are invalid.

- [ ] **Step 5: Verify Task 5**

Run: `python -m pytest tests/inference/test_video.py -q`  
Expected: all Task 5 tests PASS.

- [ ] **Step 6: Commit Task 5**

```bash
git add src/trafficvision/inference/video.py tests/inference/test_video.py tests/fixtures/README.md
git commit -m "feat: process uploaded videos safely"
```

## Task 6: History, statistics and runtime settings

**Files:**
- Create: `src/trafficvision/history.py`
- Create: `src/trafficvision/settings.py`
- Create: `src/trafficvision/service.py`
- Create: `tests/test_history.py`
- Create: `tests/test_settings.py`
- Create: `tests/test_service.py`

**Interfaces:**
- Consumes: `AnalysisRecord`, `AppConfig`, predictor, completed image/video output paths.
- Produces: `AnalysisRepository.add(record: AnalysisRecord) -> None`; `AnalysisRepository.list_recent(limit: int = 50) -> list[AnalysisRecord]`; `AnalysisRepository.class_totals() -> dict[str, int]`; `RuntimeSettingsStore.load() -> RuntimeSettings`; `RuntimeSettingsStore.save(settings: RuntimeSettings) -> None`; `AnalysisService.analyze_image_upload(filename: str, data: bytes) -> AnalysisArtifacts`; `AnalysisService.analyze_video_upload(filename: str, data: bytes, on_progress: Callable[[VideoProgress], None] | None = None) -> AnalysisArtifacts`.

- [ ] **Step 1: Write failing history tests**

Against a temporary SQLite database, assert newest-first history, limit enforcement, aggregate class totals and Unicode filenames.

- [ ] **Step 2: Write failing settings tests**

Assert missing settings returns config defaults; valid confidence/IoU/media limits round-trip; invalid values are rejected; and save uses atomic replacement so an injected write failure preserves the previous JSON.

- [ ] **Step 3: Write failing application-service transaction tests**

Assert completed image/video outputs are inserted into history only after their final files exist. Inject a mid-video failure and assert no history row is written and no `.partial` output is exposed.

- [ ] **Step 4: Run Task 6 tests and confirm failure**

Run: `python -m pytest tests/test_history.py tests/test_settings.py tests/test_service.py -q`  
Expected: FAIL because persistence modules do not exist.

- [ ] **Step 5: Implement SQLite repository and atomic settings store**

Initialize schema idempotently and use context-managed transactions. Store per-analysis class counts as JSON text, while all paths remain app-controlled. Settings are local runtime state under `artifacts/state` and are not committed.

- [ ] **Step 6: Implement the application-service boundary**

The service loads current runtime settings, stages input, calls the appropriate image/video pipeline, verifies final outputs and only then commits `AnalysisRecord`. Known domain exceptions pass through for the UI to translate; partial outputs never become successful records.

- [ ] **Step 7: Verify Task 6**

Run: `python -m pytest tests/test_history.py tests/test_settings.py tests/test_service.py -q`  
Expected: all Task 6 tests PASS.

- [ ] **Step 8: Commit Task 6**

```bash
git add src/trafficvision/history.py src/trafficvision/settings.py src/trafficvision/service.py tests/test_history.py tests/test_settings.py tests/test_service.py
git commit -m "feat: persist analysis history and settings"
```

## Task 7: Polished Streamlit shell and analysis page

**Files:**
- Create: `app.py`
- Create: `src/trafficvision/ui/__init__.py`
- Create: `src/trafficvision/ui/app.py`
- Create: `src/trafficvision/ui/theme.py`
- Create: `src/trafficvision/ui/components.py`
- Create: `src/trafficvision/ui/pages/__init__.py`
- Create: `src/trafficvision/ui/pages/analysis.py`
- Create: `tests/ui/test_app_smoke.py`
- Create: `tests/ui/test_analysis_page.py`

**Interfaces:**
- Consumes: registry, `AnalysisService`, repository and settings store.
- Produces: `main() -> None`; `render_analysis_page(services: AppServices) -> None`; `AppServices` dependency container with lazy `predictor()` loading.

- [ ] **Step 1: Write failing no-model app smoke test**

Use `streamlit.testing.v1.AppTest` with a temporary project root. Assert the app renders `TrafficVision`, shows a setup action/message when no production manifest exists, and does not crash or claim `82 lớp`.

- [ ] **Step 2: Write failing baseline analysis-page tests**

Inject fake services and assert the page shows `Baseline — chưa fine-tune biển báo Việt Nam`, accepts only declared media extensions, renders real model/class count from the manifest, displays no fabricated metrics, and exposes result/CSV download controls after image success.

- [ ] **Step 3: Run UI tests and confirm failure**

Run: `python -m pytest tests/ui/test_app_smoke.py tests/ui/test_analysis_page.py -q`  
Expected: FAIL because UI modules do not exist.

- [ ] **Step 4: Implement app shell and approved visual theme**

Match the approved navy sidebar, blue/teal accents, light cards and Vietnamese copy. Keep CSS selectors scoped to a root class where possible. Navigation items in this task are Phân tích, Lịch sử, Thống kê, Huấn luyện AI, Thông tin mô hình and Thiết lập; Huấn luyện AI displays `Giai đoạn 2 — chưa kích hoạt` and contains no training controls yet.

- [ ] **Step 5: Implement image/video analysis interactions**

Use separate tabs. Stage uploads only after the user presses Phân tích. For video, update `st.progress` through the callback. Present annotated media, detection summary, inference timing, class table and deferred download buttons. Catch known domain errors and show actionable Vietnamese messages without stack traces.

- [ ] **Step 6: Verify Task 7**

Run: `python -m pytest tests/ui/test_app_smoke.py tests/ui/test_analysis_page.py -q`  
Expected: all Task 7 tests PASS.

- [ ] **Step 7: Commit Task 7**

```bash
git add app.py src/trafficvision/ui tests/ui
git commit -m "feat: add TrafficVision analysis dashboard"
```

## Task 8: History, statistics, model information and settings pages

**Files:**
- Create: `src/trafficvision/ui/pages/history.py`
- Create: `src/trafficvision/ui/pages/statistics.py`
- Create: `src/trafficvision/ui/pages/model_info.py`
- Create: `src/trafficvision/ui/pages/settings.py`
- Create: `src/trafficvision/ui/pages/training_placeholder.py`
- Create: `tests/ui/test_secondary_pages.py`

**Interfaces:**
- Consumes: `AppServices`, `AnalysisRepository`, `RuntimeSettingsStore`, `RegisteredModel`.
- Produces: one `render_*_page(services: AppServices) -> None` function per page.

- [ ] **Step 1: Write failing page view-model tests**

Assert empty history/statistics states are explicit; populated history is newest first; model page shows model ID, backend, checksum prefix, source, dynamic class count and baseline warning; settings save validated values; training placeholder contains the approved sequence Dữ liệu → Kiểm định → Huấn luyện → Đánh giá & xuất but no start button.

- [ ] **Step 2: Run secondary-page tests and confirm failure**

Run: `python -m pytest tests/ui/test_secondary_pages.py -q`  
Expected: FAIL because page modules do not exist.

- [ ] **Step 3: Implement secondary pages**

Reuse Task 7 components. Never read model binaries in page render; use verified manifest metadata. Statistics charts use repository aggregates only. Settings changes take effect on the next analysis and display persisted values after rerun.

- [ ] **Step 4: Verify Task 8**

Run: `python -m pytest tests/ui/test_secondary_pages.py -q`  
Expected: all Task 8 tests PASS.

- [ ] **Step 5: Commit Task 8**

```bash
git add src/trafficvision/ui/pages tests/ui/test_secondary_pages.py
git commit -m "feat: complete baseline dashboard pages"
```

## Task 9: End-to-end smoke path, documentation and release checks

**Files:**
- Create: `scripts/smoke_test.py`
- Create: `tests/integration/test_baseline_flow.py`
- Create: `README.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: every public interface from Tasks 1–8.
- Produces: `python scripts/smoke_test.py --project-root . --image <path>` operator check; documented macOS/Windows setup and run commands.

- [ ] **Step 1: Write the failing integration test**

Using a fake predictor but real staging, rendering, CSV and SQLite repository, run one image through `AnalysisService`. Assert annotated output decodes, CSV contains its detection, history is inserted only after both outputs exist, and the baseline warning remains part of the returned presentation metadata.

- [ ] **Step 2: Run integration test and confirm failure**

Run: `python -m pytest tests/integration/test_baseline_flow.py -q`  
Expected: FAIL until the full service composition is wired.

- [ ] **Step 3: Implement smoke CLI composition**

The CLI loads verified production, performs one image inference and prints model ID, backend, detection count, elapsed milliseconds and output paths. It exits nonzero for missing model, checksum mismatch or invalid image.

- [ ] **Step 4: Write operator documentation**

Document virtual environment creation for PowerShell and zsh, dependency installation, `bootstrap_baseline.py`, `streamlit run app.py`, smoke test, runtime directories, baseline limitations and the exact point at which the later training plan replaces production. Link the design spec and this plan.

- [ ] **Step 5: Run the complete release gate**

Run: `python -m pytest -q`  
Expected: all tests PASS.  
Run: `python -m ruff check .`  
Expected: exit code 0.  
Run: `python -m ruff format --check .`  
Expected: exit code 0.  
Run: `git status --short`  
Expected: only intentional Task 9 changes before commit; no model, upload, DB or output artifacts.

- [ ] **Step 6: Perform a real local baseline smoke test**

Run: `python scripts/bootstrap_baseline.py --project-root .`  
Expected: verified baseline and production ONNX manifests are created.  
Run: `python scripts/smoke_test.py --project-root . --image <sample-image>`  
Expected: exit code 0 and printed output paths.  
Run: `streamlit run app.py`  
Expected: dashboard opens, baseline warning is visible, and the same sample image can be analyzed/downloaded.

- [ ] **Step 7: Commit Task 9**

```bash
git add scripts/smoke_test.py tests/integration/test_baseline_flow.py README.md .gitignore
git commit -m "docs: finish baseline application workflow"
```

## Deferred Plans

After every Task 9 gate passes, create and execute separate plans in this order:

1. **Dataset validation and EDA:** acquire the 82-class dataset, provenance, immutable snapshot, blocking/warning quality gates and generated EDA report.
2. **Training laboratory:** background YOLO11n fine-tuning job, checkpoint/resume UI, experiment metrics and GTX 1050 Ti safeguards.
3. **Evaluation and promotion:** held-out test metrics, FP/FN analysis, ONNX equivalence, CPU benchmark, backup, atomic promotion and rollback.
4. **Final academic report:** populate the approved five-chapter structure exclusively from generated artifacts and verified screenshots.

## Implementation References

- Ultralytics prediction API and memory-efficient streaming: <https://docs.ultralytics.com/modes/predict/>
- Ultralytics ONNX export options: <https://docs.ultralytics.com/modes/export/>
- Streamlit upload behavior and security caveat: <https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader>
- Streamlit progress API: <https://docs.streamlit.io/develop/api-reference/status/st.progress>
- Streamlit deferred downloads: <https://docs.streamlit.io/develop/api-reference/widgets/st.download_button>
