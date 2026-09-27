from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from trafficvision.settings import RuntimeSettings

if TYPE_CHECKING:
    from trafficvision.ui.app import AppServices


def render_settings_page(services: AppServices) -> None:
    st.title("⚙️ Thiết lập hệ thống")
    st.caption("Tùy chỉnh ngưỡng suy luận AI và giới hạn kích thước tệp tải lên.")

    current = services.settings_store.load()

    with st.form("settings_form"):
        st.subheader("1. Ngưỡng suy luận mô hình")
        col_c, col_i = st.columns(2)
        with col_c:
            new_conf = st.slider(
                "Ngưỡng tin cậy (Confidence)",
                min_value=0.05,
                max_value=0.95,
                value=float(current.confidence),
                step=0.05,
                help="Chỉ giữ lại các dự đoán có độ tin cậy lớn hơn hoặc bằng ngưỡng này.",
            )
        with col_i:
            new_iou = st.slider(
                "Ngưỡng lọc trùng (IoU / NMS)",
                min_value=0.10,
                max_value=0.95,
                value=float(current.iou),
                step=0.05,
                help="Ngưỡng loại bỏ các hộp bao trùng lặp (Non-Maximum Suppression).",
            )

        st.subheader("2. Giới hạn dung lượng tải lên")
        col_img, col_vid = st.columns(2)
        with col_img:
            img_mb = int(current.max_image_bytes / (1024 * 1024))
            new_img_mb = st.number_input(
                "Kích thước ảnh tối đa (MB)",
                min_value=1,
                max_value=100,
                value=img_mb,
                step=1,
            )
        with col_vid:
            vid_mb = int(current.max_video_bytes / (1024 * 1024))
            new_vid_mb = st.number_input(
                "Kích thước video tối đa (MB)",
                min_value=10,
                max_value=2000,
                value=vid_mb,
                step=50,
            )

        btn_save = st.form_submit_button("💾 Lưu thiết lập", type="primary")

    if btn_save:
        updated = RuntimeSettings(
            confidence=new_conf,
            iou=new_iou,
            max_image_bytes=int(new_img_mb * 1024 * 1024),
            max_video_bytes=int(new_vid_mb * 1024 * 1024),
        )
        services.settings_store.save(updated)
        st.success(
            "✅ Đã cập nhật và lưu thiết lập thành công! Các giá trị mới sẽ áp dụng cho các phiên tiếp theo."
        )
