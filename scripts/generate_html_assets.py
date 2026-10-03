#!/usr/bin/env python3
"""Script generating huong_dan_su_dung.html and slide_bao_ve_du_an.html for TrafficVision."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"


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


def build_user_guide_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tài liệu Hướng dẫn Sử dụng - TrafficVision AI</title>
  <style>
    :root {{
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --primary-light: #eff6ff;
      --secondary: #0f172a;
      --accent: #14b8a6;
      --text: #1e293b;
      --text-muted: #64748b;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --radius: 12px;
      --shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.65;
      font-size: 15px;
    }}

    /* Layout */
    .app-container {{
      display: flex;
      min-height: 100vh;
    }}

    /* Sidebar Navigation */
    .sidebar {{
      width: 280px;
      background: #0b1730;
      color: #cbd5e1;
      padding: 28px 18px;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      flex-shrink: 0;
      border-right: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .sidebar-brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 24px;
      padding-bottom: 18px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .brand-icon {{
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: linear-gradient(135deg, #14b8a6, #2563eb);
      display: grid;
      place-items: center;
      color: #fff;
      font-weight: 800;
      font-size: 18px;
    }}
    .brand-title {{
      font-size: 17px;
      font-weight: 700;
      color: #fff;
      letter-spacing: -0.02em;
    }}
    .brand-badge {{
      font-size: 10px;
      padding: 2px 7px;
      border-radius: 99px;
      background: rgba(20, 184, 166, 0.2);
      color: #2dd4bf;
      font-weight: 600;
    }}
    .nav-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: #64748b;
      margin: 18px 8px 8px;
      font-weight: 700;
    }}
    .nav-list {{
      list-style: none;
    }}
    .nav-link {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 9px 12px;
      border-radius: 8px;
      color: #94a3b8;
      text-decoration: none;
      font-size: 13px;
      font-weight: 500;
      transition: all 0.15s ease;
      margin-bottom: 3px;
    }}
    .nav-link:hover {{
      background: rgba(255, 255, 255, 0.08);
      color: #ffffff;
    }}
    .nav-link.active {{
      background: var(--primary);
      color: #ffffff;
    }}

    /* Main Content */
    .content-area {{
      flex: 1;
      max-width: 1080px;
      padding: 40px 48px;
      margin: 0 auto;
    }}

    /* Top banner */
    .header-banner {{
      background: linear-gradient(135deg, #1e3a8a, #0b1730);
      color: white;
      padding: 36px 40px;
      border-radius: 18px;
      margin-bottom: 36px;
      box-shadow: 0 10px 30px rgba(11, 23, 48, 0.15);
      position: relative;
      overflow: hidden;
    }}
    .header-banner::after {{
      content: "";
      position: absolute;
      right: -20px;
      bottom: -40px;
      width: 240px;
      height: 240px;
      background: radial-gradient(circle, rgba(20, 184, 166, 0.3) 0%, transparent 70%);
      border-radius: 50%;
    }}
    .header-tag {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(8px);
      padding: 4px 12px;
      border-radius: 99px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 12px;
    }}
    .header-banner h1 {{
      font-size: 30px;
      font-weight: 800;
      line-height: 1.25;
      margin-bottom: 10px;
    }}
    .header-banner p {{
      color: #cbd5e1;
      font-size: 15px;
      max-width: 720px;
    }}

    /* Section & Cards */
    section {{
      margin-bottom: 48px;
      scroll-margin-top: 30px;
    }}
    .section-title {{
      font-size: 22px;
      font-weight: 800;
      color: #0f172a;
      margin-bottom: 18px;
      display: flex;
      align-items: center;
      gap: 10px;
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 10px;
    }}
    .section-number {{
      display: inline-grid;
      place-items: center;
      width: 30px;
      height: 30px;
      background: var(--primary);
      color: white;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 800;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      margin-bottom: 20px;
      box-shadow: var(--shadow);
    }}

    /* Alerts / Callouts */
    .callout {{
      padding: 16px 20px;
      border-radius: 10px;
      border-left: 4px solid;
      margin: 18px 0;
      display: flex;
      gap: 14px;
      font-size: 14px;
    }}
    .callout-info {{
      background: #eff6ff;
      border-color: #3b82f6;
      color: #1e40af;
    }}
    .callout-success {{
      background: #f0fdf4;
      border-color: #22c55e;
      color: #15803d;
    }}
    .callout-warning {{
      background: #fffbeb;
      border-color: #f59e0b;
      color: #b45309;
    }}
    .callout-icon {{
      font-size: 18px;
      flex-shrink: 0;
    }}

    /* Code Block */
    pre {{
      background: #0f172a;
      color: #f8fafc;
      padding: 16px 20px;
      border-radius: 10px;
      overflow-x: auto;
      font-family: var(--font-mono);
      font-size: 13px;
      margin: 14px 0;
      border: 1px solid #1e293b;
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

    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      font-size: 14px;
    }}
    th, td {{
      padding: 12px 14px;
      border: 1px solid var(--border);
      text-align: left;
    }}
    th {{
      background: #f1f5f9;
      font-weight: 700;
      color: #334155;
    }}
    tr:nth-child(even) td {{
      background: #f8fafc;
    }}

    /* Interactive Mockup Frames for Demo */
    .mock-window {{
      border: 1px solid #cbd5e1;
      border-radius: 16px;
      background: #ffffff;
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
      overflow: hidden;
      margin: 24px 0;
    }}
    .mock-header {{
      background: #f1f5f9;
      padding: 12px 16px;
      display: flex;
      align-items: center;
      gap: 8px;
      border-bottom: 1px solid #e2e8f0;
    }}
    .mock-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }}
    .dot-red {{ background: #ef4444; }}
    .dot-yellow {{ background: #f59e0b; }}
    .dot-green {{ background: #10b981; }}
    .mock-url {{
      margin-left: 12px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 4px 12px;
      font-size: 12px;
      color: #64748b;
      font-family: var(--font-mono);
      width: 60%;
    }}
    .mock-body {{
      padding: 24px;
      background: #f8fafc;
    }}

    /* Demo Image Grid */
    .demo-showcase {{
      display: grid;
      grid-template-columns: 1.5fr 1fr;
      gap: 20px;
      align-items: start;
    }}
    .demo-img-box {{
      border: 2px solid #cbd5e1;
      border-radius: 12px;
      overflow: hidden;
      background: #000;
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
    }}
    .demo-img-box img {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .demo-caption {{
      padding: 8px 12px;
      font-size: 12px;
      background: #1e293b;
      color: #94a3b8;
      text-align: center;
    }}
    .stat-badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 11px;
    }}
    .badge-primary {{ background: #dbeafe; color: #1e40af; }}
    .badge-success {{ background: #dcfce7; color: #166534; }}
    .badge-warning {{ background: #fef3c7; color: #92400e; }}

    /* Stepper UI */
    .stepper {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin: 20px 0;
    }}
    .step-item {{
      background: #ffffff;
      border: 1px solid var(--border);
      padding: 14px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      font-weight: 600;
      color: #475569;
    }}
    .step-item.active {{
      border-color: var(--primary);
      background: var(--primary-light);
      color: var(--primary-dark);
      box-shadow: 0 4px 10px rgba(37, 99, 235, 0.1);
    }}
    .step-circle {{
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: #cbd5e1;
      color: #fff;
      display: grid;
      place-items: center;
      font-size: 11px;
      font-weight: 800;
      flex-shrink: 0;
    }}
    .step-item.active .step-circle {{
      background: var(--primary);
    }}

    /* Buttons */
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 13px;
      text-decoration: none;
      cursor: pointer;
      border: none;
      transition: all 0.15s ease;
    }}
    .btn-primary {{
      background: var(--primary);
      color: #ffffff;
    }}
    .btn-primary:hover {{
      background: var(--primary-dark);
    }}
    .btn-secondary {{
      background: #e2e8f0;
      color: #334155;
    }}

    @media (max-width: 900px) {{
      .app-container {{ flex-direction: column; }}
      .sidebar {{ width: 100%; height: auto; position: static; }}
      .demo-showcase {{ grid-template-columns: 1fr; }}
      .stepper {{ grid-template-columns: 1fr 1fr; }}
      .content-area {{ padding: 20px; }}
    }}

    @media print {{
      .sidebar {{ display: none; }}
      .content-area {{ max-width: 100%; padding: 0; }}
      .header-banner {{ background: #0f172a; color: #000; }}
    }}
  </style>
</head>
<body>

<div class="app-container">
  <!-- SIDEBAR NAVIGATION -->
  <aside class="sidebar">
    <div class="sidebar-brand">
      <div class="brand-icon">🚦</div>
      <div>
        <div class="brand-title">TrafficVision</div>
        <div class="brand-badge">Bản 2.0 • QCVN 41</div>
      </div>
    </div>

    <div class="nav-label">Mục lục tài liệu</div>
    <ul class="nav-list">
      <li><a class="nav-link" href="#sec-overview">1. Giới thiệu tổng quan</a></li>
      <li><a class="nav-link" href="#sec-requirements">2. Yêu cầu hệ thống</a></li>
      <li><a class="nav-link" href="#sec-quickstart">3. Cài đặt & Khởi động nhanh</a></li>
      <li><a class="nav-link" href="#sec-analysis">4. Phân tích Ảnh & Video</a></li>
      <li><a class="nav-link" href="#sec-history">5. Tra cứu Lịch sử</a></li>
      <li><a class="nav-link" href="#sec-statistics">6. Thống kê & Phân tích</a></li>
      <li><a class="nav-link" href="#sec-training">7. Huấn luyện AI (4 bước)</a></li>
      <li><a class="nav-link" href="#sec-model-info">8. Quản lý Model & Rollback</a></li>
      <li><a class="nav-link" href="#sec-settings">9. Thiết lập ngưỡng Conf/IoU</a></li>
      <li><a class="nav-link" href="#sec-cli">10. Công cụ Dòng lệnh (CLI)</a></li>
      <li><a class="nav-link" href="#sec-troubleshoot">11. Xử lý sự cố thường gặp</a></li>
    </ul>

    <div class="nav-label" style="margin-top: 30px;">Tài liệu liên quan</div>
    <ul class="nav-list">
      <li><a class="nav-link" href="slide_bao_ve_du_an.html" target="_blank">📊 Slide Thuyết Trình Bảo Vệ</a></li>
      <li><a class="nav-link" href="HUONG_DAN_SU_DUNG.md" target="_blank">📄 Bản Markdown (MD)</a></li>
    </ul>
  </aside>

  <!-- MAIN CONTENT AREA -->
  <main class="content-area">
    
    <!-- HEADER HERO BANNER -->
    <header class="header-banner">
      <div class="header-tag">✨ Sổ tay hướng dẫn người dùng chính thức</div>
      <h1>TrafficVision – Hướng dẫn Sử dụng</h1>
      <p>Hệ thống thị giác máy tính nhận dạng biển báo giao thông Việt Nam bằng AI, tối ưu hóa suy luận ONNX trên CPU và tích hợp phòng thí nghiệm MLOps khép kín.</p>
    </header>

    <!-- SECTION 1: OVERVIEW -->
    <section id="sec-overview">
      <h2 class="section-title"><span class="section-number">1</span> Giới thiệu tổng quan hệ thống</h2>
      <div class="card">
        <p><strong>TrafficVision</strong> là ứng dụng AI chuyên dụng giúp tự động phát hiện, định vị vị trí khung bao (Bounding Box) và phân loại các loại biển báo giao thông trên đường phố Việt Nam từ hình ảnh hoặc video ghi hình.</p>
        
        <div class="callout callout-info">
          <div class="callout-icon">💡</div>
          <div>
            <strong>Đặc tính nổi bật:</strong> Hệ thống được thiết kế theo kiến trúc chuẩn mực MLOps:
            <ul>
              <li><strong>Suy luận siêu nhẹ trên CPU:</strong> Chuyển đổi mô hình YOLO11 sang ONNX Runtime, chạy mượt mà trên laptop thông thường mà không cần GPU rời.</li>
              <li><strong>82 lớp biển báo chuẩn QCVN 41:2019/BGTVT:</strong> Nhận diện đầy đủ biển báo cấm, biển hiệu lệnh, biển cảnh báo nguy hiểm và biển chỉ dẫn bằng tiếng Việt.</li>
              <li><strong>Phòng thí nghiệm MLOps 4 bước:</strong> Quy trình kiểm định Quality Gate nghiêm ngặt, huấn luyện nền ngầm (Background Worker) và thăng cấp an toàn với tính năng Rollback 1-click.</li>
            </ul>
          </div>
        </div>

        <div style="margin-top: 16px; text-align: center;">
          <svg viewBox="0 0 850 140" style="width: 100%; max-width: 800px; height: auto;">
            <defs>
              <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#2563eb" />
                <stop offset="100%" stop-color="#14b8a6" />
              </linearGradient>
            </defs>
            <rect x="10" y="30" width="160" height="70" rx="10" fill="#0f172a" />
            <text x="90" y="65" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">Ảnh / Video đầu vào</text>
            <text x="90" y="82" fill="#94a3b8" font-size="10" text-anchor="middle">JPG, PNG, MP4</text>

            <path d="M 175 65 L 215 65" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)" />

            <rect x="220" y="30" width="180" height="70" rx="10" fill="#ffffff" stroke="#cbd5e1" stroke-width="2" />
            <text x="310" y="62" fill="#0f172a" font-size="12" font-weight="bold" text-anchor="middle">Tiền xử lý & Letterbox</text>
            <text x="310" y="80" fill="#64748b" font-size="10" text-anchor="middle">Resize 640x640 chuẩn hóa</text>

            <path d="M 405 65 L 445 65" stroke="#64748b" stroke-width="2" />

            <rect x="450" y="25" width="190" height="80" rx="12" fill="url(#grad1)" />
            <text x="545" y="62" fill="#ffffff" font-size="13" font-weight="bold" text-anchor="middle">ONNX Runtime CPU</text>
            <text x="545" y="80" fill="#e0f2fe" font-size="10" text-anchor="middle">YOLO11n • 82 lớp biển báo</text>

            <path d="M 645 65 L 685 65" stroke="#64748b" stroke-width="2" />

            <rect x="690" y="30" width="150" height="70" rx="10" fill="#0f172a" />
            <text x="765" y="62" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">Kết quả & Báo cáo</text>
            <text x="765" y="80" fill="#2dd4bf" font-size="10" text-anchor="middle">Bounding Box + CSV</text>
          </svg>
        </div>
      </div>
    </section>

    <!-- SECTION 2: REQUIREMENTS -->
    <section id="sec-requirements">
      <h2 class="section-title"><span class="section-number">2</span> Yêu cầu hệ thống & Môi trường</h2>
      <div class="card">
        <table>
          <thead>
            <tr>
              <th>Thành phần</th>
              <th>Yêu cầu tối thiểu</th>
              <th>Khuyến nghị</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Hệ điều hành</strong></td>
              <td>macOS 12+ hoặc Windows 10/11 (64-bit)</td>
              <td>macOS (Apple Silicon M1/M2/M3) hoặc Windows 11</td>
            </tr>
            <tr>
              <td><strong>Môi trường Python</strong></td>
              <td>Python 3.11</td>
              <td>Python 3.11 hoặc 3.12</td>
            </tr>
            <tr>
              <td><strong>Bộ nhớ RAM</strong></td>
              <td>4 GB RAM</td>
              <td>8 GB – 16 GB RAM</td>
            </tr>
            <tr>
              <td><strong>Ổ đĩa trống</strong></td>
              <td>2 GB dung lượng trống</td>
              <td>10 GB trở lên (phục vụ lưu dataset & runs)</td>
            </tr>
            <tr>
              <td><strong>Tăng tốc phần cứng</strong></td>
              <td>CPU đa nhân (AVX2 hỗ trợ)</td>
              <td>GPU NVIDIA (CUDA) nếu cần huấn luyện dữ liệu lớn nhanh</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- SECTION 3: QUICKSTART -->
    <section id="sec-quickstart">
      <h2 class="section-title"><span class="section-number">3</span> Cài đặt & Khởi động nhanh (Quick Start)</h2>
      <div class="card">
        <h3>1. Khởi tạo môi trường ảo</h3>
        <p>Mở ứng dụng Terminal hoặc PowerShell tại thư mục dự án và thực hiện:</p>

        <pre><code># macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

# Windows PowerShell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"</code></pre>

        <h3 style="margin-top: 20px;">2. Tải và Khởi tạo mô hình Baseline</h3>
        <p>Lần đầu tiên sử dụng, hãy chạy tập lệnh sau để nạp mô hình nền ban đầu:</p>
        <pre><code>python scripts/bootstrap_baseline.py</code></pre>

        <h3 style="margin-top: 20px;">3. Khởi chạy ứng dụng Web (1-Click)</h3>
        <div style="display: flex; gap: 12px; margin: 12px 0;">
          <div style="flex: 1; padding: 14px; background: #f1f5f9; border-radius: 8px;">
            <strong>🍎 Dành cho macOS:</strong>
            <p style="font-size: 13px; color: #64748b; margin-top: 4px;">Nhấp đúp chuột vào file <code>run.command</code> hoặc chạy lệnh <code>./run_app.sh</code></p>
          </div>
          <div style="flex: 1; padding: 14px; background: #f1f5f9; border-radius: 8px;">
            <strong>🪟 Dành cho Windows:</strong>
            <p style="font-size: 13px; color: #64748b; margin-top: 4px;">Nhấp đúp chuột vào file <code>run_app.bat</code> hoặc gõ <code>run_app.bat</code> trên CMD</p>
          </div>
        </div>
        <p>Trình duyệt sẽ tự động mở trang làm việc tại địa chỉ: <a href="http://localhost:8501" target="_blank"><code>http://localhost:8501</code></a></p>
      </div>
    </section>

    <!-- SECTION 4: ANALYSIS TAB WITH DEMO IMAGES -->
    <section id="sec-analysis">
      <h2 class="section-title"><span class="section-number">4</span> Không gian "Phân tích" (Nhận dạng Ảnh & Video)</h2>
      
      <div class="card">
        <p>Đây là màn hình hoạt động chính của ứng dụng. Người dùng có thể kéo thả tệp ảnh hoặc video từ máy tính vào để hệ thống nhận diện tức thì.</p>

        <!-- Mockup Window showing Image Analysis with Real Demo Image -->
        <div class="mock-window">
          <div class="mock-header">
            <span class="mock-dot dot-red"></span>
            <span class="mock-dot dot-yellow"></span>
            <span class="mock-dot dot-green"></span>
            <div class="mock-url">http://localhost:8501/?tab=analysis</div>
          </div>
          <div class="mock-body">
            <div class="demo-showcase">
              <!-- Left: Annotated Image Display -->
              <div>
                <h4 style="margin-bottom: 8px; color: #0f172a;">Kết quả phân tích trực quan</h4>
                <div class="demo-img-box">
                  <img src="{img2_b64}" alt="Ảnh demo nhận diện biển báo giao thông" />
                  <div class="demo-caption">Ảnh nhận diện thực tế: Bounding Box màu neon định vị biển báo kèm độ tin cậy</div>
                </div>
              </div>

              <!-- Right: Detection Summary Card -->
              <div>
                <div style="background: white; border: 1px solid var(--border); border-radius: 12px; padding: 16px;">
                  <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px; margin-bottom: 14px;">
                    <strong style="font-size: 13px; color: #0f172a;">Tóm tắt nhận diện</strong>
                    <span class="stat-badge badge-success">HOÀN TẤT</span>
                  </div>

                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px;">
                    <div style="background: #f8fafc; padding: 10px; border-radius: 8px;">
                      <div style="font-size: 20px; font-weight: 800; color: #2563eb;">01</div>
                      <div style="font-size: 10px; color: #64748b;">Biển báo phát hiện</div>
                    </div>
                    <div style="background: #f8fafc; padding: 10px; border-radius: 8px;">
                      <div style="font-size: 20px; font-weight: 800; color: #10b981;">82.8%</div>
                      <div style="font-size: 10px; color: #64748b;">Độ tin cậy cao nhất</div>
                    </div>
                    <div style="background: #f8fafc; padding: 10px; border-radius: 8px;">
                      <div style="font-size: 20px; font-weight: 800; color: #0f172a;">48.2 <span style="font-size: 10px;">ms</span></div>
                      <div style="font-size: 10px; color: #64748b;">Thời gian xử lý</div>
                    </div>
                    <div style="background: #f8fafc; padding: 10px; border-radius: 8px;">
                      <div style="font-size: 20px; font-weight: 800; color: #0f172a;">82</div>
                      <div style="font-size: 10px; color: #64748b;">Lớp biển hỗ trợ</div>
                    </div>
                  </div>

                  <h5 style="font-size: 12px; color: #334155; margin-bottom: 8px;">Chi tiết biển báo:</h5>
                  <div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin-bottom: 14px;">
                    <div style="display: flex; justify-content: space-between; padding: 8px 12px; font-size: 12px; background: #fff;">
                      <span>🛑 Biển báo Cấm / Dừng</span>
                      <strong style="color: #2563eb;">1 đối tượng</strong>
                    </div>
                  </div>

                  <!-- Download Buttons -->
                  <div style="display: flex; flex-direction: column; gap: 8px;">
                    <a class="btn btn-primary" style="justify-content: center;" href="#">📥 Tải ảnh đã chú thích</a>
                    <a class="btn btn-secondary" style="justify-content: center;" href="#">📊 Tải dữ liệu kết quả CSV</a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <h3>Quy trình phân tích chi tiết:</h3>
        <ol style="margin-left: 20px; margin-top: 10px; font-size: 14px;">
          <li><strong>Chọn loại tệp:</strong> Nhấp vào tab <code>📷 Hình ảnh</code> hoặc <code>🎥 Video</code>.</li>
          <li><strong>Tải tệp:</strong> Kéo thả ảnh (JPG, PNG, WEBP) hoặc video (MP4, AVI, MOV).</li>
          <li><strong>Nhấn nút phân tích:</strong> Bấm <code>🚀 Bắt đầu phân tích</code>. Đối với video, hệ thống hiển thị thanh tiến trình theo dõi khung hình đang xử lý.</li>
          <li><strong>Nhận kết quả:</strong> Xem khung bao biển báo trực quan, đối soát thông số ở bảng bên phải và tải kết quả lưu trữ về máy tính.</li>
        </ol>

        <h4 style="margin-top: 24px; color: #1e293b;">Ví dụ phân tích thêm với các loại biển báo tốc độ:</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 12px;">
          <div class="demo-img-box">
            <img src="{img1_b64}" alt="Demo biển báo giới hạn tốc độ" />
            <div class="demo-caption">Phát hiện biển báo Giới hạn tốc độ trên đường cao tốc</div>
          </div>
          <div class="demo-img-box">
            <img src="{img3_b64}" alt="Demo nhận diện trên đường phố" />
            <div class="demo-caption">Phát hiện nhiều đối tượng và biển báo phức tạp trong đô thị</div>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 5: HISTORY -->
    <section id="sec-history">
      <h2 class="section-title"><span class="section-number">5</span> Tra cứu Lịch sử (Local Database)</h2>
      <div class="card">
        <p>Hệ thống tự động lưu trữ mọi phiên phân tích vào cơ sở dữ liệu SQLite cục bộ (<code>artifacts/state/trafficvision.db</code>).</p>
        
        <div style="overflow-x: auto; margin-top: 14px;">
          <table>
            <thead>
              <tr>
                <th>Thời gian</th>
                <th>Tên tệp</th>
                <th>Loại</th>
                <th>Mô hình</th>
                <th>Số đối tượng</th>
                <th>Thời gian xử lý</th>
                <th>Ngưỡng Conf</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>2026-09-29 20:34:10</td>
                <td>bien-bao-toc-do.jpg</td>
                <td><span class="stat-badge badge-primary">IMAGE</span></td>
                <td>yolo11n-onnx</td>
                <td><strong>2</strong></td>
                <td>46.2 ms</td>
                <td>0.25</td>
              </tr>
              <tr>
                <td>2026-09-29 19:15:22</td>
                <td>video-camera-hanh-trinh.mp4</td>
                <td><span class="stat-badge badge-warning">VIDEO</span></td>
                <td>yolo11n-onnx</td>
                <td><strong>14</strong></td>
                <td>1.450 ms</td>
                <td>0.30</td>
              </tr>
              <tr>
                <td>2026-09-29 18:02:44</td>
                <td>nga-tu-bien-cam.jpg</td>
                <td><span class="stat-badge badge-primary">IMAGE</span></td>
                <td>yolo11n-onnx</td>
                <td><strong>1</strong></td>
                <td>42.8 ms</td>
                <td>0.25</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p style="font-size: 13px; color: #64748b; margin-top: 8px;">* Bảng hỗ trợ hiển thị tối đa 100 phiên gần nhất, giúp kiểm soát dữ liệu đầu vào và tốc độ đáp ứng của hệ thống.</p>
      </div>
    </section>

    <!-- SECTION 6: STATISTICS -->
    <section id="sec-statistics">
      <h2 class="section-title"><span class="section-number">6</span> Thống kê & Phân tích (Analytics)</h2>
      <div class="card">
        <p>Màn hình Thống kê tổng hợp toàn diện các chỉ số hiệu năng và tần suất xuất hiện của từng loại biển báo:</p>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 18px 0;">
          <div style="background: #f8fafc; border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center;">
            <div style="font-size: 32px; font-weight: 800; color: #2563eb;">28+</div>
            <div style="font-size: 13px; font-weight: 600; color: #475569; margin-top: 4px;">Tổng phiên phân tích</div>
          </div>
          <div style="background: #f8fafc; border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center;">
            <div style="font-size: 32px; font-weight: 800; color: #10b981;">65+</div>
            <div style="font-size: 13px; font-weight: 600; color: #475569; margin-top: 4px;">Tổng biển báo phát hiện</div>
          </div>
          <div style="background: #f8fafc; border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center;">
            <div style="font-size: 32px; font-weight: 800; color: #0f172a;">48.5 <span style="font-size: 14px;">ms</span></div>
            <div style="font-size: 13px; font-weight: 600; color: #475569; margin-top: 4px;">Thời gian xử lý trung bình</div>
          </div>
        </div>

        <h4 style="margin-top: 20px; margin-bottom: 10px;">Phân bố tần suất các loại biển báo phổ biến:</h4>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 3px;">
              <span>Giới hạn tốc độ (Speed Limit 40/60 km/h)</span>
              <strong>38% (25 biển)</strong>
            </div>
            <div style="height: 8px; background: #e2e8f0; border-radius: 99px; overflow: hidden;">
              <div style="width: 38%; height: 100%; background: #2563eb;"></div>
            </div>
          </div>
          <div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 3px;">
              <span>Cấm dừng & Cấm đỗ (No Parking)</span>
              <strong>28% (18 biển)</strong>
            </div>
            <div style="height: 8px; background: #e2e8f0; border-radius: 99px; overflow: hidden;">
              <div style="width: 28%; height: 100%; background: #14b8a6;"></div>
            </div>
          </div>
          <div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 3px;">
              <span>Cấm đi ngược chiều (No Entry)</span>
              <strong>18% (12 biển)</strong>
            </div>
            <div style="height: 8px; background: #e2e8f0; border-radius: 99px; overflow: hidden;">
              <div style="width: 18%; height: 100%; background: #f59e0b;"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 7: TRAINING LAB -->
    <section id="sec-training">
      <h2 class="section-title"><span class="section-number">7</span> Không gian "Huấn luyện AI" (Quy trình 4 bước Phase 2)</h2>
      <div class="card">
        <p>Phòng thí nghiệm <strong>AI Experiment Lab</strong> mang lại giải pháp MLOps hoàn chỉnh giúp đào tạo mô hình biển báo chuyên sâu cho Việt Nam:</p>

        <!-- 4 Steps Stepper -->
        <div class="stepper">
          <div class="step-item active">
            <span class="step-circle">1</span>
            <span>Tiếp nhận dữ liệu</span>
          </div>
          <div class="step-item active">
            <span class="step-circle">2</span>
            <span>Kiểm định & EDA</span>
          </div>
          <div class="step-item active">
            <span class="step-circle">3</span>
            <span>Huấn luyện nền</span>
          </div>
          <div class="step-item active">
            <span class="step-circle">4</span>
            <span>Đóng gói & Thăng cấp</span>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 20px;">
          <div style="padding: 16px; border: 1px solid var(--border); border-radius: 10px; background: #ffffff;">
            <h4 style="color: #2563eb; margin-bottom: 8px;">Bước 1: Tiếp nhận dữ liệu (Ingestion)</h4>
            <p style="font-size: 13px; color: #475569;">Quét cấu trúc YOLO từ thư mục <code>artifacts/staging/</code> hoặc tạo nhanh 100 ảnh mẫu mô phỏng (Synthetic Fixture) để kiểm tra pipeline.</p>
          </div>
          <div style="padding: 16px; border: 1px solid var(--border); border-radius: 10px; background: #ffffff;">
            <h4 style="color: #2563eb; margin-bottom: 8px;">Bước 2: Quality Gate & EDA</h4>
            <p style="font-size: 13px; color: #475569;">Kiểm tra 5 tiêu chuẩn nghiêm ngặt: loại bỏ ảnh hỏng, nhãn sai, class ID ngoài [0, 81], tọa độ lỗi và chống rò rỉ dữ liệu Train/Val qua SHA-256. Xuất Snapshot bất biến kèm <code>data.yaml</code>.</p>
          </div>
          <div style="padding: 16px; border: 1px solid var(--border); border-radius: 10px; background: #ffffff;">
            <h4 style="color: #2563eb; margin-bottom: 8px;">Bước 3: Huấn luyện nền ngầm (Background)</h4>
            <p style="font-size: 13px; color: #475569;">Cấu hình Epochs, Batch, Image Size, Patience. Huấn luyện chạy trong tiến trình nền độc lập, không gây nghẽn UI, hỗ trợ xem log thời gian thực và dừng an toàn.</p>
          </div>
          <div style="padding: 16px; border: 1px solid var(--border); border-radius: 10px; background: #ffffff;">
            <h4 style="color: #2563eb; margin-bottom: 8px;">Bước 4: Đóng gói & Thăng cấp (Promotion)</h4>
            <p style="font-size: 13px; color: #475569;">Đánh giá mAP50 trên tập test, xuất ONNX, kiểm tra sai số số học <code>max_abs_diff &le; 1e-3</code> và thăng cấp lên Production (tự động tạo bản backup mô hình cũ).</p>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 8: MODEL REGISTRY & ROLLBACK -->
    <section id="sec-model-info">
      <h2 class="section-title"><span class="section-number">8</span> Quản lý Thông tin Mô hình & Hoàn tác (Rollback)</h2>
      <div class="card">
        <p>Màn hình này cho phép theo dõi metadata mô hình và đảm bảo tính khả dụng liên tục của dịch vụ:</p>

        <div style="background: #0b1730; color: #e2e8f0; padding: 20px; border-radius: 12px; margin: 16px 0; font-size: 13px; font-family: var(--font-mono);">
          <div style="color: #38bdf8; font-weight: bold; margin-bottom: 8px;"># PRODUCTION MODEL MANIFEST</div>
          <div>Mã mô hình (Model ID): <strong>yolo11n-onnx-production</strong></div>
          <div>Trạng thái: <span style="color: #4ade80;">● PRODUCTION (ONLINE)</span></div>
          <div>Định dạng backend: <strong>ONNX (CPU Optimized, Batch 1)</strong></div>
          <div>Kích thước đầu vào: <strong>640 x 640 px</strong></div>
          <div>Mã băm toàn vẹn SHA-256: <code>e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</code></div>
        </div>

        <div class="callout callout-warning">
          <div class="callout-icon">🛡️</div>
          <div>
            <strong>Cơ chế Phục hồi khẩn cấp 1-Click (Safe Rollback):</strong><br/>
            Mỗi lần một Candidate mới được thăng cấp, hệ thống tự động lưu bản sao lưu vào thư mục <code>artifacts/backups/</code>. Nếu mô hình mới phát sinh lỗi, bạn chỉ cần chọn bản backup trong danh sách và bấm nút <strong>⏪ Phục hồi mô hình</strong> để hoàn tác ngay lập tức mà không cần khởi động lại server.
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 9: SETTINGS -->
    <section id="sec-settings">
      <h2 class="section-title"><span class="section-number">9</span> Thiết lập Hệ thống (Settings)</h2>
      <div class="card">
        <p>Người dùng có thể linh hoạt tinh chỉnh các thông số suy luận theo điều kiện ánh sáng hoặc độ phức tạp của bối cảnh giao thông:</p>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 14px;">
          <div style="background: #f8fafc; padding: 18px; border: 1px solid var(--border); border-radius: 10px;">
            <strong style="color: #0f172a;">Ngưỡng tin cậy (Confidence Threshold)</strong>
            <p style="font-size: 12px; color: #64748b; margin: 6px 0 12px;">Mặc định: <strong>0.25</strong> (Khoảng từ 0.05 đến 0.95)</p>
            <p style="font-size: 13px; color: #334155;">Tăng ngưỡng khi ảnh có nhiều chi tiết gây nhiễu nhằm loại bỏ báo động giả (False Positives). Giảm ngưỡng khi cần phát hiện biển báo ở xa hoặc mờ sương.</p>
          </div>

          <div style="background: #f8fafc; padding: 18px; border: 1px solid var(--border); border-radius: 10px;">
            <strong style="color: #0f172a;">Ngưỡng lọc trùng (IoU / NMS Threshold)</strong>
            <p style="font-size: 12px; color: #64748b; margin: 6px 0 12px;">Mặc định: <strong>0.45</strong> (Khoảng từ 0.10 đến 0.95)</p>
            <p style="font-size: 13px; color: #334155;">Dùng trong thuật toán Non-Maximum Suppression để loại bỏ các hộp bao chồng chéo nhau trên cùng một biển báo giao thông.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 10: CLI SCRIPTS -->
    <section id="sec-cli">
      <h2 class="section-title"><span class="section-number">10</span> Hướng dẫn Công cụ Dòng lệnh (CLI Scripts)</h2>
      <div class="card">
        <p>Dành cho lập trình viên và quản trị viên muốn tích hợp vào quy trình CI/CD:</p>

        <h4 style="margin-top: 14px;">1. Kiểm thử suy luận nhanh trên ảnh (Smoke test):</h4>
        <pre><code>python scripts/smoke_test.py --image path/to/sample.jpg</code></pre>

        <h4 style="margin-top: 14px;">2. Chạy kiểm định dữ liệu & tạo snapshot:</h4>
        <pre><code>python scripts/validate_dataset.py --data-dir artifacts/staging --output-dir artifacts/eda --create-snapshot</code></pre>

        <h4 style="margin-top: 14px;">3. Huấn luyện mô hình từ dòng lệnh:</h4>
        <pre><code>python scripts/train.py --data-yaml artifacts/snapshots/snapshot_latest/data.yaml --epochs 50 --batch 4 --device cpu</code></pre>

        <h4 style="margin-top: 14px;">4. Thăng cấp hoặc Hoàn tác mô hình:</h4>
        <pre><code># Thăng cấp Candidate
python scripts/promote_model.py --candidate-dir artifacts/runs/run_20260929/candidate

# Hoàn tác về bản backup gần nhất
python scripts/promote_model.py --rollback</code></pre>
      </div>
    </section>

    <!-- SECTION 11: TROUBLESHOOTING -->
    <section id="sec-troubleshoot">
      <h2 class="section-title"><span class="section-number">11</span> Xử lý sự cố thường gặp (Troubleshooting)</h2>
      <div class="card">
        <div style="margin-bottom: 16px;">
          <h4 style="color: #dc2626;">❓ Sự cố 1: Giao diện hiển thị cảnh báo "Chưa có Production model"?</h4>
          <p style="font-size: 14px; margin-top: 4px;"><strong>Cách xử lý:</strong> Chạy lệnh <code>python scripts/bootstrap_baseline.py</code> để khởi tạo mô hình nền ban đầu.</p>
        </div>

        <div style="margin-bottom: 16px;">
          <h4 style="color: #dc2626;">❓ Sự cố 2: Video xử lý chậm hoặc dung lượng quá lớn?</h4>
          <p style="font-size: 14px; margin-top: 4px;"><strong>Cách xử lý:</strong> Khuyến nghị cắt ngắn video thành các đoạn 10–30 giây độ phân giải 720p hoặc 1080p để đảm bảo tốc độ suy luận theo khung hình trên CPU mượt mà nhất.</p>
        </div>

        <div>
          <h4 style="color: #dc2626;">❓ Sự cố 3: Huấn luyện bị ngắt giữa chừng?</h4>
          <p style="font-size: 14px; margin-top: 4px;"><strong>Cách xử lý:</strong> Hệ thống lưu nhật ký tại <code>artifacts/runs/&lt;run_id&gt;/train.log</code>. Bạn có thể mở tệp này để tra cứu chi tiết thông báo lỗi.</p>
        </div>
      </div>
    </section>

    <footer style="margin-top: 60px; padding-top: 20px; border-top: 1px solid var(--border); text-align: center; color: var(--text-muted); font-size: 13px;">
      TrafficVision • Hệ thống Nhận dạng Biển báo Giao thông bằng AI • Bản quyền dự án 2026
    </footer>

  </main>
</div>

</body>
</html>
"""


def build_defense_presentation_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Báo Cáo Bảo Vệ Dự Án - TrafficVision</title>
  <style>
    :root {{
      --bg-dark: #070d19;
      --card-dark: #0f1c32;
      --card-border: rgba(255, 255, 255, 0.08);
      --accent-blue: #3b82f6;
      --accent-cyan: #06b6d4;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --font-heading: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg-dark);
      color: var(--text-main);
      font-family: var(--font-heading);
      overflow: hidden;
      height: 100vh;
      width: 100vw;
      user-select: none;
    }}

    /* Presentation Deck Container */
    .deck {{
      position: relative;
      width: 100vw;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    /* Slide Item */
    .slide {{
      position: absolute;
      width: 90vw;
      max-width: 1200px;
      height: 82vh;
      background: var(--card-dark);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 44px 56px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      opacity: 0;
      pointer-events: none;
      transform: translateY(20px) scale(0.98);
      transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5);
    }}
    .slide.active {{
      opacity: 1;
      pointer-events: auto;
      transform: translateY(0) scale(1);
    }}

    /* Slide Header */
    .slide-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding-bottom: 16px;
    }}
    .slide-tag {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      border-radius: 99px;
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .slide-title {{
      font-size: 28px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #ffffff;
      margin-top: 6px;
    }}
    .slide-subtitle {{
      color: var(--text-muted);
      font-size: 13px;
    }}

    /* Slide Content */
    .slide-body {{
      flex: 1;
      overflow-y: auto;
      padding: 8px 0;
    }}

    /* Slide Footer */
    .slide-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      padding-top: 14px;
      font-size: 12px;
      color: var(--text-muted);
    }}

    /* Progress Bar */
    .progress-bar {{
      position: fixed;
      top: 0;
      left: 0;
      height: 4px;
      background: linear-gradient(90deg, #3b82f6, #06b6d4, #10b981);
      width: 0%;
      transition: width 0.3s ease;
      z-index: 100;
    }}

    /* Controls Overlay */
    .controls {{
      position: fixed;
      bottom: 24px;
      right: 28px;
      display: flex;
      align-items: center;
      gap: 10px;
      z-index: 99;
      background: rgba(15, 28, 50, 0.8);
      backdrop-filter: blur(10px);
      padding: 6px 12px;
      border-radius: 30px;
      border: 1px solid var(--card-border);
    }}
    .ctrl-btn {{
      background: transparent;
      border: none;
      color: var(--text-main);
      width: 34px;
      height: 34px;
      border-radius: 50%;
      cursor: pointer;
      display: grid;
      place-items: center;
      font-size: 14px;
      transition: background 0.15s ease;
    }}
    .ctrl-btn:hover {{
      background: rgba(255, 255, 255, 0.15);
    }}
    .slide-count {{
      font-size: 12px;
      font-weight: 700;
      color: var(--text-muted);
      padding: 0 6px;
      font-family: var(--font-mono);
    }}

    /* Presentation Grids & Components */
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      height: 100%;
      align-items: center;
    }}
    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 18px;
    }}
    .grid-4 {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
    }}

    .box-dark {{
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 14px;
      padding: 20px;
    }}
    .box-dark h4 {{
      font-size: 16px;
      font-weight: 700;
      color: #38bdf8;
      margin-bottom: 8px;
    }}
    .box-dark p, .box-dark li {{
      font-size: 13px;
      line-height: 1.6;
      color: #cbd5e1;
    }}
    .box-dark ul {{
      margin-left: 18px;
      margin-top: 6px;
    }}

    /* Metric card */
    .metric-card {{
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 18px;
      text-align: center;
    }}
    .metric-val {{
      font-size: 32px;
      font-weight: 900;
      letter-spacing: -0.03em;
      margin-bottom: 4px;
    }}
    .metric-lbl {{
      font-size: 12px;
      color: var(--text-muted);
    }}

    /* Badges */
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
    }}
    .badge-blue {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; }}
    .badge-green {{ background: rgba(16, 185, 129, 0.2); color: #34d399; }}
    .badge-amber {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; }}

    /* Title Slide Specifics */
    .hero-title {{
      font-size: 40px;
      font-weight: 900;
      line-height: 1.2;
      background: linear-gradient(135deg, #ffffff 40%, #38bdf8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 16px;
    }}
    .hero-desc {{
      font-size: 18px;
      color: #94a3b8;
      max-width: 800px;
      line-height: 1.5;
    }}

    .team-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
      font-size: 13px;
    }}
    .team-table th, .team-table td {{
      padding: 10px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      text-align: left;
    }}
    .team-table th {{
      color: #38bdf8;
      font-weight: 700;
    }}

    /* Demo image frame */
    .slide-img {{
      width: 100%;
      max-height: 380px;
      object-fit: contain;
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.15);
      background: #000;
    }}
  </style>
</head>
<body>

  <div class="progress-bar" id="progressBar"></div>

  <div class="deck" id="deck">

    <!-- SLIDE 1: TRANG TIÊU ĐỀ -->
    <div class="slide active">
      <div class="slide-header">
        <span class="slide-tag">ĐỒ ÁN TỐT NGHIỆP / BÁO CÁO DỰ ÁN AI</span>
        <span style="color: var(--text-muted); font-size: 12px;">HỘI ĐỒNG BẢO VỆ 2026</span>
      </div>
      <div class="slide-body" style="display: flex; flex-direction: column; justify-content: center;">
        <div style="font-size: 14px; font-weight: 800; color: #38bdf8; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px;">DỰ ÁN NGHIÊN CỨU & PHÁT TRIỂN</div>
        <h1 class="hero-title">TRAFFICVISION<br><span style="font-size: 30px; font-weight: 700; color: #e2e8f0;">Nhận dạng biển báo giao thông Việt Nam bằng AI</span></h1>
        <p class="hero-desc">Hệ thống thị giác máy tính suy luận thời gian thực tối ưu hóa ONNX trên vi xử lý CPU, hỗ trợ danh mục chuẩn 82 lớp biển báo QCVN 41:2019/BGTVT và quy trình MLOps 4 bước khép kín.</p>

        <div style="margin-top: 36px; display: flex; gap: 40px;">
          <div>
            <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 700;">Nhóm thực hiện:</div>
            <div style="font-size: 14px; font-weight: 600; color: #ffffff; margin-top: 4px;">Phí Văn Nam (Trưởng nhóm) • Đỗ Thị Vân Anh • Đỗ Hữu Nghị • Quản Văn Điệp</div>
          </div>
          <div>
            <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 700;">Công nghệ cốt lõi:</div>
            <div style="font-size: 14px; font-weight: 600; color: #38bdf8; margin-top: 4px;">YOLO11 • ONNX Runtime • Streamlit • OpenCV • SQLite</div>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span>Nhấn <strong>Phím Mũi tên (← / →)</strong> hoặc phím <strong>Space</strong> để chuyển trang</span>
        <span>Phím <strong>F</strong>: Bật/Tắt toàn màn hình (Fullscreen)</span>
      </div>
    </div>

    <!-- SLIDE 2: ĐẶT VẤN ĐỀ & MỤC TIÊU -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">TỔNG QUAN ĐỀ TÀI</span>
          <h2 class="slide-title">1. Đặt vấn đề & Mục tiêu dự án</h2>
        </div>
      </div>
      <div class="slide-body">
        <div class="grid-2">
          <div class="box-dark" style="height: 100%;">
            <h4>🚨 Thách thức thực tế tại Việt Nam</h4>
            <ul>
              <li><strong>Môi trường giao thông phức tạp:</strong> Biển báo thường bị che khuất bởi tán cây, xe tải lớn, mật độ phương tiện đông đúc.</li>
              <li><strong>Đa dạng điều kiện thời tiết:</strong> Mưa bão, nắng chói, sương mù, góc chụp nghiêng từ camera hành trình khiến thị giác truyền thống dễ nhận diện sai.</li>
              <li><strong>Rào cản phần cứng:</strong> Đa phần các thiết bị giám sát và laptop hiện nay không trang bị GPU cao cấp, đòi hỏi mô hình AI phải chạy mượt trực tiếp trên CPU.</li>
              <li><strong>Nguy cơ gián đoạn dịch vụ:</strong> Việc cập nhật mô hình mới thường gây sập server nếu không có cơ chế MLOps an toàn.</li>
            </ul>
          </div>
          <div class="box-dark" style="height: 100%;">
            <h4>🎯 Mục tiêu giải pháp của TrafficVision</h4>
            <ul>
              <li><strong>Chuẩn hóa 82 lớp:</strong> Phân loại chính xác 82 loại biển báo theo Quy chuẩn kỹ thuật quốc gia QCVN 41:2019/BGTVT (Cấm, Hiệu lệnh, Cảnh báo, Chỉ dẫn).</li>
              <li><strong>Tối ưu hóa suy luận CPU:</strong> Đạt tốc độ suy luận dưới 50ms/ảnh nhờ định dạng ONNX tĩnh và cơ chế đa luồng AVX2.</li>
              <li><strong>Hỗ trợ đa phương tiện:</strong> Nhận dạng ảnh tĩnh (JPG, PNG, WEBP) và video chuyển động (MP4, AVI, MOV) kèm thanh tiến trình trực quan.</li>
              <li><strong>Vận hành an toàn tuyệt đối:</strong> Quy trình kiểm định Quality Gate 5 bước và cơ chế thăng cấp/hoàn tác (Rollback 1-click) tức thì.</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 1 / 14</span>
      </div>
    </div>

    <!-- SLIDE 3: KIẾN TRÚC TỔNG THỂ -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">KIẾN TRÚC HỆ THỐNG</span>
          <h2 class="slide-title">2. Kiến trúc giải pháp phân tầng (System Architecture)</h2>
        </div>
      </div>
      <div class="slide-body">
        <div class="grid-3" style="margin-bottom: 20px;">
          <div class="box-dark">
            <h4 style="color: #60a5fa;">Tầng Giao diện (Presentation)</h4>
            <p><strong>Streamlit Dashboard</strong></p>
            <ul style="margin-top: 6px;">
              <li>Không gian Phân tích (Ảnh / Video)</li>
              <li>Lịch sử & Thống kê KPI</li>
              <li>Phòng thí nghiệm Huấn luyện AI</li>
              <li>Model Registry & Cấu hình Settings</li>
            </ul>
          </div>
          <div class="box-dark">
            <h4 style="color: #34d399;">Tầng Nghiệp vụ (Application Service)</h4>
            <p><strong>AnalysisService & TrainingManager</strong></p>
            <ul style="margin-top: 6px;">
              <li>Tiền xử lý Letterbox & Resize 640px</li>
              <li>Điều phối tiến trình nền ngầm (Subprocess)</li>
              <li>Quản lý trạng thái State & Settings</li>
              <li>Lưu trữ phiên phân tích vào SQLite</li>
            </ul>
          </div>
          <div class="box-dark">
            <h4 style="color: #f59e0b;">Tầng Hạ tầng AI (MLOps & Runtime)</h4>
            <p><strong>ModelRegistry & ONNX Predictor</strong></p>
            <ul style="margin-top: 6px;">
              <li>ONNX Runtime Engine tối ưu CPU</li>
              <li>Lọc phi cực đại Non-Max Suppression (NMS)</li>
              <li>Quản lý Manifest & Checksum SHA-256</li>
              <li>Hệ thống lưu trữ bản sao lưu Backups</li>
            </ul>
          </div>
        </div>

        <div class="box-dark" style="background: rgba(14, 165, 233, 0.05); border-color: rgba(14, 165, 233, 0.2);">
          <strong style="color: #38bdf8;">Nguyên lý Tách biệt Tuyệt đối:</strong> Hệ thống phân chia độc lập giữa <em>Quy trình Trực tuyến</em> (Phục vụ người dùng qua Production Model bất biến) và <em>Quy trình Ngoại tuyến</em> (Huấn luyện ngầm trong Background). Nhờ đó, ngay cả khi quá trình train gặp sự cố, luồng nhận diện của người dùng vẫn hoạt động 100% ổn định.
        </div>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 2 / 14</span>
      </div>
    </div>

    <!-- SLIDE 4: BỘ DỮ LIỆU & CATALOG 82 LỚP -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">DỮ LIỆU & PHÂN LOẠI</span>
          <h2 class="slide-title">3. Bộ dữ liệu biển báo giao thông Việt Nam (82 Lớp)</h2>
        </div>
      </div>
      <div class="slide-body">
        <div class="grid-4" style="margin-bottom: 20px;">
          <div class="metric-card">
            <div class="metric-val" style="color: #38bdf8;">10.139</div>
            <div class="metric-lbl">Tổng số ảnh chuẩn hóa</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color: #34d399;">19.722</div>
            <div class="metric-lbl">Hộp bao Bounding Box</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color: #f59e0b;">82</div>
            <div class="metric-lbl">Lớp biển báo quy chuẩn</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color: #a855f7;">0</div>
            <div class="metric-lbl">Ảnh lỗi (Anomalies)</div>
          </div>
        </div>

        <div class="grid-2">
          <div class="box-dark">
            <h4>Phân chia tập dữ liệu (Dataset Split)</h4>
            <table class="team-table">
              <tr>
                <th>Tập dữ liệu</th>
                <th>Số lượng ảnh</th>
                <th>Số nhãn (Bounding Boxes)</th>
                <th>Tỷ lệ</th>
              </tr>
              <tr>
                <td><strong>Tập Huấn luyện (Train)</strong></td>
                <td>8.131</td>
                <td>15.733</td>
                <td>~80%</td>
              </tr>
              <tr>
                <td><strong>Tập Kiểm định (Val)</strong></td>
                <td>1.001</td>
                <td>2.036</td>
                <td>~10%</td>
              </tr>
              <tr>
                <td><strong>Tập Kiểm thử (Test)</strong></td>
                <td>1.007</td>
                <td>1.953</td>
                <td>~10%</td>
              </tr>
            </table>
          </div>

          <div class="box-dark">
            <h4>4 Nhóm Biển báo chính (QCVN 41:2019)</h4>
            <ul style="margin-top: 8px;">
              <li><strong style="color: #ef4444;">Nhóm Biển Cấm:</strong> Đường cấm, Cấm đi ngược chiều, Giới hạn tốc độ (40, 50, 60, 80 km/h), Cấm dừng đỗ,...</li>
              <li><strong style="color: #3b82f6;">Nhóm Biển Hiệu lệnh:</strong> Đi về bên phải, Đi thẳng, Vòng xuyến, Tốc độ tối thiểu,...</li>
              <li><strong style="color: #f59e0b;">Nhóm Biển Cảnh báo & Nguy hiểm:</strong> Cua gấp, Đường trơn trượt, Giao nhau với đường không ưu tiên,...</li>
              <li><strong style="color: #10b981;">Nhóm Biển Chỉ dẫn:</strong> Đường một chiều, Bãi đỗ xe, Camera giám sát giao thông,...</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 3 / 14</span>
      </div>
    </div>

    <!-- SLIDE 5: CỔNG KIỂM ĐỊNH QUALITY GATE -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">MLOPS QUALITY GATE</span>
          <h2 class="slide-title">4. Cổng kiểm định dữ liệu nghiêm ngặt (Quality Gate & EDA)</h2>
        </div>
      </div>
      <div class="slide-body">
        <p style="color: #cbd5e1; font-size: 14px; margin-bottom: 16px;">Để loại trừ hiện tượng "Dữ liệu rác tạo ra mô hình rác", toàn bộ dữ liệu bắt buộc phải vượt qua 5 cổng kiểm định chặn (Blocking Gates) trước khi đưa vào huấn luyện:</p>

        <div class="grid-2">
          <div class="box-dark">
            <h4 style="color: #ef4444;">5 Tiêu chí Kiểm định Chặn (Blocking Rules)</h4>
            <ol style="margin-left: 20px; font-size: 13px; line-height: 1.8; color: #cbd5e1;">
              <li><strong>CORRUPT_IMAGE:</strong> Phát hiện và loại bỏ các ảnh 0-byte, tệp hỏng header hoặc không thể decode bằng OpenCV.</li>
              <li><strong>MALFORMED_YOLO_LINE:</strong> Kiểm tra nghiêm ngặt định dạng nhãn (phải đủ 5 giá trị số phân tách bởi dấu cách).</li>
              <li><strong>CLASS_ID_OUT_OF_RANGE:</strong> Xác thực mã lớp nằm chính xác trong dải [0, 81].</li>
              <li><strong>INVALID_COORDINATES:</strong> Phát hiện tọa độ tâm, chiều rộng/chiều cao vượt ra ngoài khoảng [0, 1].</li>
              <li><strong>DATA_LEAKAGE:</strong> Kiểm tra rò rỉ dữ liệu giữa tập Train và Val/Test thông qua mã băm SHA-256 từng tệp ảnh.</li>
            </ol>
          </div>

          <div class="box-dark">
            <h4 style="color: #10b981;">Snapshot bất biến & Báo cáo EDA</h4>
            <p>Sau khi dữ liệu được phê duyệt:</p>
            <ul>
              <li>Hệ thống tự động đóng gói <strong>Dataset Snapshot</strong> bất biến lưu tại <code>artifacts/snapshots/&lt;snapshot_id&gt;/</code>.</li>
              <li>Tạo tệp cấu hình <code>data.yaml</code> chuẩn hóa kèm checksum từng tệp nhằm đảm bảo 100% khả năng tái lập thí nghiệm.</li>
              <li>Xuất báo cáo <code>eda_report.json</code> phân tích sâu: tỷ lệ khung hình ảnh, kích thước bbox COCO (Small/Medium/Large) và cảnh báo các lớp biển báo ít mẫu.</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 4 / 14</span>
      </div>
    </div>

    <!-- SLIDE 6: KỸ THUẬT MÔ HÌNH & ONNX CPU -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">MÔ HÌNH & TỐI ƯU HÓA</span>
          <h2 class="slide-title">5. Tối ưu hóa suy luận mô hình trên CPU với ONNX Runtime</h2>
        </div>
      </div>
      <div class="slide-body">
        <div class="grid-2">
          <div class="box-dark">
            <h4>Lựa chọn Kiến trúc YOLO11 Nano (yolo11n)</h4>
            <p>Mô hình tiên tiến nhất thuộc hệ sinh thái Ultralytics:</p>
            <ul>
              <li><strong>Số lượng tham số nhỏ:</strong> ~2.6 triệu tham số, dung lượng tệp ONNX chỉ ~10 MB.</li>
              <li><strong>Cơ chế Attention cải tiến:</strong> Tăng cường khả năng trích xuất đặc trưng cho các vật thể nhỏ (Small Object Detection) như biển báo ở xa.</li>
              <li><strong>Tiền xử lý chuẩn hóa Letterbox:</strong> Giữ nguyên tỷ lệ khung hình gốc (Aspect Ratio) với đệm màu xám, kích thước đầu vào cố định 640x640 px.</li>
            </ul>
          </div>

          <div class="box-dark">
            <h4>Kỹ thuật Tối ưu ONNX Runtime</h4>
            <ul>
              <li><strong>Cố định kích thước (Static Graph):</strong> Shape <code>[1, 3, 640, 640]</code> giúp compiler tối ưu hóa bộ nhớ đệm (Cache locality).</li>
              <li><strong>Đa luồng CPU (Intra-op Threads):</strong> Tận dụng toàn bộ nhân CPU của macOS Apple Silicon hoặc Intel/AMD đa nhân.</li>
              <li><strong>Kiểm định sai số số học (Parity Check):</strong> Đảm bảo độ lệch đầu ra số học giữa PyTorch gốc và ONNX:
                <br><code>max_abs_diff &le; 1e-3</code>
              </li>
              <li><strong>Tốc độ đo đạc thực tế:</strong> Chỉ từ <strong>40 – 50 ms / ảnh</strong> trên CPU thông thường!</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 5 / 14</span>
      </div>
    </div>

    <!-- SLIDE 7: PHÒNG THÍ NGHIỆM MLOPS 4 BƯỚC -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">QUY TRÌNH HUẤN LUYỆN</span>
          <h2 class="slide-title">6. Phòng thí nghiệm MLOps 4 bước (AI Experiment Lab)</h2>
        </div>
      </div>
      <div class="slide-body">
        <div class="grid-4" style="margin-bottom: 20px;">
          <div class="box-dark" style="border-top: 3px solid #3b82f6;">
            <div style="font-size: 11px; color: #3b82f6; font-weight: 800;">BƯỚC 1</div>
            <h4 style="color: #fff; font-size: 14px; margin: 4px 0 8px;">Tiếp nhận dữ liệu</h4>
            <p style="font-size: 12px; color: #94a3b8;">Nạp bộ dữ liệu YOLO staging hoặc tạo 100 mẫu Synthetic Fixture để kiểm thử nhanh quy trình.</p>
          </div>
          <div class="box-dark" style="border-top: 3px solid #10b981;">
            <div style="font-size: 11px; color: #10b981; font-weight: 800;">BƯỚC 2</div>
            <h4 style="color: #fff; font-size: 14px; margin: 4px 0 8px;">Kiểm định & Snapshot</h4>
            <p style="font-size: 12px; color: #94a3b8;">Chạy 5 cổng Quality Gate, xuất báo cáo EDA và đóng gói snapshot dữ liệu bất biến.</p>
          </div>
          <div class="box-dark" style="border-top: 3px solid #f59e0b;">
            <div style="font-size: 11px; color: #f59e0b; font-weight: 800;">BƯỚC 3</div>
            <h4 style="color: #fff; font-size: 14px; margin: 4px 0 8px;">Huấn luyện nền</h4>
            <p style="font-size: 12px; color: #94a3b8;">Tiến trình độc lập (Background Subprocess), theo dõi log trực tiếp, hỗ trợ nút Abort an toàn.</p>
          </div>
          <div class="box-dark" style="border-top: 3px solid #a855f7;">
            <div style="font-size: 11px; color: #a855f7; font-weight: 800;">BƯỚC 4</div>
            <h4 style="color: #fff; font-size: 14px; margin: 4px 0 8px;">Đóng gói & Thăng cấp</h4>
            <p style="font-size: 12px; color: #94a3b8;">Đánh giá mAP50 trên test split, đo FPS CPU, xuất Candidate và thăng cấp an toàn với backup.</p>
          </div>
        </div>

        <div class="box-dark" style="background: rgba(16, 185, 129, 0.05); border-color: rgba(16, 185, 129, 0.2);">
          <strong style="color: #34d399;">Ưu thế kỹ thuật vượt trội:</strong> Người dùng không cần kiến thức dòng lệnh phức tạp. Toàn bộ chu trình từ chuẩn bị dữ liệu đến khi mô hình AI đi vào phục vụ đều được tự động hóa và trực quan hóa 100% trên giao diện web.
        </div>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 6 / 14</span>
      </div>
    </div>

    <!-- SLIDE 8: MODEL REGISTRY & ROLLBACK -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">ĐỘ TIN CẬY & VẬN HÀNH</span>
          <h2 class="slide-title">7. Quản lý Vòng đời Mô hình & Phục hồi khẩn cấp (Rollback)</h2>
        </div>
      </div>
      <div class="slide-body">
        <div class="grid-2">
          <div class="box-dark">
            <h4>Chuyển dịch 3 trạng thái mô hình</h4>
            <ul>
              <li><strong style="color: #f59e0b;">Baseline Model:</strong> Mô hình nền tảng ban đầu (YOLO11n COCO 80 lớp), đóng vai trò điểm tựa an toàn khi khởi tạo hệ thống.</li>
              <li><strong style="color: #38bdf8;">Candidate Model:</strong> Mô hình sau khi huấn luyện trên tập biển báo Việt Nam 82 lớp, đã vượt qua bài test kiểm tra sai lệch ONNX và benchmark tốc độ.</li>
              <li><strong style="color: #10b981;">Production Model:</strong> Mô hình đang trực tiếp phục vụ người dùng. Khi được thăng cấp, toàn bộ nhãn nhận dạng trả về tiếng Việt chuẩn xác theo QCVN 41:2019.</li>
            </ul>
          </div>

          <div class="box-dark">
            <h4>Cơ chế Safe Atomic Swap & Rollback</h4>
            <p>Hệ thống loại bỏ hoàn toàn rủi ro khi triển khai mô hình mới:</p>
            <ul>
              <li><strong>Sao lưu tự động:</strong> Trước khi ghi đè Production, hệ thống tự động lưu trữ nguyên trạng mô hình hiện hành vào <code>artifacts/backups/&lt;backup_id&gt;/</code>.</li>
              <li><strong>Khôi phục 1-Click:</strong> Nếu mô hình mới phát sinh vấn đề trong thực tế, chỉ cần 1 thao tác trên Web UI để khôi phục phiên bản ổn định trước đó ngay lập tức.</li>
              <li><strong>Toàn vẹn Checksum:</strong> Mọi tệp ONNX đều được gắn kèm mã băm SHA-256 để chống can thiệp trái phép.</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 7 / 14</span>
      </div>
    </div>

    <!-- SLIDE 9: DEMO PHÂN TÍCH ẢNH & VIDEO -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">DEMO KẾT QUẢ THỰC TẾ</span>
          <h2 class="slide-title">8. Trực quan hóa kết quả nhận dạng Ảnh & Video</h2>
        </div>
      </div>
      <div class="slide-body">
        <div class="grid-2">
          <div>
            <img src="{img2_b64}" class="slide-img" alt="Ảnh kết quả phân tích">
            <div style="font-size: 11px; color: var(--text-muted); text-align: center; margin-top: 6px;">Ảnh nhận diện Bounding Box chính xác biển báo giao thông trên đường quốc lộ</div>
          </div>
          <div class="box-dark" style="height: 100%; display: flex; flex-direction: column; justify-content: space-around;">
            <div>
              <h4 style="color: #38bdf8;">Đặc tính hiển thị kết quả</h4>
              <ul>
                <li>Khung bao định vị chính xác vị trí biển báo, vẽ nhãn tiếng Việt rõ ràng.</li>
                <li>Hiển thị chỉ số tin cậy (Confidence) và thời gian suy luận (Latency) tính bằng miligiây.</li>
                <li>Tự động thống kê số lượng biển báo phát hiện theo từng phân loại cụ thể.</li>
              </ul>
            </div>
            <div>
              <h4 style="color: #34d399;">Xử lý Video thông minh</h4>
              <ul>
                <li>Đọc tuần tự từng frame của video camera hành trình (MP4, AVI, MOV).</li>
                <li>Thanh tiến trình trực quan thông báo số khung hình đã xử lý theo thời gian thực.</li>
                <li>Hỗ trợ xem lại video thành phẩm trực tiếp trên trình duyệt và tải bảng dữ liệu CSV.</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 8 / 14</span>
      </div>
    </div>

    <!-- SLIDE 10: DEMO LỊCH SỬ & THỐNG KÊ -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">DỮ LIỆU & QUẢN TRỊ</span>
          <h2 class="slide-title">9. Quản lý Lịch sử, Thống kê & Thiết lập thông số</h2>
        </div>
      </div>
      <div class="slide-body">
        <div class="grid-3">
          <div class="box-dark">
            <h4>Tra cứu Lịch sử (SQLite)</h4>
            <p>Ghi nhận tự động chi tiết mọi phiên làm việc:</p>
            <ul>
              <li>Thời điểm phân tích</li>
              <li>Tên tệp gốc & Loại tệp</li>
              <li>Mã mô hình đang dùng</li>
              <li>Số đối tượng phát hiện</li>
              <li>Độ trễ suy luận (ms)</li>
              <li>Ngưỡng Conf/IoU đã dùng</li>
            </ul>
          </div>
          <div class="box-dark">
            <h4>Báo cáo Thống kê KPI</h4>
            <p>Trực quan hóa bức tranh toàn cảnh:</p>
            <ul>
              <li>Tổng số phiên đã xử lý</li>
              <li>Tổng tích lũy biển báo tìm thấy</li>
              <li>Tốc độ phản hồi trung bình</li>
              <li>Biểu đồ phân bố tần suất từng loại biển báo giúp cơ quan quản lý nắm bắt tình hình tuyến đường</li>
            </ul>
          </div>
          <div class="box-dark">
            <h4>Thiết lập Ngưỡng linh hoạt</h4>
            <p>Tùy biến theo môi trường thực tế:</p>
            <ul>
              <li><strong>Confidence Slider (0.05 - 0.95):</strong> Lọc bỏ các phát hiện nhiễu hoặc tăng độ nhạy khi thời tiết xấu.</li>
              <li><strong>IoU / NMS Slider (0.10 - 0.95):</strong> Xóa bỏ triệt để các khung bao trùng lặp.</li>
              <li>Lưu tức thì vào runtime không cần restart.</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 9 / 14</span>
      </div>
    </div>

    <!-- SLIDE 11: KIỂM THỬ & ĐÁNH GIÁ CHẤT LƯỢNG -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">CHẤT LƯỢNG PHẦN MỀM</span>
          <h2 class="slide-title">10. Kiểm thử tự động & Tính trung thực của số liệu</h2>
        </div>
      </div>
      <div class="slide-body">
        <div class="grid-2">
          <div class="box-dark">
            <h4>Hệ thống Kiểm thử tự động (Test Suite)</h4>
            <p>Dự án tuân thủ tiêu chuẩn kỹ thuật phần mềm nghiêm ngặt với <strong>Pytest</strong>:</p>
            <ul>
              <li><strong>170+ Test Cases</strong> tự động kiểm tra toàn bộ các thành phần:
                <br>• Unit test tiền xử lý & validator
                <br>• Test tính bất biến của Snapshot & Manifest
                <br>• Test luồng suy luận ảnh & tuần tự video
                <br>• Test Promotion & Rollback nguyên tử
              </li>
              <li>Tỷ lệ vượt qua kiểm thử: <strong style="color: #34d399;">100% Passed</strong>.</li>
            </ul>
          </div>

          <div class="box-dark">
            <h4>Nguyên tắc Trung thực Khoa học</h4>
            <div class="box-dark" style="background: rgba(245, 158, 11, 0.08); border-color: rgba(245, 158, 11, 0.3); margin-top: 6px;">
              <p style="color: #fcd34d; font-size: 13px;">
                <strong>Cam kết minh bạch dữ liệu:</strong>
                Hệ thống báo cáo đúng thực trạng artifact trong repository: Phân định rõ ràng giữa phiên bản nền ban đầu (Baseline COCO 80 lớp) và lộ trình huấn luyện candidate 82 lớp. Không sử dụng số liệu giả lập mAP khi phiên train chưa kết thúc trọn vẹn trên phần cứng đích.
              </p>
            </div>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 10 / 14</span>
      </div>
    </div>

    <!-- SLIDE 12: PHÂN CÔNG THÀNH VIÊN -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">TỔ CHỨC DỰ ÁN</span>
          <h2 class="slide-title">11. Phân công vai trò & Đóng góp thành viên</h2>
        </div>
      </div>
      <div class="slide-body">
        <table class="team-table">
          <thead>
            <tr>
              <th>Họ và tên</th>
              <th>Vai trò</th>
              <th>Nhiệm vụ & Đóng góp chính</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Phí Văn Nam</strong></td>
              <td><span class="badge badge-blue">Trưởng nhóm</span></td>
              <td>Thiết kế kiến trúc hệ thống, tích hợp các thành phần MLOps, quản lý luồng dữ liệu, điều phối tiến độ và tổng hợp báo cáo.</td>
            </tr>
            <tr>
              <td><strong>Đỗ Thị Vân Anh</strong></td>
              <td><span class="badge badge-green">Kỹ sư Dữ liệu</span></td>
              <td>Thu thập và tiền xử lý bộ dữ liệu 82 lớp biển báo Việt Nam, thiết lập các bộ lọc Quality Gate, phân tích khám phá dữ liệu (EDA).</td>
            </tr>
            <tr>
              <td><strong>Đỗ Hữu Nghị</strong></td>
              <td><span class="badge badge-amber">Kỹ sư AI/ML</span></td>
              <td>Cấu hình pipeline huấn luyện YOLO11, tối ưu hóa suy luận ONNX trên CPU, kiểm tra sai số số học PyTorch vs ONNX và benchmark.</td>
            </tr>
            <tr>
              <td><strong>Quản Văn Điệp</strong></td>
              <td><span class="badge badge-blue">Kỹ sư Fullstack/QA</span></td>
              <td>Phát triển giao diện web Streamlit, hoàn thiện luồng xử lý video đa phương tiện, viết bộ kiểm thử tự động và tài liệu sử dụng.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 11 / 14</span>
      </div>
    </div>

    <!-- SLIDE 13: ĐÁNH GIÁ & HƯỚNG PHÁT TRIỂN -->
    <div class="slide">
      <div class="slide-header">
        <div>
          <span class="slide-tag">TỔNG KẾT & MỞ RỘNG</span>
          <h2 class="slide-title">12. Đánh giá ưu điểm & Hướng phát triển tương lai</h2>
        </div>
      </div>
      <div class="slide-body">
        <div class="grid-2">
          <div class="box-dark">
            <h4 style="color: #34d399;">Ưu điểm đã đạt được</h4>
            <ul>
              <li><strong>Kiến trúc sản phẩm hoàn thiện:</strong> Không chỉ dừng lại ở mô hình AI đơn lẻ mà đã hoàn thiện thành một hệ thống phần mềm có UI, database, registry và pipeline đầy đủ.</li>
              <li><strong>Hiệu năng ấn tượng trên CPU:</strong> Thời gian phản hồi 40-50ms đảm bảo tính ứng dụng cao trên các thiết bị phổ thông.</li>
              <li><strong>Quy trình chuẩn MLOps:</strong> Khả năng kiểm soát chất lượng dữ liệu, snapshot bất biến và rollback khẩn cấp an toàn.</li>
            </ul>
          </div>

          <div class="box-dark">
            <h4 style="color: #38bdf8;">Định hướng nâng cấp tiếp theo</h4>
            <ul>
              <li><strong>Kết nối Camera hành trình trực tiếp:</strong> Nhận luồng RTSP/RTMP từ camera trên xe để cảnh báo thời gian thực khi đang di chuyển.</li>
              <li><strong>Cảnh báo bằng giọng nói (Voice Alert):</strong> Tích hợp Text-to-Speech phát âm thanh cảnh báo bằng tiếng Việt khi xe vượt quá tốc độ cho phép.</li>
              <li><strong>Tích hợp bản đồ GPS:</strong> Đánh dấu vị trí tọa độ các biển báo lên bản đồ số để hỗ trợ công tác duy tu hạ tầng giao thông.</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span>TrafficVision Project Defense</span>
        <span>Mục 12 / 14</span>
      </div>
    </div>

    <!-- SLIDE 14: KẾT LUẬN & Q&A -->
    <div class="slide">
      <div class="slide-header">
        <span class="slide-tag">LỜI KẾT</span>
        <span style="color: var(--text-muted); font-size: 12px;">TRAFFICVISION DEFENSE</span>
      </div>
      <div class="slide-body" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
        <div style="width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #10b981, #3b82f6); display: grid; place-items: center; font-size: 28px; margin-bottom: 20px;">
          🚦
        </div>
        <h2 style="font-size: 36px; font-weight: 900; color: #ffffff; margin-bottom: 12px;">KẾT LUẬN & HỎI ĐÁP (Q&A)</h2>
        <p style="color: #94a3b8; font-size: 16px; max-width: 700px; line-height: 1.6; margin-bottom: 30px;">
          Dự án <strong>TrafficVision</strong> đã hoàn thành xây dựng nền tảng thị giác máy tính toàn diện, kết hợp chặt chẽ giữa học sâu nhận dạng biển báo giao thông Việt Nam và quy trình kỹ nghệ phần mềm MLOps hiện đại.
        </p>

        <div style="background: rgba(255, 255, 255, 0.05); padding: 16px 36px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1);">
          <div style="font-size: 15px; color: #38bdf8; font-weight: 700;">Nhóm xin trân trọng cảm ơn Quý Thầy Cô trong Hội đồng!</div>
          <div style="font-size: 13px; color: #cbd5e1; margin-top: 4px;">Rất mong nhận được những ý kiến đóng góp quý báu từ Quý Thầy Cô.</div>
        </div>
      </div>
      <div class="slide-footer">
        <span>Nhóm thực hiện: Phí Văn Nam, Đỗ Thị Vân Anh, Đỗ Hữu Nghị, Quản Văn Điệp</span>
        <span>Hội đồng đánh giá 2026</span>
      </div>
    </div>

  </div>

  <!-- CONTROLS & NAVIGATION -->
  <div class="controls">
    <button class="ctrl-btn" id="btnPrev" title="Trang trước (Phím ←)">◀</button>
    <span class="slide-count" id="slideCount">1 / 14</span>
    <button class="ctrl-btn" id="btnNext" title="Trang tiếp (Phím →)">▶</button>
    <button class="ctrl-btn" id="btnFullscreen" title="Toàn màn hình (Phím F)">⛶</button>
  </div>

  <script>
    const slides = document.querySelectorAll('.slide');
    const progressBar = document.getElementById('progressBar');
    const slideCount = document.getElementById('slideCount');
    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');
    const btnFullscreen = document.getElementById('btnFullscreen');
    let currentIndex = 0;

    function updateSlide(index) {{
      if (index < 0) index = 0;
      if (index >= slides.length) index = slides.length - 1;
      currentIndex = index;

      slides.forEach((s, idx) => {{
        if (idx === currentIndex) {{
          s.classList.add('active');
        }} else {{
          s.classList.remove('active');
        }}
      }});

      const progress = ((currentIndex + 1) / slides.length) * 100;
      progressBar.style.width = progress + '%';
      slideCount.textContent = (currentIndex + 1) + ' / ' + slides.length;
    }}

    btnPrev.addEventListener('click', () => updateSlide(currentIndex - 1));
    btnNext.addEventListener('click', () => updateSlide(currentIndex + 1));

    btnFullscreen.addEventListener('click', () => {{
      if (!document.fullscreenElement) {{
        document.documentElement.requestFullscreen().catch(() => {{}});
      }} else {{
        document.exitFullscreen().catch(() => {{}});
      }}
    }});

    window.addEventListener('keydown', (e) => {{
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {{
        e.preventDefault();
        updateSlide(currentIndex + 1);
      }} else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
        e.preventDefault();
        updateSlide(currentIndex - 1);
      }} else if (e.key === 'Home') {{
        e.preventDefault();
        updateSlide(0);
      }} else if (e.key === 'End') {{
        e.preventDefault();
        updateSlide(slides.length - 1);
      }} else if (e.key === 'f' || e.key === 'F') {{
        e.preventDefault();
        btnFullscreen.click();
      }}
    }});

    updateSlide(0);
  </script>
</body>
</html>
"""


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    user_guide_path = DOCS_DIR / "huong_dan_su_dung.html"
    presentation_path = DOCS_DIR / "slide_bao_ve_du_an.html"

    print("Generating huong_dan_su_dung.html...")
    guide_html = build_user_guide_html()
    user_guide_path.write_text(guide_html, encoding="utf-8")
    print(f"-> Generated {user_guide_path} ({len(guide_html):,} bytes)")

    print("Generating slide_bao_ve_du_an.html...")
    pres_html = build_defense_presentation_html()
    presentation_path.write_text(pres_html, encoding="utf-8")
    print(f"-> Generated {presentation_path} ({len(pres_html):,} bytes)")


if __name__ == "__main__":
    main()
