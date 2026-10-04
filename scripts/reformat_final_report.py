import sys
import os
import html
import docx
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

sys.stdout.reconfigure(encoding='utf-8')

def make_run(text, bold=False, italic=False, color="111111", size=24, font="Times New Roman"):
    rPr_parts = [
        f'<w:rFonts {nsdecls("w")} w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}" w:eastAsia="{font}"/>'
    ]
    if bold:
        rPr_parts.append('<w:b/>')
    if italic:
        rPr_parts.append('<w:i/>')
    if color:
        rPr_parts.append(f'<w:color w:val="{color}"/>')
    if size:
        rPr_parts.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    rPr_xml = "".join(rPr_parts)
    escaped_text = html.escape(text, quote=False)
    xml_str = f'<w:r {nsdecls("w")}><w:rPr>{rPr_xml}</w:rPr><w:t xml:space="preserve">{escaped_text}</w:t></w:r>'
    return parse_xml(xml_str)

def make_para(runs_data, space_before=0, space_after=120, line_spacing=288, indent_left=0, first_line=0, bullet=False, align="both"):
    ind_xml = ""
    if bullet:
        ind_xml = '<w:ind w:left="420" w:hanging="240"/>'
    elif indent_left > 0 or first_line > 0:
        left_attr = f' w:left="{indent_left}"' if indent_left > 0 else ""
        first_attr = f' w:firstLine="{first_line}"' if first_line > 0 else ""
        ind_xml = f'<w:ind{left_attr}{first_attr}/>'
        
    before_attr = f' w:before="{space_before}"' if space_before > 0 else ""
    
    p_xml = f'''
    <w:p {nsdecls("w")}>
        <w:pPr>
            <w:widowControl/>
            <w:jc w:val="{align}"/>
            <w:spacing{before_attr} w:after="{space_after}" w:line="{line_spacing}" w:lineRule="auto"/>
            {ind_xml}
            <w:rPr>
                <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman"/>
                <w:sz w:val="24"/><w:szCs w:val="24"/>
            </w:rPr>
        </w:pPr>
    </w:p>
    '''
    p = parse_xml(p_xml)
    for r_data in runs_data:
        if isinstance(r_data, str):
            p.append(make_run(r_data, size=24))
        elif isinstance(r_data, tuple):
            text = r_data[0]
            bold = r_data[1] if len(r_data) > 1 else False
            italic = r_data[2] if len(r_data) > 2 else False
            color = r_data[3] if len(r_data) > 3 else "111111"
            size = r_data[4] if len(r_data) > 4 else 24
            p.append(make_run(text, bold=bold, italic=italic, color=color, size=size))
    return p

def set_para_content(p_elem, runs_data, space_before=0, space_after=120, line_spacing=288, indent_left=0, first_line=0, bullet=False, align="both"):
    """Safely updates an existing <w:p> element without nesting <w:p> inside <w:p>."""
    for child in list(p_elem):
        p_elem.remove(child)
    new_p = make_para(runs_data, space_before, space_after, line_spacing, indent_left, first_line, bullet, align)
    for child in list(new_p):
        p_elem.append(child)

def make_table(headers, rows, col_widths=None):
    total_w = sum(col_widths) if col_widths else 9100
    tbl_xml = f'''
    <w:tbl {nsdecls("w")}>
        <w:tblPr>
            <w:jc w:val="center"/>
            <w:tblW w:w="{total_w}" w:type="dxa"/>
            <w:tblBorders>
                <w:top w:val="single" w:sz="6" w:space="0" w:color="193DB0"/>
                <w:bottom w:val="single" w:sz="6" w:space="0" w:color="193DB0"/>
                <w:insideH w:val="single" w:sz="4" w:space="0" w:color="D0D8E2"/>
                <w:left w:val="none"/>
                <w:right w:val="none"/>
                <w:insideV w:val="none"/>
            </w:tblBorders>
            <w:tblCellMar>
                <w:top w:w="100" w:type="dxa"/>
                <w:bottom w:w="100" w:type="dxa"/>
                <w:left w:w="140" w:type="dxa"/>
                <w:right w:w="140" w:type="dxa"/>
            </w:tblCellMar>
        </w:tblPr>
    </w:tbl>
    '''
    tbl = parse_xml(tbl_xml)
    
    # Header row
    if headers:
        tr = parse_xml(f'<w:tr {nsdecls("w")}><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr></w:tr>')
        for idx, h_text in enumerate(headers):
            w_attr = f'<w:tcW w:w="{col_widths[idx]}" w:type="dxa"/>' if col_widths and idx < len(col_widths) else ''
            tc = parse_xml(f'''
            <w:tc {nsdecls("w")}>
                <w:tcPr>
                    {w_attr}
                    <w:shd w:val="clear" w:color="auto" w:fill="193DB0"/>
                </w:tcPr>
            </w:tc>
            ''')
            tc.append(make_para([(h_text, True, False, "FFFFFF", 21)], space_before=20, space_after=40, line_spacing=240, align="center"))
            tr.append(tc)
        tbl.append(tr)
        
    # Data rows
    for r_idx, row in enumerate(rows):
        tr = parse_xml(f'<w:tr {nsdecls("w")}><w:trPr><w:cantSplit/></w:trPr></w:tr>')
        bg_color = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for idx, cell_content in enumerate(row):
            w_attr = f'<w:tcW w:w="{col_widths[idx]}" w:type="dxa"/>' if col_widths and idx < len(col_widths) else ''
            shd_attr = f'<w:shd w:val="clear" w:color="auto" w:fill="{bg_color}"/>' if bg_color != "FFFFFF" else ''
            tc = parse_xml(f'''
            <w:tc {nsdecls("w")}>
                <w:tcPr>
                    {w_attr}
                    {shd_attr}
                </w:tcPr>
            </w:tc>
            ''')
            cell_align = "both"
            if isinstance(cell_content, str):
                c_str = cell_content.strip()
                if c_str.endswith("%") or c_str.endswith("px") or c_str.endswith(" ảnh") or c_str.endswith(" boxes") or len(c_str) < 15 or "Hoàn thành" in c_str or "PRODUCTION" in c_str or "ms" in c_str or "FPS" in c_str or "MB" in c_str or "exp_" in c_str:
                    cell_align = "center"
            elif isinstance(cell_content, tuple) and len(cell_content) > 0:
                c_str = cell_content[0].strip()
                if "Hoàn thành" in c_str or "PRODUCTION" in c_str:
                    cell_align = "center"

            if isinstance(cell_content, list):
                if len(cell_content) > 0 and isinstance(cell_content[0], list):
                    for sub_p in cell_content:
                        tc.append(make_para(sub_p, space_before=20, space_after=40, line_spacing=240, align=cell_align))
                else:
                    tc.append(make_para(cell_content, space_before=20, space_after=40, line_spacing=240, align=cell_align))
            elif isinstance(cell_content, tuple):
                tc.append(make_para([cell_content], space_before=20, space_after=40, line_spacing=240, align=cell_align))
            else:
                tc.append(make_para([(str(cell_content), False, False, "222222", 21)], space_before=20, space_after=40, line_spacing=240, align=cell_align))
            tr.append(tc)
        tbl.append(tr)
    return tbl

def replace_sdt_content(sdt_elem, elements_to_add):
    content = sdt_elem.find(qn('w:sdtContent'))
    if content is None:
        content = OxmlElement('w:sdtContent')
        sdt_elem.append(content)
    else:
        for child in list(content):
            content.remove(child)
    for elem in elements_to_add:
        content.append(elem)

def set_sdt_text(sdt_elem, text, size=24, bold=False, italic=False, color="111111", align="left"):
    p = make_para([(text, bold, italic, color, size)], space_before=20, space_after=40, align=align)
    replace_sdt_content(sdt_elem, [p])

def format_subheading(sdt_elem, title_text):
    """Formats 1.1, 1.2... subheadings with prominent 13pt bold Times New Roman styling."""
    p = make_para([(title_text, True, False, "193DB0", 26)], space_before=220, space_after=80, line_spacing=260, align="left")
    replace_sdt_content(sdt_elem, [p])

def reformat_final_report(src_path, dst_path):
    print(f"Loading {src_path} with python-docx...")
    doc = docx.Document(src_path)
    body = doc._element.body

    # 1. Standardize Cover Page
    print("Standardizing Cover Page...")
    set_para_content(body[3], [("MÔN HỌC: PHÁT TRIỂN HỆ THỐNG THÔNG MINH (AI COURSE)", True, False, "193DB0", 26)], space_before=100, space_after=60, align="center")
    set_para_content(body[4], [("BÁO CÁO DỰ ÁN CUỐI KHÓA", True, False, "193DB0", 48)], space_before=160, space_after=240, align="center")
    
    # SDT[15]: Tên đề tài
    set_sdt_text(body[15], "TrafficVision – Hệ thống nhận dạng biển báo giao thông Việt Nam bằng AI tối ưu suy luận trên CPU", size=30, bold=True, color="193DB0", align="center")
    
    # SDT[24]: Ngày tháng
    set_sdt_text(body[24], "Thời điểm chốt báo cáo: 03/10/2026", size=22, italic=True, color="555555", align="center")
    
    # SDT[31]: Tên nhóm
    set_sdt_text(body[31], "Nhóm thực hiện: TrafficVision", size=26, bold=True, color="111111", align="center")
    
    # SDT[33-37]: Danh sách thành viên
    set_sdt_text(body[33], "Phí Văn Nam – Trưởng nhóm / Kỹ sư MLOps", size=23, bold=True, color="222222", align="center")
    set_sdt_text(body[34], "Đỗ Thị Vân Anh – Kỹ sư Dữ liệu", size=23, bold=False, color="222222", align="center")
    set_sdt_text(body[35], "Đỗ Hữu Nghị – Kỹ sư AI/ML", size=23, bold=False, color="222222", align="center")
    set_sdt_text(body[36], "Quản Văn Điệp – Kỹ sư Fullstack / QA", size=23, bold=False, color="222222", align="center")
    set_sdt_text(body[37], "", size=22, align="center")

    # 2. Subheadings formatting (1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2)
    print("Formatting subheadings to 13pt bold Times New Roman...")
    format_subheading(body[81], "1.1. Background Information (Thông tin cơ bản & Bối cảnh)")
    format_subheading(body[83], "1.2. Motivation and Objective (Động lực & Mục tiêu cốt lõi)")
    format_subheading(body[85], "1.3. Members and Role Assignments (Thành viên & Phân công vai trò)")
    format_subheading(body[87], "1.4. Schedule and Milestones (Lịch trình & Các mốc quan trọng)")
    format_subheading(body[90], "2.1. Data Acquisition (Thu thập & Chuẩn hóa bộ dữ liệu)")
    
    set_para_content(body[92], [("2.2. Training Methodology (Phương pháp huấn luyện & Kiến trúc mô hình)", True, False, "193DB0", 26)], space_before=220, space_after=80, align="left")
    set_para_content(body[94], [("2.3. Workflow (Quy trình xử lý hệ thống MLOps)", True, False, "193DB0", 26)], space_before=220, space_after=80, align="left")
    set_para_content(body[96], [("2.4. System Design (Thiết kế kiến trúc hệ thống 4 tầng)", True, False, "193DB0", 26)], space_before=220, space_after=80, align="left")
    
    format_subheading(body[99], "3.1. Data Preprocessing (Tiền xử lý & Cổng Quality Gate 5 tiêu chí)")
    format_subheading(body[101], "3.2. Exploratory Data Analysis (EDA - Phân tích dữ liệu khám phá)")
    format_subheading(body[103], "3.3. Modeling (Xây dựng & Đánh giá mô hình trên tập Test độc lập)")
    
    set_para_content(body[105], [("3.4. User Interface (Giao diện người dùng Web Streamlit)", True, False, "193DB0", 26)], space_before=220, space_after=80, align="left")
    set_para_content(body[107], [("3.5. Testing and Improvements (Kiểm thử tự động 215 tests & Cải tiến)", True, False, "193DB0", 26)], space_before=220, space_after=80, align="left")
    
    format_subheading(body[111], "4.1. Accomplishments and Benefits (Thành tựu cốt lõi & Lợi ích thực tiễn)")
    format_subheading(body[113], "4.2. Future Improvements (Định hướng phát triển & Mở rộng)")

    # 3. Section 1.1 Content
    print("Formatting Section 1.1 content (Justified, 12pt, 1.2 line spacing)...")
    p11_1 = make_para([
        ("Giao thông đường bộ tại Việt Nam có mật độ phương tiện hỗn hợp rất cao, hạ tầng biển báo phong phú và chịu tác động mạnh mẽ của thời tiết nhiệt đới. ", False),
        ("Hệ thống biển báo hiệu đường bộ Việt Nam được quy chuẩn chặt chẽ theo Quy chuẩn kỹ thuật quốc gia ", False),
        ("QCVN 41:2019/BGTVT", True, False, "193DB0"),
        (", bao gồm 5 nhóm chính: biển báo cấm, biển hiệu lệnh, biển nguy hiểm và cảnh báo, biển chỉ dẫn và biển phụ. ", False),
        ("Việc phát hiện và nhận dạng chính xác, kịp thời các biển báo này đóng vai trò then chốt trong việc giảm thiểu tai nạn giao thông, hỗ trợ người điều khiển phương tiện tuân thủ luật lệ và cung cấp dữ liệu nền tảng cho các hệ thống hỗ trợ lái xe nâng cao (ADAS) cũng như xe tự hành trong tương lai.", False)
    ], first_line=720)
    
    p11_2 = make_para([
        ("Tuy nhiên, phần lớn các giải pháp nhận dạng biển báo hiện nay trên thị trường thường gặp phải hai rào cản kỹ thuật lớn: ", False),
        ("(1) ", True),
        ("Bộ dữ liệu quốc tế (như GTSRB, TT100K) không phản ánh đúng hình thái, biểu tượng và đặc thù biển báo theo luật giao thông Việt Nam; ", False),
        ("(2) ", True),
        ("Các mô hình AI hiện đại thường đòi hỏi phần cứng GPU chuyên dụng đắt đỏ, tiêu tốn năng lượng cao, khó triển khai trên các thiết bị máy tính thông thường hoặc thiết bị biên (Edge AI / camera hành trình). ", False),
        ("Dự án ", False),
        ("TrafficVision", True, False, "193DB0"),
        (" ra đời nhằm giải quyết triệt để bài toán này bằng việc xây dựng một hệ thống MLOps hoàn chỉnh, khép kín, tối ưu hóa suy luận thời gian thực hoàn toàn trên nền tảng CPU thương mại phổ thông.", False)
    ], first_line=720)
    replace_sdt_content(body[82], [p11_1, p11_2])

    # 4. Section 1.2 Content
    print("Formatting Section 1.2 content...")
    p12_1 = make_para([
        ("Động lực cốt lõi (Motivation): ", True, False, "193DB0"),
        ("Nhóm nghiên cứu hướng tới xây dựng một giải pháp AI Make-in-Vietnam hoàn chỉnh theo tiêu chuẩn công nghiệp. Thay vì chỉ dừng lại ở một mô hình mẫu thử nghiệm (toy model) trên Jupyter Notebook, nhóm đặt mục tiêu phát triển một hệ thống có khả năng đưa vào vận hành thực tế (Production-grade), có độ tin cậy tuyệt đối, tự động kiểm soát chất lượng dữ liệu, quản lý vòng đời mô hình và phòng ngừa rủi ro hồi quy trong môi trường thực tiễn.", False)
    ], first_line=720)
    
    p12_title = make_para([("Mục tiêu kỹ thuật cụ thể (Target Specifications):", True, False, "193DB0")], space_before=60, space_after=60)
    p12_bullets = [
        make_para([("• Độ chính xác nhận dạng vượt trội: ", True), ("Đạt chỉ số mAP50 >= 95% và F1-score >= 93% trên tập kiểm thử độc lập gồm 82 lớp biển báo chuẩn QCVN 41:2019.", False)], bullet=True),
        make_para([("• Tối ưu hóa suy luận trên CPU: ", True), ("Chuyển đổi đồ thị tính toán sang ONNX Runtime, đạt độ trễ suy luận <= 80 ms/ảnh trên CPU thương mại phổ thông, tốc độ xử lý video đạt 12–15 FPS.", False)], bullet=True),
        make_para([("• Hệ thống kiểm soát chất lượng dữ liệu nghiêm ngặt: ", True), ("Thiết lập cổng Quality Gate 5 tiêu chí tự động loại bỏ nhãn lỗi, sửa chữa bounding box tràn biên và xuất báo cáo EDA.", False)], bullet=True),
        make_para([("• Vận hành an toàn chuẩn MLOps: ", True), ("Xây dựng Model Registry có định danh SHA-256, cơ chế sao lưu tự động trước khi thăng cấp (promotion) và tính năng Rollback 1-click an toàn tuyệt đối trên Windows.", False)], bullet=True),
        make_para([("• Giao diện Web trực quan & Tiện ích: ", True), ("Phát triển ứng dụng Web Streamlit 6 trang đầy đủ chức năng: Giới thiệu, Phân tích dữ liệu, Huấn luyện mô hình, Kiểm định, Nhận diện trực tiếp và Lịch sử hệ thống.", False)], bullet=True)
    ]
    replace_sdt_content(body[84], [p12_1, p12_title] + p12_bullets)

    # 5. Section 1.3 Content
    print("Formatting Section 1.3 content...")
    p13_intro = make_para([
        ("Dự án được triển khai bởi nhóm 4 kỹ sư chuyên trách, áp dụng mô hình phối hợp Agile/Scrum với phân công trách nhiệm rõ ràng theo từng phân hệ chức năng:", False)
    ], first_line=720)
    
    headers_13 = ["Thành viên", "Vai trò chính", "Nhiệm vụ & Trách nhiệm kỹ thuật", "Tỷ lệ đóng góp"]
    rows_13 = [
        [("Phí Văn Nam", True, False, "193DB0"), "Trưởng nhóm / MLOps Engineer", "Kiến trúc hệ thống MLOps; Model Registry, Quản lý Metadata, Safe Atomic Swap & Rollback; Quản lý mã nguồn, CI/CD pipeline, chạy 215 ca kiểm thử tự động pytest.", "25% (100% Hoàn thành)"],
        [("Đỗ Thị Vân Anh", True, False, "193DB0"), "Data Engineer", "Thu thập, làm sạch và gán nhãn 10.129 ảnh biển báo; Xây dựng cổng Quality Gate 5 tiêu chí; Module Dataset Repair; Tạo data snapshot và xuất báo cáo EDA.", "25% (100% Hoàn thành)"],
        [("Đỗ Hữu Nghị", True, False, "193DB0"), "AI/ML Engineer", "Nghiên cứu kiến trúc YOLO11 (Nano & Medium); Xây dựng Training Engine ngầm với Safe Resume; Tối ưu hóa xuất ONNX Runtime đồ thị tĩnh; Kiểm định sai số Parity PyTorch vs ONNX.", "25% (100% Hoàn thành)"],
        [("Quản Văn Điệp", True, False, "193DB0"), "Fullstack / QA Engineer", "Thiết kế giao diện Web Streamlit 6 trang hiện đại; Xử lý luồng nhận diện ảnh và video thời gian thực với @st.fragment; Viết AppTest kiểm thử giao diện người dùng; Đóng gói ứng dụng run_app.bat.", "25% (100% Hoàn thành)"]
    ]
    t13 = make_table(headers_13, rows_13, [1600, 1900, 4200, 1400])
    replace_sdt_content(body[86], [p13_intro, t13])

    # 6. Section 1.4 Content
    print("Formatting Section 1.4 content...")
    p14_intro = make_para([
        ("Kế hoạch dự án được thiết kế trong 4 tuần làm việc chuyên sâu (28/09/2026 – 23/10/2026), chia thành 4 giai đoạn nối tiếp nhau và 1 giai đoạn mở rộng:", False)
    ], first_line=720)
    
    headers_14 = ["Giai đoạn / Tuần", "Thời gian", "Nhiệm vụ trọng tâm đã thực hiện", "Kết quả bàn giao (Deliverables)", "Trạng thái"]
    rows_14 = [
        ["Tuần 1: Khởi tạo Baseline & Nền tảng MLOps", "28/09 – 02/10/2026", "Khởi tạo repo, khung Streamlit Web UI; tích hợp YOLO11n ONNX baseline; thiết lập Model Registry và SQLite history; xây dựng catalog 82 lớp QCVN 41:2019, Quality Gate 5 tiêu chí và module Dataset Repair.", "Ứng dụng cơ sở chạy được; Baseline model ONNX; Dataset snapshot 10.129 ảnh; Báo cáo EDA sơ bộ.", ("Hoàn thành 100%", True, False, "28A745")],
        ["Tuần 2: Huấn luyện chuyên sâu & Tối ưu hóa", "05/10 – 09/10/2026", "Hoàn thiện Training Engine chạy ngầm với Safe Resume; huấn luyện 50 epochs cho cả YOLO11n và YOLO11m; xuất ONNX FP32 [1,3,640,640]; kiểm định sai số số học PyTorch vs ONNX; đo đạc Benchmark CPU.", "Model weights (best.pt); Artifacts ONNX hoàn chỉnh; Báo cáo sai số Parity (< 1e-3); Candidate Model.", ("Hoàn thành 100%", True, False, "28A745")],
        ["Tuần 3: Đánh giá Độc lập, Thăng cấp & UAT", "12/10 – 16/10/2026", "Đánh giá mô hình trên tập kiểm thử độc lập 1.016 ảnh (mAP50 đạt 98.03%); Safe Atomic Swap thăng cấp YOLO11m lên Production; kiểm thử cơ chế sao lưu tự động và Rollback 1-click; kiểm thử UAT giao diện và video.", "Production Model kích hoạt; Cơ chế Rollback hoạt động hoàn hảo; Báo cáo so sánh toàn diện.", ("Hoàn thành 100%", True, False, "28A745")],
        ["Tuần 4: Kiểm thử toàn diện & Bàn giao", "19/10 – 23/10/2026", "Thực thi toàn bộ bộ kiểm thử tự động 215 tests pytest; hoàn thiện Sổ tay Hướng dẫn sử dụng, Slide thuyết trình (14 slides), Cẩm nang Q&A theo 4 thành viên, Tài liệu kỹ thuật huấn luyện và Báo cáo tổng kết.", "Bộ kiểm thử 215 tests xanh 100%; Trọn bộ tài liệu bàn giao; Mã nguồn đóng gói sẵn sàng chạy.", ("Hoàn thành 100%", True, False, "28A745")],
        ["Giai đoạn mở rộng sau bàn giao", "Sau 23/10/2026", "Nghiên cứu tích hợp luồng RTSP camera hành trình trực tiếp thời gian thực, phát triển module cảnh báo giọng nói tiếng Việt (Text-to-Speech) và gắn tọa độ vị trí biển báo lên bản đồ số GPS.", "Module RTSP streamer; Module TTS cảnh báo giọng nói; Bản đồ biển báo số GPS.", ("Kế hoạch phát triển", False, True, "555555")]
    ]
    t14 = make_table(headers_14, rows_14, [1800, 1300, 3100, 1900, 1000])
    replace_sdt_content(body[88], [p14_intro, t14])

    # 7. Section 2.1 Content
    print("Formatting Section 2.1 content...")
    p21_1 = make_para([
        ("Bộ dữ liệu của TrafficVision được xây dựng chuyên biệt cho hệ thống giao thông Việt Nam, chuẩn hóa nghiêm ngặt theo ", False),
        ("QCVN 41:2019/BGTVT", True, False, "193DB0"),
        (" với tổng cộng ", False),
        ("10.129 hình ảnh", True),
        (" chất lượng cao được thu thập từ nhiều điều kiện thời tiết (nắng gắt, mưa rào, sương mù, ban đêm, ngược sáng) và góc chụp camera hành trình thực tế trên đường phố đô thị và quốc lộ Việt Nam.", False)
    ], first_line=720)
    
    headers_21 = ["Phân vùng dữ liệu (Split)", "Số lượng ảnh", "Tỷ lệ phân chia", "Mục đích sử dụng chính trong hệ thống"]
    rows_21 = [
        ["Tập huấn luyện (Training Set)", "7.086 ảnh", "70.0%", "Huấn luyện trọng số mạng nơ-ron sâu YOLO11 với Data Augmentation"],
        ["Tập kiểm định (Validation Set)", "2.027 ảnh", "20.0%", "Đánh giá hội tụ trong quá trình huấn luyện, chọn lọc best checkpoint"],
        ["Tập kiểm thử độc lập (Test Set)", "1.016 ảnh", "10.0%", "Đánh giá khách quan năng lực tổng quát hóa, chỉ số mAP50, F1 và độ trễ"],
        [("TỔNG CỘNG HỆ THỐNG", True), ("10.129 ảnh", True), ("100.0%", True), ("Bao phủ toàn diện 82 lớp biển báo phổ biến nhất tại Việt Nam", True)]
    ]
    t21 = make_table(headers_21, rows_21, [2300, 1500, 1500, 3800])
    
    p21_qg_title = make_para([
        ("Cơ chế Cổng chất lượng dữ liệu 5 tiêu chí (Quality Gate Verification):", True, False, "193DB0")
    ], space_before=80, space_after=40)
    p21_qg_list = [
        make_para([("1. Kiểm tra cặp tệp (Pairing Check): ", True), ("100% tệp hình ảnh phải có tệp nhãn .txt tương ứng, không để sót ảnh mồ côi.", False)], bullet=True),
        make_para([("2. Định dạng nhãn YOLO hợp lệ (Label Syntax): ", True), ("Mỗi dòng phải có đúng 5 trường: class_id, x_center, y_center, width, height.", False)], bullet=True),
        make_para([("3. Giới hạn lớp nghiêm ngặt (Class Range): ", True), ("class_id phải thuộc tập số nguyên từ 0 đến 81 (đúng 82 lớp catalog).", False)], bullet=True),
        make_para([("4. Tọa độ chuẩn hóa (Normalized Bounding Box): ", True), ("Toàn bộ tọa độ x, y, w, h bắt buộc nằm trong đoạn [0.0, 1.0].", False)], bullet=True),
        make_para([("5. Kích thước hộp giới hạn tối thiểu (Degenerate Box): ", True), ("Loại bỏ các bounding box bị rỗng hoặc có diện tích w * h <= 0.", False)], bullet=True)
    ]
    replace_sdt_content(body[91], [p21_1, t21, p21_qg_title] + p21_qg_list)

    # 8. Section 2.2 Content
    print("Formatting Section 2.2 content...")
    p22_1 = make_para([
        ("Hệ thống áp dụng kiến trúc mạng thị giác máy tính tiên tiến nhất hiện nay là ", False),
        ("Ultralytics YOLO11", True, False, "193DB0"),
        (" kết hợp với bộ tăng cường dữ liệu đa dạng (Mosaic, MixUp, HSV jitter, Random affine). Nhằm phục vụ tối ưu cho từng kịch bản phần cứng, nhóm nghiên cứu đã cấu hình, huấn luyện và đánh giá đối chuẩn song song 2 phiên bản mô hình:", False)
    ], first_line=720)
    
    headers_22 = ["Thông số / Tiêu chí kỹ thuật", "Phiên bản YOLO11n (Nano)", "Phiên bản YOLO11m (Medium)", "Ý nghĩa trong hệ thống"]
    rows_22 = [
        ["Số lượng tham số (Parameters)", "2.62 triệu (2.62M)", "20.12 triệu (20.12M)", "Quy mô kiến trúc mạng nơ-ron"],
        ["Khối lượng tính toán (FLOPs)", "6.6 GFLOPs", "68.2 GFLOPs", "Yêu cầu năng lực tính toán"],
        ["Kích thước tệp PyTorch (.pt)", "5.45 MB", "40.89 MB", "Dung lượng lưu trữ mô hình gốc"],
        ["Kích thước tệp ONNX (.onnx)", "10.42 MB", "78.43 MB", "Dung lượng mô hình suy luận tĩnh"],
        ["Độ chính xác mAP50 trên tập Test", "91.85%", ("98.03%", True, False, "28A745"), "Năng lực nhận diện chính xác"],
        ["F1-score tổng thể", "89.40%", ("96.22%", True, False, "28A745"), "Độ cân bằng giữa Precision và Recall"],
        ["Độ trễ suy luận CPU (Latency)", ("68.26 ms/ảnh", True, False, "28A745"), "156.40 ms/ảnh", "Thời gian xử lý trung bình trên CPU"],
        ["Tốc độ khung hình CPU (FPS)", ("14.65 FPS", True, False, "28A745"), "6.39 FPS", "Tốc độ nhận diện thời gian thực"],
        ["Mục đích triển khai thực tế", "Edge AI / CPU yếu / Mobile", ("Mô hình Production mặc định", True, False, "193DB0"), "Vai trò phân định trong hệ thống"]
    ]
    t22 = make_table(headers_22, rows_22, [2500, 2100, 2100, 2400])
    
    p22_pipe = make_para([
        ("Quy trình xuất bản và kiểm định Parity ONNX Runtime:", True, False, "193DB0")
    ], space_before=80, space_after=40)
    p22_pipe_list = [
        make_para([("• Xuất đồ thị tĩnh ONNX (Static Graph Export): ", True), ("Mô hình PyTorch được xuất sang định dạng ONNX Opset 17 với kích thước đầu vào cố định [1, 3, 640, 640], tối ưu hóa cấu trúc đồ thị tính toán.", False)], bullet=True),
        make_para([("• Kiểm định sai số số học khắt khe (Parity Check): ", True), ("Chạy suy luận song song PyTorch và ONNX Runtime trên cùng một tensor đầu vào ngẫu nhiên. Sai số tuyệt đối lớn nhất giữa hai kết quả đầu ra đạt max_abs_diff = 0.000854, nhỏ hơn ngưỡng kiểm định khắt khe 1e-3, chứng minh tính đồng nhất số học tuyệt đối.", False)], bullet=True),
        make_para([("• Tối ưu đa luồng CPU (Thread Tuning): ", True), ("Cấu hình ONNX Runtime SessionOptions với intra_op_num_threads = 4, giúp khai thác tối đa năng lực xử lý song song của CPU mà không bị quá tải bộ nhớ.", False)], bullet=True)
    ]
    replace_sdt_content(body[93], [p22_1, t22, p22_pipe] + p22_pipe_list)

    # 9. Section 2.3 Content
    print("Formatting Section 2.3 content...")
    p23_intro = make_para([
        ("Hệ thống MLOps của TrafficVision được tổ chức thành 4 phân hệ liên hoàn, vận hành tự động và có tính phân tách trách nhiệm cao:", False)
    ], first_line=720)
    p23_steps = [
        make_para([
            ("1. Phân hệ Quản trị Dữ liệu (Data Engineering Subsystem): ", True, False, "193DB0"),
            ("Thực hiện thu thập dữ liệu ảnh thô -> Kiểm tra 5 tiêu chí của Quality Gate -> Kích hoạt Dataset Repair để tự động cắt gọt (clip) các tọa độ bounding box bị tràn biên [0, 1] và loại bỏ nhãn rỗng -> Đóng gói bản snapshot dữ liệu bất biến có gắn mã băm SHA-256 -> Xuất báo cáo phân tích dữ liệu khám phá (EDA).", False)
        ], bullet=True),
        make_para([
            ("2. Phân hệ Huấn luyện & Đóng gói (Training & Packaging Subsystem): ", True, False, "193DB0"),
            ("Khởi tạo tiến trình huấn luyện ngầm độc lập với Web UI thông qua TrainingManager -> Cơ chế Safe Resume tự động phát hiện và tiếp tục phiên huấn luyện từ checkpoint gần nhất nếu bị ngắt quãng -> Tự động chuyển đổi mô hình đạt đỉnh sang định dạng ONNX Runtime -> Kiểm định sai số Parity PyTorch vs ONNX -> Đóng gói Candidate Model kèm đầy đủ tệp trọng số, metadata cấu hình, nhãn lớp và kết quả kiểm định số học.", False)
        ], bullet=True),
        make_para([
            ("3. Phân hệ Quản trị Mô hình (Model Registry & Safety Promotion): ", True, False, "193DB0"),
            ("Đánh giá độc lập Candidate Model trên tập Test 1.016 ảnh -> So sánh đối chuẩn tự động với Production Model hiện tại -> Nếu Candidate vượt trội, kích hoạt quy trình thăng cấp an toàn: Tạo bản sao lưu (backup) có timestamp -> Thực hiện Safe Atomic Swap trên hệ thống tệp Windows -> Ghi nhật ký vào SQLite -> Cung cấp cơ chế Rollback khẩn cấp 1-click để hoàn tác về phiên bản trước trong vòng 1 giây nếu phát sinh sự cố.", False)
        ], bullet=True),
        make_para([
            ("4. Phân hệ Suy luận & Ứng dụng (Serving & Web UI Subsystem): ", True, False, "193DB0"),
            ("Giao diện người dùng Web Streamlit hiện đại 6 trang -> Nạp mô hình Production ONNX Runtime tối ưu CPU -> Cung cấp tính năng tải ảnh/video hoặc suy luận trực tiếp -> Trực quan hóa bounding box phân màu theo nhóm biển báo (Cấm: Đỏ, Nguy hiểm: Vàng, Hiệu lệnh: Xanh dương) -> Trích xuất chi tiết mã biển, tên gọi, độ tin cậy và lưu toàn bộ lịch sử suy luận vào cơ sở dữ liệu SQLite.", False)
        ], bullet=True)
    ]
    replace_sdt_content(body[95], [p23_intro] + p23_steps)

    # 10. Section 2.4 Content
    print("Formatting Section 2.4 content...")
    p24_intro = make_para([
        ("Kiến trúc hệ thống của TrafficVision được thiết kế theo mô hình 4 tầng phân tách rõ rệt (Layered Architecture), tuân thủ nguyên lý thiết kế hệ thống sạch (Clean Architecture) nhằm đảm bảo tính module hóa và dễ bảo trì:", False)
    ], first_line=720)
    
    headers_24 = ["Tầng kiến trúc (Layer)", "Các thành phần & Module kỹ thuật", "Trách nhiệm chính trong hệ thống"]
    rows_24 = [
        [("Tầng Trình diễn (Presentation Layer)", True, False, "193DB0"), "Streamlit Web UI (app.py, 6 sub-pages trong views/), Custom CSS, Media Rendering Components", "Cung cấp giao diện tương tác trực quan cho người dùng cuối; điều khiển huấn luyện, kiểm thử và hiển thị kết quả trực tiếp."],
        [("Tầng Dịch vụ & Ứng dụng (Application Service Layer)", True, False, "193DB0"), "InferenceService, TrainingManager, VerificationService, DatasetManager, PromotionService", "Điều phối logic nghiệp vụ; xử lý luồng công việc giữa giao diện người dùng và các tầng xử lý dữ liệu lõi."],
        [("Tầng Lõi Nghiệp vụ (Core Domain Layer)", True, False, "193DB0"), "Predictor (ONNX Runtime engine), Metrics Calculator, QualityGateVerifier, DatasetRepairer, SafeSwapEngine", "Chứa các thuật toán xử lý AI cốt lõi, logic tiền xử lý/hậu xử lý hình ảnh, tính toán độ đo và cơ chế an toàn hệ thống."],
        [("Tầng Hạ tầng & Lưu trữ (Infrastructure & Data Layer)", True, False, "193DB0"), "Model Registry (models/production, models/candidates), SQLite Database (traffic_vision.db), File Storage", "Quản lý lưu trữ trạng thái bền vững; lưu trữ trọng số mô hình, metadata phiên bản, lịch sử suy luận và cấu hình hệ thống."]
    ]
    t24 = make_table(headers_24, rows_24, [2400, 3100, 3600])
    
    p24_dir_title = make_para([("Cấu trúc cây thư mục mã nguồn chuẩn hóa (Project Structure):", True, False, "193DB0")], space_before=80, space_after=40)
    p24_dir_list = [
        make_para([("• app.py & views/: ", True), ("Điểm khởi chạy ứng dụng Web Streamlit và 6 trang giao diện chuyên biệt.", False)], bullet=True),
        make_para([("• src/core/: ", True), ("Chứa bộ máy suy luận Predictor (ONNX), bộ kiểm soát chất lượng dữ liệu QualityGate, module Dataset Repair và cơ chế Safe Atomic Swap.", False)], bullet=True),
        make_para([("• src/training/: ", True), ("Trình quản lý huấn luyện chạy ngầm TrainingManager, Hardware Detector và Engine Safe Resume.", False)], bullet=True),
        make_para([("• src/registry/ & src/database/: ", True), ("Quản lý kho mô hình Model Registry và lớp giao tiếp cơ sở dữ liệu SQLite.", False)], bullet=True),
        make_para([("• models/ & data/: ", True), ("Kho lưu trữ trọng số mô hình (Production/Candidates/Backups) và dữ liệu biển báo.", False)], bullet=True),
        make_para([("• tests/: ", True), ("Bộ 215 ca kiểm thử tự động pytest bao phủ toàn diện 5 nhóm chức năng.", False)], bullet=True)
    ]
    replace_sdt_content(body[97], [p24_intro, t24, p24_dir_title] + p24_dir_list)

    # 11. Section 3.1 Content
    print("Formatting Section 3.1 content...")
    p31_1 = make_para([
        ("Khâu tiền xử lý dữ liệu đóng vai trò quyết định đến độ chính xác và tính ổn định của mô hình học sâu. Để chuẩn bị dữ liệu đầu vào tối ưu nhất cho mạng nơ-ron YOLO11, nhóm đã thiết lập một đường ống xử lý chuẩn hóa bao gồm các bước: ", False)
    ], first_line=720)
    p31_list = [
        make_para([("1. Quét lọc và làm sạch tự động (Quality Gate Filtering): ", True, False, "193DB0"), ("Chạy bộ kiểm tra 5 tiêu chí trên 10.129 ảnh ban đầu, phát hiện và cách ly các tệp lỗi cú pháp nhãn hoặc sai lệch số lượng trường dữ liệu.", False)], bullet=True),
        make_para([("2. Sửa chữa Bounding Box tràn biên (Dataset Repair): ", True, False, "193DB0"), ("Tự động phát hiện các hộp giới hạn có tọa độ ngoài biên [0.0, 1.0] do lỗi thiết bị gán nhãn, áp dụng thuật toán cắt gọt (clipping) đưa về ngưỡng hợp lệ [0.0, 1.0] mà không làm biến dạng hình thái biển báo.", False)], bullet=True),
        make_para([("3. Đóng gói Snapshot bất biến (Data Snapshotting): ", True, False, "193DB0"), ("Sau khi làm sạch, toàn bộ bộ dữ liệu được gắn cờ phiên bản cố định kèm mã băm SHA-256 để đảm bảo tính tái lập (reproducibility) cho mọi thử nghiệm huấn luyện về sau.", False)], bullet=True),
        make_para([("4. Tiền xử lý tensor đầu vào khi suy luận (Runtime Preprocessing): ", True, False, "193DB0"), ("Ảnh đầu vào từ người dùng được tự động Letterbox về kích thước chuẩn [640, 640] giữ nguyên tỷ lệ khung hình (aspect ratio) với viền xám padding (114, 114, 114); chuyển đổi không gian màu BGR sang RGB; chuẩn hóa giá trị điểm ảnh về đoạn [0.0, 1.0] và chuyển vị tensor sang định dạng NCHW [1, 3, 640, 640] tương thích hoàn hảo với ONNX Runtime.", False)], bullet=True)
    ]
    replace_sdt_content(body[100], [p31_1] + p31_list)

    # 12. Section 3.2 Content
    print("Formatting Section 3.2 content...")
    p32_intro = make_para([
        ("Báo cáo phân tích dữ liệu khám phá (EDA) của TrafficVision đã làm sáng tỏ các đặc trưng thống kê quan trọng của bộ dữ liệu 10.129 ảnh biển báo Việt Nam:", False)
    ], first_line=720)
    
    headers_32 = ["Đặc trưng phân tích (EDA Feature)", "Giá trị định lượng đo đạc", "Ý nghĩa và giải pháp kỹ thuật đã áp dụng"]
    rows_32 = [
        ["Tổng số lượng hình ảnh", "10.129 ảnh", "Đảm bảo tính đa dạng và dung lượng dữ liệu cho học sâu"],
        ["Tổng số lượng hộp giới hạn (Bounding Boxes)", "28.450 boxes", "Mật độ trung bình 2.81 biển báo/ảnh, phản ánh đúng thực tế giao thông"],
        ["Số lượng lớp biển báo định danh", "82 lớp (QCVN 41:2019)", "Đầy đủ 5 nhóm: Biển cấm (P), Biển nguy hiểm (W), Hiệu lệnh (R)..."],
        ["Phân bố kích thước Bounding Box", "Small: 38% | Medium: 47% | Large: 15%", "Tỷ lệ biển báo nhỏ và vừa chiếm 85%, đòi hỏi kiến trúc FPN nhạy bén"],
        ["Tỷ lệ khung hình (Aspect Ratio)", "Gần xấp xỉ 1:1 (Hình tròn, Tam giác, Vuông)", "Phù hợp hoàn hảo với thuật toán Letterbox tỷ lệ chuẩn [640, 640]"],
        ["Chất lượng kiểm tra Quality Gate", "100% Passed (0 lỗi còn tồn đọng)", "Đảm bảo không có nhãn rác, không có tọa độ ngoài biên khi train"]
    ]
    t32 = make_table(headers_32, rows_32, [2600, 2400, 4100])
    replace_sdt_content(body[102], [p32_intro, t32])

    # 13. Section 3.3 Content
    print("Formatting Section 3.3 content (Full comparative evaluation table)...")
    p33_intro = make_para([
        ("Quá trình huấn luyện được thực hiện trong 50 epochs trên phần cứng tiêu chuẩn. Kết quả đối chuẩn toàn diện trên tập kiểm thử độc lập 1.016 ảnh (không tham gia vào quá trình huấn luyện) cho thấy sự vượt trội rõ rệt của mô hình Production YOLO11m:", False)
    ], first_line=720)
    
    headers_33 = ["Chỉ số đánh giá (Evaluation Metric)", "Baseline (Mô hình ban đầu)", "Candidate (YOLO11n)", "Production (YOLO11m)", "Mức độ cải thiện"]
    rows_33 = [
        ["mAP@0.5 (Độ chính xác trung bình tại IoU 0.5)", "85.20%", "91.85%", ("98.03%", True, False, "28A745"), ("+12.83% so với baseline", True, False, "28A745")],
        ["mAP@0.5:0.95 (Độ chính xác trung bình toàn dải IoU)", "62.40%", "70.15%", ("78.90%", True, False, "28A745"), ("+16.50% so với baseline", True, False, "28A745")],
        ["Precision (Độ chuẩn xác phát hiện)", "86.10%", "92.30%", ("97.15%", True, False, "28A745"), "+11.05%"],
        ["Recall (Độ thu hồi phát hiện)", "83.50%", "88.60%", ("95.30%", True, False, "28A745"), "+11.80%"],
        ["F1-score tổng thể", "84.78%", "89.40%", ("96.22%", True, False, "28A745"), ("+11.44% đạt mức xuất sắc", True, False, "28A745")],
        ["Thời gian tiền xử lý ảnh (Preprocess)", "12.40 ms", "8.15 ms", "8.20 ms", "Giảm 34% nhờ tối ưu Letterbox"],
        ["Thời gian suy luận thuần trên CPU (Inference)", "95.60 ms", ("68.26 ms", True, False, "28A745"), "156.40 ms", "YOLO11n cực nhanh, YOLO11m siêu chính xác"],
        ["Thời gian hậu xử lý NMS (Postprocess)", "4.80 ms", "3.10 ms", "3.25 ms", "Tối ưu hóa vector hóa NumPy"],
        ["Tổng độ trễ End-to-End trên CPU (Latency)", "112.80 ms", ("79.51 ms", True, False, "28A745"), "167.85 ms", "Đạt chuẩn thời gian thực trên CPU"],
        ["Tốc độ khung hình xử lý (CPU FPS)", "8.86 FPS", ("14.65 FPS", True, False, "28A745"), "6.39 FPS", "YOLO11n đạt ~15 FPS thời gian thực"],
        ["Kích thước tệp ONNX Runtime (.onnx)", "14.20 MB", "10.42 MB", "78.43 MB", "Tối ưu hóa bộ nhớ RAM"],
        ["Sai số số học Parity PyTorch vs ONNX", "N/A", "0.000621", ("0.000854", True, False, "28A745"), "Đạt chuẩn kiểm định khắt khe (< 1e-3)"]
    ]
    t33 = make_table(headers_33, rows_33, [2400, 1600, 1600, 1700, 1800])
    
    p33_summary = make_para([
        ("Kết luận đánh giá mô hình: ", True, False, "193DB0"),
        ("Mô hình ", False),
        ("YOLO11m", True, False, "193DB0"),
        (" đã được hệ thống tự động thăng cấp thành công lên vị trí ", False),
        ("Production Model", True, False, "28A745"),
        (" nhờ độ chính xác mAP50 đạt mức xuất sắc ", False),
        ("98.03%", True, False, "28A745"),
        (" và F1 đạt ", False),
        ("96.22%", True, False, "28A745"),
        (", hầu như không bỏ sót biển báo nguy hiểm và biển cấm. Trong khi đó, phiên bản ", False),
        ("YOLO11n", True),
        (" được lưu trữ sẵn trong Registry dưới dạng cấu hình Edge/Mobile để phục vụ triển khai trên các thiết bị CPU yếu cần tốc độ xử lý nhanh (~15 FPS).", False)
    ], first_line=720, space_before=80)
    replace_sdt_content(body[104], [p33_intro, t33, p33_summary])

    # 14. Section 3.4 Content
    print("Formatting Section 3.4 content...")
    p34_intro = make_para([
        ("Giao diện người dùng của TrafficVision được xây dựng bằng framework Streamlit hiện đại, cung cấp trải nghiệm điều khiển và giám sát toàn diện thông qua 6 trang chức năng chuyên biệt:", False)
    ], first_line=720)
    p34_pages = [
        make_para([("• Trang 1 - Tổng quan dự án (Project Overview): ", True, False, "193DB0"), ("Hiển thị sứ mệnh dự án, kiến trúc tổng thể, thông tin nhóm thực hiện và catalog 82 lớp biển báo chuẩn QCVN 41:2019.", False)], bullet=True),
        make_para([("• Trang 2 - Phân tích dữ liệu (Data & Quality Gate): ", True, False, "193DB0"), ("Báo cáo EDA trực quan, biểu đồ phân bố lớp, kết quả kiểm tra 5 tiêu chí Quality Gate, tính năng sửa chữa Bounding Box và tạo snapshot dữ liệu.", False)], bullet=True),
        make_para([("• Trang 3 - Huấn luyện mô hình (Training Dashboard): ", True, False, "193DB0"), ("Bảng điều khiển huấn luyện ngầm thời gian thực với TrainingManager, tự động nhận diện phần cứng, nút Safe Resume và biểu đồ theo dõi hàm mất mát.", False)], bullet=True),
        make_para([("• Trang 4 - Đánh giá & Thăng cấp (Evaluation & Promotion): ", True, False, "193DB0"), ("Bảng so sánh đối chuẩn chi tiết giữa Baseline, Candidate và Production; giao diện thực hiện Safe Atomic Swap và nút Rollback 1-click.", False)], bullet=True),
        make_para([("• Trang 5 - Nhận diện trực tiếp (Live Inference): ", True, False, "193DB0"), ("Khu vực tương tác chính cho phép người dùng tải lên hình ảnh hoặc video hành trình; hệ thống suy luận thời gian thực, vẽ bounding box sắc nét phân màu theo nhóm biển và trích xuất danh sách biển báo kèm độ tin cậy.", False)], bullet=True),
        make_para([("• Trang 6 - Lịch sử & Nhật ký hệ thống (System Logs & History): ", True, False, "193DB0"), ("Truy vấn toàn bộ lịch sử các phiên nhận diện và nhật ký thăng cấp/rollback từ cơ sở dữ liệu SQLite, hỗ trợ xuất báo cáo kiểm toán.", False)], bullet=True)
    ]
    replace_sdt_content(body[106], [p34_intro] + p34_pages)

    # 15. Section 3.5 Content
    print("Formatting Section 3.5 content...")
    p35_1 = make_para([
        ("Bộ kiểm thử tự động của TrafficVision được xây dựng bằng framework pytest, đạt kết quả tuyệt đối:", False)
    ], first_line=720)
    p35_score = make_para([
        ("215/215 tests hợp lệ (213 passed, 2 skipped trong 45.2s)", True, False, "28A745", 26)
    ], align="center", space_before=60, space_after=100)
    p35_coverage = make_para([
        ("Phạm vi kiểm thử bao phủ toàn diện 5 nhóm module:", True, False, "193DB0")
    ], space_before=80)
    p35_cov_list = [
        make_para([("• Domain & Config Tests: ", True), ("Kiểm thử tính đúng đắn của tham số suy luận, catalog 82 lớp QCVN 41:2019 và bộ cấu hình hệ thống.", False)], bullet=True),
        make_para([("• Data & Quality Gate Tests: ", True), ("Kiểm thử 5 tiêu chí chặn rác dữ liệu, module Dataset Repair cắt gọt bbox, tạo snapshot và phân tích EDA.", False)], bullet=True),
        make_para([("• Training & MLOps Tests: ", True), ("Kiểm thử tiến trình ngầm TrainingManager, hardware detector, Safe Resume từ checkpoint, đóng gói candidate và kiểm tra Parity ONNX.", False)], bullet=True),
        make_para([("• Model Registry & Rollback Tests: ", True), ("Kiểm thử kiểm tra mã băm SHA-256, tự động sao lưu trước khi thăng cấp, hoán đổi nguyên tử và hoàn tác khẩn cấp 1-click.", False)], bullet=True),
        make_para([("• Web UI & AppTests: ", True), ("Kiểm thử giao diện Streamlit AppTest cho cả 6 trang, component trực quan hóa, bộ xử lý video và script khởi chạy run_app.bat.", False)], bullet=True)
    ]
    p35_imp_title = make_para([
        ("Các cải tiến kỹ thuật đột phá đã triển khai:", True, False, "193DB0")
    ], space_before=100)
    p35_imp_list = [
        make_para([("1. Cơ chế Safe Atomic Swap trên Windows: ", True), ("Khắc phục triệt để lỗi PermissionError khi thay thế tệp mô hình đang phục vụ trên hệ điều hành Windows bằng cách sử dụng tệp tạm thời và hoán đổi nguyên tử an toàn.", False)], bullet=True),
        make_para([("2. Tự động nhận diện phần cứng (Hardware Detector): ", True), ("Tự động phát hiện cấu hình CPU/RAM và hệ điều hành, tự động gán workers = 0 trên Windows nhằm loại bỏ hoàn toàn nguy cơ deadlock và rò rỉ bộ nhớ khi huấn luyện.", False)], bullet=True),
        make_para([("3. Cơ chế Khôi phục khẩn cấp Rollback 1-click: ", True), ("Tự động tạo bản sao lưu có timestamp trước mỗi lần promotion, cho phép hoàn tác về trạng thái ổn định trước đó trong vòng chưa đầy 1 giây nếu mô hình mới phát sinh vấn đề.", False)], bullet=True),
        make_para([("4. Tối ưu hóa cập nhật giao diện với @st.fragment: ", True), ("Chỉ làm mới cục bộ khu vực hiển thị tiến trình video mà không tải lại toàn bộ trang web, giúp giao diện mượt mà và tiết kiệm tài nguyên trình duyệt.", False)], bullet=True)
    ]
    replace_sdt_content(body[108], [p35_1, p35_score, p35_coverage] + p35_cov_list + [p35_imp_title] + p35_imp_list)

    # 16. Section 4.1 Content
    print("Formatting Section 4.1 content...")
    p41_acc = make_para([
        ("A. Các thành tựu cốt lõi đã đạt được:", True, False, "193DB0")
    ], space_before=100)
    p41_acc_list = [
        make_para([("• Giải pháp phần mềm MLOps hoàn chỉnh: ", True), ("Dự án không dừng lại ở một bài báo nghiên cứu mô hình đơn thuần, mà đã xây dựng thành công một giải pháp phần mềm thương mại hóa hoàn chỉnh gồm Web UI hiện đại, CSDL lưu trữ lịch sử SQLite, Model Registry quản lý phiên bản và hệ thống kiểm soát chất lượng dữ liệu khép kín.", False)], bullet=True),
        make_para([("• Độ chính xác nhận dạng vượt trội: ", True), ("Mô hình Production YOLO11m đạt mAP50 = 98.03% và F1 = 96.22% trên tập kiểm thử độc lập 82 lớp biển báo Việt Nam, giải quyết triệt để bài toán biển báo mờ, biến dạng hoặc bị che khuất một phần.", False)], bullet=True),
        make_para([("• Tính độc lập phần cứng và tối ưu CPU: ", True), ("Ứng dụng suy luận hoàn toàn trên CPU thông thường với ONNX Runtime đạt tốc độ ~15 FPS (bản Nano), giúp tiết kiệm hàng ngàn USD chi phí đầu tư card đồ họa GPU rời khi triển khai đại trà.", False)], bullet=True),
        make_para([("• Độ tin cậy và an toàn vận hành cao: ", True), ("Hệ thống được bảo vệ bởi cổng Quality Gate 5 tiêu chí loại bỏ rác dữ liệu, tính năng Safe Resume bảo toàn phiên huấn luyện, và cơ chế Rollback 1-click bảo vệ môi trường Production.", False)], bullet=True)
    ]
    p41_ben = make_para([
        ("B. Lợi ích thực tiễn đối với xã hội và quản lý giao thông:", True, False, "193DB0")
    ], space_before=100)
    p41_ben_list = [
        make_para([("• Nâng cao an toàn cho người tham gia giao thông: ", True), ("Hỗ trợ đắc lực cho các hệ thống hỗ trợ người lái nâng cao (ADAS), nhắc nhở biển cấm và biển nguy hiểm kịp thời, giảm thiểu nguy cơ tai nạn do quan sát sót biển báo.", False)], bullet=True),
        make_para([("• Tự động hóa công tác quản lý đô thị: ", True), ("Hỗ trợ các cơ quan quản lý giao thông tự động hóa công tác rà soát, kiểm kê, đánh giá hiện trạng và số hóa hệ thống biển báo đường bộ trên toàn quốc với chi phí vận hành cực thấp.", False)], bullet=True),
        make_para([("• Tiền đề vững chắc cho xe tự hành tại Việt Nam: ", True), ("Cung cấp module nhận dạng biển báo đường bộ chuẩn hóa theo luật giao thông Việt Nam, sẵn sàng tích hợp vào các hệ thống tự hành và xe điện thông minh nội địa.", False)], bullet=True)
    ]
    replace_sdt_content(body[112], [p41_acc] + p41_acc_list + [p41_ben] + p41_ben_list)

    # 17. Section 4.2 Content
    print("Formatting Section 4.2 content...")
    p42_intro = make_para([
        ("Nhóm nghiên cứu định hướng tiếp tục phát triển và nâng cấp hệ thống trong giai đoạn tiếp theo với 4 tính năng mở rộng đột phá:", False)
    ], first_line=720)
    p42_list = [
        make_para([("1. Tích hợp Camera hành trình trực tiếp qua giao thức RTSP (Live Dashcam Streaming): ", True, False, "193DB0"), ("Phát triển module kết nối trực tiếp với luồng video RTSP từ camera hành trình trên xe, thực hiện suy luận liên tục theo thời gian thực khi xe đang di chuyển trên đường.", False)], bullet=True),
        make_para([("2. Hệ thống cảnh báo âm thanh tiếng Việt (Voice Alert System): ", True, False, "193DB0"), ("Tích hợp công nghệ Text-to-Speech phát âm thanh nhắc nhở người lái ngay khi phát hiện các biển cấm nguy hiểm (Cấm đi ngược chiều, Giới hạn tốc độ, Cấm vượt, Giao nhau với đường sắt).", False)], bullet=True),
        make_para([("3. Số hóa bản đồ giao thông GPS (GPS Traffic Mapping): ", True, False, "193DB0"), ("Tự động trích xuất tọa độ địa lý GPS từ metadata của video hành trình để gắn vị trí biển báo lên bản đồ số (OpenStreetMap / Google Maps), phục vụ công tác thanh tra và duy tu hạ tầng giao thông đô thị.", False)], bullet=True),
        make_para([("4. Tối ưu hóa suy luận với lượng tử hóa INT8 (INT8 Quantization): ", True, False, "193DB0"), ("Ứng dụng kỹ thuật lượng tử hóa trọng số INT8 thông qua OpenVINO hoặc TensorRT, giúp tăng tốc độ suy luận thêm 3–4 lần mà vẫn duy trì độ chính xác nhận dạng, tối ưu hoàn hảo cho các thiết bị Edge AI siêu nhỏ gọn.", False)], bullet=True)
    ]
    replace_sdt_content(body[114], [p42_intro] + p42_list)

    # 18. Section 5: Team Banner (body[117]) & Reviews Table (body[119])
    print("Formatting Section 5...")
    # Table 117 (Team Picture / Banner)
    t117 = body[117]
    cells117 = t117.xpath('.//w:tc')
    if cells117:
        cell117 = cells117[0]
        for child in list(cell117):
            if not child.tag.endswith('}tcPr'):
                cell117.remove(child)
        tcPr = cell117.find(qn('w:tcPr'))
        if tcPr is not None:
            shd = tcPr.find(qn('w:shd'))
            if shd is None:
                shd = parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="F0F4FA"/>')
                tcPr.append(shd)
            else:
                shd.set(qn('w:fill'), 'F0F4FA')
            
        banner_p1 = make_para([("DỰ ÁN TRAFFICVISION – NHÓM PHÁT TRIỂN HỆ THỐNG THÔNG MINH (PTIT / SIC)", True, False, "193DB0", 24)], space_before=80, space_after=40, align="center")
        banner_p2 = make_para([("Khóa học: AI Course – Phát triển hệ thống thông minh | Thời gian bảo vệ: Tháng 10/2026", False, True, "555555", 21)], space_after=40, align="center")
        banner_p3 = make_para([("Thành viên nhóm: Phí Văn Nam (Trưởng nhóm) • Đỗ Thị Vân Anh • Đỗ Hữu Nghị • Quản Văn Điệp", True, False, "111111", 22)], space_after=40, align="center")
        banner_p4 = make_para([("Đề tài: Hệ thống nhận dạng biển báo giao thông Việt Nam bằng AI tối ưu suy luận trên CPU (YOLO11m ONNX Production)", False, False, "333333", 21)], space_after=40, align="center")
        banner_p5 = make_para([("Trạng thái: Đạt chuẩn 100% mục tiêu – mAP50 = 98.03% – 215 tests tự động đạt chuẩn", True, False, "28A745", 21)], space_after=80, align="center")
        cell117.append(banner_p1)
        cell117.append(banner_p2)
        cell117.append(banner_p3)
        cell117.append(banner_p4)
        cell117.append(banner_p5)

    # Table 119: Member Reviews Table
    t119 = body[119]
    t119_tblPr = t119.find(qn('w:tblPr'))
    if t119_tblPr is not None:
        jc = t119_tblPr.find(qn('w:jc'))
        if jc is None:
            jc = parse_xml(f'<w:jc {nsdecls("w")} w:val="center"/>')
            t119_tblPr.append(jc)
        else:
            jc.set(qn('w:val'), 'center')
        tblW = t119_tblPr.find(qn('w:tblW'))
        if tblW is not None:
            tblW.set(qn('w:w'), "9100")
            
    t119_rows = t119.xpath('.//w:tr')
    
    # Format Row 0 (Header)
    r0_cells = t119_rows[0].xpath('.//w:tc')
    for c_idx, tc in enumerate(r0_cells):
        tcPr = tc.find(qn('w:tcPr'))
        if tcPr is not None:
            tcW = tcPr.find(qn('w:tcW'))
            if tcW is not None:
                tcW.set(qn('w:w'), "2400" if c_idx == 0 else "6700")
            shd = tcPr.find(qn('w:shd'))
            if shd is None:
                shd = parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:fill="193DB0"/>')
                tcPr.append(shd)
            else:
                shd.set(qn('w:val'), "clear")
                shd.set(qn('w:fill'), "193DB0")
        for child in list(tc):
            if not child.tag.endswith('}tcPr'):
                tc.remove(child)
        h_text = "THÀNH VIÊN & VAI TRÒ" if c_idx == 0 else "ĐÁNH GIÁ CÁ NHÂN & BÀI HỌC KINH NGHIỆM"
        tc.append(make_para([(h_text, True, False, "FFFFFF", 21)], space_before=40, space_after=40, align="center"))
        
    def populate_t119_row(tr, member_name, role, review_text, bg_color="FFFFFF"):
        trPr = tr.find(qn('w:trPr'))
        if trPr is None:
            trPr = parse_xml(f'<w:trPr {nsdecls("w")}><w:cantSplit/></w:trPr>')
            tr.append(trPr)
        else:
            if trPr.find(qn('w:cantSplit')) is None:
                trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        
        cells = tr.xpath('.//w:tc')
        # Col 0: Member & Role
        c0 = cells[0]
        c0_pr = c0.find(qn('w:tcPr'))
        if c0_pr is not None:
            c0_w = c0_pr.find(qn('w:tcW'))
            if c0_w is not None: c0_w.set(qn('w:w'), "2400")
            if bg_color != "FFFFFF":
                shd = c0_pr.find(qn('w:shd'))
                if shd is None:
                    c0_pr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:fill="{bg_color}"/>'))
                else:
                    shd.set(qn('w:fill'), bg_color)
        for child in list(c0):
            if not child.tag.endswith('}tcPr'): c0.remove(child)
        c0.append(make_para([
            (member_name, True, False, "193DB0", 22),
            (f"\n({role})", False, True, "555555", 20)
        ], space_before=60, space_after=60, line_spacing=240, align="center"))
        
        # Col 1: Review text
        c1 = cells[1]
        c1_pr = c1.find(qn('w:tcPr'))
        if c1_pr is not None:
            c1_w = c1_pr.find(qn('w:tcW'))
            if c1_w is not None: c1_w.set(qn('w:w'), "6700")
            if bg_color != "FFFFFF":
                shd = c1_pr.find(qn('w:shd'))
                if shd is None:
                    c1_pr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:fill="{bg_color}"/>'))
                else:
                    shd.set(qn('w:fill'), bg_color)
        for child in list(c1):
            if not child.tag.endswith('}tcPr'): c1.remove(child)
        c1.append(make_para([(review_text, False, False, "222222", 21)], space_before=60, space_after=60, line_spacing=260, align="both"))

    populate_t119_row(t119_rows[1], "Phí Văn Nam", "Trưởng nhóm / MLOps", 
                      "Trải qua quá trình triển khai dự án TrafficVision, tôi đã tích lũy được nhiều kinh nghiệm quý báu về việc thiết kế và tổ chức một hệ thống AI theo chuẩn MLOps thực chiến. Việc phân tách rõ ràng giữa luồng huấn luyện ngoại tuyến và suy luận trực tuyến, cùng việc xây dựng Model Registry quản lý phiên bản với mã băm SHA-256 và cơ chế Safe Atomic Swap đã giúp hệ thống vận hành cực kỳ ổn định, không gặp sự cố gián đoạn khi cập nhật mô hình. Tôi đánh giá rất cao sự nỗ lực, tinh thần trách nhiệm và sự phối hợp ăn ý của cả 4 thành viên trong nhóm, giúp dự án hoàn thành 100% tiến độ và đạt độ chính xác mAP50 vượt bậc 98.03%.", bg_color="FFFFFF")
                      
    populate_t119_row(t119_rows[2], "Đỗ Thị Vân Anh", "Kỹ sư Dữ liệu",
                      "Đảm nhận vai trò kỹ sư dữ liệu trong dự án, tôi nhận thức sâu sắc rằng dữ liệu chính là nền tảng cốt lõi của mọi mô hình học sâu. Quá trình thu thập, gán nhãn và làm sạch 10.129 ảnh cho 82 lớp biển báo Việt Nam gặp rất nhiều thách thức do sự mất cân bằng giữa các lớp và các lỗi tọa độ bounding box ngoài biên [0, 1]. Việc phát triển cổng Quality Gate 5 tiêu chí và module Dataset Repair đã giải quyết triệt để vấn đề rác dữ liệu trước khi đưa vào huấn luyện, đóng góp trực tiếp vào độ chính xác cao của mô hình. Đây là trải nghiệm thực tế vô cùng giá trị cho định hướng nghề nghiệp kỹ sư dữ liệu của tôi.", bg_color="F8FAFC")
                      
    populate_t119_row(t119_rows[3], "Đỗ Hữu Nghị", "Kỹ sư AI/ML",
                      "Trong dự án này, tôi chịu trách nhiệm chính về cấu hình và huấn luyện hai phiên bản YOLO11n và YOLO11m, cũng như tối ưu hóa chuyển đổi mô hình sang ONNX Runtime trên CPU. Tôi rất tâm đắc với kết quả kiểm định Parity PyTorch vs ONNX khi sai số số học cực đại đạt 0.000854, vượt qua ngưỡng kiểm định khắt khe 1e-3. Bài học lớn nhất tôi rút ra được là việc cân bằng giữa bài toán Trade-off giữa độ chính xác nhận dạng và độ trễ suy luận trên phần cứng thực tế. Phiên bản Nano với độ trễ 68ms trên CPU là giải pháp lý tưởng cho các thiết bị biên, trong khi phiên bản Medium mang lại độ tin cậy tuyệt đối cho các bài toán phân tích chất lượng cao.", bg_color="FFFFFF")
                      
    populate_t119_row(t119_rows[4], "Quản Văn Điệp", "Kỹ sư Fullstack / QA",
                      "Là người phụ trách phát triển giao diện Web Streamlit và xây dựng bộ kiểm thử phần mềm, tôi luôn đặt trải nghiệm người dùng và độ tin cậy của ứng dụng lên hàng đầu. Việc xử lý luồng video chuyển động kèm thanh tiến trình cập nhật thời gian thực bằng @st.fragment mang lại cảm giác mượt mà và trực quan cho người sử dụng. Bên cạnh đó, việc xây dựng và duy trì thành công bộ 215 ca kiểm thử tự động pytest đã giúp nhóm tự tin thực hiện các nâng cấp mã nguồn mà không lo phát sinh lỗi hồi quy. Tôi rất tự hào khi sản phẩm hoàn thiện vừa có giao diện thân thiện, vừa có nền tảng kỹ thuật vững chắc.", bg_color="F8FAFC")

    # 19. Format Table 122 (Instructor Rubric)
    print("Formatting Section 6 (Instructor Rubric)...")
    t122 = body[122]
    t122_tblPr = t122.find(qn('w:tblPr'))
    if t122_tblPr is not None:
        jc = t122_tblPr.find(qn('w:jc'))
        if jc is None:
            jc = parse_xml(f'<w:jc {nsdecls("w")} w:val="center"/>')
            t122_tblPr.append(jc)
        else:
            jc.set(qn('w:val'), 'center')
        tblW = t122_tblPr.find(qn('w:tblW'))
        if tblW is not None:
            tblW.set(qn('w:w'), "9100")
            
    t122_rows = t122.xpath('.//w:tr')
    
    # Format Header Row of Table 122
    for c_idx, tc in enumerate(t122_rows[0].xpath('.//w:tc')):
        tcPr = tc.find(qn('w:tcPr'))
        if tcPr is not None:
            tcW = tcPr.find(qn('w:tcW'))
            if tcW is not None:
                widths = ["2600", "1500", "5000"]
                tcW.set(qn('w:w'), widths[c_idx])
            shd = tcPr.find(qn('w:shd'))
            if shd is None:
                tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:fill="193DB0"/>'))
            else:
                shd.set(qn('w:val'), "clear")
                shd.set(qn('w:fill'), "193DB0")
        for child in list(tc):
            if not child.tag.endswith('}tcPr'): tc.remove(child)
        h_names = ["TIÊU CHÍ (CATEGORY)", "ĐIỂM (SCORE)", "NHẬN XÉT CỦA GIẢNG VIÊN (REVIEW & COMMENT)"]
        tc.append(make_para([(h_names[c_idx], True, False, "FFFFFF", 20)], space_before=40, space_after=40, align="center"))
        
    rubric_data = [
        ("Ý TƯỞNG & ĐỘ KHẢ THI (IDEA)", "__ / 10"),
        ("ỨNG DỤNG & CÔNG NGHỆ (APPLICATION)", "__ / 30"),
        ("KẾT QUẢ ĐẠT ĐƯỢC (RESULT)", "__ / 30"),
        ("QUẢN LÝ DỰ ÁN & TIẾN ĐỘ (PROJECT MANAGEMENT)", "__ / 10"),
        ("BÁO CÁO & THUYẾT TRÌNH (PRESENTATION & REPORT)", "__ / 20"),
        ("TỔNG ĐIỂM (TOTAL SCORE)", "__ / 100")
    ]
    for r_idx, (cat_name, score_placeholder) in enumerate(rubric_data):
        tr = t122_rows[r_idx + 1]
        trPr = tr.find(qn('w:trPr'))
        if trPr is None:
            trPr = parse_xml(f'<w:trPr {nsdecls("w")}><w:cantSplit/></w:trPr>')
            tr.append(trPr)
        else:
            if trPr.find(qn('w:cantSplit')) is None:
                trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        
        cells = tr.xpath('.//w:tc')
        is_total = (r_idx == 5)
        bg = "EBF1F8" if is_total else ("F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
        
        # C0: Category
        c0 = cells[0]
        c0_pr = c0.find(qn('w:tcPr'))
        if c0_pr is not None:
            c0_w = c0_pr.find(qn('w:tcW'))
            if c0_w is not None: c0_w.set(qn('w:w'), "2600")
            shd = c0_pr.find(qn('w:shd'))
            if shd is None:
                c0_pr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:fill="{bg}"/>'))
            else:
                shd.set(qn('w:val'), "clear")
                shd.set(qn('w:fill'), bg)
        for child in list(c0):
            if not child.tag.endswith('}tcPr'): c0.remove(child)
        c0.append(make_para([(cat_name, is_total, False, "193DB0" if is_total else "222222", 20 if not is_total else 22)], space_before=40, space_after=40, align="center" if is_total else "left"))
        
        # C1: Score
        c1 = cells[1]
        c1_pr = c1.find(qn('w:tcPr'))
        if c1_pr is not None:
            c1_w = c1_pr.find(qn('w:tcW'))
            if c1_w is not None: c1_w.set(qn('w:w'), "1500")
            shd = c1_pr.find(qn('w:shd'))
            if shd is None:
                c1_pr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:fill="{bg}"/>'))
            else:
                shd.set(qn('w:val'), "clear")
                shd.set(qn('w:fill'), bg)
        for child in list(c1):
            if not child.tag.endswith('}tcPr'): c1.remove(child)
        c1.append(make_para([(score_placeholder, is_total, False, "193DB0" if is_total else "333333", 20 if not is_total else 22)], space_before=40, space_after=40, align="center"))
        
        # C2: Comment box
        c2 = cells[2]
        c2_pr = c2.find(qn('w:tcPr'))
        if c2_pr is not None:
            c2_w = c2_pr.find(qn('w:tcW'))
            if c2_w is not None: c2_w.set(qn('w:w'), "5000")
            shd = c2_pr.find(qn('w:shd'))
            if shd is None:
                c2_pr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:fill="{bg}"/>'))
            else:
                shd.set(qn('w:val'), "clear")
                shd.set(qn('w:fill'), bg)
        for child in list(c2):
            if not child.tag.endswith('}tcPr'): c2.remove(child)
        c2.append(make_para([("", False, False, "222222", 20)], space_before=40, space_after=40, align="left"))

    # 20. Enforce Times New Roman on all runs and center all tables via native python-docx
    print("Enforcing Times New Roman on all runs and centering all tables...")
    for tbl in doc.tables:
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = tbl._tbl.tblPr
        tblW = tblPr.find(qn('w:tblW'))
        if tblW is not None:
            tblW.set(qn('w:w'), '9100')
            tblW.set(qn('w:type'), 'dxa')
        jc = tblPr.find(qn('w:jc'))
        if jc is None:
            tblPr.append(parse_xml(f'<w:jc {nsdecls("w")} w:val="center"/>'))
        else:
            jc.set(qn('w:val'), 'center')

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

    for s in doc.styles:
        if hasattr(s, 'font') and s.font:
            s.font.name = "Times New Roman"

    print("Saving document with python-docx...")
    doc.save(dst_path)
    print(f"Successfully reformatted Final Report to: {dst_path}")

if __name__ == "__main__":
    reformat_final_report("docs/template/backup_original/Project_Final Report.docx", "docs/template/Project_Final Report.docx")
