import sys
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
import datetime

sys.stdout.reconfigure(encoding='utf-8')

def fill_wbs(src_template_path, dst_path):
    wb = openpyxl.load_workbook(src_template_path)
    ws = wb.active
    
    # 1. Update Title and Headers
    ws['B2'] = "TrafficVision – Work Breakdown Structure (WBS)"
    ws['B8'] = "Project Team Name"
    ws['C8'] = "TrafficVision"
    ws['B9'] = "Project Topic"
    ws['C9'] = "TrafficVision – Hệ thống nhận dạng biển báo giao thông Việt Nam bằng AI"
    
    # Status Legends
    ws['J3'] = "Hoàn thành"
    ws['J4'] = "Đang thực hiện"
    ws['J5'] = "Chậm / cần xử lý"
    
    # Today date
    ws['B7'] = "Today"
    ws['C7'] = datetime.datetime(2026, 10, 3)
    ws['E7'] = datetime.datetime(2026, 10, 3)
    
    # Dates row (Row 13)
    base_dates = [
        datetime.datetime(2026, 9, 28),
        datetime.datetime(2026, 9, 29),
        datetime.datetime(2026, 9, 30),
        datetime.datetime(2026, 10, 1),
        datetime.datetime(2026, 10, 2),
        datetime.datetime(2026, 10, 5),
        datetime.datetime(2026, 10, 6),
        datetime.datetime(2026, 10, 7),
        datetime.datetime(2026, 10, 8),
        datetime.datetime(2026, 10, 9),
        datetime.datetime(2026, 10, 12),
        datetime.datetime(2026, 10, 13),
        datetime.datetime(2026, 10, 14),
        datetime.datetime(2026, 10, 15),
        datetime.datetime(2026, 10, 16),
        datetime.datetime(2026, 10, 19),
        datetime.datetime(2026, 10, 20),
        datetime.datetime(2026, 10, 21),
        datetime.datetime(2026, 10, 22),
        datetime.datetime(2026, 10, 23),
    ]
    for idx, d in enumerate(base_dates):
        ws.cell(13, 11 + idx, d)
        ws.cell(13, 11 + idx).number_format = 'yyyy-mm-dd'

    # Tasks definition
    # (row, indent_col, task_name, start_date, end_date, resp, deliv, status, [days active 1..20])
    tasks = [
        # US-01
        (14, 2, "US-01 – Kiến trúc ứng dụng baseline và Model Registry", 
         datetime.datetime(2026, 9, 27), datetime.datetime(2026, 9, 28),
         "Nam + Điệp", "Baseline ONNX CPU, manifest.json, production", "Hoàn thành", [1, 2]),
        (15, 3, "US-01.01 – Bootstrap mô hình baseline YOLO11n ONNX", 
         datetime.datetime(2026, 9, 27), datetime.datetime(2026, 9, 27),
         "Nam", "Baseline COCO + SHA-256 + ModelRegistry", "Hoàn thành", [1]),
        (16, 4, "US-01.02 – Xây dựng pipeline suy luận ảnh/video và SQLite", 
         datetime.datetime(2026, 9, 27), datetime.datetime(2026, 9, 28),
         "Điệp", "Ảnh/video chú thích, CSV thống kê, CSDL SQLite", "Hoàn thành", [1, 2]),
        (17, 5, "US-01.03 – Giao diện Streamlit đa tab & Cảnh báo baseline", 
         datetime.datetime(2026, 9, 27), datetime.datetime(2026, 9, 28),
         "Điệp + Nam", "6 trang web Streamlit; cảnh báo baseline; settings", "Hoàn thành", [1, 2]),
        
        # US-02
        (18, 2, "US-02 – Dữ liệu 82 lớp biển báo VN và Quality Gate", 
         datetime.datetime(2026, 9, 28), datetime.datetime(2026, 9, 29),
         "Vân Anh + Nghị", "Catalog QCVN 41, Quality Gate, Snapshot, EDA", "Hoàn thành", [1, 2, 3]),
        (19, 3, "US-02.01 – Chuẩn hóa danh mục 82 lớp và nạp dữ liệu", 
         datetime.datetime(2026, 9, 28), datetime.datetime(2026, 9, 28),
         "Vân Anh", "Catalog 82 lớp VN, nạp train/val/test split", "Hoàn thành", [1]),
        (20, 4, "US-02.02 – Cổng Quality Gate 5 tiêu chí & Dataset Repair", 
         datetime.datetime(2026, 9, 28), datetime.datetime(2026, 9, 29),
         "Vân Anh", "Quality Gate 5 tiêu chí chặn rác, script repair.py", "Hoàn thành", [1, 2]),
        (21, 5, "US-02.03 – Phân tích EDA 10.129 ảnh và Snapshot bất biến", 
         datetime.datetime(2026, 9, 29), datetime.datetime(2026, 9, 29),
         "Vân Anh", "Báo cáo EDA, snapshot_20260930_165016, data.yaml", "Hoàn thành", [2, 3]),
        
        # US-03
        (22, 2, "US-03 – Huấn luyện YOLO11, Đánh giá và Đóng gói Candidate", 
         datetime.datetime(2026, 9, 29), datetime.datetime(2026, 10, 2),
         "Nghị + Vân Anh", "Candidate 82 lớp hoàn chỉnh (YOLO11n + YOLO11m)", "Hoàn thành", [2, 3, 4, 5]),
        (23, 3, "US-03.01 – Huấn luyện ngầm 50 epochs & Safe Resume", 
         datetime.datetime(2026, 9, 29), datetime.datetime(2026, 10, 1),
         "Nghị", "Huấn luyện ngầm, workers=0 Windows, best.pt, log", "Hoàn thành", [2, 3, 4]),
        (24, 4, "US-03.02 – Đánh giá độc lập trên tập Test (1.016 ảnh)", 
         datetime.datetime(2026, 10, 1), datetime.datetime(2026, 10, 2),
         "Nghị + Vân Anh", "mAP50=98.03%, F1=96.22%, P=96.16%, R=96.28%", "Hoàn thành", [4, 5]),
        (25, 5, "US-03.03 – Xuất ONNX, Parity Gate & CPU Benchmark", 
         datetime.datetime(2026, 10, 1), datetime.datetime(2026, 10, 2),
         "Nghị + Nam", "ONNX tĩnh diff=0.000854 <= 1e-3, latency/FPS đo đạc", "Hoàn thành", [4, 5]),
        
        # US-04
        (26, 2, "US-04 – Thăng cấp Production, Kiểm thử và Bàn giao", 
         datetime.datetime(2026, 9, 30), datetime.datetime(2026, 10, 3),
         "Cả nhóm", "Production verified, 215 tests xanh, hồ sơ bàn giao", "Hoàn thành", [3, 4, 5, 6, 7, 8, 9, 10]),
        (27, 3, "US-04.01 – Thăng cấp an toàn Safe Atomic Swap & Rollback", 
         datetime.datetime(2026, 10, 1), datetime.datetime(2026, 10, 2),
         "Nam + Nghị", "Thăng cấp YOLO11m lên prod, sao lưu & rollback 1-click", "Hoàn thành", [4, 5]),
        (28, 4, "US-04.02 – Bộ kiểm thử hồi quy tự động 215 tests pytest", 
         datetime.datetime(2026, 9, 30), datetime.datetime(2026, 10, 2),
         "Điệp + Nam", "215/215 tests xanh (213 passed, 2 skipped)", "Hoàn thành", [3, 4, 5]),
        (29, 5, "US-04.03 – Hồ sơ bàn giao, Slide bảo vệ, Q&A và Báo cáo", 
         datetime.datetime(2026, 10, 1), datetime.datetime(2026, 10, 3),
         "Cả nhóm", "HDSD, 14 slides bảo vệ, Cẩm nang Q&A, Báo cáo dự án", "Hoàn thành", [4, 5, 6]),
        
        # US-05
        (30, 2, "US-05 – Định hướng nâng cấp và mở rộng sau bàn giao", 
         datetime.datetime(2026, 10, 12), datetime.datetime(2026, 10, 23),
         "Nam + Nghị", "RTSP camera trực tiếp, cảnh báo giọng nói, GPS", "Đang nghiên cứu", [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]),
    ]
    
    # Styling colors
    green_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
    yellow_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
    mark_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
    
    font_bold = Font(name="Times New Roman", size=11, bold=True)
    font_normal = Font(name="Times New Roman", size=10, bold=False)
    font_mark = Font(name="Times New Roman", size=10, bold=True, color="004085")
    
    thin_border = Border(
        left=Side(style='thin', color='D0D0D0'),
        right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'),
        bottom=Side(style='thin', color='D0D0D0')
    )
    
    # Clear rows 14-35 first
    for r in range(14, 36):
        for c in range(2, 31):
            cell = ws.cell(r, c)
            cell.value = None
            cell.fill = PatternFill(fill_type=None)
            
    for task_info in tasks:
        r, col_indent, tname, sdate, edate, resp, deliv, status, days = task_info
        
        # Task title at indent
        t_cell = ws.cell(r, col_indent, tname)
        t_cell.font = font_bold if col_indent == 2 else font_normal
        
        # Start date
        c_sdate = ws.cell(r, 6, sdate)
        c_sdate.font = font_normal
        c_sdate.number_format = 'yyyy-mm-dd'
        c_sdate.alignment = Alignment(horizontal='center')
        
        # End date
        c_edate = ws.cell(r, 7, edate)
        c_edate.font = font_normal
        c_edate.number_format = 'yyyy-mm-dd'
        c_edate.alignment = Alignment(horizontal='center')
        
        # Responsibility
        c_resp = ws.cell(r, 8, resp)
        c_resp.font = font_normal
        c_resp.alignment = Alignment(horizontal='left')
        
        # Deliverable
        c_deliv = ws.cell(r, 9, deliv)
        c_deliv.font = font_normal
        c_deliv.alignment = Alignment(horizontal='left')
        
        # Status
        c_status = ws.cell(r, 10, status)
        c_status.font = font_bold if status == "Hoàn thành" else font_normal
        c_status.alignment = Alignment(horizontal='center')
        c_status.fill = green_fill if status == "Hoàn thành" else yellow_fill
        
        # Timeline marks D1..D20 (cols 11..30)
        for day_num in range(1, 21):
            cell_mark = ws.cell(r, 10 + day_num)
            cell_mark.border = thin_border
            if day_num in days:
                cell_mark.value = "X"
                cell_mark.alignment = Alignment(horizontal='center', vertical='center')
                cell_mark.font = font_mark
                cell_mark.fill = mark_fill
            else:
                cell_mark.value = None
                
        # apply borders to data columns
        for c in range(2, 11):
            ws.cell(r, c).border = thin_border

    wb.save(dst_path)
    print(f"Successfully saved WBS to: {dst_path}")

if __name__ == "__main__":
    fill_wbs("docs/template/backup_original/Project_Work Breakdown Structure.xlsx", "docs/template/Project_Work Breakdown Structure.xlsx")
