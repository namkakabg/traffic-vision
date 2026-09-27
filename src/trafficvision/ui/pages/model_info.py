from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

if TYPE_CHECKING:
    from trafficvision.ui.app import AppServices


def render_model_info_page(services: AppServices) -> None:
    st.title("ℹ️ Thông tin mô hình AI")
    st.caption("Chi tiết metadata và thông số mô hình đang phục vụ suy luận.")

    prod_model = services.get_production_safe()
    if prod_model is None:
        st.warning("⚠️ Chưa có mô hình production nào được cài đặt. Vui lòng chạy bootstrap trước.")
        return

    m = prod_model.manifest

    # Baseline warning if applicable
    is_baseline = (
        m.stage == "baseline"
        or (m.source_model_id and "baseline" in m.source_model_id)
        or ("yolo11n" in m.source.lower() and len(m.class_names) != 82)
    )
    if is_baseline:
        st.warning(
            "⚠️ Baseline — chưa fine-tune biển báo Việt Nam. "
            "Mô hình đang dùng là YOLO11n pretrained nguyên bản phục vụ kiểm thử pipeline."
        )

    st.markdown(
        f"""
        <div class="tv-card">
            <h3>{m.model_id}</h3>
            <p>
                <strong>Trạng thái:</strong> {m.stage.upper()}<br/>
                <strong>Backend suy luận:</strong> {m.backend.upper()}<br/>
                <strong>Nguồn:</strong> {m.source}<br/>
                <strong>Kích thước ảnh đầu vào:</strong> {m.imgsz}x{m.imgsz}<br/>
                <strong>Số lượng lớp:</strong> {len(m.class_names)} lớp<br/>
                <strong>Mã băm SHA-256:</strong> <code>{m.sha256}</code> (prefix: <code>{m.sha256[:8]}</code>)<br/>
                <strong>Thời điểm tạo:</strong> {m.created_at}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"📋 Danh mục {len(m.class_names)} lớp đối tượng"):
        classes_data = [{"Class ID": k, "Tên lớp": v} for k, v in sorted(m.class_names.items())]
        st.dataframe(pd.DataFrame(classes_data), use_container_width=True, hide_index=True)
