import io
import re
from collections.abc import Sequence
from typing import Any

import pandas as pd
import streamlit as st

from trafficvision.domain import Detection, RegisteredModel
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
    """Return the most meaningful compact pictogram for a detected class."""
    lower = c_name.lower()

    # Prefer a pictogram that reflects the named sign over a broad sign category.
    named_sign_icons = (
        ("cấm đi ngược chiều", "⛔", "#e74444"),
        ("cấm xe tải", "🚚", "#e74444"),
        ("cấm xe buýt", "🚌", "#e74444"),
        ("cấm ô tô", "🚗", "#e74444"),
        ("cấm mô tô", "🏍️", "#e74444"),
        ("cấm xe máy", "🏍️", "#e74444"),
        ("cấm còi", "📯", "#e74444"),
        ("cấm đỗ xe", "P", "#e74444"),
        ("cấm rẽ trái", "↰", "#e74444"),
        ("cấm rẽ phải", "↱", "#e74444"),
        ("cấm quay đầu", "↶", "#e74444"),
        ("đi về bên phải", "→", "#2563eb"),
        ("đi về bên trái", "←", "#2563eb"),
        ("rẽ trái", "←", "#2563eb"),
        ("rẽ phải", "→", "#2563eb"),
        ("vòng xuyến", "↻", "#2563eb"),
        ("nơi quay đầu", "↶", "#0ea5e9"),
        ("camera", "📷", "#0ea5e9"),
        ("trẻ em", "🧒", "#f59e0b"),
        ("đường dành cho người đi bộ", "🚶", "#2563eb"),
        ("người đi bộ", "🚶", "#f59e0b"),
        ("đèn giao thông", "🚦", "#f59e0b"),
        ("đèn xanh", "🟢", "#18a77d"),
        ("đèn đỏ", "🔴", "#e74444"),
        ("đường sắt", "🚆", "#f59e0b"),
        ("công trường", "🚧", "#f59e0b"),
        ("bến xe buýt", "🚌", "#0ea5e9"),
        ("bệnh viện", "H+", "#0ea5e9"),
        ("chỗ đỗ xe", "P", "#0ea5e9"),
    )
    for keyword, icon, color in named_sign_icons:
        if keyword in lower:
            return icon, f"border-color: {color}; font-size: 13px;"

    # 1. Stop sign -> text 'STOP' in bold red matching real stop signs
    if "stop" in lower:
        return (
            "STOP",
            "border-color: #e74444; color: #e74444; font-size: 8.5px; font-weight: 900; letter-spacing: -0.5px;",
        )

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
            return (
                word.upper(),
                "border-color: #e74444; color: #17263b; font-size: 8.5px; font-weight: 900;",
            )

    # 5. Vietnamese Traffic Sign Categories
    if lower.startswith("p.") or "cam" in lower or "cấm" in lower:
        return "⛔", "border-color: #e74444; font-size: 13px;"
    if (
        lower.startswith("w.")
        or "nguy_hiem" in lower
        or "canh_bao" in lower
        or "nguy hiểm" in lower
        or "cảnh báo" in lower
    ):
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

    return "◇", "border-color: #64748b; color: #64748b; font-size: 13px;"


def render_detection_summary(
    class_counts: dict[str, int],
    total_detections: int,
    elapsed_ms: float,
    num_classes: int = 82,
    csv_bytes: bytes | None = None,
    detections: Sequence[Detection] | None = None,
    selected_index: int | None = None,
    crop_bytes: bytes | None = None,
) -> None:
    """Render modern summary panel matching design mockup with interactive detection selection."""
    max_conf_str = "0%"
    csv_rows: list[dict[str, Any]] = []

    if csv_bytes:
        try:
            df = pd.read_csv(io.BytesIO(csv_bytes))
            if not df.empty and "confidence" in df.columns:
                max_val = float(df["confidence"].max())
                max_conf_str = f"{int(round(max_val * 100))}%"
                csv_rows = df.to_dict("records")
        except Exception:
            pass

    if not max_conf_str or max_conf_str == "0%":
        if total_detections > 0:
            if detections:
                max_val = max(d.confidence for d in detections)
                max_conf_str = f"{int(round(max_val * 100))}%"
            else:
                max_conf_str = "100%"
        else:
            max_conf_str = "0%"

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

    has_individual_dets = (detections is not None and len(detections) > 0) or (len(csv_rows) > 0)

    # Render top container with stats
    st.markdown(clean_html(stats_html + "</div></div>"), unsafe_allow_html=True)

    # Section for individual detections if available
    if has_individual_dets:
        st.markdown(
            clean_html("""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px; margin-bottom:6px;">
                <span class="tv-section-label" style="padding:0;">Đối tượng nhận dạng (Bấm chọn để rọi sáng)</span>
            </div>
            """),
            unsafe_allow_html=True,
        )

        num_items = len(detections) if detections is not None else len(csv_rows)
        # Limit interactive list to first 12 items for clean UX if huge number of detections
        display_count = min(num_items, 12)

        for i in range(display_count):
            if detections is not None and i < len(detections):
                det = detections[i]
                c_name = det.class_name
                c_id = str(det.class_id)
                conf = det.confidence
            else:
                row = csv_rows[i]
                c_name = str(row.get("class_name", ""))
                c_id = str(row.get("class_id", ""))
                conf = float(row.get("confidence", 0.0))

            score_str = f"{int(round(conf * 100))}%"
            mini, style = extract_mini_badge(c_name, c_id)
            display_name = format_display_name(c_name)
            is_active = selected_index == i

            # Render button row for selecting using sign icon directly
            icon_prefix = f"{mini} " if mini else ""
            if is_active:
                btn_label = f"🎯 {icon_prefix}{display_name}  ({score_str})  ✓"
            else:
                btn_label = f"{icon_prefix}{display_name}  ({score_str})"

            if st.button(
                btn_label,
                key=f"det_row_select_{i}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                if st.session_state.get("selected_detection_idx") == i:
                    st.session_state["selected_detection_idx"] = None
                else:
                    st.session_state["selected_detection_idx"] = i
                st.rerun()

        # If a detection is currently selected, show the zoomed crop preview and clear button
        if selected_index is not None and crop_bytes is not None and 0 <= selected_index < num_items:
            if detections is not None and selected_index < len(detections):
                sel_name = detections[selected_index].class_name
                sel_id = str(detections[selected_index].class_id)
            else:
                sel_name = str(csv_rows[selected_index].get("class_name", ""))
                sel_id = str(csv_rows[selected_index].get("class_id", ""))
            sel_icon, _ = extract_mini_badge(sel_name, sel_id)
            sel_display = format_display_name(sel_name)
            sel_prefix = f"{sel_icon} " if sel_icon else ""

            st.markdown(
                clean_html(f"""
                <div class="tv-crop-card">
                    <div class="tv-crop-header">
                        <span>🔍 Chi tiết phóng to: <strong>{sel_prefix}{sel_display}</strong></span>
                        <span style="color:#2563eb; font-weight:800;">🎯 SPOTLIGHT</span>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )
            st.image(crop_bytes, caption=f"{sel_prefix}{sel_display}", use_container_width=True)

            if st.button("✖ Bỏ chọn (Xem toàn bộ ảnh)", key="btn_clear_selection", use_container_width=True):
                st.session_state["selected_detection_idx"] = None
                st.rerun()

    elif class_counts:
        # Fallback to grouped class counts
        st.markdown(
            clean_html("""
            <div class="tv-section-label" style="margin-top:8px;">Đối tượng nhận dạng</div>
            """),
            unsafe_allow_html=True,
        )
        items_html = "<div class='tv-detect'>"
        for c_name, count in class_counts.items():
            mini, style = extract_mini_badge(c_name)
            display_name = format_display_name(c_name)
            items_html += f"""
                <div class="tv-row">
                    <div class="tv-mini" style="{style}">{mini}</div>
                    <div>
                        <div class="tv-rname">{display_name}</div>
                        <div class="tv-rcode">Số lượng: {count}</div>
                    </div>
                    <div class="tv-score">{count} đối tượng</div>
                </div>
            """
        items_html += "</div>"
        st.markdown(clean_html(items_html), unsafe_allow_html=True)
    else:
        st.markdown(
            clean_html("""
            <div class="tv-notice" style="background:#f4f6fa; border-color:#e0e7ef; color:#5c6c80; margin-top:8px;">
                <span>ℹ️</span>
                <span>Không phát hiện đối tượng nào vượt ngưỡng tin cậy trong tệp tải lên.</span>
            </div>
            """),
            unsafe_allow_html=True,
        )

    # Notice disclaimer
    disclaimer_html = """
    <div class="tv-notice" style="margin-top:8px;">
        <span>ⓘ</span>
        <span>Kết quả AI mang tính hỗ trợ. Độ chính xác có thể giảm khi biển báo nhỏ, bị che khuất hoặc ảnh thiếu sáng.</span>
    </div>
    """
    st.markdown(clean_html(disclaimer_html), unsafe_allow_html=True)


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
