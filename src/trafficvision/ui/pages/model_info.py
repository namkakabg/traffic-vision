from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

from trafficvision.ui.components import render_baseline_warning
from trafficvision.ui.theme import clean_html

if TYPE_CHECKING:
    from trafficvision.ui.app import AppServices


def render_model_info_page(services: AppServices) -> None:
    """Render model metadata and manifest details with mockup design consistency."""
    prod_model = services.get_production_safe()

    st.markdown(
        clean_html("""
        <div class="tv-top">
            <div>
                <div class="tv-eyebrow">Registry & Runtime</div>
                <h1 class="tv-title">Thông tin mô hình AI</h1>
                <p class="tv-desc">Chi tiết metadata, kiến trúc và thông số mô hình đang phục vụ suy luận.</p>
            </div>
            <div class="tv-top-actions">
                <span class="tv-pill">● Model Manifest</span>
                <span class="tv-avatar">PVN</span>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    if prod_model is None:
        st.warning("⚠️ Chưa có mô hình production nào được cài đặt. Vui lòng chạy bootstrap trước.")
        return

    m = prod_model.manifest
    num_classes = len(m.class_names)
    is_baseline = (
        m.stage == "baseline"
        or (m.source_model_id and "baseline" in m.source_model_id)
        or ("yolo11n" in m.source.lower() and num_classes != 82)
    )

    if is_baseline:
        render_baseline_warning(prod_model)
        stage_badge = '<span class="tv-badge tv-badge-baseline">BASELINE</span>'
        class_desc = f"{num_classes} lớp đối tượng (Mô hình nền cơ bản)"
    else:
        stage_badge = '<span class="tv-badge tv-badge-production">PRODUCTION</span>'
        class_desc = f"{num_classes} lớp biển báo giao thông Việt Nam (Đã huấn luyện)"

    st.markdown(
        clean_html(f"""
        <div class="tv-card">
            <h3 style="margin-top:0; color:#132238; font-size:16px;">{m.model_id}</h3>
            <p style="font-size:12px; line-height:1.6; color:#475569;">
                <strong>Trạng thái:</strong> {stage_badge}<br/>
                <strong>Backend suy luận:</strong> <code>{m.backend.upper()}</code><br/>
                <strong>Nguồn mô hình:</strong> {m.source}<br/>
                <strong>Kích thước ảnh đầu vào:</strong> {m.imgsz}x{m.imgsz} px<br/>
                <strong>Số lượng lớp:</strong> {class_desc}<br/>
                <strong>Mã băm SHA-256:</strong> <code>{m.sha256}</code> (prefix: <code>{m.sha256[:8]}</code>)<br/>
                <strong>Thời điểm tạo:</strong> {m.created_at}
            </p>
        </div>
        """),
        unsafe_allow_html=True,
    )

    with st.expander(f"📋 Danh mục {len(m.class_names)} lớp đối tượng"):
        classes_data = [{"Class ID": k, "Tên lớp": v} for k, v in sorted(m.class_names.items())]
        st.dataframe(pd.DataFrame(classes_data), use_container_width=True, hide_index=True)

    # Backups history and Rollback
    st.markdown("---")
    st.markdown("### 🗄️ Lịch sử sao lưu & Khôi phục mô hình (Rollback)")
    backups = services.registry.list_backups()
    if not backups:
        st.info("Chưa có bản sao lưu nào trong hệ thống.")
    else:
        backup_rows = [
            {
                "Mã sao lưu (Backup ID)": b.backup_id,
                "Model ID": b.model_id,
                "Thời gian": b.timestamp,
            }
            for b in backups
        ]
        st.dataframe(pd.DataFrame(backup_rows), use_container_width=True, hide_index=True)

        col_rb1, col_rb2 = st.columns([2, 1], gap="medium")
        with col_rb1:
            selected_backup_id = st.selectbox(
                "Chọn bản sao lưu để khôi phục:",
                options=[b.backup_id for b in backups],
                key="select_rollback_backup",
            )
        with col_rb2:
            st.write("")
            st.write("")
            btn_rollback = st.button(
                "⏪ Phục hồi mô hình (Rollback)",
                key="btn_rollback_model",
                type="primary",
            )

        if btn_rollback:
            try:
                restored = services.registry.rollback_to_backup(selected_backup_id)
                st.success(
                    f"Đã phục hồi thành công mô hình `{restored.manifest.model_id}` "
                    f"từ bản sao lưu `{selected_backup_id}`!"
                )
                st.rerun()
            except Exception as exc:
                st.error(f"Lỗi khi phục hồi mô hình: {exc}")
