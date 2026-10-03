#!/usr/bin/env python3
"""Build comprehensive technical training guide, defense Q&A guide, slides, and export all to PDF."""

from __future__ import annotations

import base64
import io
import subprocess
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def get_image_base64(rel_path: str, max_width: int = 800) -> str:
    path = REPO_ROOT / rel_path
    if not path.is_file():
        return ""
    try:
        im = Image.open(path)
        if im.width > max_width:
            ratio = max_width / float(im.width)
            new_height = int(im.height * ratio)
            im = im.resize((max_width, new_height), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=85)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as exc:
        print(f"Error encoding {path}: {exc}")
        return ""


img1_b64 = get_image_base64("artifacts/outputs/2016b014-7e54-4b9f-a4f4-81a74c9c2701_annotated.jpg", max_width=720)
img2_b64 = get_image_base64("artifacts/outputs/1ebf731e-aee7-423d-a9f0-fd2de27738a6_annotated.jpg", max_width=800)
img3_b64 = get_image_base64("artifacts/outputs/1b1ca112-d251-4651-ab78-0b67f6fc5460_annotated.jpg", max_width=800)


def build_slide_html() -> str:
    # Read the slide template from scripts/generate_html_assets.py logic with improved @media print
    from generate_html_assets import build_defense_presentation_html
    html = build_defense_presentation_html()

    # Enhance @media print for multi-page slides export
    print_css = """
    @media print {
      @page {
        size: 16in 9in landscape;
        margin: 0;
      }
      body, html {
        overflow: visible !important;
        height: auto !important;
        background: #070d19 !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
      .progress-bar, .controls {
        display: none !important;
      }
      .deck {
        display: block !important;
        position: static !important;
        width: 100% !important;
        height: auto !important;
      }
      .slide {
        position: relative !important;
        width: 100vw !important;
        height: 100vh !important;
        max-width: none !important;
        opacity: 1 !important;
        display: flex !important;
        transform: none !important;
        page-break-after: always !important;
        break-after: page !important;
        margin: 0 !important;
        border-radius: 0 !important;
        border: none !important;
        padding: 50px 70px !important;
        box-shadow: none !important;
      }
    }
    """
    html = html.replace("</style>", f"{print_css}\n  </style>")
    return html


def build_training_deep_dive_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tài Liệu Kỹ Thuật Huấn Luyện & Phương Pháp Xử Lý Chuyên Sâu - TrafficVision</title>
  <style>
    :root {{
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --secondary: #0f172a;
      --accent: #0d9488;
      --text: #1e293b;
      --text-muted: #64748b;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.7;
      font-size: 15px;
      padding: 40px 20px;
    }}
    .container {{
      max-width: 1000px;
      margin: 0 auto;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 48px 56px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }}
    header {{
      border-bottom: 2px solid var(--border);
      padding-bottom: 24px;
      margin-bottom: 32px;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 99px;
      background: #eff6ff;
      color: var(--primary);
      font-weight: 700;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
    }}
    h1 {{
      font-size: 28px;
      color: #0f172a;
      margin-bottom: 10px;
      line-height: 1.3;
    }}
    .meta-box {{
      background: #f1f5f9;
      border-radius: 8px;
      padding: 12px 18px;
      font-size: 13px;
      color: #475569;
      display: flex;
      flex-wrap: wrap;
      gap: 24px;
      margin-top: 14px;
    }}
    h2 {{
      font-size: 20px;
      color: #0f172a;
      margin: 36px 0 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    h3 {{
      font-size: 16px;
      color: #1e293b;
      margin: 22px 0 10px;
    }}
    p, li {{
      font-size: 14.5px;
      color: #334155;
      margin-bottom: 10px;
    }}
    ul, ol {{
      margin-left: 24px;
      margin-bottom: 16px;
    }}
    pre {{
      background: #0f172a;
      color: #f8fafc;
      padding: 16px 20px;
      border-radius: 10px;
      overflow-x: auto;
      font-family: var(--font-mono);
      font-size: 13px;
      margin: 14px 0 20px;
      line-height: 1.5;
    }}
    code {{
      font-family: var(--font-mono);
      background: #e2e8f0;
      color: #0f172a;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 13px;
    }}
    pre code {{
      background: transparent;
      color: inherit;
      padding: 0;
    }}
    .callout {{
      padding: 16px 20px;
      border-radius: 10px;
      border-left: 4px solid var(--primary);
      background: #eff6ff;
      margin: 18px 0;
      font-size: 14px;
      color: #1e40af;
    }}
    .callout-warning {{
      border-color: #f59e0b;
      background: #fffbeb;
      color: #92400e;
    }}
    .callout-success {{
      border-color: #10b981;
      background: #f0fdf4;
      color: #166534;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 18px 0;
      font-size: 13.5px;
    }}
    th, td {{
      padding: 10px 14px;
      border: 1px solid var(--border);
      text-align: left;
    }}
    th {{
      background: #f1f5f9;
      color: #1e293b;
      font-weight: 700;
    }}
    .formula-box {{
      background: #fafafa;
      border: 1px dashed #cbd5e1;
      border-radius: 8px;
      padding: 14px 20px;
      font-family: var(--font-mono);
      font-size: 13px;
      color: #0f172a;
      margin: 14px 0;
    }}
    .diagram-box {{
      background: #0f172a;
      color: #38bdf8;
      border-radius: 10px;
      padding: 18px;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.45;
      overflow-x: auto;
      margin: 16px 0;
    }}
    @media print {{
      body {{ background: #fff; padding: 0; }}
      .container {{ border: none; box-shadow: none; padding: 0; max-width: 100%; }}
      pre, code {{ font-size: 11px; }}
    }}
  </style>
</head>
<body>

<div class="container">
  <header>
    <span class="badge">TÀI LIỆU KỸ THUẬT NỘI BỘ & HỘI ĐỒNG BẢO VỆ</span>
    <h1>Kiến Trúc Kỹ Thuật, Phương Pháp Xử Lý & Quy Trình Huấn Luyện AI Chuyên Sâu</h1>
    <p style="color: #64748b; font-size: 15px;">Dự án: <strong>TrafficVision – Hệ thống nhận dạng biển báo giao thông Việt Nam bằng AI</strong></p>
    
    <div class="meta-box">
      <div><strong>Tác giả:</strong> Nhóm nghiên cứu & phát triển TrafficVision</div>
      <div><strong>Kiến trúc:</strong> YOLO11 Nano (yolo11n) + ONNX Runtime</div>
      <div><strong>Chuẩn phân loại:</strong> 82 Lớp QCVN 41:2019/BGTVT</div>
      <div><strong>Cập nhật:</strong> Tháng 10/2026</div>
    </div>
  </header>

  <!-- MỤC 1: KIẾN TRÚC MÔ HÌNH -->
  <h2>1. Kiến trúc Mô hình YOLO11 Nano & Nguyên lý Nhận dạng</h2>
  <p>Hệ thống lựa chọn <strong>YOLO11 Nano (yolo11n)</strong> do Ultralytics phát hành làm kiến trúc cơ bản nhờ tỷ lệ tối ưu giữa độ chính xác nhận dạng và độ trễ suy luận trên phần cứng CPU không có GPU rời.</p>

  <div class="diagram-box">
[ Ảnh đầu vào (Input 3x640x640) ]
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. BACKBONE: Trích xuất đặc trưng đa quy mô                 │
│    - C3k2 Blocks (Cross Stage Partial với kernel tinh chỉnh)│
│    - SPPF (Spatial Pyramid Pooling - Fast)                  │
│    - C2PSA Block: Cơ chế Attention tự chú ý không gian       │
└──────────────────────────────┬──────────────────────────────┘
                               │ (P3: 80x80, P4: 40x40, P5: 20x20)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. NECK: Dung hợp đa tỷ lệ PAN-FPN (Path Aggregation)       │
│    - Ghép nối thông tin ngữ nghĩa sâu với vị trí nông       │
│    - Tăng cường khả năng nhận diện biển báo kích thước nhỏ  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. HEAD: Decoupled Head (Phân tách độc lập)                 │
│    - Nhánh 1: Phân loại lớp biển báo (Classification)       │
│    - Nhánh 2: Hồi quy tọa độ hộp bao (Bounding Box Reg)     │
└─────────────────────────────────────────────────────────────┘
  </div>

  <h3>Tại sao chọn YOLO11 Nano?</h3>
  <ul>
    <li><strong>Kích thước nhỏ gọn:</strong> Số tham số ~2.6 triệu, trọng số FP32 ONNX chỉ khoảng <strong>10.2 MB</strong>.</li>
    <li><strong>Khối C2PSA (Cross Stage Partial with Pointwise Spatial Attention):</strong> Tăng cường khả năng tập trung vào các chi tiết biển báo nhỏ ở xa (Small Objects), vốn là điểm yếu của các kiến trúc YOLO thế hệ cũ.</li>
    <li><strong>Decoupled Head:</strong> Tách biệt việc dự đoán nhãn loại biển và định vị tọa độ hộp bao, giảm thiểu xung đột gradient khi huấn luyện.</li>
  </ul>

  <!-- MỤC 2: TIỀN XỬ LÝ DỮ LIỆU -->
  <h2>2. Kỹ thuật Tiền xử lý & Chuẩn hóa Ảnh (Image Processing)</h2>
  <p>Để đảm bảo suy luận nhất quán và chính xác, mọi hình ảnh và khung hình video đều đi qua quy trình tiền xử lý toán học chuẩn hóa:</p>

  <h3>2.1. Thuật toán Letterbox (Bảo toàn tỷ lệ khung hình)</h3>
  <p>Khi ảnh đầu vào có tỷ lệ khác với tỷ lệ vuông 1:1 của mô hình (ví dụ ảnh 1920x1080 từ camera hành trình), thuật toán Letterbox sẽ:</p>
  <ol>
    <li>Tính toán tỷ lệ co giãn tối đa mà không làm biến dạng hình học: <code>gain = min(640 / width, 640 / height)</code>.</li>
    <li>Resize ảnh theo tỷ lệ <code>gain</code>.</li>
    <li>Chèn thêm đệm màu xám (Pixel value = 114) đều vào hai bên hoặc trên/dưới để đạt đúng kích thước <code>640 x 640</code>.</li>
  </ol>

  <div class="formula-box">
Tọa độ thực = (Tọa độ chuẩn hóa trên mô hình - Lượng padding) / gain
  </div>

  <h3>2.2. Chuẩn hóa không gian màu & Tensor</h3>
  <ul>
    <li>Chuyển đổi không gian màu từ BGR (OpenCV) sang <strong>RGB</strong>.</li>
    <li>Chuẩn hóa giá trị pixel từ dải số nguyên <code>[0, 255]</code> sang số thực <code>[0.0, 1.0]</code> bằng phép chia <code>255.0</code>.</li>
    <li>Hoán vị chiều dữ liệu (Permute) từ dạng HWC (Height x Width x Channel) sang <strong>CHW</strong>: <code>(1, 3, 640, 640)</code>.</li>
  </ul>

  <!-- MỤC 3: HÀM MẤT MÁT -->
  <h2>3. Hàm Mất Mát (Loss Functions) & Chiến lược Tối ưu hóa</h2>
  <p>Quá trình huấn luyện sử dụng hàm tổn thất tổng hợp gồm 3 thành phần chính:</p>

  <div class="formula-box">
Tổng Loss = &lambda;<sub>box</sub> &middot; L<sub>CIoU</sub> + &lambda;<sub>cls</sub> &middot; L<sub>BCE</sub> + &lambda;<sub>dfl</sub> &middot; L<sub>DFL</sub>
  </div>

  <ul>
    <li><strong>CIoU Loss (Complete Intersection over Union):</strong> Đo đạc độ tương đồng của hộp bao dự đoán và nhãn thật dựa trên: diện tích chồng lấn (IoU), khoảng cách giữa 2 tâm hộp và tỷ lệ cạnh dài/ngắn. Khắc phục hoàn toàn nhược điểm của hàm mất mát khoảng cách L1/L2 truyền thống.</li>
    <li><strong>BCE Loss (Binary Cross-Entropy):</strong> Tính toán tổn thất phân loại độc lập cho 82 lớp biển báo, hỗ trợ đa nhãn hiệu quả.</li>
    <li><strong>DFL Loss (Distribution Focal Loss):</strong> Hồi quy tọa độ hộp bao dưới dạng phân phối xác suất liên tục thay vì một điểm số cứng nhắc, giúp mô hình bắt viền biển báo sắc nét ngay cả khi bị che khuất một phần.</li>
  </ul>

  <h3>Chiến lược tối ưu hóa Hyperparameters:</h3>
  <table>
    <thead>
      <tr>
        <th>Siêu tham số</th>
        <th>Giá trị cấu hình</th>
        <th>Ý nghĩa kỹ thuật</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Optimizer</td>
        <td><code>AdamW</code> hoặc <code>SGD with Momentum</code></td>
        <td>Cân bằng tốc độ hội tụ và khả năng khái quát hóa dữ liệu.</td>
      </tr>
      <tr>
        <td>Learning Rate ban đầu (lr0)</td>
        <td><code>0.01</code></td>
        <td>Tốc độ học ban đầu.</td>
      </tr>
      <tr>
        <td>LR Scheduler</td>
        <td><code>Cosine Annealing</code></td>
        <td>Hạ dần learning rate theo đường cong cosin, giúp mô hình ổn định tại cực tiểu.</td>
      </tr>
      <tr>
        <td>Mixed Precision (AMP)</td>
        <td><code>Enabled</code></td>
        <td>Tự động sử dụng Float16 trong quá trình tính toán để tăng tốc và tiết kiệm 50% VRAM.</td>
      </tr>
      <tr>
        <td>Patience</td>
        <td><code>10 epochs</code></td>
        <td>Early stopping: Dừng huấn luyện nếu mAP50 trên tập Validation không tăng sau 10 epoch liên tiếp nhằm chống Overfitting.</td>
      </tr>
    </tbody>
  </table>

  <!-- MỤC 4: QUY TRÌNH MLOPS 4 BƯỚC -->
  <h2>4. Quy trình MLOps 4 Bước Khép Kín trong TrafficVision</h2>

  <div class="callout callout-success">
    <strong>Triết lý thiết kế:</strong> Mọi thử nghiệm đều phải có tính lặp lại (Reproducibility), có kiểm soát rủi ro và không được can thiệp vào môi trường phục vụ trực tuyến khi chưa được kiểm định đạt chuẩn.
  </div>

  <h3>Bước 1: Quét Dữ Liệu & Tiếp Nhận (Dataset Ingestion)</h3>
  <p>Hệ thống quét dữ liệu từ <code>artifacts/staging/</code> với 3 tập: <code>train/</code>, <code>val/</code>, <code>test/</code>. Hỗ trợ tính năng sinh <strong>Synthetic Fixture</strong> (100 mẫu giả lập) để kiểm thử toàn diện mã nguồn pipeline mà không cần tải tập dữ liệu 10.000 ảnh về máy phát triển.</p>

  <h3>Bước 2: Cổng Kiểm Định Quality Gate 5 Tiêu Chí & EDA</h3>
  <p>Chặn đứng 5 loại lỗi nguy hiểm trước khi tốn tài nguyên huấn luyện:</p>
  <ul>
    <li><code>CORRUPT_IMAGE</code>: Loại bỏ ảnh 0-byte, lỗi định dạng tệp hoặc ảnh không giải mã được.</li>
    <li><code>MALFORMED_YOLO_LINE</code>: Kiểm tra cú pháp dòng nhãn (bắt buộc đúng 5 cột số: <code>class_id center_x center_y width height</code>).</li>
    <li><code>CLASS_ID_OUT_OF_RANGE</code>: Đảm bảo class ID chỉ nằm trong dải [0, 81] tương ứng với danh mục QCVN 41:2019.</li>
    <li><code>INVALID_COORDINATES</code>: Bắt buộc tọa độ tâm và kích thước nằm trong khoảng <code>(0, 1]</code>.</li>
    <li><code>DATA_LEAKAGE</code>: Tính mã băm SHA-256 từng tệp ảnh. Nếu phát hiện cùng một ảnh xuất hiện ở cả tập Train và Val/Test, hệ thống sẽ chặn ngay lập tức để tránh đánh giá gian lận điểm mAP.</li>
  </ul>
  <p>Khi vượt qua, hệ thống tạo <strong>Snapshot bất biến</strong> tại <code>artifacts/snapshots/&lt;snapshot_id&gt;/</code> kèm <code>data.yaml</code> và xuất báo cáo <code>eda_report.json</code>.</p>

  <h3>Bước 3: Huấn Luyện Nền Ngầm (Background Subprocess Execution)</h3>
  <p>Thay vì chạy blocking làm treo giao diện Streamlit, tiến trình huấn luyện được ủy quyền cho một tiến trình hệ thống con độc lập qua module <code>TrainingManager</code>:</p>
  <ul>
    <li>Ghi nhật ký thời gian thực vào <code>artifacts/runs/&lt;run_id&gt;/train.log</code>.</li>
    <li>Cập nhật trạng thái tiến độ vào <code>state.json</code> (epoch hiện tại, loss, mAP, thời gian còn lại).</li>
    <li>Giao diện Web đọc định kỳ trạng thái để hiển thị biểu đồ và thanh tiến trình.</li>
    <li>Hỗ trợ ngắt an toàn (Safe Abort): Gửi tín hiệu <code>SIGINT</code> để Ultralytics lưu checkpoint dở dang mà không gây hỏng dữ liệu.</li>
  </ul>

  <h3>Bước 4: Đóng Gói Ứng Viên (Candidate Packaging) & Thăng Cấp (Promotion)</h3>
  <p>Sau khi kết thúc huấn luyện, mô hình phải vượt qua 3 bài kiểm tra chất lượng tự động:</p>
  <ol>
    <li><strong>Đánh giá độc lập trên tập Test:</strong> Đo đạc Precision, Recall, mAP50, mAP50-95.</li>
    <li><strong>Xuất ONNX & Kiểm tra Parity:</strong> Xuất sang ONNX đồ thị tĩnh <code>[1, 3, 640, 640]</code>. Chạy cùng một tensor đầu vào trên cả PyTorch và ONNX Runtime CPU, sau đó tính sai số tuyệt đối cực đại:
      <pre><code>max_abs_diff = np.max(np.abs(torch_output - onnx_output))
assert max_abs_diff &lt;= 1e-3, "Parity check failed!"</code></pre>
    </li>
    <li><strong>Benchmark CPU:</strong> Chạy 100 lần lặp suy luận để xác định FPS trung bình và độ trễ p50, p95.</li>
  </ol>
  <p>Chỉ khi đáp ứng toàn bộ điều kiện trên, thư mục <code>artifacts/runs/&lt;run_id&gt;/candidate/</code> mới được tạo kèm <code>manifest.json</code>.</p>

  <!-- MỤC 5: TỐI ƯU HÓA SUY LUẬN ONNX TRÊN CPU -->
  <h2>5. Kỹ Thuật Tối Ưu Hóa Suy Luận ONNX trên CPU</h2>
  <p>Nhằm đáp ứng yêu cầu chạy mượt trên máy tính văn phòng hoặc máy tính nhúng, các kỹ thuật sau được tích hợp trong <code>OnnxPredictor</code>:</p>
  <ul>
    <li><strong>Đồ thị tĩnh (Static Shape):</strong> Khóa cứng kích thước input <code>1x3x640x640</code> giúp ONNX Runtime cấp phát trước bộ nhớ (pre-allocate memory), tránh hiện tượng phân mảnh RAM.</li>
    <li><strong>Graph Optimization Level:</strong> Bật mức <code>ORT_ENABLE_ALL</code>, thực hiện gộp các phép tính liền kề (Constant Folding, Node Fusion như Conv + BatchNorm + SiLU thành một toán tử duy nhất).</li>
    <li><strong>Đa luồng CPU (Inter & Intra Op):</strong> Thiết lập số luồng tính toán tương ứng với số nhân vật lý của CPU thông qua OpenMP/AVX2.</li>
    <li><strong>Hậu xử lý NMS tối ưu (Fast Non-Maximum Suppression):</strong> Lọc nhanh các hộp bao có confidence &lt; ngưỡng cài đặt, sau đó chỉ chạy IoU trên tập ứng viên còn lại, giảm độ phức tạp thuật toán từ $O(N^2)$ xuống $O(k \log k)$.</li>
  </ul>

  <!-- MỤC 6: AN TOÀN VẬN HÀNH -->
  <h2>6. Cơ Chế An Toàn Vận Hành: Safe Atomic Swap & Rollback</h2>
  <p>Một điểm đột phá trong thiết kế của TrafficVision là sự đảm bảo an toàn tuyệt đối khi triển khai mô hình:</p>

  <div class="diagram-box">
[ Thăng cấp Candidate Mới ]
           │
           ▼
┌──────────────────────────────────────────┐
│ 1. Sao lưu tự động (Automatic Backup)     │
│    Sao chép Production hiện tại sang     │
│    artifacts/backups/backup_&lt;timestamp&gt;/ │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│ 2. Hoán đổi nguyên tử (Atomic Copy)      │
│    Ghi đè model.onnx & manifest.json     │
│    vào artifacts/production/             │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│ 3. Hậu kiểm tra tính toàn vẹn (Verify)   │
│    Kiểm tra mã băm SHA-256 & nạp thử     │
└──────────────────┬───────────────────────┘
          /                 \
     (Thành công)          (Phát hiện lỗi)
          │                         │
          ▼                         ▼
   [ Hoàn tất ]             [ Tự động Rollback ]
                            Khôi phục từ bản Backup
  </div>

  <p>Người quản trị có thể kích hoạt hoàn tác bất kỳ lúc nào chỉ bằng lệnh dòng lệnh <code>python scripts/promote_model.py --rollback</code> hoặc bấm nút trên giao diện Web.</p>

  <footer style="margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border); font-size: 13px; color: #64748b; text-align: center;">
    Tài liệu kỹ thuật TrafficVision • Lưu hành nội bộ và phục vụ hội đồng bảo vệ dự án 2026
  </footer>
</div>

</body>
</html>
"""


def build_defense_qa_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bộ Câu Hỏi & Trả Lời Bảo Vệ Đồ Án - TrafficVision</title>
  <style>
    :root {{
      --primary: #1e40af;
      --primary-light: #eff6ff;
      --border: #e2e8f0;
      --text: #1e293b;
      --text-muted: #64748b;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.7;
      font-size: 15px;
      padding: 40px 20px;
    }}
    .container {{
      max-width: 1040px;
      margin: 0 auto;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 48px 56px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.06);
    }}
    header {{
      border-bottom: 2px solid var(--border);
      padding-bottom: 24px;
      margin-bottom: 32px;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 99px;
      background: #eff6ff;
      color: #2563eb;
      font-weight: 700;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
    }}
    h1 {{
      font-size: 28px;
      color: #0f172a;
      line-height: 1.3;
      margin-bottom: 8px;
    }}
    .member-section {{
      margin-top: 40px;
      border-top: 2px dashed var(--border);
      padding-top: 28px;
    }}
    .member-header {{
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 20px;
    }}
    .member-avatar {{
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, #2563eb, #14b8a6);
      color: white;
      display: grid;
      place-items: center;
      font-weight: 800;
      font-size: 16px;
    }}
    .member-name {{
      font-size: 20px;
      font-weight: 800;
      color: #0f172a;
    }}
    .member-role {{
      font-size: 13px;
      color: #2563eb;
      font-weight: 600;
    }}
    .qa-card {{
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.02);
      transition: border-color 0.2s ease;
    }}
    .qa-card:hover {{
      border-color: #93c5fd;
    }}
    .question {{
      font-size: 15px;
      font-weight: 700;
      color: #1e3a8a;
      display: flex;
      gap: 10px;
      margin-bottom: 10px;
    }}
    .q-icon {{
      background: #dbeafe;
      color: #1d4ed8;
      width: 24px;
      height: 24px;
      border-radius: 6px;
      display: inline-grid;
      place-items: center;
      font-size: 12px;
      font-weight: 800;
      flex-shrink: 0;
    }}
    .answer {{
      font-size: 14px;
      color: #334155;
      padding-left: 34px;
      line-height: 1.65;
    }}
    .answer strong {{
      color: #0f172a;
    }}
    .tip-box {{
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-radius: 8px;
      padding: 8px 14px;
      margin-top: 10px;
      font-size: 12.5px;
      color: #166534;
    }}
    .code-inline {{
      font-family: var(--font-mono);
      background: #f1f5f9;
      padding: 2px 6px;
      border-radius: 4px;
      color: #0f172a;
      font-size: 12.5px;
    }}
    @media print {{
      body {{ background: #fff; padding: 0; }}
      .container {{ border: none; box-shadow: none; padding: 0; max-width: 100%; }}
      .qa-card {{ page-break-inside: avoid; }}
    }}
  </style>
</head>
<body>

<div class="container">
  <header>
    <span class="badge">TÀI LIỆU BẢO VỆ ĐỒ ÁN / HỎI ĐÁP PHẢN BIỆN</span>
    <h1>Cẩm Nang Trả Lời Câu Hỏi Phản Biện Của Hội Đồng (Q&A)</h1>
    <p style="color: #64748b; font-size: 15px;">Dự án: <strong>TrafficVision – Nhận dạng biển báo giao thông Việt Nam bằng AI</strong></p>
    <p style="font-size: 13px; color: #475569; margin-top: 6px;">Tài liệu được phân chia cụ thể theo từng mảng công việc phụ trách của 4 thành viên trong nhóm, giúp các bạn nắm chắc kiến thức và tự tin trả lời trước Thầy Cô.</p>
  </header>

  <!-- ========================================== -->
  <!-- PHẦN 1: PHÍ VĂN NAM (TRƯỞNG NHÓM) -->
  <!-- ========================================== -->
  <div class="member-section" style="border-top: none; padding-top: 0;">
    <div class="member-header">
      <div class="member-avatar">PVN</div>
      <div>
        <div class="member-name">1. Phí Văn Nam (Trưởng nhóm)</div>
        <div class="member-role">Phụ trách: Kiến trúc tổng thể, Tích hợp MLOps, Luồng dữ liệu hệ thống, Cơ sở dữ liệu SQLite & Quản trị rủi ro</div>
      </div>
    </div>

    <!-- CÂU 1 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q1</span>
        <span>Thầy/Cô hỏi: Tại sao nhóm lại thiết kế hệ thống tách biệt giữa Quy trình Trực tuyến (Online Inference) và Quy trình Ngoại tuyến (Offline Training)? Lợi ích kiến trúc ở đây là gì?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, đây là nguyên lý thiết kế tối quan trọng trong kỹ nghệ phần mềm AI (MLOps). Việc tách biệt mang lại 3 lợi ích cốt lõi:</p>
        <ol style="margin-left: 20px; margin-top: 4px;">
          <li><strong>Tính sẵn sàng dịch vụ (High Availability):</strong> Người dùng khi tải ảnh hoặc video để phân tích chỉ tương tác với <code>Production Model</code> ở trạng thái chỉ đọc (Read-only). Quá trình huấn luyện mô hình mới có thể kéo dài hàng giờ và tiêu tốn nhiều CPU/GPU nhưng diễn ra hoàn toàn ở một tiến trình nền độc lập, không làm đơ hoặc nghẽn giao diện người dùng.</li>
          <li><strong>Bảo vệ môi trường Production:</strong> Nếu quá trình huấn luyện bị lỗi, hết bộ nhớ hoặc mô hình mới chưa đạt độ chính xác mAP kỳ vọng, luồng phục vụ hiện tại hoàn toàn không bị ảnh hưởng.</li>
          <li><strong>Khả năng mở rộng (Scalability):</strong> Chúng ta có thể dễ dàng tách tầng huấn luyện sang một cụm máy chủ GPU đám mây chuyên dụng mà không cần viết lại mã nguồn tầng ứng dụng giao diện.</li>
        </ol>
        <div class="tip-box">
          💡 <em>Mẹo ghi điểm:</em> Nhấn mạnh nhóm đã cài đặt <code>TrainingManager</code> chạy ngầm dạng Subprocess và ghi nhận trạng thái vào <code>state.json</code>.
        </div>
      </div>
    </div>

    <!-- CÂU 2 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q2</span>
        <span>Thầy/Cô hỏi: Cơ chế Thăng cấp (Promotion) và Hoàn tác (Rollback) của nhóm hoạt động như thế nào? Làm sao đảm bảo mô hình không bị hỏng khi đang cập nhật?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, nhóm sử dụng cơ chế <strong>Hoán đổi nguyên tử an toàn (Safe Atomic Swap)</strong> được quản lý bởi <code>ModelRegistry</code>:</p>
        <ol style="margin-left: 20px; margin-top: 4px;">
          <li><strong>Bước 1 (Tự động Sao lưu):</strong> Trước khi bất kỳ mô hình mới nào ghi đè lên production, hệ thống lập tức sao chép nguyên vẹn mô hình cũ cùng tệp <code>manifest.json</code> vào thư mục sao lưu: <code>artifacts/backups/backup_&lt;timestamp&gt;/</code>.</li>
          <li><strong>Bước 2 (Kiểm định Checksum SHA-256):</strong> Mô hình Candidate chỉ được phép thăng cấp nếu tệp ONNX hợp lệ, đúng cấu trúc 82 lớp và khớp chính xác mã băm SHA-256 để chống lỗi hỏng tệp.</li>
          <li><strong>Bước 3 (Rollback 1-Click):</strong> Nếu sau khi thăng cấp có bất kỳ sự cố nào, hệ thống hỗ trợ khôi phục tức thì về bản sao lưu trước đó chỉ với 1 cú click chuột trên Web UI hoặc lệnh <code>python scripts/promote_model.py --rollback</code> mà không cần khởi động lại ứng dụng.</li>
        </ol>
      </div>
    </div>

    <!-- CÂU 3 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q3</span>
        <span>Thầy/Cô hỏi: Tại sao nhóm chọn SQLite làm cơ sở dữ liệu lưu trữ lịch sử thay vì MySQL hay MongoDB?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, lý do nhóm chọn <strong>SQLite</strong>:</p>
        <ul>
          <li><strong>Cấu hình không phụ thuộc (Zero Configuration):</strong> Toàn bộ cơ sở dữ liệu nằm trong tệp <code>trafficvision.db</code> tại <code>artifacts/state/</code>. Người dùng tải mã nguồn về là có thể chạy ngay lập tức mà không cần cài đặt máy chủ DB riêng hay cấu hình username/password phức tạp.</li>
          <li><strong>Hiệu năng đọc ghi cực nhanh:</strong> Với quy mô hàng trăm nghìn phiên nhật ký cục bộ, SQLite chạy in-process với độ trễ dưới 1 mili-giây, hoàn toàn đáp ứng tốt nhu cầu lưu trữ tệp, thời gian xử lý và danh sách bounding boxes.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ========================================== -->
  <!-- PHẦN 2: ĐỖ THỊ VÂN ANH (KỸ SƯ DỮ LIỆU) -->
  <!-- ========================================== -->
  <div class="member-section">
    <div class="member-header">
      <div class="member-avatar" style="background: linear-gradient(135deg, #10b981, #0d9488);">DVA</div>
      <div>
        <div class="member-name">2. Đỗ Thị Vân Anh (Kỹ sư Dữ liệu & EDA)</div>
        <div class="member-role">Phụ trách: Thu thập tập dữ liệu biển báo Việt Nam 82 lớp, Xây dựng bộ lọc Quality Gate, Phân tích khám phá dữ liệu (EDA) & Snapshot bất biến</div>
      </div>
    </div>

    <!-- CÂU 4 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q4</span>
        <span>Thầy/Cô hỏi: Bộ dữ liệu 82 lớp của nhóm có đặc điểm gì? Quy mô ra sao và nhóm chia tập Train/Val/Test theo tỷ lệ nào?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, bộ dữ liệu của nhóm được chuẩn hóa theo danh mục 82 lớp biển báo giao thông Việt Nam theo Quy chuẩn kỹ thuật quốc gia QCVN 41:2019/BGTVT:</p>
        <ul>
          <li><strong>Tổng quy mô:</strong> Gồm <strong>10.139 ảnh</strong> với <strong>19.722 nhãn hộp bao (Bounding Boxes)</strong> được định dạng theo chuẩn YOLO (Class_id, x_center, y_center, width, height).</li>
          <li><strong>Phân chia tỷ lệ (Split):</strong> Nhóm chia theo tỷ lệ chuẩn <strong>80 : 10 : 10</strong>:
            <br>• Tập Huấn luyện (Train): <strong>8.131 ảnh</strong> (15.733 boxes)
            <br>• Tập Kiểm định (Val): <strong>1.001 ảnh</strong> (2.036 boxes)
            <br>• Tập Kiểm thử (Test): <strong>1.007 ảnh</strong> (1.953 boxes)
          </li>
          <li>Dữ liệu bao gồm 4 nhóm chính: Biển báo cấm (đỏ), Biển hiệu lệnh (xanh dương), Biển cảnh báo nguy hiểm (vàng hình tam giác) và Biển chỉ dẫn (chữ nhật/vuông).</li>
        </ul>
      </div>
    </div>

    <!-- CÂU 5 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q5</span>
        <span>Thầy/Cô hỏi: Quality Gate trong hệ thống kiểm tra những lỗi gì? Tại sao phải kiểm tra Data Leakage bằng SHA-256?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, <strong>Quality Gate</strong> là cổng kiểm soát chất lượng tự động ngăn chặn 5 lỗi kỹ thuật nghiêm ngặt:</p>
        <ol style="margin-left: 20px;">
          <li><code>CORRUPT_IMAGE</code>: Ảnh bị lỗi byte hoặc không thể giải mã bằng OpenCV.</li>
          <li><code>MALFORMED_YOLO_LINE</code>: Dòng nhãn thiếu/thừa cột giá trị.</li>
          <li><code>CLASS_ID_OUT_OF_RANGE</code>: Class ID nằm ngoài khoảng 0 – 81.</li>
          <li><code>INVALID_COORDINATES</code>: Tọa độ bbox nằm ngoài khoảng hợp lệ [0, 1].</li>
          <li><strong>DATA_LEAKAGE (Rò rỉ dữ liệu):</strong> Nhóm tính mã băm SHA-256 của từng bức ảnh. Nếu có bức ảnh trong tập Train lại vô tình xuất hiện trong tập Val hoặc Test (do trùng lặp file), hệ thống sẽ báo lỗi chặn ngay lập tức. Điều này đảm bảo mô hình không bị hiện tượng "học vẹt", giúp số liệu đánh giá mAP phản ánh đúng 100% năng lực nhận dạng thực tế trên dữ liệu chưa từng thấy.</li>
        </ol>
      </div>
    </div>

    <!-- CÂU 6 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q6</span>
        <span>Thầy/Cô hỏi: Thế nào là "Dataset Snapshot bất biến"? Tại sao không trỏ trực tiếp vào thư mục staging để huấn luyện?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, nếu trỏ trực tiếp vào thư mục staging, dữ liệu có thể bị ai đó thêm, sửa, xóa nhãn trong lúc đang huấn luyện, dẫn đến kết quả không thể tái lập (Loss of Reproducibility). Vì vậy, sau khi Quality Gate kiểm định thành công, hệ thống sẽ sao chép toàn bộ dữ liệu vào một thư mục bất biến: <code>artifacts/snapshots/&lt;snapshot_id&gt;/</code>, đi kèm file cấu hình <code>data.yaml</code> và bản băm SHA-256 của toàn bộ danh sách file. Bất kỳ lần huấn luyện nào cũng truy vết được chính xác tập dữ liệu gốc đã dùng.</p>
      </div>
    </div>
  </div>

  <!-- ========================================== -->
  <!-- PHẦN 3: ĐỖ HỮU NGHỊ (KỸ SƯ AI/ML) -->
  <!-- ========================================== -->
  <div class="member-section">
    <div class="member-header">
      <div class="member-avatar" style="background: linear-gradient(135deg, #f59e0b, #d97706);">DHN</div>
      <div>
        <div class="member-name">3. Đỗ Hữu Nghị (Kỹ sư AI/ML & Tối ưu hóa mô hình)</div>
        <div class="member-role">Phụ trách: Cấu hình huấn luyện YOLO11, Tối ưu hóa ONNX Runtime CPU, Kiểm định sai số số học & Benchmark hiệu năng</div>
      </div>
    </div>

    <!-- CÂU 7 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q7</span>
        <span>Thầy/Cô hỏi: Tại sao mô hình lại chạy được mượt mà trên CPU với tốc độ 40-50ms mà không cần GPU rời? Nhóm đã áp dụng những kỹ thuật tối ưu nào?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, để đạt được tốc độ suy luận dưới 50ms trên CPU thông thường, nhóm đã phối hợp 4 kỹ thuật tối ưu hóa:</p>
        <ol style="margin-left: 20px;">
          <li><strong>Chuyển đổi đồ thị sang ONNX Runtime:</strong> Bỏ qua overhead của framework PyTorch, ONNX Runtime biên dịch đồ thị tính toán tối ưu riêng cho tập chỉ thị phần cứng CPU (AVX2, AVX-512 hoặc Apple Silicon NEON).</li>
          <li><strong>Đồ thị tĩnh (Static Shape [1, 3, 640, 640]):</strong> Kích thước ảnh cố định giúp runtime cấp phát bộ nhớ một lần duy nhất, tránh chi phí cấp phát lại bộ nhớ liên tục trong mỗi frame.</li>
          <li><strong>Tối ưu hóa đồ thị (Graph Optimization ORT_ENABLE_ALL):</strong> Tự động gộp các lớp liên tiếp (ví dụ: gộp Convolution + Batch Normalization + Activation Function SiLU thành 1 kernel tính toán duy nhất).</li>
          <li><strong>Cấu hình đa luồng nội bộ (Intra-op Threads):</strong> Khai thác triệt để các nhân xử lý song song của CPU.</li>
        </ol>
      </div>
    </div>

    <!-- CÂU 8 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q8</span>
        <span>Thầy/Cô hỏi: Kiểm tra sai số số học Parity Check giữa PyTorch và ONNX có ý nghĩa gì? Ngưỡng 1e-3 được tính như thế nào?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, khi chuyển đổi một mạng nơ-ron từ PyTorch sang định dạng ONNX, có nguy cơ các toán tử số học bị sai lệch do khác biệt về cách cài đặt hàm toán học hoặc làm tròn số thực. Nhóm đã xây dựng bài kiểm tra tự động:</p>
        <p>Cùng đưa 1 tensor ảnh đầu vào ngẫu nhiên qua cả hai mô hình (PyTorch <code>.pt</code> và ONNX <code>.onnx</code>), sau đó đo độ lệch tuyệt đối cực đại:</p>
        <p class="code-inline">max_abs_diff = np.max(np.abs(output_pytorch - output_onnx))</p>
        <p>Nếu <code>max_abs_diff &le; 1e-3</code> (dưới một phần nghìn), chúng em khẳng định mô hình ONNX phản ánh chính xác 100% logic của mô hình PyTorch gốc, không bị biến dạng kết quả nhận diện.</p>
      </div>
    </div>

    <!-- CÂU 9 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q9</span>
        <span>Thầy/Cô hỏi: Hãy giải thích các thành phần trong hàm mất mát (Loss function) của YOLO11 khi nhận dạng biển báo?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, hàm mất mát của YOLO11 gồm 3 thành phần chính:</p>
        <ul>
          <li><strong>CIoU Loss (Box Loss):</strong> Tối ưu hóa tọa độ hộp bao dựa trên tỷ lệ diện tích giao nhau, khoảng cách tâm và tỷ lệ co giãn hình học. Biển báo giao thông có hình tròn, hình tam giác hoặc hình vuông rõ rệt, CIoU giúp khung bao ôm sát biển báo nhất.</li>
          <li><strong>BCE Loss (Classification Loss):</strong> Sử dụng hàm mất mát Binary Cross-Entropy để phân loại độc lập điểm số tin cậy cho 82 lớp biển báo.</li>
          <li><strong>DFL Loss (Distribution Focal Loss):</strong> Hồi quy phân phối xác suất cho 4 tọa độ đường viền của bounding box, đặc biệt hiệu quả khi biển báo bị che khuất một phần bởi cây cối hoặc xe cộ.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ========================================== -->
  <!-- PHẦN 4: QUẢN VĂN ĐIỆP (KỸ SƯ FULLSTACK/QA) -->
  <!-- ========================================== -->
  <div class="member-section">
    <div class="member-header">
      <div class="member-avatar" style="background: linear-gradient(135deg, #6366f1, #4f46e5);">QVD</div>
      <div>
        <div class="member-name">4. Quản Văn Điệp (Kỹ sư Fullstack / QA & Giao diện)</div>
        <div class="member-role">Phụ trách: Phát triển ứng dụng Web Streamlit, Xử lý suy luận video đa phương tiện, Bộ kiểm thử tự động Pytest & Hướng dẫn sử dụng</div>
      </div>
    </div>

    <!-- CÂU 10 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q10</span>
        <span>Thầy/Cô hỏi: Framework Streamlit có đặc điểm là chạy lại toàn bộ mã nguồn mỗi khi người dùng tương tác (Rerun). Nhóm đã xử lý bài toán này như thế nào để giao diện không bị giật lag và không bị mất trạng thái?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, để khắc phục đặc tính rerun của Streamlit, em đã áp dụng 3 giải pháp kiến trúc:</p>
        <ol style="margin-left: 20px;">
          <li><strong>Quản lý trạng thái bằng <code>st.session_state</code>:</strong> Mọi kết quả phân tích (ảnh đã vẽ bounding box, bảng CSV kết quả, mã phiên hiện tại) đều được lưu vào <code>session_state</code>. Khi người dùng thao tác ở bảng điều khiển bên phải, ảnh bên trái không cần tính toán lại mà hiển thị tức thì từ bộ nhớ đệm.</li>
          <li><strong>Singleton Pattern cho AppServices:</strong> Các đối tượng nặng như Model ONNX, Database Repository, Config chỉ được khởi tạo một lần duy nhất.</li>
          <li><strong>Tách trang (Modular Pages):</strong> Tách biệt mã nguồn thành các module độc lập trong <code>trafficvision/ui/pages/</code> (analysis, history, training, settings...), giúp mã nguồn gọn gàng và tải trang mượt mà.</li>
        </ol>
      </div>
    </div>

    <!-- CÂU 11 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q11</span>
        <span>Thầy/Cô hỏi: Luồng xử lý video hoạt động như thế nào? Tại sao người dùng có thể xem được thanh tiến trình (Progress bar) theo từng khung hình?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, đối với tệp video (MP4, AVI, MOV):</p>
        <ol style="margin-left: 20px;">
          <li>Hệ thống sử dụng OpenCV <code>cv2.VideoCapture</code> để đọc tuần tự từng frame hình ảnh.</li>
          <li>Hàm xử lý <code>analyze_video_upload</code> chấp nhận một hàm callback <code>on_progress</code>. Mỗi khi xử lý xong một khung hình, callback này được gọi kèm thông số <code>VideoProgress(current_frame, total_frames, fraction)</code>.</li>
          <li>Streamlit nhận callback và cập nhật thanh <code>st.progress()</code> theo thời gian thực trên màn hình, giúp người dùng biết chính xác video đang được xử lý đến đâu và dự kiến thời gian hoàn thành.</li>
          <li>Sau khi hoàn thành, video đã gắn nhãn bounding box được đóng gói bằng <code>cv2.VideoWriter</code> và hiển thị trực tiếp trên trình phát HTML5 của trang web.</li>
        </ol>
      </div>
    </div>

    <!-- CÂU 12 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q12</span>
        <span>Thầy/Cô hỏi: Bộ kiểm thử tự động của nhóm có bao nhiêu test case? Nhóm kiểm thử những khía cạnh nào của hệ thống?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, hệ thống hiện có hơn <strong>170 test cases tự động</strong> được viết bằng thư viện <strong>Pytest</strong> với tỷ lệ vượt qua 100%:</p>
        <ul>
          <li><strong>Unit Tests:</strong> Kiểm tra thuật toán Letterbox, hàm chuyển đổi tọa độ Bounding Box, đọc/ghi tệp nhãn YOLO, bộ kiểm định Quality Gate 5 tiêu chí.</li>
          <li><strong>Integration Tests:</strong> Kiểm tra quy trình luồng phân tích ảnh/video đầu-cuối (End-to-End), lưu lịch sử vào SQLite, xuất CSV dữ liệu.</li>
          <li><strong>MLOps & Registry Tests:</strong> Kiểm tra tính toàn vẹn mã băm SHA-256 của Manifest, kiểm tra cơ chế sao lưu tự động và khả năng Rollback mô hình khi gặp lỗi.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ========================================== -->
  <!-- PHẦN 5: CÂU HỎI CHUNG CHO CẢ NHÓM -->
  <!-- ========================================== -->
  <div class="member-section">
    <div class="member-header">
      <div class="member-avatar" style="background: linear-gradient(135deg, #ef4444, #dc2626);">ALL</div>
      <div>
        <div class="member-name">5. Câu hỏi Chiến lược & Tính Khoa học Chung cho Cả Nhóm</div>
        <div class="member-role">Dành cho bất kỳ thành viên nào được Hội đồng chỉ định trả lời</div>
      </div>
    </div>

    <!-- CÂU 13 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q13</span>
        <span>Thầy/Cô hỏi: Trong báo cáo dự án, nhóm ghi nhận chỉ số mAP và FPS của mô hình 82 lớp là "Chưa có số liệu thực nghiệm". Tại sao nhóm không đưa ra một con số minh họa 85% hay 90% cho đẹp báo cáo?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời (Rất quan trọng - Điểm tự hào về đạo đức khoa học):</strong>
        <p>Thưa Quý Thầy Cô trong Hội đồng, đây là quyết định thể hiện <strong>Tính trung thực khoa học (Academic Integrity)</strong> cao nhất của nhóm chúng em:</p>
        <p>Tại thời điểm chốt báo cáo, hệ thống phần mềm, toàn bộ kiến trúc MLOps, Quality Gate và bộ kiểm thử 170 test case đã hoàn thành 100%. Tuy nhiên, do một phiên huấn luyện đầy đủ 50 epochs trên tập dữ liệu lớn 10.000 ảnh bằng vi xử lý CPU cần thời gian tính toán rất lớn và chưa kết thúc hoàn chỉnh, nhóm kiên quyết <strong>không bịa đặt số liệu hoặc lấy số liệu giả định</strong>.</p>
        <p>Hệ thống hiện tại đang chạy ổn định với mô hình nền tảng Baseline đã được kiểm định, và đường ống (Pipeline) MLOps sẵn sàng tạo ra Candidate 82 lớp chuẩn xác ngay khi quá trình huấn luyện hoàn tất. Thầy Cô có thể kiểm chứng toàn bộ mã nguồn kiểm định độc lập trong repository.</p>
        <div class="tip-box">
          ⭐ <em>Hội đồng luôn đánh giá cực kỳ cao những nhóm sinh viên dũng cảm thừa nhận đúng trạng thái thực tế của dự án thay vì ngụy tạo các con số mAP đẹp mắt!</em>
        </div>
      </div>
    </div>

    <!-- CÂU 14 -->
    <div class="qa-card">
      <div class="question">
        <span class="q-icon">Q14</span>
        <span>Thầy/Cô hỏi: Nếu đưa sản phẩm này vào ứng dụng thương mại thực tế, nhóm dự định phát triển tiếp theo những hướng nào?</span>
      </div>
      <div class="answer">
        <strong>Sinh viên trả lời:</strong>
        <p>Thưa Thầy Cô, nhóm đã định hướng 3 bước mở rộng thực tế tiếp theo:</p>
        <ol style="margin-left: 20px;">
          <li><strong>Kết nối Camera hành trình trực tiếp (Dashcam RTSP stream):</strong> Lấy luồng video thời gian thực từ camera gắn trên gương xe hơi để đưa ra cảnh báo tức thì cho tài xế khi đang lái xe.</li>
          <li><strong>Cảnh báo giọng nói tiếng Việt (Voice Alert):</strong> Ví dụ khi phát hiện biển "Giới hạn tốc độ 40km/h" mà xe đang chạy quá tốc độ, hệ thống sẽ phát âm thanh nhắc nhở qua loa xe.</li>
          <li><strong>Bản đồ số hóa biển báo giao thông:</strong> Kết hợp tọa độ định vị GPS để tự động vẽ bản đồ các biển báo trên từng cung đường, hỗ trợ Sở Giao thông Vận tải kiểm tra và bảo dưỡng biển báo bị hư hỏng.</li>
        </ol>
      </div>
    </div>
  </div>

  <footer style="margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border); font-size: 13px; color: #64748b; text-align: center;">
    Cẩm nang bảo vệ đồ án TrafficVision • Chúc nhóm hoàn thành xuất sắc buổi bảo vệ!
  </footer>
</div>

</body>
</html>
"""


def export_html_to_pdf(html_path: Path, pdf_path: Path, landscape: bool = False) -> bool:
    """Export an HTML file to PDF using headless Chrome."""
    if not Path(CHROME_BIN).is_file():
        print(f"Error: Chrome binary not found at {CHROME_BIN}")
        return False

    cmd = [
        CHROME_BIN,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={pdf_path}",
        "--no-pdf-header-footer",
    ]
    cmd.append(f"file://{html_path.resolve()}")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if pdf_path.is_file() and pdf_path.stat().st_size > 1000:
            print(f"-> Exported PDF: {pdf_path} ({pdf_path.stat().st_size:,} bytes)")
            return True
        else:
            print(f"Error exporting PDF {pdf_path}: {res.stderr}")
            return False
    except Exception as exc:
        print(f"Exception during PDF export of {html_path}: {exc}")
        return False


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Update slide HTML with print styles & generate PDF
    slide_html_path = DOCS_DIR / "slide_bao_ve_du_an.html"
    slide_pdf_path = DOCS_DIR / "slide_bao_ve_du_an.pdf"
    slide_html = build_slide_html()
    slide_html_path.write_text(slide_html, encoding="utf-8")
    print(f"Updated {slide_html_path}")
    export_html_to_pdf(slide_html_path, slide_pdf_path)

    # 2. Build training deep-dive HTML & PDF
    training_html_path = DOCS_DIR / "tai_lieu_huan_luyen_chuyen_sau.html"
    training_pdf_path = DOCS_DIR / "tai_lieu_huan_luyen_chuyen_sau.pdf"
    training_html = build_training_deep_dive_html()
    training_html_path.write_text(training_html, encoding="utf-8")
    print(f"Generated {training_html_path}")
    export_html_to_pdf(training_html_path, training_pdf_path)

    # 3. Build defense Q&A HTML & PDF
    qa_html_path = DOCS_DIR / "cau_hoi_bao_ve_du_an.html"
    qa_pdf_path = DOCS_DIR / "cau_hoi_bao_ve_du_an.pdf"
    qa_html = build_defense_qa_html()
    qa_html_path.write_text(qa_html, encoding="utf-8")
    print(f"Generated {qa_html_path}")
    export_html_to_pdf(qa_html_path, qa_pdf_path)

    # 4. Also export user guide to PDF for completeness
    guide_html_path = DOCS_DIR / "huong_dan_su_dung.html"
    guide_pdf_path = DOCS_DIR / "huong_dan_su_dung.pdf"
    if guide_html_path.is_file():
        export_html_to_pdf(guide_html_path, guide_pdf_path)

    print("\n--- All HTML and PDF deliverables built successfully! ---")


if __name__ == "__main__":
    main()
