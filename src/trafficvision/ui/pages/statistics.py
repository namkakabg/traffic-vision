from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

from trafficvision.ui.theme import clean_html

if TYPE_CHECKING:
    from trafficvision.ui.app import AppServices


def render_statistics_page(services: AppServices) -> None:
    """Render aggregate detection statistics with mockup design consistency."""
    records = services.repository.list_recent(limit=1000)
    class_totals = services.repository.class_totals()

    st.markdown(
        clean_html("""
        <div class="tv-top">
            <div>
                <div class="tv-eyebrow">Analytics & Performance</div>
                <h1 class="tv-title">Thống kê nhận dạng</h1>
                <p class="tv-desc">Tổng hợp hiệu năng suy luận và tần suất phát hiện các loại biển báo giao thông.</p>
            </div>
            <div class="tv-top-actions">
                <span class="tv-pill">● Tổng hợp tự động</span>
                <span class="tv-avatar">PVN</span>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    if not records or not class_totals:
        st.info("ℹ️ Chưa có dữ liệu thống kê. Hãy thực hiện phân tích ảnh hoặc video trước.")
        return

    total_analyses = len(records)
    total_detections = sum(class_totals.values())
    avg_inference_ms = sum(r.inference_ms for r in records) / total_analyses

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Tổng số phiên", value=total_analyses)
    with col2:
        st.metric(label="Tổng biển báo phát hiện", value=total_detections)
    with col3:
        st.metric(label="Thời gian TB (ms)", value=f"{avg_inference_ms:.1f}")

    st.markdown(
        clean_html("""
        <div style="font-size:13px; font-weight:800; color:#132238; margin: 16px 0 8px 0;">
            Phân bố số lượng theo loại biển báo
        </div>
        """),
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(
        [{"Lớp biển báo": k, "Số lượng": v} for k, v in class_totals.items()]
    ).sort_values(by="Số lượng", ascending=False)

    st.bar_chart(df.set_index("Lớp biển báo"), use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
