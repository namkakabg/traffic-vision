# TrafficVision — Hard-case Correction & Fine-tune Design

## 1. Mục tiêu và ranh giới

TrafficVision bổ sung một quy trình cục bộ để người dùng biến ảnh nhận dạng sai thành dữ liệu có kiểm soát: **upload → gợi ý box/lớp → sửa → hàng chờ → duyệt → snapshot fine-tune → Candidate → so sánh challenge**.

Mục tiêu là cải thiện các lỗi thực tế như biển nhỏ trong poster, biển xa, mờ hoặc nghiêng mà không làm thay đổi mô hình Production, baseline, tập test độc lập hay dữ liệu gốc.

Ngoài phạm vi: tự tải ảnh Internet, tự gán nhãn không cần người duyệt, tự chạy fine-tune sau mỗi lần duyệt, tự promotion Candidate, hoặc khẳng định mô hình mới tốt hơn khi chưa có báo cáo challenge.

## 2. Quy trình người dùng

1. Người dùng upload JPG/JPEG/PNG/WebP từ trang **Cải thiện dữ liệu**.
2. Model đang chọn suy luận trước để gợi ý box và Top-3 lớp. Người dùng có thể thêm, xóa, kéo/đổi kích thước box và đổi lớp.
3. Khi chọn một row trong **Đối tượng nhận dạng**, ảnh tự focus/zoom box tương ứng; box có viền cam dày, các box khác giảm nhấn. Hover chỉ xem trước; click box trên ảnh chọn và cuộn tới đúng row. Hành vi phải dùng được bằng bàn phím.
4. Bộ chọn lớp không yêu cầu nhớ ID: gợi ý Top-3, tìm theo tên tiếng Việt/mã biển, nhóm biển và ảnh mẫu khi catalog có reference asset. Tên lớp thực tế luôn lấy từ catalog 82 lớp của snapshot/model, không hard-code ở UI.
5. Người dùng gửi bản sửa vào hàng chờ cùng lý do lỗi và lựa chọn đích: `fine_tune` hoặc `challenge_only`.
6. Người duyệt kiểm tra ảnh, box, lớp và lý do; có thể xác nhận hoặc từ chối. Chỉ bản xác nhận mới trở thành dữ liệu snapshot.
7. Người dùng duyệt mục tiêu thu thập do app đề xuất rồi chủ động bấm **Tạo dataset & fine-tune từ model hiện tại**.
8. Run fine-tune mới khởi tạo từ checkpoint `best.pt` được chọn, tạo Candidate mới và hiển thị so sánh trước/sau trên challenge. Production chỉ đổi qua thao tác promotion hiện hữu.

## 3. Dữ liệu, provenance và cô lập tập

### 3.1 Correction store

Lưu ảnh gốc bất biến và revision gán nhãn vào `artifacts/corrections/`:

```text
artifacts/corrections/
├── items/<correction_id>/source.<ext>   # JPG/JPEG/PNG/WebP upload bất biến
├── items/<correction_id>/preview.png    # preview/crop phục vụ UI
├── items/<correction_id>/revision.json  # box YOLO chuẩn hóa, lớp, lý do, hash
├── challenge/                           # chỉ các bản đã duyệt challenge_only
└── state.db                             # hàng chờ, revision, người duyệt, mục tiêu
```

Mỗi revision lưu hash ảnh, thời điểm, trạng thái `draft | pending_review | approved | rejected`, người tạo/người duyệt (tên local do người dùng nhập), lý do, source model/run và annotation. Ảnh/crop dùng để xem, nhưng snapshot fine-tune giữ **ảnh gốc với toàn bộ box đã duyệt** để model học đúng bối cảnh nhiều biển nhỏ.

### 3.2 Bất biến và chống rò rỉ

- Tập test của `artifacts/snapshots/<id>/test/` không bị ghi, copy hay hợp nhất.
- Bản `challenge_only` không tham gia train/val; chỉ dùng báo cáo before/after.
- Bản `fine_tune` được hash và so với source split/challenge trước khi snapshot. Trùng nội dung là lỗi chặn, không âm thầm loại để che lỗi.
- Snapshot fine-tune mới chứa manifest nguồn, correction IDs/revisions, class mapping, hash, seed, validation report và checkpoint base.
- Dữ liệu gốc được trộn với correction đã duyệt; không fine-tune chỉ trên correction mới.

## 4. Bảng thiếu dữ liệu và mục tiêu thu thập

`CollectionGoal` có các lớp mục tiêu, bối cảnh (`biển_đơn`, `poster_nhiều_biển`, `xa_nhỏ`, `mờ`, `nghiêng`) và trạng thái `draft | user_approved | ready_for_fine_tune | superseded`.

App đề xuất mục tiêu từ bằng chứng thực:

- số object theo lớp trong snapshot hiện tại;
- correction/challenge đã duyệt theo lớp và bối cảnh;
- prediction sai và cặp lớp nhầm từ challenge;
- AP theo lớp của Candidate khi có.

Mỗi đề xuất phải giải thích rõ nguyên nhân, số đã có và mức khuyến nghị; người dùng có thể sửa/duyệt trước khi app mở hành động fine-tune. App không tuyên bố có một ngưỡng phổ quát hay tự coi dữ liệu đã đủ chỉ theo tổng số ảnh.

## 5. Snapshot, fine-tune và đánh giá

### 5.1 Tạo snapshot

Từ một `CollectionGoal` đã duyệt, builder chọn correction `approved` với mục tiêu `fine_tune`, tạo ảnh/YOLO labels bất biến và hợp nhất với dữ liệu gốc. Builder gọi validator hiện hữu, tạo báo cáo phân bố lớp/bối cảnh, và dừng khi có lỗi chặn.

### 5.2 Fine-tune

Fine-tune là run mới, không phải `resume=True` của run cũ: `base_model` trỏ đến checkpoint `best.pt` được người dùng chọn, còn data trỏ snapshot mới. Cấu hình device/workers, log, checkpoint, test evaluation, ONNX export, parity và Candidate tiếp tục dùng pipeline training hiện hữu.

### 5.3 Challenge report

Trước và sau fine-tune, hệ thống chạy cùng challenge đã duyệt, lưu prediction từng object, box, lớp dự kiến/lớp dự đoán, confidence và timestamp. Báo cáo chỉ so sánh cùng tập challenge, theo lớp/bối cảnh; không thay thế số liệu tập test độc lập.

Candidate mới chỉ có trạng thái "cần review". Màn hình báo cáo nêu rõ nếu challenge thiếu mẫu, một lớp không cải thiện, hoặc chạy challenge lỗi.

## 6. Kiến trúc module

| Module | Trách nhiệm |
|---|---|
| `data.corrections` | models/repository SQLite, hash, revision, approval và query queue |
| `data.annotations` | chuẩn hóa/validate box, chuyển đổi YOLO, preview crop |
| `data.collection_goals` | tính gap giải thích được và trạng thái goal |
| `data.hard_case_snapshot` | dựng snapshot mới, bảo vệ split/challenge và provenance |
| `training.challenge` | chạy/ghi before-after per-object report |
| `ui.pages.corrections` | upload, annotation, queue, data-gap board và hành động fine-tune |
| `training.manager` / `training.runner` | launch run mới từ checkpoint base; không thay semantics resume lỗi |

Các module giao tiếp qua DTO Pydantic và paths `AppPaths`; UI không tự ghi YOLO hay copy file trực tiếp.

## 7. Xử lý lỗi và bảo mật dữ liệu

- Reject file không phải JPG/JPEG/PNG/WebP, vượt hạn upload hiện hữu, corrupt image, box ngoài ảnh, box có diện tích bằng 0, class ngoài catalog hoặc annotation trống.
- WebP được giải mã và chuẩn hóa RGB/RGBA theo cùng quy tắc an toàn như JPEG/PNG để tạo preview và snapshot; ảnh gốc WebP vẫn được lưu bất biến cùng hash/provenance.
- Cảnh báo (không tự chặn) khi box rất nhỏ, lớp mất cân bằng hoặc challenge còn ít mẫu; user phải xác nhận goal.
- Không cho sửa bản đã `approved` tại chỗ: tạo revision mới quay lại hàng chờ, giúp provenance tái tạo được.
- Không chứa ảnh/nội dung annotation trong log kỹ thuật; UI chỉ hiện nội dung cho thao tác local hiện tại.
- Lỗi validation/snapshot/fine-tune/challenge phải giữ correction và checkpoint, nêu path an toàn và cho phép retry có chủ đích.

## 8. Tiêu chí chấp nhận và kiểm thử

1. Upload JPG/JPEG/PNG/WebP ảnh nhiều biển tạo gợi ý có thể thêm/xóa/sửa; click row/box focus hai chiều.
2. Lớp chọn từ catalog hợp lệ; search, nhóm và Top-3 không thay đổi class ID.
3. Pending/reject không vào snapshot; approved `fine_tune` vào snapshot; approved `challenge_only` không vào train/val.
4. Hash duplicate với train/val/test/challenge bị validator báo đúng ranh giới.
5. Data-gap board chỉ dùng dữ liệu có thật và mỗi recommendation có lý do hiển thị được.
6. Fine-tune run mới nhận base `best.pt`, dữ liệu gốc + approved correction và không dùng `resume=True`.
7. Challenge before/after dùng đúng cùng challenge IDs, không bị báo nhầm là test metric.
8. Candidate/Production cũ không đổi cho đến khi user promotion; full pytest và Ruff đạt.

## 9. Quyết định đã chốt

- Local Streamlit UI; không tự tải ảnh Internet.
- Upload correction hỗ trợ JPG/JPEG/PNG/WebP; WebP giữ file gốc và qua cùng gate giải mã/chuẩn hóa an toàn.
- Model gợi ý box/Top-3 nhưng người dùng luôn có quyền thêm/xóa/sửa.
- Queue bắt buộc duyệt trước khi vào fine-tune.
- App đề xuất mục tiêu thu thập dựa trên dữ liệu/đánh giá thực; user duyệt.
- Fine-tune chạy thủ công từ `best.pt`, dùng snapshot hợp nhất; không train từ YOLO pretrained ban đầu.
- Không tự promotion: Candidate mới luôn chờ người dùng review và promotion rõ ràng.
- Challenge cô lập, report before/after; không auto-promotion.
