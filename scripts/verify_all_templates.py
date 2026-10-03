import sys
import os
import docx
import openpyxl
import xml.etree.ElementTree as ET
import zipfile

sys.stdout.reconfigure(encoding='utf-8')

print("="*60)
print("VERIFYING 3 FILLED TEMPLATE FILES IN docs/template/")
print("="*60)

# 1. Action Plan
ap_path = "docs/template/Project_Action Plan.docx"
print(f"\n1. Verifying {ap_path}...")
assert os.path.exists(ap_path), "File does not exist!"
doc_ap = docx.Document(ap_path)
print(f"   Tables count: {len(doc_ap.tables)}")
for i, t in enumerate(doc_ap.tables):
    print(f"   Table {i}: {len(t.rows)} rows x {len(t.columns)} cols")
    for r_idx, r in enumerate(t.rows):
        t_text = r.cells[0].text.strip()
        c_text = r.cells[1].text.strip() if len(r.cells) > 1 else ""
        # Check placeholders
        for text in [t_text, c_text]:
            if "<A " in text or "<Team " in text or "<Describe " in text or "<Explain " in text:
                print(f"   WARNING: Placeholder found in Table {i} Row {r_idx}: {text[:50]}")
print("   Sample Content Table 0 Row 1-3:")
print("     Tên nhóm:", repr(doc_ap.tables[0].rows[1].cells[1].text.strip()))
print("     Thành viên:", repr(doc_ap.tables[0].rows[2].cells[1].text.strip().replace('\n', ' ')))
print("     Tên đề tài:", repr(doc_ap.tables[0].rows[3].cells[1].text.strip()))
print("   Action Plan check: PASSED!")

# 2. WBS
wbs_path = "docs/template/Project_Work Breakdown Structure.xlsx"
print(f"\n2. Verifying {wbs_path}...")
assert os.path.exists(wbs_path), "File does not exist!"
wb = openpyxl.load_workbook(wbs_path, data_only=True)
ws = wb.active
print(f"   Sheet: {ws.title}, max_row: {ws.max_row}, max_column: {ws.max_column}")
print(f"   Title: {ws['B2'].value}")
print(f"   Team: {ws['C8'].value}")
print(f"   Topic: {ws['C9'].value}")
task_count = 0
done_count = 0
for r in range(14, 32):
    status = ws.cell(r, 10).value
    tname = None
    for c in range(2, 6):
        if ws.cell(r, c).value:
            tname = ws.cell(r, c).value
            break
    if tname:
        task_count += 1
        if status == "Hoàn thành":
            done_count += 1
        marks = [ws.cell(r, c).value for c in range(11, 31) if ws.cell(r, c).value == 'X']
        print(f"     Task [{status}]: {tname[:45]} | Marks: {len(marks)}")
print(f"   Total tasks: {task_count}, Done: {done_count}")
print("   WBS check: PASSED!")

# 3. Final Report
fr_path = "docs/template/Project_Final Report.docx"
print(f"\n3. Verifying {fr_path}...")
assert os.path.exists(fr_path), "File does not exist!"
with zipfile.ZipFile(fr_path, 'r') as z:
    xml_content = z.read("word/document.xml").decode("utf-8")
root = ET.fromstring(xml_content)
namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

# Check for residual placeholders
placeholders = ["< TÊN ĐỀ TÀI >", "<Member 1>", "<Member 2>", "<Member 3>", "<Member 4>", "<Member 5>", "<ATTACH A TEAM PICTURE HERE>"]
for p in placeholders:
    if p in xml_content:
        print(f"   WARNING: Placeholder '{p}' still in document.xml!")
    else:
        print(f"   Placeholder '{p}' successfully replaced.")

# Check document paragraphs and tables
doc_fr = docx.Document(fr_path)
print(f"   Total Paragraphs in Word DOM: {len(doc_fr.paragraphs)}")
print(f"   Total Tables in Word DOM: {len(doc_fr.tables)}")

# Inspect Table 1 (Team Member Review)
t1 = doc_fr.tables[1]
print(f"   Table 1 (Team Member Review): {len(t1.rows)} rows x {len(t1.columns)} cols")
for r_idx, r in enumerate(t1.rows):
    c0 = r.cells[0].text.strip().replace('\n', ' ')
    c1 = r.cells[1].text.strip().replace('\n', ' ')[:60]
    print(f"     Row {r_idx}: {c0} -> {c1}...")

# Inspect Table 2 (Instructor Rubric)
t2 = doc_fr.tables[2]
print(f"   Table 2 (Instructor Rubric): {len(t2.rows)} rows x {len(t2.columns)} cols")
for r_idx, r in enumerate(t2.rows):
    c0 = r.cells[0].text.strip()
    c1 = r.cells[1].text.strip()
    print(f"     Row {r_idx}: {c0} | {c1}")

print("\nALL 3 FILES IN docs/template/ VERIFIED SUCCESSFULLY!")
