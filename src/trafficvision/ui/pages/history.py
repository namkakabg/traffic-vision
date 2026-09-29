from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

from trafficvision.ui.theme import clean_html

if TYPE_CHECKING:
    from trafficvision.ui.app import AppServices


def render_history_page(services: AppServices) -> None:
    """Render analysis history page with mockup design consistency."""
    records = services.repository.list_recent(limit=100)

    st.markdown(
        clean_html(f"""
        <div class="tv-top">
            <div>
                <div class="tv-eyebrow">Local Storage</div>
                <h1 class="tv-title">Lịch sử phân tích</h1>
                <p class="tv-desc">Xem lại các phiên nhận dạng ảnh và video gần đây được lưu trữ cục bộ.</p>
            </div>
            <div class="tv-top-actions">
                <span class="tv-pill">● SQLite · {len(records)} phiên</span>
                <span class="tv-avatar">PVN</span>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    if not records:
        st.info("ℹ️ Chưa có phiên phân tích nào được lưu trong lịch sử.")
        return

    rows = []
    for r in records:
        rows.append(
            {
                "Thời gian": r.created_at[:19].replace("T", " "),
                "Tệp": r.original_filename,
                "Loại": r.media_type.upper(),
                "Mô hình": r.model_id,
                "Số đối tượng": r.total_detections,
                "Thời gian xử lý (ms)": f"{r.inference_ms:.1f}",
                "Ngưỡng Conf": f"{r.confidence_threshold:.2f}",
                "Ngưỡng IoU": f"{r.iou_threshold:.2f}",
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
