#!/usr/bin/env python3
"""Parse docs/test-design.md and generate an interactive, responsive docs/test-design.html."""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(r"e:\PTIT\Project\traffic-vision\traffic-vision")
DOCS_DIR = REPO_ROOT / "docs"
MD_FILE = DOCS_DIR / "test-design.md"
HTML_FILE = DOCS_DIR / "test-design.html"


def inline_format(text: str) -> str:
    """Format markdown inline code, bold, italic, links."""
    if not text:
        return ""

    # Replace backticks first with placeholders to protect code content
    code_tokens = []
    def save_code(m):
        code_tokens.append(html.escape(m.group(1)))
        return f"__CODE_TOKEN_{len(code_tokens)-1}__"

    text = re.sub(r"`([^`]+)`", save_code, text)

    # Basic HTML escape for remaining text
    text = html.escape(text, quote=False)

    # Bold **text**
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # Italic *(text)* or *text*
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    # Links [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    # Restore code tokens
    for idx, c in enumerate(code_tokens):
        text = text.replace(f"__CODE_TOKEN_{idx}__", f'<code class="code-span">{c}</code>')

    return text


def parse_markdown_table(table_text: str) -> tuple[list[str], list[list[str]]]:
    """Parse a markdown table into headers and rows."""
    lines = [l.strip() for l in table_text.strip().split("\n") if l.strip()]
    if len(lines) < 2:
        return [], []
    headers = [c.strip() for c in lines[0].strip("|").split("|")]
    rows = []
    for line in lines[2:]:
        cols = [c.strip() for c in line.strip("|").split("|")]
        while len(cols) < len(headers):
            cols.append("")
        rows.append(cols[:len(headers)])
    return headers, rows


def render_html_table(headers: list[str], rows: list[list[str]], table_class: str = "styled-table", is_cell_html: bool = False) -> str:
    """Render headers and rows as HTML table."""
    h_html = "".join(f"<th>{inline_format(h)}</th>" for h in headers)
    r_html_list = []
    for r in rows:
        cells = []
        for c in r:
            if is_cell_html:
                cells.append(f"<td>{c}</td>")
            else:
                cells.append(f"<td>{inline_format(c)}</td>")
        r_html_list.append(f"<tr>{''.join(cells)}</tr>")
    rows_html = "\n".join(r_html_list)
    return f"""<div class="table-container">
  <table class="{table_class}">
    <thead><tr>{h_html}</tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>"""


def parse_test_design():
    with open(MD_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into major sections
    raw_sections = re.split(r"\n(?=##\s+)", content)
    header_raw = raw_sections[0] if raw_sections else ""

    # Parse metadata
    title_match = re.search(r"^#\s+(.+)$", header_raw, re.MULTILINE)
    doc_title = title_match.group(1).strip() if title_match else "Tài liệu Thiết kế Kiểm thử — TrafficVision"

    meta_dict = {}
    for line in header_raw.split("\n"):
        m = re.match(r"^\*\*([^*]+):\*\*\s*(.+)$", line.strip())
        if m:
            meta_dict[m.group(1).strip()] = m.group(2).strip()

    sections_data = []

    for sec in raw_sections[1:]:
        sec_lines = sec.strip().split("\n")
        h2_line = sec_lines[0].strip()
        h2_title = re.sub(r"^##\s+", "", h2_line).strip()

        sec_body = "\n".join(sec_lines[1:]).strip()

        # Skip raw markdown TOC because the sidebar provides rich interactive TOC
        if h2_title.startswith("Mục lục"):
            continue

        sec_data = {
            "title": h2_title,
            "raw": sec,
            "body": sec_body,
        }
        sections_data.append(sec_data)

    return doc_title, meta_dict, sections_data


def generate_html():
    doc_title, meta_dict, sections_data = parse_test_design()

    all_tcs = []
    tc_pattern = r"###\s+(TC-[A-Z0-9\-]+):\s*(.+?)\n+(.*?)(?=\n###|\n##|\Z)"
    
    with open(MD_FILE, "r", encoding="utf-8") as f:
        full_text = f.read()

    raw_tcs = re.findall(tc_pattern, full_text, re.DOTALL)
    for tc_id, tc_title, tc_body in raw_tcs:
        clean_body = re.sub(r"\n*---\s*$", "", tc_body.strip())

        prio = "P1"
        tag = None
        p_match = re.search(r"\*\*Mức độ:\*\*\s*(.+)", clean_body)
        if p_match:
            praw = p_match.group(1).strip()
            if praw.startswith("P0"):
                prio = "P0"
            elif praw.startswith("P1"):
                prio = "P1"
            elif praw.startswith("P2"):
                prio = "P2"
            t_match = re.search(r"\*\((.+?)\)\*", praw)
            if t_match:
                tag = t_match.group(1).strip()

        table_html = ""
        table_match = re.search(r"(\|[^\n]+\|\n\|[\s\-:|]+\|\n(?:\|[^\n]+\|\n?)+)", clean_body)
        if table_match:
            t_str = table_match.group(1)
            headers, rows = parse_markdown_table(t_str)
            table_html = render_html_table(headers, rows, table_class="styled-table tc-param-table")
            clean_body = clean_body.replace(t_str, "").strip()

        fields = {}
        cur_key = None
        cur_lines = []
        for l in clean_body.split("\n"):
            km = re.match(r"^\*\*([A-Za-z0-9_ À-ỹ\s]+):\*\*\s*(.*)", l)
            if km:
                if cur_key:
                    fields[cur_key] = cur_lines
                cur_key = km.group(1).strip()
                first_val = km.group(2).strip()
                cur_lines = [first_val] if first_val else []
            else:
                if l.strip():
                    cur_lines.append(l.strip())
        if cur_key:
            fields[cur_key] = cur_lines

        all_tcs.append({
            "id": tc_id,
            "title": tc_title.strip(),
            "priority": prio,
            "tag": tag,
            "table_html": table_html,
            "fields": fields,
        })

    # Stats calculations
    total_tcs = len(all_tcs)
    p0_count = sum(1 for tc in all_tcs if tc["priority"] == "P0")
    p1_count = sum(1 for tc in all_tcs if tc["priority"] == "P1")
    p2_count = sum(1 for tc in all_tcs if tc["priority"] == "P2")
    security_count = sum(1 for tc in all_tcs if tc.get("tag") == "Security")
    rf1_count = sum(1 for tc in all_tcs if tc.get("tag") == "Review Focus Plan 1")
    rf2_count = sum(1 for tc in all_tcs if tc.get("tag") == "Review Focus Plan 2")

    def render_tc_card(tc: dict) -> str:
        tcid = tc["id"]
        title = html.escape(tc["title"])
        prio = tc["priority"]
        tag = tc["tag"]

        prio_badge_cls = {
            "P0": "badge-p0",
            "P1": "badge-p1",
            "P2": "badge-p2",
        }.get(prio, "badge-p1")

        prio_label = {
            "P0": "P0 — Critical",
            "P1": "P1 — High",
            "P2": "P2 — Medium",
        }.get(prio, prio)

        tag_badge_html = ""
        if tag == "Security":
            tag_badge_html = '<span class="badge badge-security"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Security</span>'
        elif tag:
            tag_badge_html = f'<span class="badge badge-focus">{html.escape(tag)}</span>'

        fields_html = []
        fields = tc["fields"]

        # Condition
        if "Điều kiện" in fields:
            val = " ".join(fields["Điều kiện"])
            fields_html.append(f"""<div class="tc-field">
  <span class="field-label condition-label">Điều kiện:</span>
  <span class="field-content">{inline_format(val)}</span>
</div>""")

        # Input
        for in_key in ["Input", "Input a", "Input b"]:
            if in_key in fields:
                val = " ".join(fields[in_key])
                label = f"{in_key}:"
                fields_html.append(f"""<div class="tc-field">
  <span class="field-label input-label">{label}</span>
  <span class="field-content">{inline_format(val)}</span>
</div>""")

        # Flow
        if "Flow" in fields:
            val = " ".join(fields["Flow"])
            fields_html.append(f"""<div class="tc-field">
  <span class="field-label flow-label">Flow:</span>
  <span class="field-content">{inline_format(val)}</span>
</div>""")

        # Command(s)
        for cmd_key in ["Command", "Commands"]:
            if cmd_key in fields:
                val = " ".join(fields[cmd_key])
                fields_html.append(f"""<div class="tc-field">
  <span class="field-label cmd-label">{cmd_key}:</span>
  <span class="field-content"><code class="cmd-code">{inline_format(val)}</code></span>
</div>""")

        # Embedded parameters table
        if tc["table_html"]:
            fields_html.append(f'<div class="tc-table-wrapper">{tc["table_html"]}</div>')

        # Expected Result
        if "Kết quả mong đợi" in fields:
            lines = fields["Kết quả mong đợi"]
            bullets = [l[1:].strip() for l in lines if l.startswith("- ") or l.startswith("* ")]
            if bullets:
                b_items = "".join(f'<li><span class="check-icon">✓</span> <span>{inline_format(b)}</span></li>' for b in bullets)
                expected_content = f'<ul class="expected-list">{b_items}</ul>'
            else:
                expected_content = f'<div class="expected-text">{inline_format(" ".join(lines))}</div>'

            fields_html.append(f"""<div class="tc-field expected-field">
  <span class="field-label expected-label">Kết quả mong đợi:</span>
  <div class="field-content">{expected_content}</div>
</div>""")

        body_rendered = "\n".join(fields_html)

        search_terms = f"{tcid} {tc['title']} {prio} {tag or ''} {' '.join(str(v) for v in fields.values())}".lower()
        search_attr = html.escape(search_terms, quote=True)

        return f"""<div class="tc-card" id="{tcid}" data-id="{tcid}" data-prio="{prio}" data-tag="{tag or ''}" data-search="{search_attr}">
  <div class="tc-card-header">
    <div class="tc-header-left">
      <a href="#{tcid}" class="tc-id-badge" onclick="copyTcLink(event, '{tcid}')" title="Nhấp để copy link">{tcid}</a>
      <h4 class="tc-title">{title}</h4>
    </div>
    <div class="tc-header-right">
      {tag_badge_html}
      <span class="badge {prio_badge_cls}">{prio_label}</span>
      <button class="status-btn" onclick="toggleTestStatus('{tcid}')" title="Đánh dấu trạng thái kiểm thử">
        <span class="status-indicator"></span>
        <span class="status-text">Pending</span>
      </button>
    </div>
  </div>
  <div class="tc-card-body">
    {body_rendered}
  </div>
</div>"""

    # Build sections HTML
    sections_html_parts = []
    nav_links_parts = []

    for sec in sections_data:
        title = sec["title"]
        body = sec["body"]

        slug = re.sub(r"[^a-zA-Z0-9\-_]+", "-", title.lower()).strip("-")
        if not slug:
            slug = f"sec-{len(sections_html_parts)}"

        # Category grouping
        group = "TỔNG QUAN"
        if any(m in title for m in ["Module A", "Module B", "Module C", "Module D", "Module E", "Module F", "Module G"]):
            group = "GIAI ĐOẠN 1: INFERENCE & APP"
        elif any(m in title for m in ["Module H", "Module I", "Module J", "Module K", "Module L", "Module M", "Module N"]):
            group = "GIAI ĐOẠN 2: HUẤN LUYỆN & PIPELINE"
        elif "Integration" in title or "UAT" in title or "Acceptance" in title:
            group = "KIỂM THỬ HỆ THỐNG & UAT"
        elif "Phụ lục" in title:
            group = "PHỤ LỤC & TỔNG HỢP"

        nav_links_parts.append({
            "group": group,
            "title": title,
            "slug": slug,
        })

        if title.startswith("1. Phạm vi kiểm thử"):
            t_match = re.search(r"(\|[^\n]+\|\n\|[\s\-:|]+\|\n(?:\|[^\n]+\|\n?)+)", body)
            if t_match:
                headers, rows = parse_markdown_table(t_match.group(1))
                scope_table_html = render_html_table(headers, rows, "styled-table scope-table")
            else:
                scope_table_html = ""

            sec_html = f"""<section class="doc-section" id="{slug}">
  <div class="section-header">
    <div class="section-tag">Khung kiểm thử</div>
    <h2 class="section-title">{title}</h2>
  </div>
  <div class="section-content">
    <p class="section-desc">Phạm vi xác định rõ các ranh giới kiểm thử tự động, tích hợp end-to-end và nghiệm thu UAT cho hệ thống TrafficVision.</p>
    {scope_table_html}
  </div>
</section>"""
            sections_html_parts.append(sec_html)

        elif title.startswith("2. Chiến lược kiểm thử"):
            principles = []
            for line in body.split("\n"):
                if line.startswith("- "):
                    principles.append(line[2:].strip())

            principle_cards = []
            principle_icons = [
                ('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>', "TDD — Test-Driven Development"),
                ('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>', "Môi trường Cô lập"),
                ('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/></svg>', "Dữ liệu Tổng hợp Synthetic"),
                ('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>', "Thanh xanh Tuyệt đối")
            ]

            for idx, p in enumerate(principles):
                icon, ptitle = principle_icons[idx] if idx < len(principle_icons) else (principle_icons[0][0], f"Nguyên tắc {idx+1}")
                principle_cards.append(f"""<div class="principle-card">
  <div class="principle-icon">{icon}</div>
  <div class="principle-info">
    <h4>{ptitle}</h4>
    <p>{inline_format(p)}</p>
  </div>
</div>""")
            principles_html = "\n".join(principle_cards)

            sec_html = f"""<section class="doc-section" id="{slug}">
  <div class="section-header">
    <div class="section-tag">Kiến trúc QA</div>
    <h2 class="section-title">{title}</h2>
  </div>
  <div class="section-content">
    <div class="strategy-grid">
      <div class="pyramid-container">
        <h3 class="subsection-title">Pyramid Kiểm thử TrafficVision</h3>
        <div class="pyramid-visual">
          <div class="pyramid-tier tier-uat">
            <span class="tier-label">UAT thủ công</span>
            <span class="tier-desc">Hiếm, thực tế, chậm</span>
          </div>
          <div class="pyramid-tier tier-int">
            <span class="tier-label">Integration Tests</span>
            <span class="tier-desc">Mỗi task 1 luồng E2E</span>
          </div>
          <div class="pyramid-tier tier-ui">
            <span class="tier-label">UI Tests (Streamlit AppTest)</span>
            <span class="tier-desc">Mỗi trang 1+ test</span>
          </div>
          <div class="pyramid-tier tier-unit">
            <span class="tier-label">Unit Tests (Pytest, Mock, Fixture)</span>
            <span class="tier-desc">Nền tảng: Đa số, nhanh, TDD</span>
          </div>
        </div>
      </div>
      <div class="principles-container">
        <h3 class="subsection-title">4 Nguyên tắc Bắt buộc</h3>
        <div class="principles-grid">
          {principles_html}
        </div>
      </div>
    </div>
  </div>
</section>"""
            sections_html_parts.append(sec_html)

        elif "Module " in title or title.startswith("17. Integration Tests"):
            files_quote = ""
            test_files_quote = ""
            for l in body.split("\n"):
                if l.startswith("> **Files:**"):
                    files_quote = l.replace("> **Files:**", "").strip()
                elif l.startswith("> **Test files:**"):
                    test_files_quote = l.replace("> **Test files:**", "").strip()
                elif l.startswith(">") and "Test files:" in l:
                    test_files_quote = l.replace(">", "").strip()

            meta_bar_items = []
            if files_quote:
                meta_bar_items.append(f'<div class="meta-item"><span class="meta-label">Mã nguồn:</span> <span class="meta-val">{inline_format(files_quote)}</span></div>')
            if test_files_quote:
                meta_bar_items.append(f'<div class="meta-item"><span class="meta-label">File kiểm thử:</span> <span class="meta-val">{inline_format(test_files_quote)}</span></div>')
            meta_bar_html = f'<div class="module-meta-bar">{"".join(meta_bar_items)}</div>' if meta_bar_items else ""

            sec_tcs = re.findall(tc_pattern, body, re.DOTALL)
            module_tc_cards = []
            for stc_id, stc_title, stc_body in sec_tcs:
                match_tc = next((t for t in all_tcs if t["id"] == stc_id), None)
                if match_tc:
                    module_tc_cards.append(render_tc_card(match_tc))

            tc_cards_html = "\n".join(module_tc_cards)
            tc_count = len(sec_tcs)

            sec_html = f"""<section class="doc-section module-section" id="{slug}">
  <div class="section-header">
    <div class="section-header-top">
      <div class="section-tag">Module Component</div>
      <span class="tc-counter-badge">{tc_count} Test Cases</span>
    </div>
    <h2 class="section-title">{title}</h2>
    {meta_bar_html}
  </div>
  <div class="section-content">
    <div class="tc-cards-list">
      {tc_cards_html}
    </div>
  </div>
</section>"""
            sections_html_parts.append(sec_html)

        elif title.startswith("18. UAT & Hiệu năng"):
            t_match = re.search(r"(\|[^\n]+\|\n\|[\s\-:|]+\|\n(?:\|[^\n]+\|\n?)+)", body)
            if t_match:
                headers, rows = parse_markdown_table(t_match.group(1))
                headers.append("Trạng thái")
                enhanced_rows = []
                for r in rows:
                    uat_id = r[0]
                    device = r[4] if len(r) > 4 else ""
                    dev_badge = f'<span class="device-badge">{html.escape(device)}</span>'
                    enhanced_row = [
                        f'<strong class="uat-id">{html.escape(uat_id)}</strong>',
                        inline_format(r[1]),
                        inline_format(r[2]),
                        inline_format(r[3]),
                        dev_badge,
                        f'<button class="status-btn" onclick="toggleTestStatus(\'{html.escape(uat_id)}\')"><span class="status-indicator"></span><span class="status-text">Pending</span></button>'
                    ]
                    enhanced_rows.append(enhanced_row)
                uat_table_html = render_html_table(headers, enhanced_rows, "styled-table uat-table", is_cell_html=True)
            else:
                uat_table_html = ""

            sec_html = f"""<section class="doc-section" id="{slug}">
  <div class="section-header">
    <div class="section-tag">Thực nghiệm & Trải nghiệm</div>
    <h2 class="section-title">{title}</h2>
    <div class="section-note">Thực hiện thủ công trên môi trường thực tế (macOS & Windows). Tham chiếu Spec §10.3</div>
  </div>
  <div class="section-content">
    {uat_table_html}
  </div>
</section>"""
            sections_html_parts.append(sec_html)

        elif title.startswith("19. Acceptance Criteria Checklist"):
            t_match = re.search(r"(\|[^\n]+\|\n\|[\s\-:|]+\|\n(?:\|[^\n]+\|\n?)+)", body)
            if t_match:
                headers, rows = parse_markdown_table(t_match.group(1))
                ac_cards = []
                for r in rows:
                    ac_id = r[0]
                    criteria = r[1]
                    related_tcs = r[2]
                    def link_tc(m):
                        target = m.group(0)
                        return f'<a href="#{target}" class="tc-jump-link">{target}</a>'
                    related_html = re.sub(r"TC-[A-Z0-9\-]+|UAT-\d+", link_tc, html.escape(related_tcs))

                    ac_cards.append(f"""<div class="ac-item" id="card-{ac_id}">
  <label class="ac-checkbox-wrapper">
    <input type="checkbox" id="check-{ac_id}" onchange="updateACProgress('{ac_id}', this.checked)">
    <span class="ac-custom-check"></span>
  </label>
  <div class="ac-content">
    <div class="ac-header">
      <span class="ac-code">{ac_id}</span>
      <h4 class="ac-title">{inline_format(criteria)}</h4>
    </div>
    <div class="ac-meta">
      <span class="ac-tcs-label">Test cases liên quan:</span> {related_html}
    </div>
  </div>
</div>""")
                ac_list_html = "\n".join(ac_cards)
            else:
                ac_list_html = ""

            sec_html = f"""<section class="doc-section" id="{slug}">
  <div class="section-header">
    <div class="section-tag">Nghiệm thu Đồ án</div>
    <h2 class="section-title">{title}</h2>
    <div class="section-note">Tham chiếu Spec §15 — Tiêu chuẩn nghiệm thu cốt lõi bảo đảm dự án sẵn sàng bảo vệ.</div>
  </div>
  <div class="section-content">
    <div class="ac-progress-box">
      <div class="ac-progress-header">
        <span class="ac-progress-title">Tiến độ Nghiệm thu Tiêu chí (AC)</span>
        <span class="ac-progress-stat" id="acProgressStat">0 / 9 tiêu chí hoàn tất (0%)</span>
      </div>
      <div class="ac-progress-bar-bg">
        <div class="ac-progress-bar-fill" id="acProgressBarFill" style="width: 0%;"></div>
      </div>
    </div>
    <div class="ac-checklist">
      {ac_list_html}
    </div>
  </div>
</section>"""
            sections_html_parts.append(sec_html)

        elif "Phụ lục A" in title:
            t_match = re.search(r"(\|[^\n]+\|\n\|[\s\-:|]+\|\n(?:\|[^\n]+\|\n?)+)", body)
            if t_match:
                headers, rows = parse_markdown_table(t_match.group(1))
                enhanced_rows = []
                for r in rows:
                    if "Tổng cộng" in r[0]:
                        enhanced_rows.append([
                            f'<strong class="total-row">{r[0]}</strong>',
                            f'<strong class="total-row">{inline_format(r[1])}</strong>',
                            f'<strong class="total-row">{inline_format(r[2])}</strong>',
                            f'<span class="total-badge">{inline_format(r[3])}</span>',
                        ])
                    else:
                        mod_badge = f'<span class="mod-pill">{inline_format(r[0])}</span>'
                        tc_badge = f'<span class="badge badge-count">{inline_format(r[3])}</span>'
                        enhanced_rows.append([mod_badge, inline_format(r[1]), inline_format(r[2]), tc_badge])
                map_table_html = render_html_table(headers, enhanced_rows, "styled-table mapping-table", is_cell_html=True)
            else:
                map_table_html = ""

            sec_html = f"""<section class="doc-section" id="{slug}">
  <div class="section-header">
    <div class="section-tag">Tra cứu Kiểm thử</div>
    <h2 class="section-title">{title}</h2>
  </div>
  <div class="section-content">
    <p class="section-desc">Bảng tổng hợp tương ứng giữa các module tính năng, file kiểm thử tự động với Pytest và số lượng test case chi tiết.</p>
    {map_table_html}
  </div>
</section>"""
            sections_html_parts.append(sec_html)

        elif "Phụ lục B" in title:
            t_match = re.search(r"(\|[^\n]+\|\n\|[\s\-:|]+\|\n(?:\|[^\n]+\|\n?)+)", body)
            if t_match:
                headers, rows = parse_markdown_table(t_match.group(1))
                matrix_rows = []
                for r in rows:
                    praw = r[0]
                    cls = "badge-p1"
                    if "P0" in praw:
                        cls = "badge-p0"
                    elif "P2" in praw:
                        cls = "badge-p2"
                    matrix_rows.append([
                        f'<span class="badge {cls}">{inline_format(praw)}</span>',
                        inline_format(r[1]),
                        f'<span class="action-highlight">{inline_format(r[2])}</span>'
                    ])
                matrix_table_html = render_html_table(headers, matrix_rows, "styled-table matrix-table", is_cell_html=True)
            else:
                matrix_table_html = ""

            sec_html = f"""<section class="doc-section" id="{slug}">
  <div class="section-header">
    <div class="section-tag">Chính sách Phản ứng</div>
    <h2 class="section-title">{title}</h2>
  </div>
  <div class="section-content">
    {matrix_table_html}
    <div class="doc-footer-note">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
      <span>Tài liệu thiết kế kiểm thử tự động tạo từ kiến trúc đặc tả <code>2026-09-27-trafficvision-design.md</code> cùng 2 bản kế hoạch phát triển (Baseline App & Training Pipeline). Cập nhật đồng bộ theo phiên bản phát hành phần mềm.</span>
    </div>
  </div>
</section>"""
            sections_html_parts.append(sec_html)

    nav_html_parts = []
    current_grp = ""
    for item in nav_links_parts:
        if item["group"] != current_grp:
            current_grp = item["group"]
            nav_html_parts.append(f'<div class="nav-group-title">{html.escape(current_grp)}</div>')
        nav_html_parts.append(f'<a href="#{item["slug"]}" class="nav-item" data-target="{item["slug"]}"><span class="nav-indicator"></span><span class="nav-text">{html.escape(item["title"])}</span></a>')

    sidebar_nav_html = "\n".join(nav_html_parts)
    main_content_html = "\n".join(sections_html_parts)

    full_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(doc_title)}</title>
  <meta name="description" content="Tài liệu Thiết kế Kiểm thử toàn diện hệ thống nhận dạng biển báo giao thông TrafficVision với 134 Test Cases, 215 Pytest tests, UAT và Tiêu chuẩn Nghiệm thu.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --primary-light: #eff6ff;
      --secondary: #0b1730;
      --accent: #14b8a6;
      --accent-light: #f0fdfa;
      --text: #1e293b;
      --text-muted: #64748b;
      --text-subtle: #94a3b8;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --border-dark: rgba(255, 255, 255, 0.1);
      
      --p0-color: #ef4444;
      --p0-bg: #fef2f2;
      --p0-border: #fecaca;
      
      --p1-color: #f59e0b;
      --p1-bg: #fffbeb;
      --p1-border: #fde68a;
      
      --p2-color: #3b82f6;
      --p2-bg: #eff6ff;
      --p2-border: #bfdbfe;
      
      --security-color: #dc2626;
      --security-bg: #fee2e2;
      
      --focus-color: #6366f1;
      --focus-bg: #e0e7ff;
      
      --success: #10b981;
      --success-bg: #ecfdf5;
      --success-border: #a7f3d0;
      
      --radius-sm: 6px;
      --radius: 12px;
      --radius-lg: 16px;
      --radius-xl: 20px;
      
      --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.05);
      --shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
      --shadow-lg: 0 12px 30px rgba(0, 0, 0, 0.08);
      
      --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', ui-monospace, Menlo, Monaco, Consolas, monospace;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    html {{
      scroll-behavior: smooth;
      font-size: 15px;
    }}
    
    body {{
      font-family: var(--font-sans);
      background: var(--bg);
      color: var(--text);
      line-height: 1.65;
      -webkit-font-smoothing: antialiased;
    }}

    /* App Container Layout */
    .app-layout {{
      display: flex;
      min-height: 100vh;
    }}

    /* Sidebar */
    .sidebar {{
      width: 320px;
      background: var(--secondary);
      color: #cbd5e1;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      flex-shrink: 0;
      border-right: 1px solid var(--border-dark);
      display: flex;
      flex-direction: column;
      z-index: 100;
      transition: transform 0.3s ease;
    }}

    .sidebar-header {{
      padding: 24px 20px 16px;
      border-bottom: 1px solid var(--border-dark);
    }}

    .brand-box {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }}

    .brand-logo {{
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--accent), var(--primary));
      display: grid;
      place-items: center;
      color: #ffffff;
      font-size: 20px;
      font-weight: 800;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }}

    .brand-meta {{
      display: flex;
      flex-direction: column;
    }}

    .brand-name {{
      font-size: 18px;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.02em;
    }}

    .brand-tagline {{
      font-size: 11px;
      color: #94a3b8;
      font-weight: 500;
    }}

    .sidebar-search-box {{
      position: relative;
    }}

    .sidebar-search-box input {{
      width: 100%;
      background: rgba(255, 255, 255, 0.07);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 8px;
      padding: 8px 12px 8px 34px;
      color: #ffffff;
      font-size: 13px;
      font-family: inherit;
      outline: none;
      transition: all 0.2s;
    }}

    .sidebar-search-box input:focus {{
      border-color: var(--primary);
      background: rgba(255, 255, 255, 0.12);
      box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.25);
    }}

    .sidebar-search-icon {{
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      color: #64748b;
      pointer-events: none;
    }}

    .sidebar-nav {{
      flex: 1;
      padding: 16px 12px 30px;
      overflow-y: auto;
    }}

    .nav-group-title {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #64748b;
      margin: 18px 8px 6px;
    }}

    .nav-item {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 12px;
      border-radius: 8px;
      color: #94a3b8;
      text-decoration: none;
      font-size: 13px;
      font-weight: 500;
      transition: all 0.15s ease;
      margin-bottom: 2px;
    }}

    .nav-item:hover {{
      background: rgba(255, 255, 255, 0.06);
      color: #ffffff;
    }}

    .nav-item.active {{
      background: var(--primary);
      color: #ffffff;
      font-weight: 600;
    }}

    .nav-indicator {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #475569;
      flex-shrink: 0;
      transition: all 0.2s;
    }}

    .nav-item.active .nav-indicator {{
      background: #ffffff;
      transform: scale(1.3);
    }}

    .nav-text {{
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    /* Main Content Area */
    .main-wrapper {{
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
    }}

    /* Top Sticky Action Bar */
    .top-action-bar {{
      position: sticky;
      top: 0;
      background: rgba(255, 255, 255, 0.94);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 12px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      z-index: 90;
    }}

    .filter-chips {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .chip-btn {{
      border: 1px solid var(--border);
      background: #ffffff;
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: 99px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s;
    }}

    .chip-btn:hover {{
      border-color: var(--primary);
      color: var(--primary);
    }}

    .chip-btn.active {{
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
      box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25);
    }}

    .chip-count {{
      font-size: 11px;
      padding: 1px 6px;
      border-radius: 99px;
      background: rgba(0, 0, 0, 0.08);
    }}

    .chip-btn.active .chip-count {{
      background: rgba(255, 255, 255, 0.25);
    }}

    .top-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .action-btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 14px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border);
      background: #ffffff;
      color: var(--text);
      transition: all 0.15s;
    }}

    .action-btn:hover {{
      background: #f1f5f9;
      border-color: #cbd5e1;
    }}

    .action-btn.primary {{
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
    }}

    .action-btn.primary:hover {{
      background: var(--primary-dark);
    }}

    /* Mobile toggle */
    .mobile-menu-btn {{
      display: none;
      background: transparent;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px;
      color: var(--text);
      cursor: pointer;
    }}

    /* Content Container */
    .content-container {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 40px 36px 80px;
      width: 100%;
    }}

    /* Hero Banner */
    .hero-banner {{
      background: linear-gradient(135deg, #1e3a8a 0%, #0b1730 100%);
      color: #ffffff;
      border-radius: var(--radius-xl);
      padding: 40px 48px;
      margin-bottom: 36px;
      box-shadow: var(--shadow-lg);
      position: relative;
      overflow: hidden;
    }}

    .hero-banner::after {{
      content: "";
      position: absolute;
      right: -30px;
      bottom: -60px;
      width: 320px;
      height: 320px;
      background: radial-gradient(circle, rgba(20, 184, 166, 0.25) 0%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
    }}

    .hero-tags {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }}

    .hero-tag {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: rgba(255, 255, 255, 0.12);
      backdrop-filter: blur(8px);
      padding: 4px 12px;
      border-radius: 99px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #67e8f9;
    }}

    .hero-title {{
      font-size: 32px;
      font-weight: 800;
      line-height: 1.25;
      margin-bottom: 12px;
      letter-spacing: -0.02em;
    }}

    .hero-desc {{
      font-size: 15px;
      color: #cbd5e1;
      max-width: 800px;
      margin-bottom: 24px;
    }}

    .hero-meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: var(--radius);
      padding: 16px 20px;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .meta-box-item {{
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}

    .meta-box-label {{
      font-size: 11px;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 600;
    }}

    .meta-box-value {{
      font-size: 13px;
      color: #ffffff;
      font-weight: 600;
      word-break: break-word;
    }}

    .meta-box-value code {{
      font-family: var(--font-mono);
      font-size: 11.5px;
      background: rgba(0, 0, 0, 0.25);
      padding: 2px 6px;
      border-radius: 4px;
      color: #67e8f9;
    }}

    /* KPI Summary Cards */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 40px;
    }}

    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      box-shadow: var(--shadow-sm);
      display: flex;
      flex-direction: column;
      gap: 6px;
      transition: transform 0.2s, box-shadow 0.2s;
    }}

    .kpi-card:hover {{
      transform: translateY(-2px);
      box-shadow: var(--shadow);
    }}

    .kpi-number {{
      font-size: 28px;
      font-weight: 800;
      color: var(--secondary);
      line-height: 1;
    }}

    .kpi-number.accent {{ color: var(--primary); }}
    .kpi-number.critical {{ color: var(--p0-color); }}
    .kpi-number.high {{ color: var(--p1-color); }}
    .kpi-number.success {{ color: var(--success); }}

    .kpi-label {{
      font-size: 13px;
      font-weight: 600;
      color: var(--text);
    }}

    .kpi-subtext {{
      font-size: 11.5px;
      color: var(--text-muted);
    }}

    /* Search Results Indicator */
    .search-alert {{
      display: none;
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: var(--radius);
      padding: 12px 18px;
      margin-bottom: 24px;
      align-items: center;
      justify-content: space-between;
      color: #1e40af;
      font-size: 14px;
      font-weight: 500;
    }}

    .search-alert.active {{
      display: flex;
    }}

    .search-clear-btn {{
      background: none;
      border: none;
      color: var(--primary);
      font-weight: 700;
      cursor: pointer;
      text-decoration: underline;
    }}

    /* Sections */
    .doc-section {{
      margin-bottom: 48px;
      scroll-margin-top: 80px;
    }}

    .section-header {{
      margin-bottom: 20px;
    }}

    .section-header-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 4px;
    }}

    .section-tag {{
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--primary);
    }}

    .section-title {{
      font-size: 22px;
      font-weight: 800;
      color: var(--secondary);
      letter-spacing: -0.01em;
      margin-bottom: 6px;
    }}

    .section-desc {{
      color: var(--text-muted);
      font-size: 14.5px;
      margin-bottom: 16px;
    }}

    .section-note {{
      font-size: 13px;
      color: var(--text-muted);
      background: #f1f5f9;
      border-left: 3px solid var(--primary);
      padding: 8px 14px;
      border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
      margin-top: 8px;
    }}

    .tc-counter-badge {{
      font-size: 12px;
      font-weight: 700;
      background: #eff6ff;
      color: var(--primary);
      padding: 3px 10px;
      border-radius: 99px;
      border: 1px solid #bfdbfe;
    }}

    .module-meta-bar {{
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 14px;
      margin-top: 10px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .meta-item {{
      font-size: 13px;
      color: var(--text);
    }}

    .meta-label {{
      font-weight: 700;
      color: var(--text-muted);
      margin-right: 6px;
    }}

    /* Testing Strategy Grid */
    .strategy-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }}

    @media (max-width: 900px) {{
      .strategy-grid {{ grid-template-columns: 1fr; }}
    }}

    .subsection-title {{
      font-size: 16px;
      font-weight: 700;
      color: var(--secondary);
      margin-bottom: 14px;
    }}

    .pyramid-container {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      box-shadow: var(--shadow-sm);
    }}

    .pyramid-visual {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      margin-top: 16px;
    }}

    .pyramid-tier {{
      border-radius: 8px;
      padding: 12px 16px;
      text-align: center;
      display: flex;
      flex-direction: column;
      gap: 2px;
      transition: transform 0.2s;
      cursor: default;
    }}

    .pyramid-tier:hover {{
      transform: scale(1.02);
    }}

    .tier-uat {{
      width: 48%;
      background: #fee2e2;
      border: 1px solid #fca5a5;
      color: #991b1b;
    }}

    .tier-int {{
      width: 65%;
      background: #fef3c7;
      border: 1px solid #fcd34d;
      color: #92400e;
    }}

    .tier-ui {{
      width: 82%;
      background: #e0e7ff;
      border: 1px solid #a5b4fc;
      color: #3730a3;
    }}

    .tier-unit {{
      width: 100%;
      background: #dbeafe;
      border: 1px solid #93c5fd;
      color: #1e40af;
    }}

    .tier-label {{
      font-weight: 700;
      font-size: 13px;
    }}

    .tier-desc {{
      font-size: 11px;
      opacity: 0.85;
    }}

    .principles-container {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      box-shadow: var(--shadow-sm);
    }}

    .principles-grid {{
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .principle-card {{
      display: flex;
      align-items: flex-start;
      gap: 14px;
      padding: 12px 14px;
      border-radius: 8px;
      background: #f8fafc;
      border: 1px solid var(--border);
    }}

    .principle-icon {{
      color: var(--primary);
      flex-shrink: 0;
      margin-top: 2px;
    }}

    .principle-info h4 {{
      font-size: 13.5px;
      font-weight: 700;
      color: var(--secondary);
      margin-bottom: 2px;
    }}

    .principle-info p {{
      font-size: 12.5px;
      color: var(--text-muted);
      line-height: 1.5;
    }}

    /* Test Case Cards */
    .tc-cards-list {{
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .tc-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      overflow: hidden;
      transition: border-color 0.2s, box-shadow 0.2s;
    }}

    .tc-card:hover {{
      border-color: #cbd5e1;
      box-shadow: var(--shadow);
    }}

    .tc-card-header {{
      padding: 14px 20px;
      background: #f8fafc;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }}

    .tc-header-left {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .tc-id-badge {{
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 700;
      background: #0f172a;
      color: #38bdf8;
      padding: 3px 8px;
      border-radius: 6px;
      text-decoration: none;
      letter-spacing: 0.02em;
      transition: background 0.15s, color 0.15s;
    }}

    .tc-id-badge:hover {{
      background: var(--primary);
      color: #ffffff;
    }}

    .tc-title {{
      font-size: 15px;
      font-weight: 700;
      color: var(--secondary);
    }}

    .tc-header-right {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    /* Badges */
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 9px;
      border-radius: 99px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .badge-p0 {{
      background: var(--p0-bg);
      color: var(--p0-color);
      border: 1px solid var(--p0-border);
    }}

    .badge-p1 {{
      background: var(--p1-bg);
      color: var(--p1-color);
      border: 1px solid var(--p1-border);
    }}

    .badge-p2 {{
      background: var(--p2-bg);
      color: var(--p2-color);
      border: 1px solid var(--p2-border);
    }}

    .badge-security {{
      background: var(--security-bg);
      color: var(--security-color);
      border: 1px solid #fecaca;
    }}

    .badge-focus {{
      background: var(--focus-bg);
      color: var(--focus-color);
      border: 1px solid #c7d2fe;
    }}

    .status-btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 99px;
      font-size: 11px;
      font-weight: 600;
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      color: #475569;
      cursor: pointer;
      transition: all 0.15s;
    }}

    .status-btn:hover {{
      background: #e2e8f0;
    }}

    .status-indicator {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #94a3b8;
    }}

    .status-btn.passed {{
      background: var(--success-bg);
      border-color: var(--success-border);
      color: #065f46;
    }}

    .status-btn.passed .status-indicator {{
      background: var(--success);
    }}

    /* Card Body */
    .tc-card-body {{
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .tc-field {{
      display: flex;
      align-items: baseline;
      gap: 10px;
      font-size: 13.5px;
    }}

    .field-label {{
      font-weight: 700;
      min-width: 90px;
      flex-shrink: 0;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .condition-label {{ color: #7c3aed; }}
    .input-label {{ color: #0284c7; }}
    .flow-label {{ color: #059669; }}
    .cmd-label {{ color: #d97706; }}
    .expected-label {{ color: #0f172a; align-self: flex-start; margin-top: 4px; }}

    .field-content {{
      flex: 1;
      color: #334155;
    }}

    .expected-field {{
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 14px;
      margin-top: 4px;
    }}

    .expected-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .expected-list li {{
      display: flex;
      align-items: baseline;
      gap: 8px;
    }}

    .check-icon {{
      color: var(--success);
      font-weight: 800;
      font-size: 14px;
      flex-shrink: 0;
    }}

    .code-span {{
      font-family: var(--font-mono);
      font-size: 12px;
      background: #f1f5f9;
      color: #0f172a;
      padding: 2px 6px;
      border-radius: 4px;
      border: 1px solid #e2e8f0;
    }}

    .cmd-code {{
      font-family: var(--font-mono);
      font-size: 12.5px;
      background: #0f172a;
      color: #38bdf8;
      padding: 4px 8px;
      border-radius: 6px;
      display: inline-block;
    }}

    /* Tables */
    .table-container {{
      overflow-x: auto;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      box-shadow: var(--shadow-sm);
      margin: 12px 0;
    }}

    .styled-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13.5px;
      background: #ffffff;
      text-align: left;
    }}

    .styled-table th {{
      background: #f8fafc;
      color: #475569;
      font-weight: 700;
      padding: 12px 16px;
      border-bottom: 2px solid var(--border);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .styled-table td {{
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      color: var(--text);
    }}

    .styled-table tr:last-child td {{
      border-bottom: none;
    }}

    .styled-table tr:hover td {{
      background: #f8fafc;
    }}

    .tc-param-table {{
      margin: 4px 0 10px;
      font-size: 12.5px;
    }}

    .tc-param-table th, .tc-param-table td {{
      padding: 8px 12px;
    }}

    .device-badge {{
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      background: #f1f5f9;
      color: #475569;
      padding: 2px 8px;
      border-radius: 4px;
      border: 1px solid #cbd5e1;
    }}

    .uat-id {{
      font-family: var(--font-mono);
      color: var(--primary);
    }}

    /* Acceptance Criteria Section */
    .ac-progress-box {{
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 18px 24px;
      box-shadow: var(--shadow-sm);
      margin-bottom: 20px;
    }}

    .ac-progress-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }}

    .ac-progress-title {{
      font-weight: 700;
      color: var(--secondary);
      font-size: 14px;
    }}

    .ac-progress-stat {{
      font-size: 13px;
      font-weight: 700;
      color: var(--primary);
    }}

    .ac-progress-bar-bg {{
      height: 10px;
      background: #e2e8f0;
      border-radius: 99px;
      overflow: hidden;
    }}

    .ac-progress-bar-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--primary));
      border-radius: 99px;
      transition: width 0.3s ease;
    }}

    .ac-checklist {{
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .ac-item {{
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 16px 20px;
      display: flex;
      align-items: flex-start;
      gap: 16px;
      transition: border-color 0.2s, background 0.2s;
    }}

    .ac-item.completed {{
      background: #f0fdf4;
      border-color: #bbf7d0;
    }}

    .ac-checkbox-wrapper {{
      cursor: pointer;
      margin-top: 3px;
    }}

    .ac-checkbox-wrapper input {{
      display: none;
    }}

    .ac-custom-check {{
      width: 22px;
      height: 22px;
      border: 2px solid #cbd5e1;
      border-radius: 6px;
      display: grid;
      place-items: center;
      transition: all 0.15s;
    }}

    .ac-checkbox-wrapper input:checked + .ac-custom-check {{
      background: var(--success);
      border-color: var(--success);
      color: #ffffff;
    }}

    .ac-checkbox-wrapper input:checked + .ac-custom-check::after {{
      content: "✓";
      font-size: 14px;
      font-weight: 800;
    }}

    .ac-content {{
      flex: 1;
    }}

    .ac-header {{
      display: flex;
      align-items: baseline;
      gap: 10px;
      margin-bottom: 6px;
    }}

    .ac-code {{
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 700;
      background: #0f172a;
      color: #ffffff;
      padding: 2px 7px;
      border-radius: 4px;
    }}

    .ac-title {{
      font-size: 14.5px;
      font-weight: 700;
      color: var(--secondary);
    }}

    .ac-meta {{
      font-size: 13px;
      color: var(--text-muted);
    }}

    .ac-tcs-label {{
      font-weight: 600;
    }}

    .tc-jump-link {{
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--primary);
      text-decoration: none;
      background: #eff6ff;
      padding: 1px 6px;
      border-radius: 4px;
      border: 1px solid #bfdbfe;
      margin: 0 2px;
      display: inline-block;
      transition: all 0.15s;
    }}

    .tc-jump-link:hover {{
      background: var(--primary);
      color: #ffffff;
    }}

    /* Mapping table badges */
    .mod-pill {{
      font-family: var(--font-mono);
      font-weight: 700;
      color: var(--secondary);
    }}

    .badge-count {{
      background: #eff6ff;
      color: var(--primary);
      border: 1px solid #bfdbfe;
      font-family: var(--font-mono);
    }}

    .total-row {{
      color: var(--primary);
      font-weight: 800;
    }}

    .total-badge {{
      color: #ffffff;
      background: var(--primary);
      padding: 3px 10px;
      border-radius: 99px;
      font-weight: 800;
      font-family: var(--font-mono);
      display: inline-block;
    }}

    .action-highlight {{
      font-weight: 600;
      color: var(--primary);
    }}

    .doc-footer-note {{
      margin-top: 24px;
      background: #f1f5f9;
      border-radius: var(--radius);
      padding: 14px 18px;
      font-size: 13px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    /* Toast Notification */
    .toast-msg {{
      position: fixed;
      bottom: 80px;
      right: 24px;
      background: #0f172a;
      color: #ffffff;
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      box-shadow: var(--shadow-lg);
      transform: translateY(30px);
      opacity: 0;
      transition: all 0.25s ease;
      z-index: 1000;
      pointer-events: none;
    }}

    .toast-msg.show {{
      transform: translateY(0);
      opacity: 1;
    }}

    /* Floating Back to Top Button */
    .floating-tools {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      z-index: 95;
    }}

    .fab-btn {{
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: var(--secondary);
      color: #ffffff;
      border: 1px solid rgba(255, 255, 255, 0.2);
      display: grid;
      place-items: center;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
      transition: all 0.2s;
    }}

    .fab-btn:hover {{
      background: var(--primary);
      transform: translateY(-2px);
    }}

    /* Responsive adjustments */
    @media (max-width: 1024px) {{
      .sidebar {{
        position: fixed;
        left: 0;
        top: 0;
        transform: translateX(-100%);
      }}

      .sidebar.open {{
        transform: translateX(0);
      }}

      .mobile-menu-btn {{
        display: block;
      }}

      .content-container {{
        padding: 24px 20px 60px;
      }}

      .hero-banner {{
        padding: 30px 24px;
      }}

      .hero-title {{
        font-size: 26px;
      }}
    }}

    /* Print styling for PDF conversion */
    @media print {{
      body {{
        background: #ffffff !important;
        color: #000000 !important;
      }}

      .sidebar, .top-action-bar, .floating-tools, .mobile-menu-btn, .search-alert, .toast-msg {{
        display: none !important;
      }}

      .app-layout {{
        display: block !important;
      }}

      .content-container {{
        max-width: 100% !important;
        padding: 0 !important;
      }}

      .hero-banner {{
        background: #0f172a !important;
        color: #ffffff !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        page-break-after: avoid;
      }}

      .tc-card, .ac-item, .principle-card, .pyramid-container {{
        break-inside: avoid;
        page-break-inside: avoid;
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
      }}

      .tc-card-body {{
        display: flex !important;
      }}

      .tc-card-header {{
        background: #f1f5f9 !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }}

      .badge, .device-badge, .code-span, .cmd-code {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }}
    }}
  </style>
</head>
<body>

  <div class="app-layout">
    <!-- Sidebar Navigation -->
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-header">
        <div class="brand-box">
          <div class="brand-logo">TV</div>
          <div class="brand-meta">
            <span class="brand-name">TrafficVision</span>
            <span class="brand-tagline">Test Design v1.0</span>
          </div>
        </div>
        <div class="sidebar-search-box">
          <svg class="sidebar-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" id="quickSearchInput" placeholder="Tìm kiếm nhanh test case..." oninput="handleSearch(this.value)">
        </div>
      </div>
      <nav class="sidebar-nav">
        {sidebar_nav_html}
      </nav>
    </aside>

    <!-- Main Content Area -->
    <main class="main-wrapper">
      <!-- Top Action Toolbar -->
      <header class="top-action-bar">
        <div style="display: flex; align-items: center; gap: 12px;">
          <button class="mobile-menu-btn" onclick="toggleSidebar()" title="Mở danh mục">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
          </button>
          <div class="filter-chips">
            <button class="chip-btn active" data-filter="all" onclick="setFilter('all')">Tất cả <span class="chip-count">{total_tcs}</span></button>
            <button class="chip-btn" data-filter="P0" onclick="setFilter('P0')">P0 Critical <span class="chip-count" style="color: #ef4444; font-weight: 700;">{p0_count}</span></button>
            <button class="chip-btn" data-filter="P1" onclick="setFilter('P1')">P1 High <span class="chip-count" style="color: #f59e0b; font-weight: 700;">{p1_count}</span></button>
            <button class="chip-btn" data-filter="P2" onclick="setFilter('P2')">P2 Medium <span class="chip-count" style="color: #3b82f6; font-weight: 700;">{p2_count}</span></button>
            <button class="chip-btn" data-filter="Security" onclick="setFilter('Security')">Security <span class="chip-count">{security_count}</span></button>
            <button class="chip-btn" data-filter="Focus" onclick="setFilter('Focus')">Review Focus <span class="chip-count">{rf1_count + rf2_count}</span></button>
          </div>
        </div>
        <div class="top-actions">
          <button class="action-btn" onclick="toggleAllCards()" id="toggleAllBtn">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            <span>Thu gọn</span>
          </button>
          <button class="action-btn primary" onclick="window.print()">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
            <span>Xuất PDF / In</span>
          </button>
        </div>
      </header>

      <!-- Main Container -->
      <div class="content-container">
        <!-- Hero Header -->
        <div class="hero-banner">
          <div class="hero-tags">
            <span class="hero-tag">Quality Assurance</span>
            <span class="hero-tag">TrafficVision v1.0</span>
            <span class="hero-tag">37 Test Files</span>
            <span class="hero-tag">215 Tests Pytest</span>
          </div>
          <h1 class="hero-title">{html.escape(doc_title)}</h1>
          <p class="hero-desc">Tài liệu đặc tả toàn bộ chiến lược, các ca kiểm thử tự động, tích hợp end-to-end, tiêu chuẩn chất lượng (Quality Gate) và tiêu chí nghiệm thu cho hệ thống nhận dạng biển báo giao thông Việt Nam.</p>
          
          <div class="hero-meta-grid">
            <div class="meta-box-item">
              <span class="meta-box-label">Dự án</span>
              <span class="meta-box-value">{html.escape(meta_dict.get("Dự án", "TrafficVision"))}</span>
            </div>
            <div class="meta-box-item">
              <span class="meta-box-label">Phiên bản & Ngày</span>
              <span class="meta-box-value">v{html.escape(meta_dict.get("Phiên bản tài liệu", "1.0"))} — {html.escape(meta_dict.get("Ngày", "03/10/2026"))}</span>
            </div>
            <div class="meta-box-item">
              <span class="meta-box-label">Tham chiếu Spec</span>
              <span class="meta-box-value"><code>{html.escape(meta_dict.get("Tham chiếu Spec", "").replace("`", ""))}</code></span>
            </div>
            <div class="meta-box-item">
              <span class="meta-box-label">Tham chiếu Plans</span>
              <span class="meta-box-value"><code>Plan 1 Baseline</code> + <code>Plan 2 Pipeline</code></span>
            </div>
          </div>
        </div>

        <!-- KPI Metric Grid -->
        <div class="kpi-grid">
          <div class="kpi-card">
            <span class="kpi-number accent">215</span>
            <span class="kpi-label">Pytest Tests</span>
            <span class="kpi-subtext">37 files kiểm thử tự động</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-number">{total_tcs}</span>
            <span class="kpi-label">Test Cases Thiết kế</span>
            <span class="kpi-subtext">Đặc tả chi tiết từng module</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-number critical">{p0_count}</span>
            <span class="kpi-label">P0 Critical</span>
            <span class="kpi-subtext">Toàn vẹn & An toàn bảo mật</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-number high">{p1_count}</span>
            <span class="kpi-label">P1 High</span>
            <span class="kpi-subtext">Chức năng & Logic xử lý</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-number success">10</span>
            <span class="kpi-label">Kịch bản UAT</span>
            <span class="kpi-subtext">Ảnh, video, CPU & OS</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-number accent">9</span>
            <span class="kpi-label">Tiêu chí AC</span>
            <span class="kpi-subtext">Acceptance Criteria bảo vệ</span>
          </div>
        </div>

        <!-- Search Status Alert -->
        <div class="search-alert" id="searchAlert">
          <span>Tìm thấy <strong id="searchMatchCount">0</strong> test cases phù hợp với từ khóa "<span id="searchKeyword"></span>"</span>
          <button class="search-clear-btn" onclick="clearSearch()">Xóa tìm kiếm</button>
        </div>

        <!-- Rendered Sections -->
        {main_content_html}
      </div>
    </main>
  </div>

  <!-- Toast message -->
  <div class="toast-msg" id="toastMsg">Đã sao chép link test case vào clipboard!</div>

  <!-- Floating Tools -->
  <div class="floating-tools">
    <button class="fab-btn" onclick="scrollToTop()" title="Lên đầu trang">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="18 15 12 9 6 15"/></svg>
    </button>
  </div>

  <script>
    let currentFilter = 'all';
    let currentKeyword = '';
    let isAllCollapsed = false;

    function copyTcLink(event, tcid) {{
      event.preventDefault();
      const url = window.location.origin + window.location.pathname + '#' + tcid;
      navigator.clipboard.writeText(url).then(() => {{
        showToast('Đã sao chép liên kết ' + tcid + '!');
      }}).catch(() => {{
        window.location.hash = tcid;
      }});
      history.pushState(null, null, '#' + tcid);
      const card = document.getElementById(tcid);
      if (card) {{
        card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      }}
    }}

    function showToast(msg) {{
      const toast = document.getElementById('toastMsg');
      if (!toast) return;
      toast.textContent = msg;
      toast.classList.add('show');
      setTimeout(() => {{
        toast.classList.remove('show');
      }}, 2500);
    }}

    function loadTestStatuses() {{
      try {{
        const saved = JSON.parse(localStorage.getItem('tv_test_status') || '{{}}');
        for (const [tcid, status] of Object.entries(saved)) {{
          const card = document.getElementById(tcid);
          if (card) {{
            const btn = card.querySelector('.status-btn');
            if (btn && status === 'passed') {{
              btn.classList.add('passed');
              btn.querySelector('.status-text').textContent = 'Passed';
            }}
          }}
        }}
      }} catch (e) {{}}

      try {{
        const savedAc = JSON.parse(localStorage.getItem('tv_ac_status') || '{{}}');
        for (const [acid, checked] of Object.entries(savedAc)) {{
          const chk = document.getElementById('check-' + acid);
          if (chk && checked) {{
            chk.checked = true;
            const card = document.getElementById('card-' + acid);
            if (card) card.classList.add('completed');
          }}
        }}
        recalcACProgress();
      }} catch (e) {{}}
    }}

    function toggleTestStatus(tcid) {{
      const card = document.getElementById(tcid);
      let btn = null;
      if (card) {{
        btn = card.querySelector('.status-btn');
      }} else {{
        // Might be UAT row button
        const rows = document.querySelectorAll('.uat-table tbody tr');
        rows.forEach(r => {{
          const idEl = r.querySelector('.uat-id');
          if (idEl && idEl.textContent.trim() === tcid) {{
            btn = r.querySelector('.status-btn');
          }}
        }});
      }}
      if (!btn) return;

      const isPassed = btn.classList.contains('passed');
      if (isPassed) {{
        btn.classList.remove('passed');
        btn.querySelector('.status-text').textContent = 'Pending';
      }} else {{
        btn.classList.add('passed');
        btn.querySelector('.status-text').textContent = 'Passed';
      }}

      try {{
        const saved = JSON.parse(localStorage.getItem('tv_test_status') || '{{}}');
        saved[tcid] = !isPassed ? 'passed' : 'pending';
        localStorage.setItem('tv_test_status', JSON.stringify(saved));
      }} catch (e) {{}}
    }}

    function updateACProgress(acid, isChecked) {{
      const card = document.getElementById('card-' + acid);
      if (card) {{
        if (isChecked) card.classList.add('completed');
        else card.classList.remove('completed');
      }}

      try {{
        const savedAc = JSON.parse(localStorage.getItem('tv_ac_status') || '{{}}');
        savedAc[acid] = isChecked;
        localStorage.setItem('tv_ac_status', JSON.stringify(savedAc));
      }} catch (e) {{}}

      recalcACProgress();
    }}

    function recalcACProgress() {{
      const checkboxes = document.querySelectorAll('.ac-checkbox-wrapper input[type="checkbox"]');
      const total = checkboxes.length;
      if (total === 0) return;
      let checked = 0;
      checkboxes.forEach(c => {{ if (c.checked) checked++; }});
      const percent = Math.round((checked / total) * 100);

      const stat = document.getElementById('acProgressStat');
      const fill = document.getElementById('acProgressBarFill');
      if (stat) stat.textContent = `${{checked}} / ${{total}} tiêu chí hoàn tất (${{percent}}%)`;
      if (fill) fill.style.width = `${{percent}}%`;
    }}

    function setFilter(filterType) {{
      currentFilter = filterType;
      document.querySelectorAll('.chip-btn').forEach(btn => {{
        if (btn.getAttribute('data-filter') === filterType) btn.classList.add('active');
        else btn.classList.remove('active');
      }});
      applyFilters();
    }}

    function handleSearch(val) {{
      currentKeyword = val.trim().toLowerCase();
      applyFilters();
    }}

    function clearSearch() {{
      currentKeyword = '';
      const input = document.getElementById('quickSearchInput');
      if (input) input.value = '';
      applyFilters();
    }}

    function applyFilters() {{
      const cards = document.querySelectorAll('.tc-card');
      let visibleCount = 0;

      cards.forEach(card => {{
        const prio = card.getAttribute('data-prio');
        const tag = card.getAttribute('data-tag');
        const searchTerms = card.getAttribute('data-search') || '';

        let matchesFilter = true;
        if (currentFilter === 'P0' && prio !== 'P0') matchesFilter = false;
        else if (currentFilter === 'P1' && prio !== 'P1') matchesFilter = false;
        else if (currentFilter === 'P2' && prio !== 'P2') matchesFilter = false;
        else if (currentFilter === 'Security' && tag !== 'Security') matchesFilter = false;
        else if (currentFilter === 'Focus' && !tag.includes('Review Focus')) matchesFilter = false;

        let matchesSearch = true;
        if (currentKeyword) {{
          matchesSearch = searchTerms.includes(currentKeyword);
        }}

        if (matchesFilter && matchesSearch) {{
          card.style.display = 'block';
          visibleCount++;
        }} else {{
          card.style.display = 'none';
        }}
      }});

      const alertBox = document.getElementById('searchAlert');
      const countEl = document.getElementById('searchMatchCount');
      const kwEl = document.getElementById('searchKeyword');

      if (currentKeyword) {{
        alertBox.classList.add('active');
        if (countEl) countEl.textContent = visibleCount;
        if (kwEl) kwEl.textContent = currentKeyword;
      }} else {{
        alertBox.classList.remove('active');
      }}

      document.querySelectorAll('.module-section').forEach(sec => {{
        const secCards = sec.querySelectorAll('.tc-card');
        const hasVisible = Array.from(secCards).some(c => c.style.display !== 'none');
        sec.style.display = hasVisible ? 'block' : 'none';
      }});
    }}

    function toggleAllCards() {{
      isAllCollapsed = !isAllCollapsed;
      const bodies = document.querySelectorAll('.tc-card-body');
      const btn = document.getElementById('toggleAllBtn');

      bodies.forEach(b => {{
        b.style.display = isAllCollapsed ? 'none' : 'flex';
      }});

      if (btn) {{
        btn.querySelector('span').textContent = isAllCollapsed ? 'Mở rộng' : 'Thu gọn';
      }}
    }}

    function toggleSidebar() {{
      const sidebar = document.getElementById('sidebar');
      if (sidebar) sidebar.classList.toggle('open');
    }}

    function scrollToTop() {{
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}

    window.addEventListener('scroll', () => {{
      const sections = document.querySelectorAll('.doc-section');
      const navItems = document.querySelectorAll('.nav-item');
      let currentId = '';

      sections.forEach(sec => {{
        const rect = sec.getBoundingClientRect();
        if (rect.top <= 140 && rect.bottom >= 140) {{
          currentId = sec.getAttribute('id');
        }}
      }});

      if (currentId) {{
        navItems.forEach(item => {{
          if (item.getAttribute('data-target') === currentId) {{
            item.classList.add('active');
          }} else {{
            item.classList.remove('active');
          }}
        }});
      }}
    }});

    document.addEventListener('DOMContentLoaded', () => {{
      loadTestStatuses();
    }});
  </script>
</body>
</html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"Generated {HTML_FILE} successfully! Size: {HTML_FILE.stat().st_size} bytes")


if __name__ == "__main__":
    generate_html()
