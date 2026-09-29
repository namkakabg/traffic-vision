from __future__ import annotations

import io
import re

import pandas as pd
import streamlit as st

from trafficvision.domain import RegisteredModel
from trafficvision.ui.theme import clean_html


def render_baseline_warning(model: RegisteredModel | None) -> None:
    """Render baseline warning banner if model is baseline or missing."""
    if model is None:
        st.warning(
            "⚠️ Hệ thống chưa được cài đặt mô hình production. "
            "Vui lòng chạy lệnh bootstrap trong terminal: `python scripts/bootstrap_baseline.py`"
        )
        return

    is_baseline = (
        model.manifest.stage == "baseline"
        or (model.manifest.source_model_id and "baseline" in model.manifest.source_model_id)
        or ("yolo11n" in model.manifest.source.lower() and len(model.manifest.class_names) != 82)
        or ("baseline" in model.manifest.model_id.lower())
        or (len(model.manifest.class_names) != 82)
    )
    if is_baseline:
        st.warning(
            "⚠️ Baseline — chưa fine-tune biển báo Việt Nam. "
            "Hệ thống đang chạy mô hình gốc YOLO11n ONNX để kiểm chứng ứng dụng."
        )


def format_display_name(c_name: str) -> str:
    """Provide friendly Vietnamese label alongside original class name."""
    coco_vn = {
        "stop sign": "Biển dừng lại (STOP)",
        "traffic light": "Đèn tín hiệu giao thông",
        "truck": "Xe tải (truck)",
        "car": "Ô tô (car)",
        "motorcycle": "Xe máy (motorcycle)",
        "person": "Người đi bộ (person)",
        "bicycle": "Xe đạp (bicycle)",
        "bus": "Xe buýt (bus)",
    }
    return coco_vn.get(c_name.lower(), c_name)


def extract_mini_badge(c_name: str, c_id: str = "") -> tuple[str, str]:
    """Extract recognized text (e.g. 'STOP', '50') or icon and style for mini circular badge."""
    lower = c_name.lower()

    # 1. Stop sign -> text 'STOP' in bold red matching real stop signs
    if "stop" in lower:
        return "STOP", "border-color: #e74444; color: #e74444; font-size: 8.5px; font-weight: 900; letter-spacing: -0.5px;"

    # 2. Check for speed limit numbers (e.g., 50, 60, 80, P.127-50, etc.)
    speed_matches = re.findall(r"\b(20|30|40|50|60|70|80|90|100|120)\b", c_name)
    if not speed_matches:
        speed_matches = re.findall(r"[-_\.]?(20|30|40|50|60|70|80|90|100|120)", c_name)
    if speed_matches:
        num = speed_matches[0]
        return num, "border-color: #e74444; color: #17263b; font-size: 11px; font-weight: 900;"

    # 3. Check general numbers in class name or class ID
    nums = re.findall(r"\d+", c_name)
    if nums and len(nums[0]) <= 3:
        return nums[0], "border-color: #e74444; color: #17263b; font-size: 10px; font-weight: 900;"

    # 4. Words on signs (SLOW, BUS, TAXI, ZONE)
    for word in ["slow", "bus", "taxi", "zone"]:
        if word in lower:
            return word.upper(), "border-color: #e74444; color: #17263b; font-size: 8.5px; font-weight: 900;"

    # 5. Vietnamese Traffic Sign Categories
    if lower.startswith("p.") or "cam" in lower or "cấm" in lower:
        return "⛔", "border-color: #e74444; font-size: 13px;"
    if lower.startswith("w.") or "nguy_hiem" in lower or "canh_bao" in lower:
        return "⚠️", "border-color: #f59e0b; font-size: 13px;"
    if lower.startswith("r.") or "hieu_lenh" in lower:
        return "🔵", "border-color: #2563eb; font-size: 13px;"
    if lower.startswith("i.") or "chi_dan" in lower:
        return "🟦", "border-color: #0ea5e9; font-size: 13px;"

    # 6. Common traffic and baseline COCO classes
    coco_map = {
        "truck": "🚚",
        "person": "🚶",
        "car": "🚗",
        "motorcycle": "🏍️",
        "bus": "🚌",
        "bicycle": "🚲",
        "train": "🚆",
        "traffic light": "🚦",
        "fire hydrant": "🧯",
    }
    for k, v in coco_map.items():
        if k in lower:
            return v, "border-color: #2563eb; font-size: 13px;"

    return "🚦", "border-color: #2563eb; font-size: 13px;"


def render_detection_summary(
    class_counts: dict[str, int],
    total_detections: int,
    elapsed_ms: float,
    num_classes: int = 82,
    csv_bytes: bytes | None = None,
) -> None:
    """Render modern summary panel matching design mockup."""
    # Determine max confidence and detection items from CSV if available
    max_conf_str = "0%"
    detection_items: list[dict[str, str]] = []

    if csv_bytes:
        try:
            df = pd.read_csv(io.BytesIO(csv_bytes))
            if not df.empty and "confidence" in df.columns:
                max_val = float(df["confidence"].max())
                max_conf_str = f"{int(round(max_val * 100))}%"

                # Extract prominent detections for display
                for _, row in df.head(8).iterrows():
                    c_id = str(row.get("class_id", ""))
                    c_name = str(row.get("class_name", ""))
                    conf = float(row.get("confidence", 0.0))
                    score_str = f"{int(round(conf * 100))}%"

                    mini, style = extract_mini_badge(c_name, c_id)
                    display_name = format_display_name(c_name)

                    detection_items.append(
                        {
                            "mini": mini,
                            "style": style,
                            "name": display_name,
                            "code": f"Mã lớp: {c_id}" if c_id else "Phát hiện",
                            "score": score_str,
                        }
                    )
        except Exception:
            pass

    if not detection_items and class_counts:
        max_conf_str = "100%" if total_detections > 0 else "0%"
        for c_name, count in class_counts.items():
            mini, style = extract_mini_badge(c_name)
            display_name = format_display_name(c_name)
            detection_items.append(
                {
                    "mini": mini,
                    "style": style,
                    "name": display_name,
                    "code": f"Số lượng: {count}",
                    "score": f"{count} đối tượng",
                }
            )

    # Format numbers
    det_formatted = f"{total_detections:02d}" if total_detections < 100 else str(total_detections)
    time_formatted = f"{elapsed_ms:.0f}"

    # Build HTML for stats grid
    stats_html = f"""
    <div class="tv-panel">
        <div class="tv-panelhead">
            <span class="tv-paneltitle">Tóm tắt phân tích</span>
            <span style="color:#18a77d; font-size:10px; font-weight:800; letter-spacing:0.06em;">● HOÀN TẤT</span>
        </div>
        <div class="tv-panelcontent">
            <div class="tv-stats">
                <div class="tv-stat">
                    <div class="tv-statnum">{det_formatted}</div>
                    <div class="tv-statlabel">Biển báo phát hiện</div>
                </div>
                <div class="tv-stat">
                    <div class="tv-statnum">{max_conf_str}</div>
                    <div class="tv-statlabel">Độ tin cậy cao nhất</div>
                </div>
                <div class="tv-stat">
                    <div class="tv-statnum">{time_formatted}<span style="font-size:11px; font-weight:600; color:#7a8798;"> ms</span></div>
                    <div class="tv-statlabel">Thời gian suy luận</div>
                </div>
                <div class="tv-stat">
                    <div class="tv-statnum">{num_classes}</div>
                    <div class="tv-statlabel">Lớp được hỗ trợ</div>
                </div>
            </div>
    """

    # Build HTML for detection items
    if detection_items:
        items_html = """
            <div class="tv-section-label">Đối tượng nhận dạng</div>
            <div class="tv-detect">
        """
        for it in detection_items:
            items_html += f"""
                <div class="tv-row">
                    <div class="tv-mini" style="{it['style']}">{it['mini']}</div>
                    <div>
                        <div class="tv-rname">{it['name']}</div>
                        <div class="tv-rcode">{it['code']}</div>
                    </div>
                    <div class="tv-score">{it['score']}</div>
                </div>
            """
        items_html += "</div>"
        stats_html += items_html
    else:
        stats_html += """
            <div class="tv-notice" style="background:#f4f6fa; border-color:#e0e7ef; color:#5c6c80;">
                <span>ℹ️</span>
                <span>Không phát hiện đối tượng nào vượt ngưỡng tin cậy trong tệp tải lên.</span>
            </div>
        """

    # Notice disclaimer
    stats_html += """
            <div class="tv-notice">
                <span>ⓘ</span>
                <span>Kết quả AI mang tính hỗ trợ. Độ chính xác có thể giảm khi biển báo nhỏ, bị che khuất hoặc ảnh thiếu sáng.</span>
            </div>
        </div>
    </div>
    """

    st.markdown(clean_html(stats_html), unsafe_allow_html=True)


def render_download_buttons(
    annotated_bytes: bytes,
    media_filename: str,
    csv_bytes: bytes,
    csv_filename: str,
    media_mime: str = "image/jpeg",
) -> None:
    """Render download buttons matching mockup styles."""
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.download_button(
            label="↓ Tải tệp kết quả",
            data=annotated_bytes,
            file_name=media_filename,
            mime=media_mime,
            use_container_width=True,
            key=f"dl_media_{media_filename}",
        )
    with c2:
        st.download_button(
            label="📊 Tải CSV",
            data=csv_bytes,
            file_name=csv_filename,
            mime="text/csv",
            use_container_width=True,
            key=f"dl_csv_{csv_filename}",
        )
