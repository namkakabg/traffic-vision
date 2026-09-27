# Đặc tả thiết kế TrafficVision

**Tên đề tài:** TrafficVision – Nhận dạng biển báo giao thông bằng AI  
**Ngày chốt thiết kế:** 27/09/2026  
**Mục tiêu:** Xây dựng đồ án môn Phân tích hệ thống thông minh có web demo chất lượng, nhận dạng biển báo giao thông Việt Nam trong ảnh và video, huấn luyện được qua giao diện và chạy suy luận tốt trên CPU macOS/Windows.

## 1. Phạm vi và tiêu chí thành công

TrafficVision là hệ thống thị giác máy tính đầu cuối gồm chuẩn bị dữ liệu, phân tích dữ liệu khám phá, huấn luyện, đánh giá, quản lý phiên bản mô hình và suy luận trên web. Hệ thống dùng một mô hình phát hiện vật thể để vừa định vị vừa phân loại biển báo.

Thứ tự bàn giao là **ứng dụng trước, huấn luyện sau**. Giai đoạn đầu dựng toàn bộ web và pipeline ảnh/video bằng YOLO11n pretrained gốc để kiểm chứng luồng end-to-end. Mô hình gốc chỉ là baseline kỹ thuật, chưa chuyên biệt cho biển báo Việt Nam và không được dùng để tuyên bố độ chính xác cuối. Sau khi ứng dụng ổn định, nhóm mới kiểm định dữ liệu, fine-tune mô hình và thay baseline bằng mô hình 82 lớp thông qua model registry mà không sửa luồng giao diện.

Phiên bản đầu tiên phải:

- Nhận ảnh JPG/PNG và video MP4/AVI/MOV do người dùng tải lên.
- Phát hiện, khoanh vùng và gắn nhãn tối đa 82 loại biển báo giao thông Việt Nam.
- Hiển thị độ tin cậy, thời gian suy luận, thống kê kết quả và cho tải kết quả đã chú thích.
- Có giao diện kiểm định dữ liệu, cấu hình và theo dõi huấn luyện.
- Chạy suy luận bằng CPU trên macOS và Windows; hỗ trợ CUDA trên máy Windows có GTX 1050 Ti để huấn luyện.
- Lưu đầy đủ cấu hình, seed, số liệu và biểu đồ để kết quả báo cáo có thể tái tạo.
- Không ghi đè mô hình đang dùng và không cho phép huấn luyện khi dữ liệu có lỗi nghiêm trọng.

Không thuộc phạm vi phiên bản đầu: camera trực tiếp, ứng dụng di động, hệ thống tài khoản nhiều người dùng, triển khai cloud công cộng và điều khiển phương tiện tự hành.

## 2. Người dùng và luồng nghiệp vụ

### 2.1. Người trình diễn/người phân tích

1. Mở trang Phân tích.
2. Chọn ảnh hoặc video.
3. Điều chỉnh ngưỡng tin cậy nếu cần.
4. Chạy nhận dạng và theo dõi tiến độ.
5. Xem khung bao, nhãn tiếng Việt, độ tin cậy, thống kê và thời gian xử lý.
6. Tải ảnh/video đã chú thích và bảng CSV kết quả.

### 2.2. Người huấn luyện mô hình

1. Chọn bộ dữ liệu và chạy kiểm định.
2. Xem lỗi chặn, cảnh báo và báo cáo EDA.
3. Cấu hình mô hình, epoch, batch size, kích thước ảnh và early stopping.
4. Khởi chạy hoặc tiếp tục phiên huấn luyện từ checkpoint.
5. Theo dõi loss, Precision, Recall, mAP và tài nguyên phần cứng.
6. Đánh giá candidate trên tập test, xuất ONNX và benchmark CPU.
7. Chỉ định candidate đạt yêu cầu làm mô hình production.

## 3. Kiến trúc hệ thống

Hệ thống tách thành hai quy trình để huấn luyện không ảnh hưởng đến web suy luận.

### 3.1. Thứ tự triển khai

```text
GIAI ĐOẠN 1 — ỨNG DỤNG VỚI MÔ HÌNH GỐC
YOLO11n pretrained gốc
    -> export/kiểm tra ONNX
    -> model manifest động
    -> upload ảnh/video
    -> suy luận + hiển thị + CSV
    -> test end-to-end trên CPU

GIAI ĐOẠN 2 — DỮ LIỆU VÀ HUẤN LUYỆN
Bộ dữ liệu biển báo Việt Nam
    -> validation + EDA
    -> fine-tune từ YOLO11n pretrained
    -> đánh giá + export ONNX
    -> candidate
    -> backup baseline/production cũ
    -> promotion mô hình 82 lớp
```

Inference không được hard-code số lớp hoặc tên lớp. Mỗi model đi kèm manifest chứa loại model, phiên bản, class mapping, input size, checksum và trạng thái `baseline`, `candidate` hoặc `production`. Vì vậy cùng một ứng dụng có thể chạy trước với nhãn gốc của model pretrained và tự chuyển sang 82 nhãn tiếng Việt sau promotion.

### 3.2. Hai quy trình vận hành

```text
QUY TRÌNH NGOẠI TUYẾN
Bộ dữ liệu Việt Nam
    -> kiểm định + snapshot
    -> tiền xử lý + EDA
    -> huấn luyện YOLO11n
    -> đánh giá tập test
    -> xuất và kiểm tra ONNX
    -> candidate model

QUY TRÌNH TRỰC TUYẾN
Ảnh/video tải lên
    -> kiểm tra tệp
    -> giải mã + resize/letterbox
    -> ONNX Runtime trên CPU
    -> NMS + ánh xạ nhãn tiếng Việt
    -> ảnh/video chú thích + thống kê + CSV
```

Các mô-đun chính:

- `data`: tải/đăng ký nguồn dữ liệu, kiểm định, snapshot, chia tập và EDA.
- `training`: cấu hình thí nghiệm, tiến trình nền, checkpoint và đánh giá.
- `registry`: quản lý candidate, production, backup, checksum và rollback.
- `inference`: tải mô hình ONNX, tiền/hậu xử lý ảnh và xử lý video.
- `web`: giao diện Streamlit, điều phối thao tác và hiển thị báo cáo.
- `reporting`: kết xuất JSON, CSV, biểu đồ, báo cáo dữ liệu và báo cáo thí nghiệm.

Mỗi mô-đun có giao diện rõ ràng và không phụ thuộc trực tiếp vào trạng thái giao diện. CLI và web dùng chung các service để kết quả nhất quán và dễ kiểm thử.

## 4. Dữ liệu

Nguồn khởi đầu là bộ **Traffic-sign-detection-VietNam**, định dạng YOLO, gồm 10.157 ảnh và 82 lớp, giấy phép CC BY 4.0. Tài liệu dự án phải ghi nguồn và điều khoản giấy phép. Nguồn tham chiếu: <https://huggingface.co/datasets/star092304/Traffic-sign-detection-VietNam>.

### 4.1. Quality gate trước huấn luyện

Trình kiểm định phải kiểm tra:

- Ảnh không đọc được, sai phần mở rộng hoặc có kích thước bằng 0.
- Thiếu cặp ảnh–nhãn, nhãn rỗng và ảnh nền hợp lệ.
- Mỗi dòng nhãn đúng cấu trúc YOLO và chứa giá trị số hữu hạn.
- Class ID thuộc miền 0–81 và khớp danh mục 82 lớp.
- Tọa độ chuẩn hóa thuộc `[0,1]`; chiều rộng, chiều cao và diện tích box hợp lệ.
- Ảnh/nhãn trùng chính xác, ảnh gần trùng bằng perceptual hash và trùng giữa các tập.
- Phân bố lớp, lớp thiếu mẫu, box quá nhỏ và các ngoại lệ thống kê.

Lỗi ảnh hỏng, class ID sai, tọa độ sai, thiếu mapping hoặc rò rỉ bản sao chính xác giữa các tập là lỗi chặn. Nút huấn luyện bị khóa cho đến khi lỗi chặn được xử lý. Mất cân bằng lớp, box rất nhỏ hoặc lớp ít mẫu là cảnh báo; người dùng phải xác nhận trước khi tiếp tục.

Mỗi lần huấn luyện gắn với một snapshot bất biến gồm manifest tệp, checksum, mapping lớp, cấu hình chia tập, seed, thời gian và kết quả kiểm định. Không âm thầm sửa dữ liệu gốc; mọi bản sửa nằm trong `data/processed` và có nhật ký biến đổi.

### 4.2. EDA

Pipeline tạo tự động:

- Số ảnh và số đối tượng theo train/validation/test.
- Phân bố số mẫu theo lớp và tỷ lệ mất cân bằng.
- Kích thước, tỷ lệ khung hình và độ phân giải ảnh.
- Phân bố tâm, chiều rộng, chiều cao và diện tích bounding box.
- Tỷ lệ biển nhỏ/vừa/lớn.
- Lưới ảnh mẫu có nhãn, ảnh nền và các mẫu bất thường.

## 5. Huấn luyện và đánh giá

Mô hình cơ sở là chính YOLO11n pretrained đã dùng để xây dựng ứng dụng ở giai đoạn 1. Bản gốc được giữ bất biến; huấn luyện luôn tạo một run mới từ trọng số gốc hoặc checkpoint được chọn. Cấu hình mặc định: ảnh 640 px, batch 4 cho GTX 1050 Ti 4 GB, tối đa 50 epoch, patience 10, mixed precision khi CUDA hỗ trợ và seed cố định. Hệ thống cho phép giảm kích thước ảnh hoặc batch khi thiếu VRAM và có thể tiếp tục từ `last.pt`.

Mỗi phiên có `run_id` riêng và lưu cấu hình, môi trường, phần cứng, phiên bản dữ liệu, log, đường cong, checkpoint `last.pt`/`best.pt` và kết quả đánh giá. Không checkpoint nào ghi đè phiên khác.

Đánh giá cuối cùng chỉ dùng tập test độc lập sau khi đã chốt siêu tham số. Chỉ số bắt buộc:

- Precision, Recall và F1 tại ngưỡng được công bố.
- mAP@50 và mAP@50–95.
- AP theo lớp và confusion matrix.
- Phân tích false positive, false negative và nhầm lớp.
- Thời gian suy luận, FPS và bộ nhớ trên CPU macOS/Windows; CUDA là số liệu bổ sung.

Số liệu báo cáo phải sinh từ artifact thật. Không dùng giá trị giả hoặc thay số liệu thí nghiệm bằng số minh họa.

## 6. Quản lý và backup mô hình

```text
artifacts/
├── baseline/            # YOLO11n pretrained gốc + manifest, bất biến
├── production/          # mô hình ONNX đang phục vụ web
├── backups/             # các production cũ, có timestamp và checksum
└── runs/<run_id>/       # checkpoint, candidate, metrics và cấu hình
```

Ở giai đoạn 1, production trỏ tới bản ONNX xuất từ baseline để ứng dụng có thể chạy ngay. Giao diện phải hiển thị rõ `Baseline — chưa fine-tune biển báo Việt Nam`. Sau promotion ở giai đoạn 2, production trỏ tới candidate 82 lớp đã vượt qua kiểm định; baseline vẫn được giữ nguyên để đối chiếu và phục hồi.

Mô hình đang huấn luyện chỉ là candidate. Trước khi promotion:

1. Kiểm tra candidate tồn tại và checksum hợp lệ.
2. Chạy smoke test ONNX bằng ảnh mẫu.
3. So sánh đầu ra ONNX với checkpoint gốc trong dung sai định trước.
4. Benchmark CPU và xác nhận danh sách 82 lớp.
5. Sao lưu production hiện tại bằng timestamp, manifest và checksum.
6. Chuyển candidate thành production bằng thao tác thay thế nguyên tử.
7. Nếu bước xác minh sau chuyển đổi thất bại, rollback về backup gần nhất.

Ứng dụng suy luận tiếp tục dùng production cũ trong khi huấn luyện diễn ra.

## 7. Giao diện web

Phong cách đã duyệt: dashboard hiện đại, nền sáng, thanh điều hướng xanh navy, màu nhấn xanh dương/xanh ngọc, phân cấp thông tin rõ và nội dung tiếng Việt.

Các trang chính:

- **Phân tích:** tab ảnh/video, vùng tải tệp, xem kết quả trực quan, thống kê và tải đầu ra.
- **Lịch sử:** các phiên phân tích gần đây trong phiên chạy cục bộ.
- **Thống kê:** phân bố lớp phát hiện và hiệu năng xử lý.
- **Huấn luyện AI:** bước Dữ liệu → Kiểm định → Huấn luyện → Đánh giá & xuất; cấu hình và tiến độ thời gian thực.
- **Thông tin mô hình:** phiên bản production, dataset snapshot, metrics, runtime và lịch sử backup.
- **Thiết lập:** ngưỡng confidence, IoU/NMS, thư mục đầu ra và tùy chọn video.

Huấn luyện chạy bằng tiến trình nền độc lập với vòng đời render của Streamlit. Trạng thái công việc được lưu trên đĩa để reload/đóng tab không làm mất phiên. Giao diện có thể yêu cầu tạm dừng an toàn sau epoch hiện tại và tiếp tục từ checkpoint.

Mọi thông tin lớp, tên model và trạng thái huấn luyện lấy từ model manifest. Khi đang dùng mô hình gốc, giao diện không hiển thị `82 lớp biển báo Việt Nam` hoặc metrics chưa tồn tại; thay vào đó ghi rõ đây là baseline. Sau khi mô hình đã huấn luyện được promotion, giao diện tự cập nhật tên lớp và metrics mà không cần thay mã nguồn trang Phân tích.

## 8. Xử lý ảnh và video

Ảnh được kiểm tra định dạng/dung lượng, chuẩn hóa màu, letterbox về kích thước mô hình, suy luận batch 1 và ánh xạ box về ảnh gốc. Hậu xử lý áp dụng ngưỡng confidence và NMS, rồi gắn nhãn tiếng Việt bằng font hỗ trợ Unicode.

Video được đọc tuần tự để không giữ toàn bộ nội dung trong RAM. Hệ thống bảo toàn kích thước và FPS đầu vào khi có thể, hiển thị tiến độ, số frame lỗi, FPS xử lý và thống kê theo lớp. Nếu codec đầu ra không được trình duyệt hỗ trợ, hệ thống chuyển sang MP4/H.264 khi môi trường có codec tương ứng và báo phương án thay thế khi không có.

Đầu ra CSV tối thiểu gồm tên tệp, frame/timestamp, class ID, tên lớp, confidence và tọa độ bounding box.

## 9. Xử lý lỗi và giới hạn tài nguyên

- Từ chối tệp không hỗ trợ và giới hạn dung lượng/thời lượng cấu hình được.
- Báo rõ khi thiếu model, model lỗi, thiếu mapping lớp hoặc ONNX Runtime không khởi tạo được.
- Bắt lỗi từng frame video; không làm mất toàn bộ kết quả đã xử lý nếu một frame lỗi.
- Theo dõi dung lượng đĩa trước huấn luyện/xuất video và không khởi chạy nếu không đủ.
- Khi CUDA hết VRAM, giữ checkpoint và hướng dẫn giảm batch/imgsz; không tự xóa artifact.
- Chỉ hiển thị số liệu thực. Trạng thái chưa có kết quả dùng `N/A`, không dùng số mẫu giả.
- Kết quả AI có thông báo đây là hệ thống hỗ trợ, độ chính xác có thể giảm với biển nhỏ, che khuất, nhòe hoặc thiếu sáng.

## 10. Kiểm thử

### 10.1. Unit test

- Parser YAML/nhãn và toàn bộ quy tắc validation.
- Snapshot/checksum và phân loại lỗi chặn/cảnh báo.
- Letterbox, ánh xạ tọa độ, NMS và mapping nhãn.
- Model registry, backup, promotion và rollback.
- Trích xuất frame, tổng hợp thống kê và CSV.

### 10.2. Integration test

- Upload ảnh → suy luận → ảnh chú thích → CSV.
- Upload video ngắn → tiến độ → video kết quả → thống kê.
- Validation đạt/không đạt → trạng thái nút huấn luyện.
- Huấn luyện thử trên tập nhỏ → checkpoint → tiếp tục → đánh giá.
- Export ONNX → kiểm tra tương đương → promotion → tải lại production.

### 10.3. UAT và hiệu năng

- Ảnh không có biển, nhiều biển, biển rất nhỏ, ảnh thiếu sáng và ảnh sai định dạng.
- Video dài, video codec lỗi và thao tác reload trong khi job đang chạy.
- CPU macOS và Windows; CUDA GTX 1050 Ti cho huấn luyện.
- Kịch bản rollback khi candidate hoặc ONNX bị lỗi.

## 11. Cấu trúc dự án dự kiến

```text
Traffic_Vison/
├── app/                  # các trang và component Streamlit
├── src/trafficvision/
│   ├── data/
│   ├── training/
│   ├── registry/
│   ├── inference/
│   └── reporting/
├── configs/
├── scripts/
├── tests/
├── notebooks/
├── data/                 # raw/processed bị loại khỏi Git
├── artifacts/            # model/runs/backups bị loại khỏi Git
├── reports/
└── docs/
```

## 12. Thành viên và phân công

- **Phí Văn Nam — Trưởng nhóm:** kiến trúc, tích hợp hệ thống, quản lý tiến độ và điều phối báo cáo.
- **Đỗ Thị Vân Anh:** thu thập/kiểm định dữ liệu, tiền xử lý và EDA.
- **Đỗ Hữu Nghị:** huấn luyện, đánh giá, phân tích lỗi và tối ưu/xuất mô hình.
- **Quản Văn Điệp:** giao diện web, luồng suy luận, kiểm thử và tài liệu sử dụng.

Các thành viên cùng review dữ liệu, kịch bản demo và báo cáo cuối để tránh một mô-đun chỉ có một người hiểu.

## 13. Lịch trình bốn tuần

| Tuần | Công việc chính | Mốc bàn giao |
|---|---|---|
| 1 | Khởi tạo dự án, model adapter/registry và web phân tích ảnh/video bằng YOLO11n gốc | Ứng dụng end-to-end chạy CPU với baseline |
| 2 | Thu thập dữ liệu, validation, snapshot, EDA và giao diện huấn luyện | Dataset đã kiểm định + báo cáo EDA |
| 3 | Fine-tune, đánh giá, FP/FN, export ONNX, backup và promotion | Demo chạy mô hình 82 lớp + số liệu test |
| 4 | Kiểm thử, benchmark, cải tiến, hoàn thiện báo cáo và luyện demo | Bản nộp và kịch bản bảo vệ |

## 14. Báo cáo cuối kỳ

Báo cáo viết bằng tiếng Việt, số liệu lấy từ artifact của hệ thống và bám cấu trúc:

1. Giới thiệu
   1.1. Thông tin cơ bản
   1.2. Động lực và mục tiêu
   1.3. Thành viên và phân công vai trò
   1.4. Lịch trình và các mốc quan trọng
2. Triển khai dự án
   2.1. Thu thập dữ liệu
   2.2. Phương pháp huấn luyện
   2.3. Quy trình xử lý hệ thống
   2.4. Sơ đồ hệ thống
3. Kết quả
   3.1. Tiền xử lý dữ liệu
   3.2. Phân tích dữ liệu khám phá (EDA)
   3.3. Xây dựng mô hình
   3.4. Giao diện người dùng
   3.5. Kiểm thử và cải tiến
4. Projected Impact
   4.1. Accomplishments and Benefits
   4.2. Future Improvements
5. Kết luận

Nếu chưa chạy thí nghiệm thật, phần kết quả để rõ `Chưa có số liệu` thay vì điền số giả. Khi pipeline hoàn tất, công cụ tạo báo cáo sẽ thay các trường bằng metrics, biểu đồ và ảnh đầu ra thực tế.

## 15. Tiêu chí nghiệm thu

Thiết kế được xem là triển khai đạt khi:

1. Cài đặt được trên môi trường Python được hỗ trợ ở cả macOS và Windows.
2. Trước khi chuẩn bị dữ liệu/huấn luyện, ứng dụng đã xử lý được một ảnh và một video bằng baseline, tạo đầu ra trực quan và CSV trên CPU.
3. Giao diện đọc model manifest động, hiển thị đúng trạng thái baseline và không hard-code 82 lớp.
4. Validation khóa huấn luyện khi fixture dữ liệu chứa lỗi chặn và tạo báo cáo giải thích được.
5. Huấn luyện thử tạo checkpoint riêng, có thể tiếp tục và không thay đổi baseline/production đang chạy.
6. ONNX sau fine-tune chạy trên CPU, trả đúng 82 tên lớp và có benchmark tái tạo được.
7. Promotion luôn tạo backup; test lỗi có thể rollback về production cũ.
8. Test tự động trọng yếu vượt qua và hướng dẫn demo tái hiện được trên máy khác.
9. Báo cáo cuối chứa số liệu, biểu đồ và hình ảnh sinh từ chính phiên bản code/model được bàn giao.
