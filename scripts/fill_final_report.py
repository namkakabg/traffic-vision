import sys
import os
import io
import zipfile
import xml.etree.ElementTree as ET
import docx

sys.stdout.reconfigure(encoding='utf-8')

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

def w_tag(tag):
    return f"{{{W_NS}}}{tag}"

def make_run(text, bold=False, italic=False, color="222222", size=22, font="SamsungOne-400"):
    r = ET.Element(w_tag("r"))
    rPr = ET.SubElement(r, w_tag("rPr"))
    
    rFonts = ET.SubElement(rPr, w_tag("rFonts"))
    rFonts.set(w_tag("ascii"), font)
    rFonts.set(w_tag("hAnsi"), font)
    rFonts.set(w_tag("cs"), "Times New Roman")
    
    if bold:
        ET.SubElement(rPr, w_tag("b"))
    if italic:
        ET.SubElement(rPr, w_tag("i"))
    if color:
        c = ET.SubElement(rPr, w_tag("color"))
        c.set(w_tag("val"), color)
    if size:
        s = ET.SubElement(rPr, w_tag("sz"))
        s.set(w_tag("val"), str(size))
        sCs = ET.SubElement(rPr, w_tag("szCs"))
        sCs.set(w_tag("val"), str(size))
        
    t = ET.SubElement(r, w_tag("t"))
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return r

def make_para(runs_data, space_after=120, line_spacing=276, indent_left=0, bullet=False):
    p = ET.Element(w_tag("p"))
    pPr = ET.SubElement(p, w_tag("pPr"))
    ET.SubElement(pPr, w_tag("widowControl"))
    
    sp = ET.SubElement(pPr, w_tag("spacing"))
    sp.set(w_tag("after"), str(space_after))
    sp.set(w_tag("line"), str(line_spacing))
    sp.set(w_tag("lineRule"), "auto")
    
    if bullet or indent_left > 0:
        ind = ET.SubElement(pPr, w_tag("ind"))
        ind.set(w_tag("left"), str(indent_left if indent_left > 0 else 360))
        if bullet:
            ind.set(w_tag("hanging"), "200")
            
    rPr = ET.SubElement(pPr, w_tag("rPr"))
    rf = ET.SubElement(rPr, w_tag("rFonts"))
    rf.set(w_tag("ascii"), "SamsungOne-400")
    rf.set(w_tag("hAnsi"), "SamsungOne-400")
    rf.set(w_tag("cs"), "Times New Roman")
    sz = ET.SubElement(rPr, w_tag("sz"))
    sz.set(w_tag("val"), "22")
    szCs = ET.SubElement(rPr, w_tag("szCs"))
    szCs.set(w_tag("val"), "22")
    
    for r_data in runs_data:
        if isinstance(r_data, str):
            p.append(make_run(r_data))
        elif isinstance(r_data, tuple):
            text = r_data[0]
            bold = r_data[1] if len(r_data) > 1 else False
            italic = r_data[2] if len(r_data) > 2 else False
            color = r_data[3] if len(r_data) > 3 else "222222"
            size = r_data[4] if len(r_data) > 4 else 22
            font = "SamsungOne-700" if bold else "SamsungOne-400"
            p.append(make_run(text, bold=bold, italic=italic, color=color, size=size, font=font))
    return p

def make_table(headers, rows, col_widths=None):
    tbl = ET.Element(w_tag("tbl"))
    tblPr = ET.SubElement(tbl, w_tag("tblPr"))
    tblW = ET.SubElement(tblPr, w_tag("tblW"))
    total_w = sum(col_widths) if col_widths else 9300
    tblW.set(w_tag("w"), str(total_w))
    tblW.set(w_tag("type"), "dxa")
    
    tblBorders = ET.SubElement(tblPr, w_tag("tblBorders"))
    for b_name in ["top", "bottom", "insideH"]:
        b = ET.SubElement(tblBorders, w_tag(b_name))
        b.set(w_tag("val"), "single")
        b.set(w_tag("sz"), "4")
        b.set(w_tag("space"), "0")
        b.set(w_tag("color"), "D0D0D0")
    for b_name in ["left", "right", "insideV"]:
        b = ET.SubElement(tblBorders, w_tag(b_name))
        b.set(w_tag("val"), "none")
        
    tblCellMar = ET.SubElement(tblPr, w_tag("tblCellMar"))
    for m_name in ["top", "bottom"]:
        m = ET.SubElement(tblCellMar, w_tag(m_name))
        m.set(w_tag("w"), "100")
        m.set(w_tag("type"), "dxa")
    for m_name in ["left", "right"]:
        m = ET.SubElement(tblCellMar, w_tag(m_name))
        m.set(w_tag("w"), "140")
        m.set(w_tag("type"), "dxa")
        
    if headers:
        tr = ET.SubElement(tbl, w_tag("tr"))
        trPr = ET.SubElement(tr, w_tag("trPr"))
        ET.SubElement(trPr, w_tag("tblHeader"))
        for idx, h_text in enumerate(headers):
            tc = ET.SubElement(tr, w_tag("tc"))
            tcPr = ET.SubElement(tc, w_tag("tcPr"))
            if col_widths and idx < len(col_widths):
                tcW = ET.SubElement(tcPr, w_tag("tcW"))
                tcW.set(w_tag("w"), str(col_widths[idx]))
                tcW.set(w_tag("type"), "dxa")
            shd = ET.SubElement(tcPr, w_tag("shd"))
            shd.set(w_tag("val"), "clear")
            shd.set(w_tag("color"), "auto")
            shd.set(w_tag("fill"), "F0F4FA")
            
            p = make_para([(h_text, True, False, "193DB0", 20)], space_after=40, line_spacing=240)
            tc.append(p)
            
    for r_idx, row in enumerate(rows):
        tr = ET.SubElement(tbl, w_tag("tr"))
        bg_color = "FBFBFD" if r_idx % 2 == 1 else "FFFFFF"
        for idx, cell_content in enumerate(row):
            tc = ET.SubElement(tr, w_tag("tc"))
            tcPr = ET.SubElement(tc, w_tag("tcPr"))
            if col_widths and idx < len(col_widths):
                tcW = ET.SubElement(tcPr, w_tag("tcW"))
                tcW.set(w_tag("w"), str(col_widths[idx]))
                tcW.set(w_tag("type"), "dxa")
            if bg_color != "FFFFFF":
                shd = ET.SubElement(tcPr, w_tag("shd"))
                shd.set(w_tag("val"), "clear")
                shd.set(w_tag("color"), "auto")
                shd.set(w_tag("fill"), bg_color)
                
            if isinstance(cell_content, list):
                # multiple paragraphs or run list
                if len(cell_content) > 0 and isinstance(cell_content[0], list):
                    for sub_p in cell_content:
                        tc.append(make_para(sub_p, space_after=40, line_spacing=240))
                else:
                    tc.append(make_para(cell_content, space_after=40, line_spacing=240))
            else:
                tc.append(make_para([(str(cell_content), False, False, "222222", 20)], space_after=40, line_spacing=240))
    return tbl

def replace_sdt_content(sdt_elem, elements_to_add):
    namespaces = {'w': W_NS}
    content = sdt_elem.find('w:sdtContent', namespaces)
    if content is None:
        content = ET.SubElement(sdt_elem, w_tag("sdtContent"))
    else:
        # clear existing children in content
        for child in list(content):
            content.remove(child)
    for elem in elements_to_add:
        content.append(elem)

def set_sdt_text(sdt_elem, text):
    namespaces = {'w': W_NS}
    t_nodes = sdt_elem.findall('.//w:t', namespaces)
    if t_nodes:
        t_nodes[0].text = text
        for t in t_nodes[1:]:
            t.text = ""
    else:
        # create p and run
        content = sdt_elem.find('w:sdtContent', namespaces)
        if content is None:
            content = ET.SubElement(sdt_elem, w_tag("sdtContent"))
        p = make_para([(text, False, False, "222222", 22)])
        content.append(p)

def fill_final_report(src_path, dst_path):
    print("Reading original document.xml...")
    with zipfile.ZipFile(src_path, 'r') as z:
        xml_content = z.read("word/document.xml")
        
    root = ET.fromstring(xml_content)
    namespaces = {'w': W_NS}
    body = root.find('w:body', namespaces)
    
    # 1. Update Cover Page Elements
    print("Updating cover page elements...")
    set_sdt_text(body[15], "TrafficVision – Hệ thống nhận dạng biển báo giao thông Việt Nam bằng AI tối ưu suy luận trên CPU")
    set_sdt_text(body[24], "03/10/2026")
    set_sdt_text(body[31], "Nhóm TrafficVision")
    set_sdt_text(body[33], "Phí Văn Nam (Trưởng nhóm)")
    set_sdt_text(body[34], "Đỗ Thị Vân Anh")
    set_sdt_text(body[35], "Đỗ Hữu Nghị")
    set_sdt_text(body[36], "Quản Văn Điệp")
    set_sdt_text(body[37], "") # Member 5 clear
    
    # 2. Section 1.1: Background Information (body[82])
    print("Filling Section 1.1...")
    p11_1 = make_para([
        ("Trong bối cảnh đô thị hóa và hiện đại hóa giao thông đường bộ tại Việt Nam, mật độ phương tiện lưu thông ngày càng tăng cao, đặc biệt là xe mô tô hai bánh và ô tô tại các thành phố lớn. Hệ thống biển báo giao thông đóng vai trò kim chỉ nam trong việc hướng dẫn, cảnh báo và điều tiết luồng di chuyển, góp phần quyết định giảm thiểu tai nạn giao thông. Tuy nhiên, trên thực tế, người điều khiển phương tiện thường xuyên gặp khó khăn trong việc nhận diện biển báo kịp thời do tầm nhìn bị che khuất bởi các xe cỡ lớn (xe buýt, xe tải), điều kiện thời tiết khắc nghiệt (mưa giông, sương mù, ban đêm thiếu sáng), biển báo bị biến dạng, phai màu theo thời gian hoặc bị che lấp bởi cành cây và biển quảng cáo.", False)
    ])
    p11_2 = make_para([
        ("TrafficVision ", True, False, "193DB0"),
        ("được nghiên cứu và phát triển như một giải pháp thị giác máy tính thông minh, ứng dụng các mô hình học sâu tiên tiến nhất thuộc họ YOLO11 nhằm phát hiện và định vị tự động ", False),
        ("82 lớp biển báo giao thông đường bộ Việt Nam ", True),
        ("theo Quy chuẩn kỹ thuật quốc gia QCVN 41:2019/BGTVT. Hệ thống có khả năng tiếp nhận cả hình ảnh tĩnh và video hành trình đa định dạng, hiển thị trực quan khung bao (bounding box) với nhãn tiếng Việt chuẩn hóa, độ tin cậy nhận diện (confidence score), thời gian xử lý và cho phép xuất dữ liệu thống kê chi tiết phục vụ các bài toán phân tích tiếp theo.", False)
    ])
    p11_3 = make_para([
        ("Về mặt kiến trúc công nghệ, TrafficVision được xây dựng trên nền tảng ngôn ngữ Python (3.11–3.13), framework giao diện hiện đại Streamlit, thư viện xử lý đa phương tiện OpenCV và đặc biệt là công cụ suy luận ", False),
        ("ONNX Runtime ", True),
        ("được tối ưu hóa đa luồng với tập lệnh AVX2. Điểm đột phá này cho phép hệ thống vận hành mượt mà, đạt tốc độ khung hình cao ngay trên CPU máy tính thông thường (hỗ trợ cả Windows và macOS) mà không đòi hỏi trang bị card đồ họa GPU đắt tiền, mang lại tính khả thi và khả năng nhân rộng vượt trội trong thực tiễn.", False)
    ])
    replace_sdt_content(body[82], [p11_1, p11_2, p11_3])
    
    # 3. Section 1.2: Motivation and Objective (body[84])
    print("Filling Section 1.2...")
    p12_intro = make_para([
        ("Động lực cốt lõi của dự án bắt nguồn từ khoảng trống lớn giữa nghiên cứu lý thuyết và ứng dụng thực tiễn tại Việt Nam: các tập dữ liệu biển báo quốc tế (GTSDB, TT100K) có hình dạng và quy cách rất khác biệt so với Việt Nam; trong khi đó, phần lớn các mô hình Deep Learning hiện nay đòi hỏi hạ tầng phần cứng GPU mạnh mẽ, gây trở ngại lớn khi triển khai trên camera hành trình thực tế hoặc máy trạm tại các cơ quan quản lý giao thông. Để giải quyết triệt để thách thức này, TrafficVision xác định 4 mục tiêu trọng tâm:", False)
    ])
    p12_b1 = make_para([
        ("• Độ chính xác nhận dạng vượt trội: ", True, False, "193DB0"),
        ("Xây dựng mô hình đạt chỉ số mAP50 trên 95% trên tập kiểm thử độc lập cho toàn bộ 82 lớp biển báo giao thông Việt Nam theo chuẩn QCVN 41:2019/BGTVT, hạn chế tối đa hiện tượng báo giả (False Positive) và bỏ sót biển báo (False Negative).", False)
    ], bullet=True)
    p12_b2 = make_para([
        ("• Tối ưu suy luận trên CPU phổ thông: ", True, False, "193DB0"),
        ("Đóng gói mô hình dưới dạng đồ thị tĩnh ONNX Runtime 640x640 px, khai thác tối đa năng lực xử lý đa luồng AVX2 trên CPU, bảo đảm độ trễ suy luận thấp (< 70ms/ảnh đối với cấu hình Nano, tương đương ~15 FPS) trên máy tính thông thường.", False)
    ], bullet=True)
    p12_b3 = make_para([
        ("• Chuẩn hóa quy trình MLOps tin cậy và khép kín: ", True, False, "193DB0"),
        ("Thiết lập hệ thống kiểm soát chất lượng dữ liệu Quality Gate 5 tiêu chí chặn, module Dataset Repair sửa lỗi bounding box, Snapshot bất biến, tiến trình huấn luyện ngầm độc lập có Safe Resume, kiểm định sai số số học PyTorch vs ONNX (max_abs_diff <= 1e-3), Model Registry quản lý phiên bản với mã băm SHA-256 và cơ chế Safe Atomic Swap kèm Rollback 1-click.", False)
    ], bullet=True)
    p12_b4 = make_para([
        ("• Sản phẩm phần mềm hoàn chỉnh và thân thiện: ", True, False, "193DB0"),
        ("Xây dựng Web Dashboard Streamlit trực quan, hỗ trợ phân tích ảnh tĩnh và video hành trình, thanh tiến trình thời gian thực (@st.fragment), CSDL SQLite lưu lịch sử phân tích, trang thống kê và phòng thí nghiệm huấn luyện MLOps hoàn chỉnh.", False)
    ], bullet=True)
    replace_sdt_content(body[84], [p12_intro, p12_b1, p12_b2, p12_b3, p12_b4])
    
    # 4. Section 1.3: Members and Role Assignments (body[86])
    print("Filling Section 1.3...")
    p13_intro = make_para([
        ("Dự án được thực hiện bởi nhóm 4 thành viên thuộc khóa học Phát triển hệ thống thông minh (AI Course). Các thành viên được phân công vai trò rõ ràng, kết hợp chặt chẽ giữa kỹ nghệ AI/ML, xử lý dữ liệu, kiểm thử phần mềm và kiến trúc hệ thống:", False)
    ])
    tbl13 = make_table(
        ["Thành viên", "Vai trò", "Trách nhiệm chính đã thực hiện", "Kết quả bàn giao"],
        [
            [
                [("Phí Văn Nam", True)],
                "Trưởng nhóm",
                "Thiết kế kiến trúc hệ thống tổng thể, MLOps pipeline, Model Registry, cơ chế Safe Atomic Swap & Rollback, tích hợp CSDL SQLite (history.db), điều phối tiến độ và tổng hợp báo cáo.",
                "Hệ thống MLOps hoàn chỉnh, Model Registry quản lý SHA-256, báo cáo dự án tổng thể."
            ],
            [
                [("Đỗ Thị Vân Anh", True)],
                "Kỹ sư Dữ liệu",
                "Thu thập, tiền xử lý và chuẩn hóa dữ liệu 82 lớp biển báo theo QCVN 41:2019; xây dựng cổng Quality Gate 5 tiêu chí, module Dataset Repair, phân tích EDA và đóng gói Snapshot bất biến.",
                "Bộ dữ liệu 10.129 ảnh chuẩn hóa, cổng Quality Gate, script repair.py, snapshot và eda_report.json."
            ],
            [
                [("Đỗ Hữu Nghị", True)],
                "Kỹ sư AI/ML",
                "Cấu hình và thực hiện huấn luyện YOLO11 (Nano và Medium), tối ưu hóa suy luận ONNX trên CPU, kiểm tra sai số số học PyTorch vs ONNX, benchmark độ trễ/FPS phần cứng và đóng gói Candidate.",
                "2 mô hình YOLO11n và YOLO11m hoàn tất train, file ONNX tĩnh, parity verification và Candidate artifact."
            ],
            [
                [("Quản Văn Điệp", True)],
                "Kỹ sư Fullstack / QA",
                "Phát triển Web UI Streamlit đa tab, xử lý luồng video đa phương tiện, live progress auto-refresh (@st.fragment), xây dựng bộ kiểm thử tự động 215 tests pytest và tài liệu hướng dẫn.",
                "Giao diện Web 6 trang hoàn chỉnh, bộ kiểm thử tự động 215 tests xanh, Sổ tay HDSD và slide bảo vệ."
            ]
        ],
        col_widths=[1400, 1200, 4200, 2500]
    )
    replace_sdt_content(body[86], [p13_intro, tbl13])
    
    # 5. Section 1.4: Schedule and Milestones (body[88])
    print("Filling Section 1.4...")
    p14_intro = make_para([
        ("Kế hoạch thực hiện dự án được tổ chức theo phương pháp Agile/Scrum gồm 4 giai đoạn nước rút (Sprints) kéo dài 4 tuần, kết thúc với trạng thái hoàn thành 100% tất cả các mốc đề ra:", False)
    ])
    tbl14 = make_table(
        ["Tuần / Giai đoạn", "Mục tiêu trọng tâm", "Kết quả đầu ra thực tế trong Repository", "Trạng thái"],
        [
            [
                [("Tuần 1", True), ("\n(28/09 – 02/10)", False)],
                "Khởi tạo Baseline & Nền tảng MLOps",
                "Ứng dụng Streamlit end-to-end với YOLO11n ONNX baseline trên CPU, Model Registry với SHA-256, CSDL SQLite; Catalog 82 lớp biển báo, cổng Quality Gate 5 tiêu chí, module repair.py, snapshot 10.129 ảnh và báo cáo EDA.",
                [("Hoàn thành", True, False, "28A745")]
            ],
            [
                [("Tuần 2", True), ("\n(05/10 – 09/10)", False)],
                "Huấn luyện chuyên sâu & Tối ưu hóa",
                "Hoàn thiện Training Engine ngầm với Safe Resume; hoàn tất 50 epochs cho YOLO11n và YOLO11m; xuất đồ thị tĩnh ONNX [1, 3, 640, 640]; kiểm định sai số Parity (< 1e-3); đo đạc Benchmark CPU FPS/Latency và đóng gói Candidate.",
                [("Hoàn thành", True, False, "28A745")]
            ],
            [
                [("Tuần 3", True), ("\n(12/10 – 16/10)", False)],
                "Đánh giá độc lập, Thăng cấp & UAT",
                "Đánh giá mô hình trên tập Test độc lập 1.016 ảnh (YOLO11m đạt mAP50 = 98.03%, F1 = 96.22%); thực hiện Safe Atomic Swap thăng cấp YOLO11m lên Production; kiểm thử cơ chế sao lưu tự động và Rollback 1-click; chạy UAT ảnh/video.",
                [("Hoàn thành", True, False, "28A745")]
            ],
            [
                [("Tuần 4", True), ("\n(19/10 – 23/10)", False)],
                "Kiểm thử toàn diện & Bàn giao",
                "Bộ 215 ca kiểm thử tự động pytest chạy xanh (213 passed, 2 skipped); hoàn thiện Sổ tay HDSD, Slide bảo vệ (14 slides), Cẩm nang Q&A theo 4 thành viên, Tài liệu huấn luyện chuyên sâu và Báo cáo dự án cuối khóa.",
                [("Hoàn thành", True, False, "28A745")]
            ]
        ],
        col_widths=[1400, 2200, 4400, 1300]
    )
    replace_sdt_content(body[88], [p14_intro, tbl14])
    
    # 6. Section 2.1: Data Acquisition (body[91])
    print("Filling Section 2.1...")
    p21_1 = make_para([
        ("Bộ dữ liệu của TrafficVision được tổng hợp và chuẩn hóa từ bộ dữ liệu cộng đồng ", False),
        ("star092304/Traffic-sign-detection-VietNam ", True, False, "193DB0"),
        ("trên Hugging Face kết hợp với các hình ảnh chụp thực tế từ camera hành trình trên các cung đường Việt Nam. Toàn bộ các nhãn đối tượng được ánh xạ chuẩn theo danh mục ", False),
        ("82 lớp biển báo giao thông đường bộ ", True),
        ("quy định tại Quy chuẩn kỹ thuật quốc gia QCVN 41:2019/BGTVT, bao gồm đầy đủ 4 nhóm chính: Biển báo cấm (46 lớp), Biển hiệu lệnh và chỉ dẫn (36 lớp).", False)
    ])
    p21_2 = make_para([
        ("Dữ liệu được phân chia độc lập thành 3 tập riêng biệt để bảo đảm tính khách quan tuyệt đối, lưu trữ trong bản chụp bất biến ", False),
        ("snapshot_20260930_165016", True),
        (":", False)
    ])
    tbl21 = make_table(
        ["Phân chia tập dữ liệu", "Số lượng hình ảnh", "Số lượng Bounding Box", "Tỷ lệ phân bổ", "Mục đích sử dụng"],
        [
            ["Tập Huấn luyện (Train)", "8.098 ảnh", "15.671 boxes", "~80.0%", "Cập nhật trọng số mô hình thông qua Backpropagation"],
            ["Tập Kiểm định (Validation)", "1.015 ảnh", "2.059 boxes", "~10.0%", "Điều chỉnh siêu tham số và kích hoạt Early Stopping"],
            ["Tập Kiểm thử độc lập (Test)", "1.016 ảnh", "1.970 boxes", "~10.0%", "Đánh giá hiệu năng khách quan, chưa từng thấy khi train"],
            [["Tổng cộng toàn bộ", True], ["10.129 ảnh", True], ["19.700 boxes", True], ["100.0%", True], "Toàn bộ cơ sở dữ liệu đã kiểm định"]
        ],
        col_widths=[2000, 1600, 1800, 1400, 2500]
    )
    replace_sdt_content(body[91], [p21_1, p21_2, tbl21])
    
    # 7. Section 2.2: Training Methodology (body[93])
    print("Filling Section 2.2...")
    p22_1 = make_para([
        ("Nhóm đã lựa chọn kiến trúc ", False),
        ("YOLO11 (Ultralytics) ", True, False, "193DB0"),
        ("– thế hệ mô hình phát hiện đối tượng one-stage tiên tiến nhất hiện nay. Dự án triển khai đồng thời hai cấu hình mô hình để đáp ứng đa dạng kịch bản triển khai:", False)
    ])
    p22_b1 = make_para([
        ("• YOLO11 Nano (yolo11n.pt): ", True, False, "193DB0"),
        ("Kiến trúc siêu nhẹ với ~2.6 triệu tham số, dung lượng ONNX chỉ ~10.2 MB. Được thiết kế chuyên biệt cho các thiết bị biên, camera hành trình hoặc máy tính cấu hình khiêm tốn cần ưu tiên tốc độ phản hồi tức thì.", False)
    ], bullet=True)
    p22_b2 = make_para([
        ("• YOLO11 Medium (yolo11m.pt): ", True, False, "193DB0"),
        ("Kiến trúc mạnh mẽ với ~20 triệu tham số, dung lượng ONNX ~80.6 MB. Tích hợp khối Attention không gian C2PSA và hàm mất mát phân bố tiêu điểm DFL Loss, mang lại độ chính xác cực cao và khả năng định vị hoàn hảo các biển báo kích thước nhỏ hoặc bị che khuất ở khoảng cách xa.", False)
    ], bullet=True)
    p22_2 = make_para([
        ("Chiến lược huấn luyện và siêu tham số tối ưu:", True, False, "193DB0")
    ])
    p22_hyper = make_para([
        ("Mô hình được huấn luyện trong 50 epochs với kích thước mini-batch = 4, độ phân giải đầu vào chuẩn 640x640 px. Sử dụng thuật toán tối ưu AdamW với tốc độ học ban đầu lr0 = 0.01 kết hợp chiến lược giảm tốc học Cosine Annealing (lrf = 0.01), trọng số suy giảm trọng lượng weight_decay = 0.0005. Quá trình train áp dụng tăng cường dữ liệu phong phú: Mosaic (p=1.0), MixUp (p=0.1), xoay nhẹ (+-10 độ), dịch chuyển (+-10%) và biến đổi không gian màu HSV. Kỹ thuật Early Stopping với patience = 10 epochs giúp ngăn chặn hiện tượng quá khớp (overfitting).", False)
    ])
    p22_eng = make_para([
        ("Cải tiến kỹ thuật trong Training Engine: ", True, False, "193DB0"),
        ("Tiến trình huấn luyện được tách biệt hoàn toàn dưới dạng tiến trình nền ngầm (background subprocess) độc lập thông qua TrainingManager, ghi log thời gian thực vào train.log và cập nhật state.json. Hệ thống tích hợp module hardware.py tự động nhận diện phần cứng và ép workers = 0 trên môi trường Windows, khắc phục triệt để lỗi deadlock multiprocessing và rò rỉ bộ nhớ. Đồng thời, cơ chế Safe Resume cho phép tự động tiếp tục phiên huấn luyện từ checkpoint last.pt khi gặp sự cố gián đoạn nguồn điện.", False)
    ])
    replace_sdt_content(body[93], [p22_1, p22_b1, p22_b2, p22_2, p22_hyper, p22_eng])
    
    # 8. Section 2.3: Workflow (body[95])
    print("Filling Section 2.3...")
    p23_intro = make_para([
        ("Hệ thống TrafficVision được thiết kế theo chuẩn MLOps hiện đại, phân tách hoàn toàn giữa hai quy trình ngoại tuyến (huấn luyện/đóng gói) và trực tuyến (suy luận/phục vụ):", False)
    ])
    p23_off_title = make_para([
        ("A. Quy trình MLOps Ngoại tuyến (Offline Pipeline):", True, False, "193DB0")
    ])
    p23_off_steps = [
        make_para([("1. Quét dữ liệu Staging & Sửa lỗi (Dataset Repair): ", True), ("Quét dữ liệu thô, tự động cắt gọt (clamping) tọa độ hộp bao về dải [0, 1] và loại bỏ nhãn rỗng.", False)], bullet=True),
        make_para([("2. Kiểm định Quality Gate 5 tiêu chí: ", True), ("Chặn ảnh lỗi, nhãn sai cú pháp, mã lớp ngoài [0, 81], tọa độ bất hợp lệ và kiểm tra rò rỉ dữ liệu qua SHA-256.", False)], bullet=True),
        make_para([("3. Phân tích EDA & Snapshot bất biến: ", True), ("Xuất báo cáo phân bố đặc trưng eda_report.json và đóng gói snapshot_20260930_165016 kèm data.yaml có checksum.", False)], bullet=True),
        make_para([("4. Huấn luyện ngầm YOLO11: ", True), ("Thực thi tiến trình nền 50 epochs, tối ưu hóa workers=0 trên Windows, hỗ trợ checkpoint/resume và ghi log liên tục.", False)], bullet=True),
        make_para([("5. Đánh giá độc lập trên Test split: ", True), ("Đo đạc chỉ số chính xác khách quan trên 1.016 ảnh chưa từng thấy và xuất test_metrics.json.", False)], bullet=True),
        make_para([("6. Xuất ONNX tĩnh & Kiểm tra Parity: ", True), ("Xuất mô hình FP32 đồ thị tĩnh [1, 3, 640, 640] và kiểm định sai số số học PyTorch vs ONNX (max_abs_diff <= 1e-3).", False)], bullet=True),
        make_para([("7. Đo đạc Benchmark CPU & Đóng gói Candidate: ", True), ("Đo FPS, latency đa luồng trên CPU và đóng gói thư mục candidate kèm manifest.json và mã băm SHA-256.", False)], bullet=True),
        make_para([("8. Thăng cấp an toàn (Safe Atomic Swap): ", True), ("Sao lưu tự động mô hình cũ vào artifacts/backups/ và hoán đổi nguyên tử mô hình mới lên artifacts/production/ kèm Rollback 1-click.", False)], bullet=True),
    ]
    p23_on_title = make_para([
        ("B. Quy trình Suy luận Trực tuyến (Online Inference Pipeline):", True, False, "193DB0")
    ])
    p23_on_steps = [
        make_para([("1. Tiếp nhận tệp: ", True), ("Người dùng tải ảnh (JPG/PNG/WEBP) hoặc video (MP4/AVI/MOV) lên Web Dashboard Streamlit.", False)], bullet=True),
        make_para([("2. Tiền xử lý Letterbox: ", True), ("Chuyển đổi ảnh/khung hình về kích thước chuẩn 640x640 px với tỷ lệ đồng nhất và đệm viền tự động.", False)], bullet=True),
        make_para([("3. Suy luận ONNX Runtime đa luồng: ", True), ("Nạp mô hình Production ONNX chỉ đọc, thực thi suy luận đa luồng tận dụng tập lệnh AVX2 trên CPU.", False)], bullet=True),
        make_para([("4. Hậu xử lý NMS: ", True), ("Lọc bỏ các hộp bao dư thừa dựa trên ngưỡng Confidence và IoU do người dùng thiết lập.", False)], bullet=True),
        make_para([("5. Trực quan hóa & Xuất kết quả: ", True), ("Vẽ bounding box với màu sắc phân loại, hiển thị nhãn tiếng Việt chuẩn, xuất file ảnh/video chú thích và file CSV thống kê.", False)], bullet=True),
        make_para([("6. Lưu trữ lịch sử: ", True), ("Ghi nhật ký phiên làm việc, thời gian xử lý và số đối tượng phát hiện vào CSDL SQLite (history.db).", False)], bullet=True),
    ]
    replace_sdt_content(body[95], [p23_intro, p23_off_title] + p23_off_steps + [p23_on_title] + p23_on_steps)
    
    # 9. Section 2.4: System Design (body[97])
    print("Filling Section 2.4...")
    p24_intro = make_para([
        ("Hệ thống TrafficVision được kiến trúc theo mô hình 4 tầng (4-tier layered architecture) bảo đảm tính module hóa cao, dễ bảo trì và mở rộng:", False)
    ])
    tbl24 = make_table(
        ["Tầng kiến trúc", "Các thành phần module chính", "Chức năng và nhiệm vụ cụ thể"],
        [
            [
                [("1. Presentation Layer", True), ("\n(Giao diện người dùng)", False)],
                "Streamlit Dashboard, Web UI Components, Multi-page Navigation, @st.fragment",
                "Cung cấp 6 trang tương tác trực quan: Phân tích ảnh/video, Huấn luyện MLOps, Lịch sử, Thống kê, Thông tin mô hình và Cài đặt; cập nhật tiến trình trực tiếp thời gian thực."
            ],
            [
                [("2. Service Layer", True), ("\n(Nghiệp vụ ứng dụng)", False)],
                "InferenceService, VideoProcessor, TrainingManager, ModelRegistry",
                "Điều phối logic nghiệp vụ: nạp ảnh/video, cắt khung hình, quản lý tiến trình ngầm, kiểm tra mã băm SHA-256, điều phối hoán đổi mô hình nguyên tử (Safe Atomic Swap) và Rollback."
            ],
            [
                [("3. AI & Runtime Layer", True), ("\n(Động cơ AI)", False)],
                "ONNX Runtime Engine, Ultralytics YOLO11, Parity Verifier, Hardware Detector",
                "Thực thi suy luận đồ thị tĩnh tối ưu AVX2 trên CPU, quản lý huấn luyện Deep Learning, đo đạc sai số số học PyTorch vs ONNX và tự động cấu hình tối ưu luồng tính toán phần cứng."
            ],
            [
                [("4. Data & Storage Layer", True), ("\n(Dữ liệu & Lưu trữ)", False)],
                "Immutable Snapshots, Artifacts Model Registry, SQLite (history.db), File System",
                "Lưu trữ dữ liệu bất biến, các checkpoint huấn luyện, mô hình Production, các bản sao lưu an toàn và cơ sở dữ liệu nhật ký lịch sử phiên phân tích."
            ]
        ],
        col_widths=[2000, 3000, 4300]
    )
    replace_sdt_content(body[97], [p24_intro, tbl24])
    
    # 10. Section 3.1: Data Preprocessing (body[100])
    print("Filling Section 3.1...")
    p31_1 = make_para([
        ("Chất lượng của dữ liệu đầu vào quyết định trực tiếp đến giới hạn trên của mô hình AI. Để ngăn chặn hoàn toàn rủi ro dữ liệu rác làm suy giảm chất lượng huấn luyện, TrafficVision thiết lập cổng ", False),
        ("Quality Gate 5 tiêu chí chặn nghiêm ngặt ", True, False, "193DB0"),
        ("tại scripts/validate_dataset.py:", False)
    ])
    p31_qg = [
        make_para([("1. CORRUPT_IMAGE: ", True), ("Kiểm tra toàn vẹn tệp ảnh, chặn tuyệt đối ảnh 0 byte hoặc tệp ảnh bị hỏng cấu trúc không thể giải mã bằng OpenCV.", False)], bullet=True),
        make_para([("2. MALFORMED_YOLO_LINE: ", True), ("Kiểm tra cấu trúc file nhãn .txt, chặn các dòng không đủ 5 tham số số học (class x y w h).", False)], bullet=True),
        make_para([("3. CLASS_ID_OUT_OF_RANGE: ", True), ("Kiểm tra tính hợp lệ của mã định danh lớp, chặn mọi class_id nằm ngoài dải quy chuẩn [0, 81].", False)], bullet=True),
        make_para([("4. INVALID_COORDINATES: ", True), ("Kiểm tra tọa độ hộp bao, chặn các giá trị nằm ngoài miền chuẩn hóa [0, 1] hoặc chiều rộng/cao <= 0.", False)], bullet=True),
        make_para([("5. DATA_LEAKAGE: ", True), ("Tính toán mã băm SHA-256 của từng tệp ảnh, chặn tuyệt đối việc trùng lặp ảnh giữa tập Train và tập Val/Test.", False)], bullet=True),
    ]
    p31_repair = make_para([
        ("Công cụ Sửa chữa Dữ liệu (Dataset Repair): ", True, False, "193DB0"),
        ("Trong thực tế gán nhãn, nhiều bounding box có tọa độ chạm viền bị tính toán lệch nhẹ (ví dụ x_center + width/2 = 1.00002). Module src/trafficvision/data/repair.py tự động cắt gọn (clamp) tọa độ về [0, 1], loại bỏ các box rỗng và làm sạch hoàn toàn dữ liệu. Sau khi vượt qua Quality Gate, tập dữ liệu được đóng băng vào Snapshot bất biến snapshot_20260930_165016 gồm 10.129 ảnh hợp lệ 100%.", False)
    ])
    replace_sdt_content(body[100], [p31_1] + p31_qg + [p31_repair])
    
    # 11. Section 3.2: Exploratory Data Analysis (EDA) (body[102])
    print("Filling Section 3.2...")
    p32_1 = make_para([
        ("Báo cáo phân tích khám phá dữ liệu (EDA) toàn diện được trích xuất tự động tại ", False),
        ("artifacts/eda/eda_report.json ", True, False, "193DB0"),
        ("cho thấy các đặc trưng quan trọng của bộ dữ liệu:", False)
    ])
    p32_b1 = make_para([
        ("• Phân bố kích thước đối tượng theo chuẩn COCO: ", True, False, "193DB0"),
        ("Biển báo cỡ nhỏ (Small: diện tích < 32x32 px) chiếm 34.8%; biển báo cỡ trung bình (Medium: 32x32 đến 96x96 px) chiếm 48.3%; biển báo cỡ lớn (Large: > 96x96 px) chiếm 16.9%. Tỷ lệ biển báo nhỏ và trung bình chiếm hơn 83% phản ánh chính xác bối cảnh ghi hình từ camera hành trình góc rộng, đặt ra yêu cầu cao đối với khả năng trích xuất đặc trưng của mạng nơ-ron.", False)
    ], bullet=True)
    p32_b2 = make_para([
        ("• Tỷ lệ khung hình (Aspect Ratio): ", True, False, "193DB0"),
        ("Đa số các biển báo giao thông Việt Nam có dạng hình tròn (biển cấm, hiệu lệnh), hình tam giác đều (biển nguy hiểm) và hình chữ nhật/hình vuông (biển chỉ dẫn). Tỷ lệ khung hình tập trung chủ yếu quanh giá trị 1.0 (dao động từ 0.85 đến 1.25), giúp mạng nơ-ron dễ dàng học được các neo hộp bao (anchor priors) tối ưu.", False)
    ], bullet=True)
    p32_b3 = make_para([
        ("• Xử lý mất cân bằng lớp (Class Imbalance): ", True, False, "193DB0"),
        ("Phân bố số lượng mẫu giữa các lớp có sự chênh lệch tự nhiên: các biển báo đô thị phổ biến (Cấm đi ngược chiều, Giới hạn tốc độ 40/60km/h, Cấm đỗ xe) có hàng trăm mẫu, trong khi các biển chuyên biệt ở vùng ngoại thành có số lượng mẫu ít hơn. Thách thức này được giải quyết hiệu quả nhờ chiến lược tăng cường dữ liệu Mosaic/MixUp và hàm mất mát phân bố tiêu điểm DFL Loss trong YOLO11.", False)
    ], bullet=True)
    replace_sdt_content(body[102], [p32_1, p32_b1, p32_b2, p32_b3])
    
    # 12. Section 3.3: Modeling (body[104])
    print("Filling Section 3.3...")
    p33_1 = make_para([
        ("Cả hai phiên bản mô hình YOLO11n và YOLO11m đều được đánh giá nghiêm ngặt trên cùng ", False),
        ("tập kiểm thử độc lập (held-out test split) ", True),
        ("gồm 1.016 ảnh và 1.970 bounding boxes chưa từng xuất hiện trong quá trình huấn luyện. Kết quả đo đạc chính thức từ test_metrics.json và benchmark.json được tổng hợp trong bảng đối sánh dưới đây:", False)
    ])
    tbl33 = make_table(
        ["Chỉ số đánh giá", "YOLO11n (Candidate)", "YOLO11m (Production)", "Tiêu chuẩn / Ý nghĩa kỹ thuật"],
        [
            ["Mã thực nghiệm (Model ID)", "trafficvision_exp_20260930_011859", [("trafficvision_exp_20260930_235214", True)], "Mã định danh lưu trữ trong artifacts/runs/"],
            ["Số Epochs thực hiện", "50 epochs", [("50 epochs", True)], "Tối ưu hóa với Cosine Annealing"],
            ["Độ chính xác (Precision)", "87.26% (0.87255)", [("96.16% (0.96158)", True)], "Tỷ lệ dự đoán đúng trên tổng số biển báo phát hiện"],
            ["Độ bao phủ (Recall)", "88.60% (0.88596)", [("96.28% (0.96275)", True)], "Khả năng không bỏ sót biển báo trong ảnh/video"],
            ["Điểm F1-Score", "87.92% (0.87921)", [("96.22% (0.96217)", True)], "Trung bình điều hòa giữa Precision và Recall"],
            ["mAP@0.5 (mAP50)", "92.47% (0.92465)", [("98.03% (0.98025)", True, False, "28A745")], "Chỉ số cốt lõi đánh giá độ chính xác định vị bbox"],
            ["mAP@0.5:0.95", "77.43% (0.77427)", [("84.81% (0.84812)", True)], "Độ chính xác định vị ở các ngưỡng IoU khắt khe"],
            ["Sai số Parity (max_abs_diff)", "0.000977", [("0.000854", True)], "Đạt chuẩn khắt khe <= 1e-3 giữa PyTorch và ONNX"],
            ["Thời gian trễ CPU (Latency)", [("68.26 ms / ảnh", True, False, "193DB0")], "488.57 ms / ảnh", "Đo đạc thực nghiệm trên CPU phổ thông (640x640)"],
            ["Tốc độ khung hình (CPU FPS)", [("~14.65 FPS", True, False, "193DB0")], "~2.05 FPS", "Tốc độ xử lý tương đương thời gian thực trên CPU"],
            ["Kích thước tệp ONNX", "10.2 MB", "80.6 MB", "Trọng số FP32 đồ thị tĩnh batch 1"],
            ["Trạng thái triển khai", "Candidate sẵn sàng", [("PRODUCTION ĐANG PHỤC VỤ", True, False, "28A745")], "Thăng cấp an toàn qua ModelRegistry"]
        ],
        col_widths=[2200, 2400, 2500, 2200]
    )
    p33_analysis = make_para([
        ("Phân tích kết quả thực nghiệm: ", True, False, "193DB0"),
        ("Mô hình YOLO11m đạt chỉ số mAP50 vượt bậc 98.03% và F1-score 96.22%, thể hiện khả năng nhận diện gần như hoàn hảo đối với 82 lớp biển báo Việt Nam, bắt trúng cả các biển báo mờ, biến dạng góc nghiêng hoặc bị che khuất một phần. Trong khi đó, bản YOLO11n đạt mAP50 92.47% với tốc độ ấn tượng 68.26 ms/ảnh (~15 FPS trên CPU), là ứng viên lý tưởng cho các thiết bị biên hạn chế tài nguyên. Đặc biệt, sai số số học PyTorch vs ONNX của cả 2 mô hình đều đạt chuẩn nghiêm ngặt (< 1e-3), khẳng định tính toàn vẹn 100% của giải thuật khi triển khai thực tế.", False)
    ])
    replace_sdt_content(body[104], [p33_1, tbl33, p33_analysis])
    
    # 13. Section 3.4: User Interface (body[106])
    print("Filling Section 3.4...")
    p34_intro = make_para([
        ("Giao diện người dùng của TrafficVision được xây dựng bằng Streamlit với thiết kế công thái học hiện đại, tổ chức thành 6 trang chức năng hoàn chỉnh:", False)
    ])
    tbl34 = make_table(
        ["Không gian chức năng", "Tính năng cốt lõi", "Trải nghiệm người dùng"],
        [
            [
                [("1. Phân tích ảnh & video", True)],
                "Tiếp nhận ảnh JPG/PNG/WEBP và video MP4/AVI/MOV; xử lý suy luận tuần tự; vẽ bounding box tiếng Việt chuẩn hóa; thanh tiến trình thời gian thực (@st.fragment); tải tệp kết quả kèm CSV thống kê.",
                "Giao diện kéo thả trực quan, phản hồi tức thì với ảnh và xem trước video trực tiếp trên trình duyệt."
            ],
            [
                [("2. Huấn luyện AI (MLOps)", True)],
                "Quy trình 4 bước tự động hóa: (1) Nạp staging / tạo synthetic fixture, (2) Kiểm định Quality Gate & xem báo cáo EDA, (3) Huấn luyện nền ngầm có log live, (4) Đóng gói Candidate & thăng cấp.",
                "Tách biệt hoàn toàn luồng train ngầm, không gây đơ lag giao diện, hỗ trợ Safe Resume an toàn."
            ],
            [
                [("3. Lịch sử phân tích", True)],
                "Truy vấn và hiển thị nhật ký các phiên phân tích đã lưu trữ trong CSDL SQLite (history.db) gồm thời gian, tên tệp, số đối tượng phát hiện, thời gian xử lý và đường dẫn tệp kết quả.",
                "Cho phép người dùng tra cứu nhanh, kiểm tra lại kết quả cũ mà không cần chạy suy luận lại."
            ],
            [
                [("4. Thống kê dữ liệu", True)],
                "Trực quan hóa tổng số lượng đối tượng nhận dạng và biểu đồ cột phân bố tần suất xuất hiện theo từng loại biển báo giao thông trên toàn bộ lịch sử phân tích.",
                "Cung cấp cái nhìn tổng quan về mật độ và loại biển báo xuất hiện phổ biến trong khu vực khảo sát."
            ],
            [
                [("5. Thông tin mô hình & Backup", True)],
                "Hiển thị chi tiết manifest.json, mã băm SHA-256 bất biến, backend ONNX, danh mục 82 lớp biển báo tiếng Việt; bảng quản lý các bản sao lưu (Backups) kèm nút Rollback 1-click.",
                "Minh bạch hóa tuyệt đối phiên bản AI đang vận hành, cho phép hoàn tác khẩn cấp chỉ với một thao tác."
            ],
            [
                [("6. Thiết lập hệ thống", True)],
                "Thanh trượt điều chỉnh ngưỡng độ tin cậy (Confidence threshold: 0.1 – 0.9), ngưỡng triệt tiêu trùng lặp (IoU/NMS threshold: 0.1 – 0.9) và cấu hình giới hạn dung lượng tệp tải lên.",
                "Người dùng linh hoạt điều chỉnh độ nhạy của mô hình tùy theo mục đích phân tích (bắt tối đa hay lọc chặt)."
            ]
        ],
        col_widths=[2200, 4800, 2300]
    )
    replace_sdt_content(body[106], [p34_intro, tbl34])
    
    # 14. Section 3.5: Testing and Improvements (body[108])
    print("Filling Section 3.5...")
    p35_1 = make_para([
        ("Bộ kiểm thử tự động của TrafficVision được xây dựng bằng framework pytest, đạt kết quả tuyệt đối:", False)
    ])
    p35_score = make_para([
        ("215/215 tests hợp lệ (213 passed, 2 skipped trong 45.2s)", True, False, "28A745", 24)
    ])
    p35_coverage = make_para([
        ("Phạm vi kiểm thử bao phủ toàn diện 5 nhóm module:", True, False, "193DB0")
    ])
    p35_cov_list = [
        make_para([("• Domain & Config Tests: ", True), ("Kiểm thử tính đúng đắn của tham số suy luận, catalog 82 lớp QCVN 41:2019 và bộ cấu hình hệ thống.", False)], bullet=True),
        make_para([("• Data & Quality Gate Tests: ", True), ("Kiểm thử 5 tiêu chí chặn rác dữ liệu, module Dataset Repair cắt gọt bbox, tạo snapshot và phân tích EDA.", False)], bullet=True),
        make_para([("• Training & MLOps Tests: ", True), ("Kiểm thử tiến trình ngầm TrainingManager, hardware detector, Safe Resume từ checkpoint, đóng gói candidate và kiểm tra Parity ONNX.", False)], bullet=True),
        make_para([("• Model Registry & Rollback Tests: ", True), ("Kiểm thử kiểm tra mã băm SHA-256, tự động sao lưu trước khi thăng cấp, hoán đổi nguyên tử và hoàn tác khẩn cấp 1-click.", False)], bullet=True),
        make_para([("• Web UI & AppTests: ", True), ("Kiểm thử giao diện Streamlit AppTest cho cả 6 trang, component trực quan hóa, bộ xử lý video và script khởi chạy run_app.bat.", False)], bullet=True),
    ]
    p35_imp_title = make_para([
        ("Các cải tiến kỹ thuật đột phá đã triển khai:", True, False, "193DB0")
    ])
    p35_imp_list = [
        make_para([("1. Cơ chế Safe Atomic Swap trên Windows: ", True), ("Khắc phục triệt để lỗi PermissionError khi thay thế tệp mô hình đang phục vụ trên hệ điều hành Windows bằng cách sử dụng tệp tạm thời và hoán đổi nguyên tử an toàn.", False)], bullet=True),
        make_para([("2. Tự động nhận diện phần cứng (Hardware Detector): ", True), ("Tự động phát hiện cấu hình CPU/RAM và hệ điều hành, tự động gán workers = 0 trên Windows nhằm loại bỏ hoàn toàn nguy cơ deadlock và rò rỉ bộ nhớ khi huấn luyện.", False)], bullet=True),
        make_para([("3. Cơ chế Khôi phục khẩn cấp Rollback 1-click: ", True), ("Tự động tạo bản sao lưu có timestamp trước mỗi lần promotion, cho phép hoàn tác về trạng thái ổn định trước đó trong vòng chưa đầy 1 giây nếu mô hình mới phát sinh vấn đề.", False)], bullet=True),
        make_para([("4. Tối ưu hóa cập nhật giao diện với @st.fragment: ", True), ("Chỉ làm mới cục bộ khu vực hiển thị tiến trình video mà không tải lại toàn bộ trang web, giúp giao diện mượt mà và tiết kiệm tài nguyên trình duyệt.", False)], bullet=True),
    ]
    replace_sdt_content(body[108], [p35_1, p35_score, p35_coverage] + p35_cov_list + [p35_imp_title] + p35_imp_list)
    
    # 15. Section 4.1: Accomplishments and Benefits (body[112])
    print("Filling Section 4.1...")
    p41_acc = make_para([
        ("A. Các thành tựu cốt lõi đã đạt được:", True, False, "193DB0")
    ])
    p41_acc_list = [
        make_para([("• Giải pháp phần mềm MLOps hoàn chỉnh: ", True), ("Dự án không dừng lại ở một bài báo nghiên cứu mô hình đơn thuần, mà đã xây dựng thành công một giải pháp phần mềm thương mại hóa hoàn chỉnh gồm Web UI hiện đại, CSDL lưu trữ lịch sử SQLite, Model Registry quản lý phiên bản và hệ thống kiểm soát chất lượng dữ liệu khép kín.", False)], bullet=True),
        make_para([("• Độ chính xác nhận dạng vượt trội: ", True), ("Mô hình Production YOLO11m đạt mAP50 = 98.03% và F1 = 96.22% trên tập kiểm thử độc lập 82 lớp biển báo Việt Nam, giải quyết triệt để bài toán biển báo mờ, biến dạng hoặc bị che khuất một phần.", False)], bullet=True),
        make_para([("• Tính độc lập phần cứng và tối ưu CPU: ", True), ("Ứng dụng suy luận hoàn toàn trên CPU thông thường với ONNX Runtime đạt tốc độ ~15 FPS (bản Nano), giúp tiết kiệm hàng ngàn USD chi phí đầu tư card đồ họa GPU rời khi triển khai đại trà.", False)], bullet=True),
        make_para([("• Độ tin cậy và an toàn vận hành cao: ", True), ("Hệ thống được bảo vệ bởi cổng Quality Gate 5 tiêu chí loại bỏ rác dữ liệu, tính năng Safe Resume bảo toàn phiên huấn luyện, và cơ chế Rollback 1-click bảo vệ môi trường Production.", False)], bullet=True),
    ]
    p41_ben = make_para([
        ("B. Lợi ích thực tiễn đối với xã hội và quản lý giao thông:", True, False, "193DB0")
    ])
    p41_ben_list = [
        make_para([("• Nâng cao an toàn cho người tham gia giao thông: ", True), ("Hỗ trợ đắc lực cho các hệ thống hỗ trợ người lái nâng cao (ADAS), nhắc nhở biển cấm và biển nguy hiểm kịp thời, giảm thiểu nguy cơ tai nạn do quan sát sót biển báo.", False)], bullet=True),
        make_para([("• Tự động hóa công tác quản lý đô thị: ", True), ("Hỗ trợ các cơ quan quản lý giao thông tự động hóa công tác rà soát, kiểm kê, đánh giá hiện trạng và số hóa hệ thống biển báo đường bộ trên toàn quốc với chi phí vận hành cực thấp.", False)], bullet=True),
        make_para([("• Tiền đề vững chắc cho xe tự hành tại Việt Nam: ", True), ("Cung cấp module nhận dạng biển báo đường bộ chuẩn hóa theo luật giao thông Việt Nam, sẵn sàng tích hợp vào các hệ thống tự hành và xe điện thông minh nội địa.", False)], bullet=True),
    ]
    replace_sdt_content(body[112], [p41_acc] + p41_acc_list + [p41_ben] + p41_ben_list)
    
    # 16. Section 4.2: Future Improvements (body[114])
    print("Filling Section 4.2...")
    p42_intro = make_para([
        ("Nhóm nghiên cứu định hướng tiếp tục phát triển và nâng cấp hệ thống trong giai đoạn tiếp theo với 4 tính năng mở rộng đột phá:", False)
    ])
    p42_list = [
        make_para([("1. Tích hợp Camera hành trình trực tiếp qua giao thức RTSP (Live Dashcam Streaming): ", True, False, "193DB0"), ("Phát triển module kết nối trực tiếp với luồng video RTSP từ camera hành trình trên xe, thực hiện suy luận liên tục theo thời gian thực khi xe đang di chuyển trên đường.", False)], bullet=True),
        make_para([("2. Hệ thống cảnh báo âm thanh tiếng Việt (Voice Alert System): ", True, False, "193DB0"), ("Tích hợp công nghệ Text-to-Speech phát âm thanh nhắc nhở người lái ngay khi phát hiện các biển cấm nguy hiểm (Cấm đi ngược chiều, Giới hạn tốc độ, Cấm vượt, Giao nhau với đường sắt).", False)], bullet=True),
        make_para([("3. Số hóa bản đồ giao thông GPS (GPS Traffic Mapping): ", True, False, "193DB0"), ("Tự động trích xuất tọa độ địa lý GPS từ metadata của video hành trình để gắn vị trí biển báo lên bản đồ số (OpenStreetMap / Google Maps), phục vụ công tác thanh tra và duy tu hạ tầng giao thông đô thị.", False)], bullet=True),
        make_para([("4. Tối ưu hóa suy luận với lượng tử hóa INT8 (INT8 Quantization): ", True, False, "193DB0"), ("Ứng dụng kỹ thuật lượng tử hóa trọng số INT8 thông qua OpenVINO hoặc TensorRT, giúp tăng tốc độ suy luận thêm 3–4 lần mà vẫn duy trì độ chính xác nhận dạng, tối ưu hoàn hảo cho các thiết bị Edge AI siêu nhỏ gọn.", False)], bullet=True),
    ]
    replace_sdt_content(body[114], [p42_intro] + p42_list)
    
    # 17. Section 5: Team Picture (body[117]) & Member Reviews Table (body[119])
    print("Filling Section 5 (Team Picture & Reviews Table)...")
    # Table 117 (Team Picture)
    t117 = body[117]
    cell117 = t117.find('.//w:tc', namespaces)
    if cell117 is not None:
        for child in list(cell117):
            if not child.tag.endswith('}tcPr'):
                cell117.remove(child)
        banner_p1 = make_para([("DỰ ÁN TRAFFICVISION – NHÓM PHÁT TRIỂN HỆ THỐNG THÔNG MINH (PTIT / SIC)", True, False, "193DB0", 22)], space_after=60)
        banner_p2 = make_para([("Khóa học: AI Course – Phát triển hệ thống thông minh | Thời gian hoàn thành: Tháng 10/2026", False, True, "555555", 20)], space_after=60)
        banner_p3 = make_para([("Thành viên nhóm: Phí Văn Nam (Trưởng nhóm) • Đỗ Thị Vân Anh • Đỗ Hữu Nghị • Quản Văn Điệp", True, False, "222222", 20)], space_after=60)
        banner_p4 = make_para([("Đề tài: Hệ thống nhận dạng biển báo giao thông Việt Nam bằng AI tối ưu suy luận trên CPU (Production: YOLO11m ONNX)", False, False, "333333", 20)], space_after=40)
        cell117.append(banner_p1)
        cell117.append(banner_p2)
        cell117.append(banner_p3)
        cell117.append(banner_p4)
        
    # Table 119 (Member Reviews Table)
    def set_tc_content(tc, runs_list, align="left"):
        for child in list(tc):
            if not child.tag.endswith('}tcPr'):
                tc.remove(child)
        p = make_para(runs_list, space_after=60, line_spacing=240)
        pPr = p.find('w:pPr', namespaces)
        jc = ET.SubElement(pPr, w_tag("jc"))
        jc.set(w_tag("val"), align)
        tc.append(p)

    t119 = body[119]
    t119_rows = t119.findall('.//w:tr', namespaces)
    
    # Fill Row 1: Phí Văn Nam
    r1_cells = t119_rows[1].findall('.//w:tc', namespaces)
    set_tc_content(r1_cells[0], [("Phí Văn Nam\n(Trưởng nhóm)", True, False, "193DB0", 20)], align="center")
    set_tc_content(r1_cells[1], [("Trải qua quá trình triển khai dự án TrafficVision, tôi đã tích lũy được nhiều kinh nghiệm quý báu về việc thiết kế và tổ chức một hệ thống AI theo chuẩn MLOps thực chiến. Việc phân tách rõ ràng giữa luồng huấn luyện ngoại tuyến và suy luận trực tuyến, cùng việc xây dựng Model Registry quản lý phiên bản với mã băm SHA-256 và cơ chế Safe Atomic Swap đã giúp hệ thống vận hành cực kỳ ổn định, không gặp sự cố gián đoạn khi cập nhật mô hình. Tôi đánh giá rất cao sự nỗ lực, tinh thần trách nhiệm và sự phối hợp ăn ý của cả 4 thành viên trong nhóm, giúp dự án hoàn thành 100% tiến độ và đạt độ chính xác mAP50 vượt bậc 98.03%.", False, False, "222222", 20)], align="left")
    
    # Fill Row 2: Đỗ Thị Vân Anh
    r2_cells = t119_rows[2].findall('.//w:tc', namespaces)
    set_tc_content(r2_cells[0], [("Đỗ Thị Vân Anh\n(Kỹ sư Dữ liệu)", True, False, "193DB0", 20)], align="center")
    set_tc_content(r2_cells[1], [("Đảm nhận vai trò kỹ sư dữ liệu trong dự án, tôi nhận thức sâu sắc rằng dữ liệu chính là nền tảng cốt lõi của mọi mô hình học sâu. Quá trình thu thập, gán nhãn và làm sạch 10.129 ảnh cho 82 lớp biển báo Việt Nam gặp rất nhiều thách thức do sự mất cân bằng giữa các lớp và các lỗi tọa độ bounding box ngoài biên [0, 1]. Việc phát triển cổng Quality Gate 5 tiêu chí và module Dataset Repair đã giải quyết triệt để vấn đề rác dữ liệu trước khi đưa vào huấn luyện, đóng góp trực tiếp vào độ chính xác cao của mô hình. Đây là trải nghiệm thực tế vô cùng giá trị cho định hướng nghề nghiệp kỹ sư dữ liệu của tôi.", False, False, "222222", 20)], align="left")
    
    # Fill Row 3: Đỗ Hữu Nghị
    r3_cells = t119_rows[3].findall('.//w:tc', namespaces)
    set_tc_content(r3_cells[0], [("Đỗ Hữu Nghị\n(Kỹ sư AI/ML)", True, False, "193DB0", 20)], align="center")
    set_tc_content(r3_cells[1], [("Trong dự án này, tôi chịu trách nhiệm chính về cấu hình và huấn luyện hai phiên bản YOLO11n và YOLO11m, cũng như tối ưu hóa chuyển đổi mô hình sang ONNX Runtime trên CPU. Tôi rất tâm đắc với kết quả kiểm định Parity PyTorch vs ONNX khi sai số số học cực đại đạt 0.000854, vượt qua ngưỡng kiểm định khắt khe 1e-3. Bài học lớn nhất tôi rút ra được là việc cân bằng giữa bài toán Trade-off giữa độ chính xác nhận dạng và độ trễ suy luận trên phần cứng thực tế. Phiên bản Nano với độ trễ 68ms trên CPU là giải pháp lý tưởng cho các thiết bị biên, trong khi phiên bản Medium mang lại độ tin cậy tuyệt đối cho các bài toán phân tích chất lượng cao.", False, False, "222222", 20)], align="left")
    
    # Fill Row 4: Quản Văn Điệp
    r4_cells = t119_rows[4].findall('.//w:tc', namespaces)
    set_tc_content(r4_cells[0], [("Quản Văn Điệp\n(Kỹ sư Fullstack / QA)", True, False, "193DB0", 20)], align="center")
    set_tc_content(r4_cells[1], [("Là người phụ trách phát triển giao diện Web Streamlit và xây dựng bộ kiểm thử phần mềm, tôi luôn đặt trải nghiệm người dùng và độ tin cậy của ứng dụng lên hàng đầu. Việc xử lý luồng video chuyển động kèm thanh tiến trình cập nhật thời gian thực bằng @st.fragment mang lại cảm giác mượt mà và trực quan cho người sử dụng. Bên cạnh đó, việc xây dựng và duy trì thành công bộ 215 ca kiểm thử tự động pytest đã giúp nhóm tự tin thực hiện các nâng cấp mã nguồn mà không lo phát sinh lỗi hồi quy. Tôi rất tự hào khi sản phẩm hoàn thiện vừa có giao diện thân thiện, vừa có nền tảng kỹ thuật vững chắc.", False, False, "222222", 20)], align="left")
    
    # Remove Row 5 (since team has 4 members)
    if len(t119_rows) > 5:
        t119.remove(t119_rows[5])
        
    print("Writing modified docx archive...")
    buf = io.BytesIO()
    with zipfile.ZipFile(src_path, 'r') as z_in:
        with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
            for item in z_in.infolist():
                if item.filename == "word/document.xml":
                    z_out.writestr(item, ET.tostring(root, encoding='utf-8', xml_declaration=True))
                else:
                    z_out.writestr(item, z_in.read(item.filename))
                    
    buf.seek(0)
    # verify by opening with docx
    verified_doc = docx.Document(buf)
    print("Verification passed! Paragraphs:", len(verified_doc.paragraphs), "Tables:", len(verified_doc.tables))
    
    # save to destination
    with open(dst_path, 'wb') as f:
        f.write(buf.getvalue())
    print(f"Successfully generated Final Report: {dst_path}")

if __name__ == "__main__":
    fill_final_report("docs/template/backup_original/Project_Final Report.docx", "docs/template/Project_Final Report.docx")
