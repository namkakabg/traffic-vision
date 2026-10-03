import sys
import os
import docx
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import io
import zipfile
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

def set_run_font(run, font_name="Times New Roman", font_size=Pt(11.5), bold=False, italic=False, color_rgb=None):
    run.font.name = font_name
    run.font.size = font_size
    run.font.bold = bold
    run.font.italic = italic
    if color_rgb:
        run.font.color.rgb = color_rgb
    # Also set eastAsia and cs in XML to avoid font fallback
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is not None:
        rFonts.set(qn('w:ascii'), font_name)
        rFonts.set(qn('w:hAnsi'), font_name)
        rFonts.set(qn('w:cs'), font_name)
        rFonts.set(qn('w:eastAsia'), font_name)

def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_background(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)

def set_cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement('w:cantSplit'))

def set_table_borders(table, color="B0C4DE"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="{color}"/>
            <w:bottom w:val="single" w:sz="6" w:space="0" w:color="{color}"/>
            <w:left w:val="single" w:sz="6" w:space="0" w:color="{color}"/>
            <w:right w:val="single" w:sz="6" w:space="0" w:color="{color}"/>
            <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E0E6ED"/>
            <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E0E6ED"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def format_action_plan(src_path, dst_path):
    print(f"Loading {src_path}...")
    doc = docx.Document(src_path)
    
    # 1. Update Document Styles to Times New Roman
    for s in doc.styles:
        if hasattr(s, 'font') and s.font:
            s.font.name = "Times New Roman"
            
    # Page setup: A4, standard academic margins (Top 2cm, Bottom 2cm, Left 2.5cm, Right 2cm)
    for section in doc.sections:
        section.top_margin = Inches(0.8)     # ~2.0 cm
        section.bottom_margin = Inches(0.8)  # ~2.0 cm
        section.left_margin = Inches(1.0)    # ~2.54 cm
        section.right_margin = Inches(0.8)   # ~2.0 cm
        
    # 2. Format Header Paragraphs
    # P[3]: "AI Course"
    # P[4]: "Kế hoạch dự án"
    if len(doc.paragraphs) > 3:
        p3 = doc.paragraphs[3]
        p3.text = ""
        p3.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p3.paragraph_format.space_before = Pt(0)
        p3.paragraph_format.space_after = Pt(2)
        r3 = p3.add_run("PHÁT TRIỂN HỆ THỐNG THÔNG MINH – AI COURSE")
        set_run_font(r3, "Times New Roman", Pt(12), bold=True, color_rgb=RGBColor(0x19, 0x3D, 0xB0))
        
    if len(doc.paragraphs) > 4:
        p4 = doc.paragraphs[4]
        p4.text = ""
        p4.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p4.paragraph_format.space_before = Pt(4)
        p4.paragraph_format.space_after = Pt(14)
        r4 = p4.add_run("KẾ HOẠCH HÀNH ĐỘNG DỰ ÁN (ACTION PLAN)")
        set_run_font(r4, "Times New Roman", Pt(22), bold=True, color_rgb=RGBColor(0x19, 0x3D, 0xB0))

    # Helper function to clear and set cell content with strict Times New Roman & Justification
    def populate_cell(cell, paragraphs_data, is_header=False, bg_color=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
        # clear paragraphs
        p0 = cell.paragraphs[0]
        p0.text = ""
        for p_extra in cell.paragraphs[1:]:
            p_extra._element.getparent().remove(p_extra._element)
            
        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
        if bg_color:
            set_cell_background(cell, bg_color)
            
        for idx, p_info in enumerate(paragraphs_data):
            p = p0 if idx == 0 else cell.add_paragraph()
            p.alignment = align
            p.paragraph_format.line_spacing = 1.18
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(4)
            
            if isinstance(p_info, str):
                p_info = [(p_info, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))]
                
            for run_spec in p_info:
                text = run_spec[0]
                bold = run_spec[1] if len(run_spec) > 1 else False
                italic = run_spec[2] if len(run_spec) > 2 else False
                color = run_spec[3] if len(run_spec) > 3 else (RGBColor(0x19, 0x3D, 0xB0) if is_header else RGBColor(0x22, 0x22, 0x22))
                size = run_spec[4] if len(run_spec) > 4 else (Pt(12) if is_header else Pt(11.5))
                
                r = p.add_run(text)
                set_run_font(r, "Times New Roman", size, bold=bold, italic=italic, color_rgb=color)

    def set_cell_width(cell, width_dxa):
        tcPr = cell._tc.get_or_add_tcPr()
        tcW = tcPr.find(qn('w:tcW'))
        if tcW is None:
            tcW = OxmlElement('w:tcW')
            tcPr.append(tcW)
        tcW.set(qn('w:w'), str(width_dxa))
        tcW.set(qn('w:type'), 'dxa')

    def set_full_row(table_row, content_data, is_header=False, bg_color=None, align=WD_ALIGN_PARAGRAPH.LEFT):
        """Merges all cells in the row into a single full-width cell and populates it ONCE."""
        tcs = table_row._tr.findall(qn('w:tc'))
        if len(tcs) > 1:
            merged_cell = table_row.cells[0].merge(table_row.cells[-1])
        else:
            merged_cell = table_row.cells[0]
        set_cell_width(merged_cell, 9100)
        populate_cell(merged_cell, content_data, is_header=is_header, bg_color=bg_color, align=align)
        return merged_cell

    # 3. Format Table 0
    t0 = doc.tables[0]
    t0.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t0, color="193DB0")
    
    # R0: Môn học
    set_cell_width(t0.rows[0].cells[0], 2200)
    set_cell_width(t0.rows[0].cells[1], 6900)
    populate_cell(t0.rows[0].cells[0], [[("Môn học", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5))]], bg_color="F0F4FA", align=WD_ALIGN_PARAGRAPH.LEFT)
    populate_cell(t0.rows[0].cells[1], [[("Phát triển hệ thống thông minh", True, False, RGBColor(0x11, 0x11, 0x11), Pt(11.5))]], align=WD_ALIGN_PARAGRAPH.LEFT)
    
    # R1: Tên nhóm
    set_cell_width(t0.rows[1].cells[0], 2200)
    set_cell_width(t0.rows[1].cells[1], 6900)
    populate_cell(t0.rows[1].cells[0], [[("Tên nhóm", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5))]], bg_color="F0F4FA", align=WD_ALIGN_PARAGRAPH.LEFT)
    populate_cell(t0.rows[1].cells[1], [[("TrafficVision", True, False, RGBColor(0x11, 0x11, 0x11), Pt(11.5))]], align=WD_ALIGN_PARAGRAPH.LEFT)
    
    # R2: Trưởng nhóm/ Các thành viên nhóm
    set_cell_width(t0.rows[2].cells[0], 2200)
    set_cell_width(t0.rows[2].cells[1], 6900)
    populate_cell(t0.rows[2].cells[0], [[("Trưởng nhóm /\nThành viên", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5))]], bg_color="F0F4FA", align=WD_ALIGN_PARAGRAPH.LEFT)
    populate_cell(t0.rows[2].cells[1], [
        [("Phí Văn Nam (Trưởng nhóm)", True, False, RGBColor(0x11, 0x11, 0x11), Pt(11.5))],
        [("Đỗ Thị Vân Anh • Đỗ Hữu Nghị • Quản Văn Điệp", False, False, RGBColor(0x33, 0x33, 0x33), Pt(11.5))]
    ], align=WD_ALIGN_PARAGRAPH.LEFT)
    
    # R3: Tên đề tài
    set_cell_width(t0.rows[3].cells[0], 2200)
    set_cell_width(t0.rows[3].cells[1], 6900)
    populate_cell(t0.rows[3].cells[0], [[("Tên đề tài", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5))]], bg_color="F0F4FA", align=WD_ALIGN_PARAGRAPH.LEFT)
    populate_cell(t0.rows[3].cells[1], [[("TrafficVision – Hệ thống nhận dạng biển báo giao thông Việt Nam bằng AI tối ưu suy luận trên CPU", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5))]], align=WD_ALIGN_PARAGRAPH.LEFT)
    
    # R4: Section Header "Mục tiêu" (Merged 1 cell, non-duplicated)
    set_full_row(t0.rows[4], [[("MỤC TIÊU DỰ ÁN", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(12))]], is_header=True, bg_color="EBF1F8", align=WD_ALIGN_PARAGRAPH.LEFT)
        
    # R5: Mục tiêu content
    muc_tieu = [
        [("1. Nhận dạng chính xác 82 lớp biển báo giao thông Việt Nam: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Xây dựng mô hình thị giác máy tính nhận dạng và định vị chính xác 82 lớp biển báo giao thông đường bộ theo Quy chuẩn kỹ thuật quốc gia QCVN 41:2019/BGTVT trên cả ảnh tĩnh độ phân giải cao và video hành trình.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("2. Tối ưu hóa suy luận trên phần cứng CPU phổ thông: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Đóng gói mô hình dưới dạng ONNX Runtime đồ thị tĩnh 640x640 px, khai thác tập chỉ thị AVX2 đa luồng, đảm bảo tốc độ đáp ứng gần thời gian thực (~15 FPS cho bản Nano) mà không đòi hỏi GPU rời đắt tiền.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("3. Xây dựng quy trình MLOps khép kín và tin cậy: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Thiết lập cổng Quality Gate 5 tiêu chí chặn rác dữ liệu, module Dataset Repair sửa lỗi bounding box, snapshot dữ liệu bất biến, tiến trình huấn luyện ngầm độc lập có Safe Resume, kiểm định sai lệch PyTorch vs ONNX (max_abs_diff <= 1e-3), đóng gói Candidate và thăng cấp an toàn (Safe Atomic Swap) kèm cơ chế Rollback 1-click.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("4. Cung cấp sản phẩm phần mềm hoàn chỉnh: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Xây dựng Web Dashboard Streamlit trực quan, hỗ trợ kéo thả ảnh/video, hiển thị bounding box tiếng Việt chuẩn hóa, thanh tiến trình thời gian thực (@st.fragment), xuất tệp CSV thống kê và lưu lịch sử CSDL SQLite.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))]
    ]
    set_full_row(t0.rows[5], muc_tieu, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        
    # R6: Section Header "Tóm tắt" (Merged 1 cell, non-duplicated)
    set_full_row(t0.rows[6], [[("TÓM TẮT DỰ ÁN", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(12))]], is_header=True, bg_color="EBF1F8", align=WD_ALIGN_PARAGRAPH.LEFT)
        
    # R7: Tóm tắt content
    tom_tat = [
        [("TrafficVision ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("là hệ thống thị giác máy tính thông minh giải quyết bài toán tự động nhận diện biển báo giao thông đường bộ tại Việt Nam. Dự án triển khai mô hình học sâu tiên tiến YOLO11 (Ultralytics) gồm hai cấu hình: ", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5)),
         ("YOLO11m (Medium) ", True, False, RGBColor(0x11, 0x11, 0x11), Pt(11.5)),
         ("cho độ chính xác cao và ", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5)),
         ("YOLO11n (Nano) ", True, False, RGBColor(0x11, 0x11, 0x11), Pt(11.5)),
         ("siêu nhẹ tối ưu độ trễ cho biên. Bộ dữ liệu chuẩn hóa gồm 10.129 ảnh và 19.700 bounding boxes bao phủ 82 lớp biển báo, được kiểm định qua Quality Gate 5 tiêu chí và đóng gói Snapshot bất biến.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("Mô hình được xuất sang định dạng ONNX Runtime đồ thị tĩnh và suy luận tối ưu trên CPU. Kết quả thực nghiệm trên tập kiểm thử độc lập (held-out test split) gồm 1.016 ảnh cho thấy mô hình YOLO11m đạt kết quả vượt bậc: ", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5)),
         ("mAP50 = 98.03%, Precision = 96.16%, Recall = 96.28%, F1-score = 96.22%", True, False, RGBColor(0x28, 0xA7, 0x45), Pt(11.5)),
         (", vượt qua kiểm tra sai số số học PyTorch vs ONNX (max_abs_diff = 0.000854 <= 1e-3) và đã chính thức thăng cấp lên Production. Bản YOLO11n đạt mAP50 = 92.47% với độ trễ CPU chỉ 68.26 ms/ảnh (~14.65 FPS). Hệ thống được bảo chứng độ tin cậy bởi bộ kiểm thử tự động 215 tests, giao diện Web Streamlit đa chức năng và đầy đủ tài liệu kỹ thuật.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))]
    ]
    set_full_row(t0.rows[7], tom_tat, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        
    # R8: Section Header "Phương pháp" (Merged 1 cell, non-duplicated)
    set_full_row(t0.rows[8], [[("PHƯƠNG PHÁP TRIỂN KHAI", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(12))]], is_header=True, bg_color="EBF1F8", align=WD_ALIGN_PARAGRAPH.LEFT)
        
    # R9: Phương pháp content
    phuong_phap = [
        [("• Kiến trúc mô hình: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Sử dụng kiến trúc YOLO11 tiên tiến với cơ chế Attention không gian C2PSA và hàm mất mát phân bố tiêu điểm DFL Loss, giúp phát hiện hiệu quả các biển báo nhỏ ở xa và trong điều kiện ánh sáng phức tạp.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Quản lý chất lượng dữ liệu: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Áp dụng cổng Quality Gate 5 tiêu chí (Corrupt Image, Format Line, Class ID 0-81, BBox Coords [0, 1], Data Leakage SHA-256) kết hợp module Dataset Repair tự động clamping tọa độ và loại bỏ box rỗng trước khi đóng gói Snapshot bất biến.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Huấn luyện ngầm & Khả năng chịu lỗi: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Huấn luyện qua tiến trình nền độc lập (background runner) với cấu hình workers=0 tối ưu trên Windows, hỗ trợ Checkpoint & Safe Resume phục hồi an toàn từ last.pt.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Tối ưu suy luận & Parity Gate: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Xuất mô hình sang ONNX đồ thị tĩnh 640x640, suy luận qua ONNX Runtime CPU với tập lệnh AVX2 đa luồng, kiểm định sai số số học cực đại PyTorch vs ONNX (max_abs_diff <= 1e-3).", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• MLOps Model Registry: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Quản lý phiên bản mô hình qua manifest.json động và mã băm SHA-256; cơ chế Safe Atomic Swap đảm bảo cập nhật mô hình production không gián đoạn dịch vụ cùng khả năng Rollback 1-click tức thì.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))]
    ]
    set_full_row(t0.rows[9], phuong_phap, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        
    for row in t0.rows:
        set_cant_split(row)

    # 4. Format Table 1
    t1 = doc.tables[1]
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t1, color="193DB0")
    
    # R0: Header "Dữ liệu" (Merged 1 cell, non-duplicated)
    set_full_row(t1.rows[0], [[("DỮ LIỆU HUẤN LUYỆN VÀ TIỀN XỬ LÝ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(12))]], is_header=True, bg_color="EBF1F8", align=WD_ALIGN_PARAGRAPH.LEFT)
        
    # R1: Dữ liệu content
    du_lieu = [
        [("• Nguồn dữ liệu: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Bộ dữ liệu star092304/Traffic-sign-detection-VietNam từ Hugging Face kết hợp ảnh chụp thực tế camera hành trình tại Việt Nam, chuẩn hóa theo danh mục 82 lớp biển báo của Quy chuẩn QCVN 41:2019/BGTVT.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Quy mô dữ liệu: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Tổng cộng 10.129 ảnh với 19.700 bounding boxes, phân bổ thành: Tập Train (8.098 ảnh / 15.671 boxes), Tập Val (1.015 ảnh / 2.059 boxes) và Tập Test độc lập (1.016 ảnh / 1.970 boxes).", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Tiền xử lý & Snapshot: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Dữ liệu thô đưa vào staging, vượt qua cổng kiểm định 5 tiêu chí, sửa lỗi tọa độ qua Dataset Repair và đóng gói vào Snapshot bất biến snapshot_20260930_165016 kèm tệp data.yaml và báo cáo EDA toàn diện (phân bố nhãn, kích thước bbox COCO small/medium/large, tỉ lệ khung hình).", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))]
    ]
    set_full_row(t1.rows[1], du_lieu, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        
    # R2: Header "Đầu ra mong muốn đạt được" (Merged 1 cell, non-duplicated)
    set_full_row(t1.rows[2], [[("ĐẦU RA MONG MUỐN ĐẠT ĐƯỢC", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(12))]], is_header=True, bg_color="EBF1F8", align=WD_ALIGN_PARAGRAPH.LEFT)
        
    # R3: Đầu ra content
    dau_ra = [
        [("• Kết quả mô hình AI: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Mô hình Production (YOLO11m) nhận diện 82 lớp biển báo đạt mAP50 = 98.03%, F1-score = 96.22%, sai số số học PyTorch vs ONNX = 0.000854 <= 1e-3. Mô hình Candidate (YOLO11n) đạt mAP50 = 92.47% với độ trễ CPU chỉ 68.26 ms/ảnh (~14.65 FPS).", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Gói sản phẩm phần mềm: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Ứng dụng Web Streamlit hoàn chỉnh cho phép phân tích ảnh và video trực quan, hiển thị nhãn tiếng Việt chuẩn hóa, thanh tiến trình tự động làm mới, xuất tệp CSV thống kê và lưu trữ lịch sử phiên vào CSDL SQLite.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Artifact MLOps & Chất lượng: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Toàn bộ artifact bất biến (Snapshot, Checkpoint, ONNX, Manifest SHA-256, test_metrics.json, benchmark.json); bộ kiểm thử tự động đạt 215/215 tests (213 passed, 2 skipped).", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Lợi ích thực tiễn: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Hỗ trợ đắc lực cho các hệ thống cảnh báo lái xe an toàn (ADAS); tự động hóa công tác khảo sát, số hóa và duy tu biển báo của cơ quan quản lý giao thông đô thị với chi phí phần cứng tối thiểu.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))]
    ]
    set_full_row(t1.rows[3], dau_ra, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        
    # R4: Header "Vai trò của từng thành viên trong nhóm" (Merged 1 cell, non-duplicated)
    set_full_row(t1.rows[4], [[("VAI TRÒ VÀ TRÁCH NHIỆM THÀNH VIÊN", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(12))]], is_header=True, bg_color="EBF1F8", align=WD_ALIGN_PARAGRAPH.LEFT)
        
    # R5: Vai trò content
    vai_tro = [
        [("• Phí Văn Nam (Trưởng nhóm): ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Thiết kế kiến trúc hệ thống tổng thể, MLOps pipeline, Model Registry, cơ chế Safe Atomic Swap & Rollback, tích hợp CSDL SQLite (history.db), điều phối tiến độ và tổng hợp báo cáo dự án.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Đỗ Thị Vân Anh (Kỹ sư Dữ liệu): ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Thu thập, tiền xử lý và chuẩn hóa dữ liệu 82 lớp biển báo theo QCVN 41:2019; xây dựng cổng Quality Gate 5 tiêu chí chặn, module Dataset Repair, phân tích EDA và đóng gói Snapshot bất biến.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Đỗ Hữu Nghị (Kỹ sư AI/ML): ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Cấu hình huấn luyện YOLO11 (Nano và Medium), tối ưu hóa suy luận ONNX trên CPU, kiểm tra sai số số học PyTorch vs ONNX, benchmark độ trễ/FPS phần cứng và đóng gói Model Candidate.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Quản Văn Điệp (Kỹ sư Fullstack / QA): ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Phát triển Web Dashboard Streamlit đa chức năng, xử lý luồng đa phương tiện ảnh/video, cơ chế cập nhật tiến trình thời gian thực (@st.fragment), xây dựng bộ kiểm thử tự động 215 tests và hoàn thiện tài liệu hướng dẫn.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))],
        [("• Trách nhiệm chung: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Thẩm định chéo dữ liệu, đánh giá kết quả thực nghiệm, tham gia diễn tập bảo vệ đồ án và cam kết tính trung thực 100% của mọi số liệu trích xuất từ artifact.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))]
    ]
    set_full_row(t1.rows[5], vai_tro, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        
    for row in t1.rows:
        set_cant_split(row)

    # 5. Format Table 2
    t2 = doc.tables[2]
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t2, color="193DB0")
    
    # R0: Header "Tóm tắt lịch trình" (Merged 1 cell, non-duplicated)
    set_full_row(t2.rows[0], [[("TÓM TẮT LỊCH TRÌNH THỰC HIỆN", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(12))]], is_header=True, bg_color="EBF1F8", align=WD_ALIGN_PARAGRAPH.LEFT)
        
    # R1: Lịch trình content
    lich_trinh = [
        [("• Tuần 1 (28/09 – 02/10/2026) – Khởi tạo Baseline & Nền tảng MLOps: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Xây dựng khung ứng dụng Streamlit end-to-end; tích hợp mô hình YOLO11n ONNX baseline trên CPU; thiết kế Model Registry, SQLite history; hoàn thiện catalog 82 lớp biển báo Việt Nam, cổng Quality Gate 5 tiêu chí, module Dataset Repair, đóng gói snapshot 10.129 ảnh và xuất báo cáo EDA. ", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5)),
         ("(Hoàn thành 100%)", True, False, RGBColor(0x28, 0xA7, 0x45), Pt(11.5))],
        [("• Tuần 2 (05/10 – 09/10/2026) – Huấn luyện chuyên sâu & Tối ưu hóa: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Hoàn thiện Training Engine ngầm với tính năng Safe Resume; huấn luyện 50 epochs cho cả hai cấu hình YOLO11n và YOLO11m; xuất mô hình ONNX đồ thị tĩnh [1, 3, 640, 640]; kiểm định sai số số học PyTorch vs ONNX (max_abs_diff <= 1e-3); đo đạc Benchmark CPU FPS và Latency; đóng gói Candidate hoàn chỉnh. ", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5)),
         ("(Hoàn thành 100%)", True, False, RGBColor(0x28, 0xA7, 0x45), Pt(11.5))],
        [("• Tuần 3 (12/10 – 16/10/2026) – Đánh giá Độc lập, Thăng cấp & UAT: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Đánh giá mô hình trên tập kiểm thử độc lập 1.016 ảnh (YOLO11m đạt mAP50 = 98.03%, F1 = 96.22%); thực hiện Safe Atomic Swap thăng cấp YOLO11m lên Production; kiểm thử cơ chế sao lưu tự động và Rollback 1-click; kiểm thử chấp nhận người dùng (UAT) trên ảnh thực tế và video camera hành trình. ", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5)),
         ("(Hoàn thành 100%)", True, False, RGBColor(0x28, 0xA7, 0x45), Pt(11.5))],
        [("• Tuần 4 (19/10 – 23/10/2026) – Kiểm thử toàn diện & Bàn giao: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Chạy bộ kiểm thử tự động hoàn chỉnh 215 tests (213 passed, 2 skipped); hoàn thiện hồ sơ bàn giao gồm Sổ tay Hướng dẫn sử dụng, Slide thuyết trình bảo vệ (14 slides), Cẩm nang Q&A theo 4 thành viên, Tài liệu kỹ thuật huấn luyện chuyên sâu và Báo cáo dự án cuối khóa. ", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5)),
         ("(Hoàn thành 100%)", True, False, RGBColor(0x28, 0xA7, 0x45), Pt(11.5))],
        [("• Giai đoạn mở rộng sau bàn giao: ", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(11.5)),
         ("Nghiên cứu tích hợp luồng RTSP camera hành trình trực tiếp thời gian thực, phát triển module cảnh báo giọng nói tiếng Việt (Text-to-Speech) và gắn tọa độ vị trí biển báo lên bản đồ số GPS.", False, False, RGBColor(0x22, 0x22, 0x22), Pt(11.5))]
    ]
    set_full_row(t2.rows[1], lich_trinh, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        
    # R2: Header "Nhận xét của giáo viên" (Merged 1 cell, non-duplicated)
    set_full_row(t2.rows[2], [[("NHẬN XÉT VÀ ĐÁNH GIÁ CỦA GIẢNG VIÊN", True, False, RGBColor(0x19, 0x3D, 0xB0), Pt(12))]], is_header=True, bg_color="EBF1F8", align=WD_ALIGN_PARAGRAPH.LEFT)
        
    # R3: Nhận xét content
    nhan_xet = [
        [("(Dành cho giảng viên ghi ý kiến nhận xét và đánh giá kế hoạch hành động của nhóm sinh viên)", False, True, RGBColor(0x77, 0x77, 0x77), Pt(11.5))],
        [("\n\n\n\n", False, False, RGBColor(0x77, 0x77, 0x77), Pt(11.5))]
    ]
    set_full_row(t2.rows[3], nhan_xet, align=WD_ALIGN_PARAGRAPH.LEFT)
        
    for row in t2.rows:
        set_cant_split(row)

    # Enforce table centering and width
    for tbl in doc.tables:
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = tbl._tbl.tblPr
        tblW = tblPr.find(qn('w:tblW'))
        if tblW is not None:
            tblW.set(qn('w:w'), '9100')
            tblW.set(qn('w:type'), 'dxa')

    # Enforce Times New Roman on every run in the document using native oxml
    for r in doc._element.xpath('.//w:r'):
        rPr = r.get_or_add_rPr()
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = OxmlElement('w:rFonts')
            rPr.insert(0, rFonts)
        rFonts.set(qn('w:ascii'), 'Times New Roman')
        rFonts.set(qn('w:hAnsi'), 'Times New Roman')
        rFonts.set(qn('w:cs'), 'Times New Roman')
        rFonts.set(qn('w:eastAsia'), 'Times New Roman')

    # Also enforce Times New Roman on all styles
    for s in doc.styles:
        if hasattr(s, 'font') and s.font:
            s.font.name = "Times New Roman"

    doc.save(dst_path)
    print(f"Successfully reformatted Action Plan to: {dst_path}")

if __name__ == "__main__":
    format_action_plan("docs/template/backup_original/Project_Action Plan.docx", "docs/template/Project_Action Plan.docx")
