param(
    [string]$TemplatePath = (Join-Path $PSScriptRoot "..\docs\Project_Final Report.docx"),
    [string]$OutputPath = (Join-Path $PSScriptRoot "..\docs\TrafficVision_Project_Final_Report.docx")
)

$ErrorActionPreference = "Stop"

$template = (Resolve-Path -LiteralPath $TemplatePath).Path
$output = [System.IO.Path]::GetFullPath($OutputPath)
Copy-Item -LiteralPath $template -Destination $output -Force

$reportText = @'
1. Giới thiệu

1.1. Thông tin cơ bản

Tên đề tài: TrafficVision – Nhận dạng biển báo giao thông Việt Nam bằng AI.

Nhóm thực hiện: RoadVision. Môn học: Phát triển hệ thống thông minh. Thời gian kế hoạch: 28/09/2026–26/10/2026. Báo cáo này phản ánh thiết kế, cấu phần đã xây dựng và các bằng chứng hiện có tại ngày 02/10/2026.

TrafficVision là ứng dụng web Streamlit chạy cục bộ để tiếp nhận ảnh và video, phát hiện/khoanh vùng đối tượng bằng YOLO, trả ảnh hoặc video đã chú thích, bảng CSV và thông tin trạng thái mô hình. Ứng dụng được thiết kế để chạy trước với YOLO11n baseline trên ONNX Runtime CPU, sau đó nâng cấp có kiểm soát lên mô hình biển báo Việt Nam sau khi hoàn thành kiểm định dữ liệu và đánh giá độc lập.

1.2. Động lực và Mục tiêu

Nhận dạng biển báo giao thông là bài toán thị giác máy tính có ý nghĩa thực tiễn, nhưng kết quả chỉ đáng tin cậy khi dữ liệu, mô hình, cấu hình và kết quả đánh giá có thể truy vết. TrafficVision chọn cách triển khai ứng dụng trước để chứng minh luồng end-to-end, sau đó mới đưa dữ liệu vào huấn luyện. Cách làm này tránh trình bày nhầm mô hình pretrained tổng quát là mô hình nhận dạng biển báo Việt Nam.

Mục tiêu thứ nhất là xây dựng luồng phân tích ảnh/video cục bộ, có kiểm tra đầu vào, hiển thị detection, confidence, thống kê và đầu ra tải xuống. Mục tiêu thứ hai là xây dựng pipeline dữ liệu YOLO 82 lớp gồm Quality Gate, EDA, snapshot bất biến, huấn luyện/fine-tune, checkpoint, đánh giá test độc lập, xuất ONNX và Candidate. Mục tiêu thứ ba là quản lý vòng đời mô hình bằng manifest, checksum, backup, promotion và rollback, đồng thời bàn giao báo cáo, mã nguồn, hướng dẫn và demo có thể tái lập.

Phạm vi không gồm webcam trực tiếp, tài khoản nhiều người dùng, triển khai cloud công cộng hay điều khiển phương tiện. Kết quả AI chỉ có tính hỗ trợ tham khảo; hệ thống phải nêu rõ giới hạn khi biển báo nhỏ, xa, mờ, nghiêng hoặc che khuất.

1.3. Thành viên và Phân công vai trò

Phí Văn Nam – Trưởng nhóm: quản lý WBS và các quality gate; thiết kế kiến trúc, model registry, tích hợp hệ thống, promotion/rollback, tổng hợp báo cáo và rehearsal demo.

Đỗ Thị Vân Anh – Dữ liệu: tiếp nhận dữ liệu, kiểm kê, Quality Gate, repair có kiểm soát, EDA, snapshot, catalog lớp và provenance.

Đỗ Hữu Nghị – Huấn luyện và đánh giá: cấu hình training, checkpoint/resume, fine-tune, đánh giá test độc lập, phân tích lỗi, ONNX/parity và đóng gói Candidate.

Quản Văn Điệp – Giao diện và QA: Streamlit UI, luồng ảnh/video, trạng thái lỗi, accessibility, UI/browser tests, hướng dẫn sử dụng và hỗ trợ demo.

1.4. Lịch trình và Các mốc quan trọng

Tuần 1 (28/09–04/10): hoàn thiện ứng dụng baseline, registry, manifest, ONNX, phân tích ảnh/video, CSV và các trang Streamlit. Mốc: demo end-to-end CPU với cảnh báo baseline rõ ràng.

Tuần 2 (05/10–11/10): kiểm định dữ liệu, repair có kiểm soát, EDA, snapshot và giao diện huấn luyện. Mốc: snapshot không có lỗi blocking và sẵn sàng huấn luyện.

Tuần 3 (12/10–18/10): train/fine-tune hoặc resume an toàn, đánh giá độc lập, export ONNX, parity, Candidate và hard-case correction. Mốc: Candidate có đủ bằng chứng để review, Production không tự thay đổi.

Tuần 4 (19/10–25/10): challenge report, test tự động/UI, benchmark CPU, README, báo cáo, slide và demo. Bàn giao dự kiến: 26/10/2026.

2. Triển khai dự án

2.1. Thu thập dữ liệu

Nguồn dữ liệu đích được chỉ định trong đặc tả là Traffic-sign-detection-VietNam trên Hugging Face, định dạng YOLO, gồm 10.157 ảnh và 82 lớp, giấy phép CC BY 4.0. Nguồn, phiên bản và thời điểm tiếp nhận phải được ghi nhận cùng artifact. YOLO11n COCO chỉ là baseline kỹ thuật; không dùng tập nhãn COCO hoặc kết quả baseline để tuyên bố hiệu năng cuối cho biển báo Việt Nam.

Dataset được kiểm tra theo các split train/val/test. Quality Gate chặn ảnh hỏng, dòng nhãn sai định dạng, class ID ngoài miền 0–81, tọa độ không hợp lệ và trùng checksum giữa các split. Các cảnh báo như mất cân bằng lớp hoặc bounding box quá nhỏ được ghi nhận để review thay vì bị loại âm thầm.

Sau khi đạt gate, hệ thống tạo snapshot bất biến gồm data.yaml, danh mục lớp, checksum, seed, validation report, EDA report và provenance. Test split được cô lập, không gộp lại vào train/val. Điều này bảo vệ tính độc lập của số liệu đánh giá cuối.

2.2. Phương pháp huấn luyện

Pipeline sử dụng YOLO với hai trạng thái tách bạch. Baseline là YOLO11n pretrained được export ONNX batch 1 để kiểm chứng ứng dụng. Fine-tune là một run mới từ checkpoint base được lựa chọn, dùng snapshot hợp lệ, không ghi đè Baseline hoặc Production.

Cấu hình huấn luyện phải lưu run ID, data.yaml, base model, epoch, batch size, imgsz, patience, AMP, thiết bị, seed, log và checkpoint best.pt/last.pt. Trên máy Windows có tài nguyên hạn chế, workers=0 và CPU fallback được ưu tiên để giảm áp lực bộ nhớ. Resume chỉ dùng checkpoint last.pt của run dừng/lỗi và vẫn giữ run ID, log và lịch sử.

Đánh giá Candidate thực hiện trên test split độc lập. Gói Candidate cần có checkpoint/ONNX, manifest, checksum, metrics thực tế, benchmark CPU và kết quả parity. Promotion chỉ được phép sau khi các điều kiện trên hợp lệ; thao tác tạo backup Production trước và cho phép rollback.

2.3. Quy trình xử lý hệ thống

Luồng suy luận: người dùng tải ảnh/video → hệ thống kiểm tra định dạng, dung lượng và nội dung → staging bằng tên do ứng dụng sinh → đọc Production manifest và kiểm tra checksum → suy luận YOLO/ONNX → vẽ box/nhãn → tạo ảnh hoặc video đầu ra, CSV và lịch sử cục bộ → UI hiển thị kết quả hoặc lỗi có hướng dẫn phục hồi.

Luồng dữ liệu và huấn luyện: tiếp nhận dữ liệu → Quality Gate → EDA → snapshot bất biến → cấu hình train/fine-tune → checkpoint/log → test độc lập → export ONNX/parity → Candidate → review → promotion hoặc rollback.

Luồng cải tiến hard case: upload ảnh khó → model gợi ý box/lớp → người dùng sửa annotation → pending review → approved hoặc rejected → snapshot fine-tune/challenge → fine-tune run mới từ best.pt → so sánh before/after trên cùng challenge. Challenge_only không được đưa vào train/val, và Candidate không được tự promotion.

2.4. Sơ đồ hệ thống

Giao diện Streamlit gồm các trang Phân tích, Lịch sử, Thống kê, Huấn luyện AI, Thông tin mô hình, Thiết lập và Cải thiện dữ liệu. UI chỉ gọi các service/domain contract, không tự ghi nhãn YOLO hoặc tự ánh xạ lớp.

Tầng ứng dụng gồm các module cấu hình/domain, media staging, inference ảnh/video, rendering/CSV, history SQLite, settings, model registry và training manager. Tầng dữ liệu gồm staging, snapshots, runs, outputs, state, corrections và backups. Model registry là ranh giới kiểm tra manifest/checksum, tách trạng thái baseline, candidate và production.

3. Kết quả

3.1. Tiền xử lý dữ liệu

Thiết kế hiện có kiểm soát việc đọc ảnh, nhãn và đường dẫn. Ảnh/video không được tin cậy chỉ theo phần mở rộng; tên tệp người dùng không được dùng trực tiếp làm đường dẫn runtime. Dữ liệu hợp lệ được chuẩn hóa theo cấu trúc YOLO và chỉ snapshot sau khi Quality Gate không còn lỗi blocking.

Kết quả định lượng cuối cho số ảnh hợp lệ, phân bố lớp và tỉ lệ cảnh báo phải được lấy từ validation/EDA artifact của snapshot được dùng để huấn luyện. Báo cáo này không tự điền các con số đó trước khi artifact cuối được chốt.

3.2. Phân tích dữ liệu khám phá (EDA)

EDA được thiết kế để tổng hợp số lượng ảnh và bounding box theo split/lớp, kích thước ảnh, aspect ratio, kích thước box, vị trí box, lớp thiếu mẫu và mẫu bất thường. Báo cáo EDA phục vụ quyết định review dữ liệu và collection goal, không phải là bằng chứng hiệu năng mô hình.

Các bảng/biểu đồ EDA cuối cần được sinh từ snapshot có manifest tương ứng. Khi bổ sung vào báo cáo nộp, mỗi hình phải ghi snapshot ID, ngày tạo và đường dẫn artifact để người đọc có thể kiểm tra nguồn số liệu.

3.3. Xây dựng mô hình

Ứng dụng đã được thiết kế để chạy baseline trước và chỉ thay model qua registry. Manifest là nguồn duy nhất cho model ID, backend, input size, class mapping, checksum và stage. Vì vậy UI không hard-code số lớp hoặc tên lớp; khi Candidate 82 lớp được promotion hợp lệ, giao diện đọc metadata mới mà không đổi luồng phân tích.

Tại thời điểm báo cáo, không công bố accuracy, Precision, Recall, F1, mAP, latency hay FPS chính thức của mô hình biển báo Việt Nam vì chưa có artifact đánh giá test cuối được chốt trong báo cáo. Các số liệu này chỉ được bổ sung từ test_metrics.json và benchmark.json của Candidate đã review, kèm snapshot ID và runtime fingerprint.

3.4. Giao diện người dùng

Trang Phân tích hỗ trợ ảnh JPG/PNG/WebP và video MP4/AVI/MOV; người dùng cấu hình confidence/IoU, xem detection, thống kê, tiến độ video và tải đầu ra. Các trang Lịch sử/Thống kê đọc dữ liệu cục bộ. Trang Huấn luyện AI trình bày quy trình dữ liệu → kiểm định/EDA → huấn luyện → đánh giá/xuất. Trang Thông tin mô hình hiển thị manifest, checksum, stage và lịch sử backup; Thiết lập quản lý các giới hạn runtime.

Giao diện phải hiển thị trạng thái baseline một cách trung thực. Khi model chưa fine-tune cho biển báo Việt Nam, không được gắn nhãn 82 lớp hoặc hiển thị metric chưa tồn tại. Khi lỗi đầu vào, registry, training hoặc export xảy ra, UI phải nêu nguyên nhân và cho phép người dùng retry có chủ đích.

3.5. Kiểm thử và cải tiến

Kế hoạch kiểm thử bao phủ unit test cho cấu hình/domain, Quality Gate, snapshot, EDA, registry, media, inference, rendering, history, training, candidate và promotion/rollback; integration test cho luồng dataset → snapshot → training → Candidate → promotion → inference; UI/browser test cho trạng thái chính và lỗi biên.

Các trường hợp biên trọng yếu gồm tệp giả mạo định dạng, ảnh/video hỏng, path traversal, video lỗi giữa chừng, checksum model bị thay đổi, nhãn/tọa độ YOLO sai, data leakage, resume run không hợp lệ và promotion lỗi. Các run test còn đang được hoàn tất/đối chiếu tại thời điểm lập báo cáo nên không ghi nhận một tổng số pass giả định. Bằng chứng nộp cuối phải đính kèm command, thời điểm chạy và kết quả thực tế.

4. Projected Impact

4.1. Accomplishments and Benefits

TrafficVision tạo một quy trình có thể trình diễn từ dữ liệu đến suy luận thay vì chỉ cung cấp một notebook huấn luyện. Tách Baseline/Candidate/Production giúp nhóm diễn giải đúng bằng chứng; snapshot/checksum/provenance giúp kết quả tái lập; promotion/rollback giúp giảm rủi ro khi thay mô hình. Correction queue và challenge cô lập tạo cơ chế thu thập lỗi thực tế mà không làm ô nhiễm test set.

Với người dùng học tập, ứng dụng cho thấy trực quan kết quả phát hiện trên ảnh/video, giới hạn dữ liệu/mô hình và cách kiểm chứng một hệ thống AI. Với nhóm phát triển, các artifact có cấu trúc hỗ trợ truy vết nguồn dữ liệu, cấu hình và thay đổi mô hình.

4.2. Future Improvements

Sau khi hoàn thành các gate bắt buộc, nhóm có thể mở rộng bộ challenge với ảnh biển nhỏ, xa, mờ và nghiêng; bổ sung phân tích lỗi theo lớp/bối cảnh; tối ưu inference CPU từ benchmark có kiểm soát; và cải thiện catalog hình mẫu cho thao tác annotation. Các mở rộng như camera trực tiếp, triển khai cloud hoặc tài khoản nhiều người dùng chỉ được xem xét sau khi phạm vi MVP, số liệu test và cơ chế vận hành hiện tại đạt nghiệm thu.

5. Kết luận

TrafficVision được định hướng là hệ thống nhận dạng biển báo có bằng chứng truy vết, không chỉ là demo mô hình. Điểm cốt lõi của đồ án là chuỗi kiểm soát: dữ liệu hợp lệ → snapshot tái lập → run có checkpoint → test độc lập → Candidate có manifest/checksum → review → promotion/rollback. Báo cáo giữ ranh giới bằng chứng rõ ràng: baseline hỗ trợ kiểm chứng ứng dụng, còn hiệu năng biển báo Việt Nam chỉ được kết luận khi có evaluation artifact cuối.

Trước khi nộp chính thức, nhóm cần bổ sung ảnh nhóm, ảnh chụp giao diện, biểu đồ EDA, bảng test metrics, benchmark CPU và liên kết artifact tương ứng sau khi các kết quả này được tạo và review.
'@

$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $document = $word.Documents.Open($output)

    function Replace-DocumentText([string]$findText, [string]$replaceText) {
        $range = $document.Content
        $find = $range.Find
        $find.ClearFormatting()
        $find.Replacement.ClearFormatting()
        $find.Text = $findText
        $find.Replacement.Text = $replaceText
        $find.Forward = $true
        $find.Wrap = 1
        $find.Format = $false
        if ($find.Execute()) {
            $range.Text = $replaceText
        }
    }

    Replace-DocumentText "< TÊN ĐỀ TÀI >" "TRAFFICVISION – NHẬN DẠNG BIỂN BÁO GIAO THÔNG VIỆT NAM BẰNG AI"
    Replace-DocumentText "< Date (DD/MM/YY) >" "02/10/2026"
    Replace-DocumentText "Tên nhóm" "Nhóm RoadVision"
    Replace-DocumentText "<Member 1>" "Phí Văn Nam – Trưởng nhóm"
    Replace-DocumentText "<Member 2>" "Đỗ Thị Vân Anh"
    Replace-DocumentText "<Member 3>" "Đỗ Hữu Nghị"
    Replace-DocumentText "<Member 4>" "Quản Văn Điệp"
    Replace-DocumentText "<Member 5>" ""
    Replace-DocumentText "<ATTACH A TEAM PICTURE HERE>" "Ảnh nhóm RoadVision – bổ sung khi có ảnh chính thức"

    $startRange = $document.Content.Duplicate
    $startFind = $startRange.Find
    $startFind.ClearFormatting()
    $startFind.Text = "1. Introduction"
    if (-not $startFind.Execute()) { throw "Không tìm thấy vùng nội dung báo cáo trong template." }

    $endRange = $document.Content.Duplicate
    $endFind = $endRange.Find
    $endFind.ClearFormatting()
    $endFind.Text = "5. Team Member Review and Comment"
    if (-not $endFind.Execute()) { throw "Không tìm thấy vùng nhận xét nhóm trong template." }

    $body = $document.Range($startRange.Start, $endRange.Start)
    $body.Text = $reportText
    $body.Font.Name = "Times New Roman"
    $body.Font.Size = 12
    $body.ParagraphFormat.SpaceAfter = 6
    $body.ParagraphFormat.LineSpacingRule = 0
    $body.ParagraphFormat.LineSpacing = 14

    foreach ($paragraph in $body.Paragraphs) {
        $line = $paragraph.Range.Text.Trim("`r", "`n", [char]7, [char]12)
        if ($line -match '^[1-5]\. (Giới thiệu|Triển khai dự án|Kết quả|Projected Impact|Kết luận)$') {
            $paragraph.Range.Font.Bold = 1
            $paragraph.Range.Font.Size = 14
            $paragraph.Range.ParagraphFormat.SpaceBefore = 12
        }
        elseif ($line -match '^[1-5]\.[1-9]\. ') {
            $paragraph.Range.Font.Bold = 1
            $paragraph.Range.Font.Size = 12
            $paragraph.Range.ParagraphFormat.SpaceBefore = 6
        }
    }

    $document.Fields.Update() | Out-Null
    $document.Save()
    $document.Close($true)
    $document = $null
} finally {
    if ($document) { $document.Close($false) }
    if ($word) {
        $word.Quit()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
    }
}

Write-Output "FINAL_REPORT_TEMPLATE_COPY=PASS"
