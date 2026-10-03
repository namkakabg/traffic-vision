# Kế hoạch triển khai hiệu chỉnh hard-case và fine-tune

> **Dành cho agent thực thi:** BẮT BUỘC dùng sub-skill `superpowers:subagent-driven-development` (khuyến nghị) hoặc `superpowers:executing-plans` để thực hiện kế hoạch theo từng task. Dùng checkbox `- [ ]` để theo dõi tiến độ.

**Mục tiêu:** Cho phép người dùng TrafficVision cục bộ biến các nhận dạng sai đã được duyệt thành Candidate fine-tune hard-case độc lập, không thay đổi tập test độc lập hoặc model Production.

**Kiến trúc:** Bổ sung kho hiệu chỉnh bất biến, gồm SQLite riêng và các tệp ảnh/revision; sau đó tạo snapshot hard-case đã duyệt, song song với source snapshot. Trang hiệu chỉnh Streamlit đảm nhiệm annotation/review có gợi ý từ model; `TrainingManager` hiện tại tạo run mới từ `best.pt` đã chọn, còn evaluator challenge riêng so sánh cùng một tập correction giữ lại trước và sau fine-tune.

**Công nghệ:** Python 3.13, Streamlit, Pydantic, Pillow, SQLite, Ultralytics YOLO, pytest, Ruff.

**Đặc tả:** `docs/superpowers/specs/2026-09-30-hard-case-correction-design.md`

## Ràng buộc chung

- Mọi dữ liệu ở cục bộ; không tải ảnh hoặc nhãn từ Internet.
- Upload correction nhận JPG/JPEG/PNG/WebP, tuân thủ giới hạn media hiện có, giữ nguyên upload/hash gốc và tạo preview chuẩn hóa an toàn.
- Tên/ID lớp luôn lấy từ catalog 82 lớp đang hoạt động hoặc manifest model đã chọn; không hard-code danh sách lớp ở UI.
- Revision pending/rejected không bao giờ vào snapshot; correction `challenge_only` không vào train/val; test split hiện có không bị thay đổi dù chỉ một byte.
- Fine-tune là run mới từ `best.pt` đã chọn, không dùng `resume=True`; dữ liệu gồm base data cộng các correction đã duyệt.
- Giữ các cơ chế validation hiện có, đóng gói Candidate, promotion Production, an toàn GPU/CPU và `workers=0`.
- Không tự động train hoặc tự động promote.

## Điểm cần review kỹ

- WebP có alpha/EXIF orientation phải cho ra preview có đúng hình học được dùng bởi box trên UI và export YOLO. (Task 2)
- Correction có hash trùng source train/val/test hoặc challenge không bao giờ được vào fine-tune. (Task 3)
- Sửa correction đã approved phải tạo revision pending mới, không được sửa trực tiếp provenance của snapshot. (Task 1)
- Mỗi gợi ý thu thập phải trích dẫn số lượng/evidence challenge đang có, không được bịa claim về confusion. (Task 4)
- Lệnh fine-tune phải dùng `best.pt` được chọn với `resume_checkpoint=None` và không được thay đổi registry state. (Task 5)

---

### Task 1: Kho provenance correction và state machine review

**Tệp:**
- Create: src/trafficvision/data/corrections.py
- Modify: src/trafficvision/config.py
- Modify: src/trafficvision/data/__init__.py
- Test: tests/data/test_corrections.py

**Giao diện:**
- Đầu vào: `AppPaths`, catalog 82 lớp, quy ước SHA-256 hiện có.
- Đầu ra: `CorrectionPaths`, `CorrectionRevision`, `BoxAnnotationDraft`, `CorrectionStatus`, `CorrectionTarget` và `CorrectionRepository`.

- [ ] **Bước 1: Viết test repository thất bại**

Viết `test_approved_revision_is_immutable_and_edit_creates_pending_successor`: tạo revision pending, approve nó, sửa lại, rồi kiểm tra bản gốc vẫn approved còn successor là pending với `parent_revision_id`.

Kiểm thử source hash, target, reviewer/author, class ID không hợp lệ, thứ tự list xác định được và hành vi mở lại SQLite.

- [ ] **Bước 2: Xác nhận RED**

Chạy: `.venv\Scripts\python.exe -m pytest tests/data/test_corrections.py -q`

Kỳ vọng: FAIL vì chưa có correction DTO/repository.

- [ ] **Bước 3: Triển khai kho dữ liệu**

Thêm `CorrectionPaths` bên dưới `artifacts/corrections` để lưu source image bất biến, preview, revision JSON và `state.db`. Triển khai schema/create/get/list/revise/approve/reject của repository với đóng kết nối SQLite tường minh và state transition hợp lệ.

- [ ] **Bước 4: Xác nhận GREEN**

Chạy: `.venv\Scripts\python.exe -m pytest tests/data/test_corrections.py -q`

Kỳ vọng: PASS.

- [ ] **Bước 5: Commit**

git add src/trafficvision/config.py src/trafficvision/data/corrections.py src/trafficvision/data/__init__.py tests/data/test_corrections.py
git commit -m "feat: add reviewed correction store"

### Task 2: Hình học annotation an toàn với WebP và gợi ý model

**Tệp:**
- Create: src/trafficvision/data/annotations.py
- Modify: src/trafficvision/inference/ultralytics.py
- Test: tests/data/test_annotations.py
- Test: tests/inference/test_ultralytics.py

**Giao diện:**
- Đầu vào: `CorrectionRevision`, media limit đã cấu hình, Ultralytics adapter đang hoạt động.
- Đầu ra: `NormalizedImage`, `BoxAnnotation` đã validate, chuyển đổi pixel/YOLO, preview crop helper và `suggest_annotations()`.

- [ ] **Bước 1: Viết test thất bại**

Viết `test_webp_rgba_upload_preserves_source_and_exports_yolo_geometry`: fixture WebP tạo preview chuẩn hóa trong khi source hash/tệp không đổi; một pixel box đã biết tạo ra đúng dòng YOLO kỳ vọng.

Kiểm thử tệp hỏng/quá lớn/không được phép, ảnh cần EXIF-transpose, box bằng không/vượt biên, thêm/xóa/đổi nhãn annotation và gợi ý không có detection.

- [ ] **Bước 2: Xác nhận RED**

Chạy: `.venv\Scripts\python.exe -m pytest tests/data/test_annotations.py tests/inference/test_ultralytics.py -q`

Kỳ vọng: FAIL vì chưa có annotation interfaces.

- [ ] **Bước 3: Triển khai normalization và ranh giới gợi ý**

Dùng Pillow chỉ decode extension được cấu hình, EXIF-transpose và chuẩn hóa preview PNG RGB/RGBA mà không thay đổi source upload. Dùng làm tròn tọa độ cố định cho chuyển đổi box <-> YOLO. Thêm phương thức inference chỉ cho correction, trả về box và ứng viên Top-3; gợi ý không bao giờ tự lưu thành reviewed label.

- [ ] **Bước 4: Xác nhận GREEN**

Chạy: `.venv\Scripts\python.exe -m pytest tests/data/test_annotations.py tests/inference/test_ultralytics.py -q`

Kỳ vọng: PASS.

- [ ] **Bước 5: Commit**

git add src/trafficvision/data/annotations.py src/trafficvision/inference/ultralytics.py tests/data/test_annotations.py tests/inference/test_ultralytics.py
git commit -m "feat: add safe correction annotations"

### Task 3: Snapshot hard-case tách biệt và validation rò rỉ dữ liệu

**Tệp:**
- Create: src/trafficvision/data/hard_case_snapshot.py
- Modify: src/trafficvision/data/validator.py
- Modify: src/trafficvision/data/__init__.py
- Test: tests/data/test_hard_case_snapshot.py
- Test: tests/data/test_validator.py

**Giao diện:**
- Đầu vào: correction đã approved, `DatasetSnapshot` nguồn, annotations và `validate_dataset()`.
- Đầu ra: `HardCaseSnapshot` với `data.yaml`, provenance manifest, correction ID và tham chiếu source snapshot.

- [ ] **Bước 1: Viết test thất bại về tách split**

Viết `test_builder_keeps_challenge_only_and_base_test_out_of_fine_tune_snapshot`: revision `fine_tune` đi vào train/val đầu ra; revision `challenge_only` không đi vào; hash test base gốc không thay đổi.

Kiểm thử correction trùng base test/challenge, correction pending/rejected, chọn lặp revision, chuyển đổi label lỗi và xung đột snapshot bất biến.

- [ ] **Bước 2: Xác nhận RED**

Chạy: `.venv\Scripts\python.exe -m pytest tests/data/test_hard_case_snapshot.py tests/data/test_validator.py -q`

Kỳ vọng: FAIL vì chưa có hard-case snapshot builder và prohibited-hash validation.

- [ ] **Bước 3: Triển khai builder và boundary**

Copy source train/val cùng ảnh gốc/YOLO label của các `fine_tune` đã approved vào snapshot mới. Thêm input prohibited hash cho validator; trùng base test/challenge là `DATA_LEAKAGE` blocking. Lưu hashes, source snapshot ID, correction revision ID, phân bố và validation report vào manifest. Không copy challenge content vào training snapshot.

- [ ] **Bước 4: Xác nhận GREEN**

Chạy: `.venv\Scripts\python.exe -m pytest tests/data/test_hard_case_snapshot.py tests/data/test_validator.py -q`

Kỳ vọng: PASS.

- [ ] **Bước 5: Commit**

git add src/trafficvision/data/hard_case_snapshot.py src/trafficvision/data/validator.py src/trafficvision/data/__init__.py tests/data/test_hard_case_snapshot.py tests/data/test_validator.py
git commit -m "feat: build isolated hard-case snapshots"

### Task 4: Mục tiêu thu thập dựa trên evidence và báo cáo challenge

**Tệp:**
- Create: src/trafficvision/data/collection_goals.py
- Create: src/trafficvision/training/challenge.py
- Test: tests/data/test_collection_goals.py
- Test: tests/training/test_challenge.py

**Giao diện:**
- Đầu vào: manifests, correction đã approved, per-class AP Candidate tùy chọn và revision challenge.
- Đầu ra: `CollectionGoal`, bản ghi evidence `DataGap` và `ChallengeReport` được khóa theo revision ID bất biến.

- [ ] **Bước 1: Viết test thất bại**

Viết `test_gap_recommendation_names_actual_shortfall_and_missing_context`: kiểm tra gap của lớp mục tiêu nêu đúng số lượng lớp quan sát được và thiếu context `poster_nhieu_bien`.

Kiểm thử challenge không có/rỗng, revision ID trước-sau không khớp, lưu expected/predicted trên mỗi object, người dùng duyệt threshold và chuyển trạng thái `ready_for_fine_tune`.

- [ ] **Bước 2: Xác nhận RED**

Chạy: `.venv\Scripts\python.exe -m pytest tests/data/test_collection_goals.py tests/training/test_challenge.py -q`

Kỳ vọng: FAIL vì chưa có goal/challenge interfaces.

- [ ] **Bước 3: Triển khai mục tiêu chỉ dựa trên evidence và báo cáo cùng tập**

Tính coverage lớp/context chỉ từ dữ liệu lưu trữ; gắn evidence vào mọi đề xuất và yêu cầu người dùng duyệt rõ ràng trước trạng thái ready. Đánh giá đúng tập revision `challenge_only` cho từng model, lưu box/class/confidence expected/predicted. So sánh từ chối revision set khác nhau và gọi kết quả là challenge, không phải test.

- [ ] **Bước 4: Xác nhận GREEN**

Chạy: `.venv\Scripts\python.exe -m pytest tests/data/test_collection_goals.py tests/training/test_challenge.py -q`

Kỳ vọng: PASS.

- [ ] **Bước 5: Commit**

git add src/trafficvision/data/collection_goals.py src/trafficvision/training/challenge.py tests/data/test_collection_goals.py tests/training/test_challenge.py
git commit -m "feat: add hard-case gap and challenge reports"

### Task 5: Khởi chạy fine-tune từ `best.pt` đã chọn

**Tệp:**
- Modify: src/trafficvision/training/config.py
- Modify: src/trafficvision/training/manager.py
- Modify: src/trafficvision/training/runner.py
- Test: tests/training/test_training_config.py
- Test: tests/training/test_training_manager.py
- Test: tests/training/test_training_runner.py

**Giao diện:**
- Đầu vào: `CollectionGoal` đã approved, `HardCaseSnapshot.data_yaml_path` và Candidate/run `best.pt` được chọn.
- Đầu ra: `TrainingConfig`/metadata run mới có `base_model` là `best.pt` và `resume_checkpoint` là `None`.

- [ ] **Bước 1: Viết test khởi chạy thất bại**

Viết `test_start_hard_case_fine_tune_uses_checkpoint_as_base_not_resume`: kiểm tra `run_config` đã lưu và xác nhận `base_model` bằng `best.pt`, `resume_checkpoint` là `None`, có metadata source snapshot/goal/checkpoint hash và dùng run ID riêng biệt.

Bao phủ checkpoint thiếu, goal chưa approved, snapshot blocking, lan truyền `workers=0`/device, runner không có argument `resume=True` và registry không thay đổi.

- [ ] **Bước 2: Xác nhận RED**

Chạy: `.venv\Scripts\python.exe -m pytest tests/training/test_training_config.py tests/training/test_training_manager.py tests/training/test_training_runner.py -q`

Kỳ vọng: FAIL vì chưa có hard-case fine-tune API.

- [ ] **Bước 3: Triển khai API tường minh**

Thêm `TrainingManager.start_hard_case_fine_tune()`. Validate toàn bộ input, tạo run mới với `base_model=selected checkpoint` và snapshot đã chọn; ghi provenance vào run metadata. Không tái sử dụng `resume_training()` và không thay đổi production/candidate registry.

- [ ] **Bước 4: Xác nhận GREEN**

Chạy: `.venv\Scripts\python.exe -m pytest tests/training/test_training_config.py tests/training/test_training_manager.py tests/training/test_training_runner.py -q`

Kỳ vọng: PASS.

- [ ] **Bước 5: Commit**

git add src/trafficvision/training/config.py src/trafficvision/training/manager.py src/trafficvision/training/runner.py tests/training/test_training_config.py tests/training/test_training_manager.py tests/training/test_training_runner.py
git commit -m "feat: launch hard-case fine-tune runs"

### Task 6: Trang hiệu chỉnh và review Streamlit

**Tệp:**
- Create: src/trafficvision/ui/pages/corrections.py
- Modify: src/trafficvision/ui/app.py
- Modify: src/trafficvision/ui/theme.py
- Test: tests/ui/test_corrections_page.py
- Test: tests/ui/test_secondary_pages.py

**Giao diện:**
- Đầu vào: correction repository, gợi ý annotation, collection goal, snapshot builder, challenge report và hard-case training API.
- Đầu ra: navigation **Cải thiện dữ liệu**, UI draft/review, focus hai chiều row-box, gap board và control khởi chạy fine-tune rõ ràng.

- [ ] **Bước 1: Viết AppTest flow thất bại**

Viết `test_corrections_page_selects_annotation_row_and_exposes_matching_focus_box`: chọn row số 2 và kiểm tra UI render marker selected box số 2.

Kiểm thử correction pending không thể bật fine-tune; WebP được nhận; extension không hợp lệ bị từ chối; catalog search chọn đúng ID; chọn trực tiếp box đổi selected row; `challenge_only` bị loại; launch lỗi vẫn giữ draft/error.

- [ ] **Bước 2: Xác nhận RED**

Chạy: `.venv\Scripts\python.exe -m pytest tests/ui/test_corrections_page.py tests/ui/test_secondary_pages.py -q`

Kỳ vọng: FAIL vì chưa có route/page correction.

- [ ] **Bước 3: Triển khai UI theo section có giới hạn rõ ràng**

Route **Cải thiện dữ liệu** từ `ui.app`. Bổ sung upload/preview, suggested box, control thêm/xóa/đổi nhãn, picker Top-3/search/group/reference, chọn reason/target, queue/revision review và focus row-box bằng chuột/bàn phím. Chỉ lưu ID vào session state; data service sở hữu file và label.

- [ ] **Bước 4: Thêm control goal/challenge/fine-tune**

Hiển thị gap row có evidence và threshold đã approved. Chỉ bật **Tạo dataset & fine-tune từ model hiện tại** khi goal đã ready/approved và người dùng chọn rõ `best.pt`. Hiển thị báo cáo challenge trước/sau, nêu rõ Candidate/Production không đổi cho tới khi người dùng promote thủ công.

- [ ] **Bước 5: Xác nhận GREEN**

Chạy: `.venv\Scripts\python.exe -m pytest tests/ui/test_corrections_page.py tests/ui/test_secondary_pages.py -q`

Kỳ vọng: PASS.

- [ ] **Bước 6: Commit**

git add src/trafficvision/ui/pages/corrections.py src/trafficvision/ui/app.py src/trafficvision/ui/theme.py tests/ui/test_corrections_page.py tests/ui/test_secondary_pages.py
git commit -m "feat: add reviewed hard-case correction UI"

### Task 7: Chứng minh end-to-end và bàn giao vận hành

**Tệp:**
- Modify: tests/integration/test_phase2_flow.py
- Modify: README.md
- Create: docs/hard-case-correction-operator-guide.md

**Giao diện:**
- Đầu vào: toàn bộ correction, snapshot, challenge, training và UI interface phía trước.
- Đầu ra: evidence regression end-to-end và hướng dẫn vận hành cục bộ bằng tiếng Việt.

- [ ] **Bước 1: Viết test end-to-end thất bại**

Viết `test_reviewed_hard_case_creates_candidate_without_test_leakage_or_production_change`: dùng fixture tổng hợp cục bộ để submit/approve một correction `fine_tune` và một correction `challenge_only`, tạo snapshot, khởi chạy fake fine-tune, so sánh challenge report cùng ID, sau đó kiểm tra test hash và production manifest không đổi còn Candidate mới đã xuất hiện.

- [ ] **Bước 2: Xác nhận RED**

Chạy: `.venv\Scripts\python.exe -m pytest tests/integration/test_phase2_flow.py::test_reviewed_hard_case_creates_candidate_without_test_leakage_or_production_change -q`

Kỳ vọng: FAIL cho đến khi toàn bộ component được nối với nhau.

- [ ] **Bước 3: Hoàn thiện riêng các seam liên module do test chỉ ra**

Giữ fixture tổng hợp/cục bộ. Không làm yếu provenance correction, isolation, validation hoặc Candidate/Production boundary chỉ để test pass.

- [ ] **Bước 4: Viết tài liệu vận hành**

Tài liệu hóa upload WebP, hành vi row/box, class picker, queue/review, gap evidence, phân biệt challenge với test, fine-tune thủ công từ `best.pt`, review Candidate và promotion/rollback tường minh.

- [ ] **Bước 5: Chạy validation toàn bộ**

Chạy: `.venv\Scripts\python.exe -m pytest -q`

Chạy: `.venv\Scripts\python.exe -m ruff check src tests`

Kỳ vọng: toàn bộ test và lint pass. Nếu CLI no-wait test đã biết để lại background runner, chỉ terminate PID test tạm đã xác minh và phải báo lại; không được terminate app/training process của người dùng.

- [ ] **Bước 6: Commit**

git add tests/integration/test_phase2_flow.py README.md docs/hard-case-correction-operator-guide.md
git commit -m "docs: document hard-case correction workflow"

## Tự review kế hoạch

- Phủ đặc tả: Task 1–2 bao phủ queue/provenance/WebP/annotation; Task 3–4 bao phủ isolation/gap/challenge; Task 5 bao phủ fine-tune run mới; Task 6 bao phủ UI; Task 7 chứng minh các boundary và tài liệu hóa cách dùng.
- Nhất quán kiểu dữ liệu: correction repository cấp dữ liệu cho snapshot/goal/UI; `HardCaseSnapshot` cấp dữ liệu cho `start_hard_case_fine_tune`; `ChallengeReport` dùng revision ID bất biến.
- Điểm review: mỗi input rủi ro cao có một task/test chịu trách nhiệm rõ ràng.
- Phạm vi: kế hoạch không thay thế inference, registry, baseline, test split hoặc promotion flow hiện có.
