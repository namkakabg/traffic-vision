from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from trafficvision.settings import RuntimeSettings
from trafficvision.ui.theme import clean_html

if TYPE_CHECKING:
    from trafficvision.ui.app import AppServices


def render_settings_page(services: AppServices) -> None:
    """Render runtime settings form with mockup design consistency."""
    current = services.settings_store.load()

    st.markdown(
        clean_html("""
        <div class="tv-top">
            <div>
                <div class="tv-eyebrow">Preferences & Thresholds</div>
                <h1 class="tv-title">Thiết lập hệ thống</h1>
                <p class="tv-desc">Tùy chỉnh ngưỡng suy luận AI và giới hạn kích thước tệp tải lên.</p>
            </div>
            <div class="tv-top-actions">
                <span class="tv-pill">● Cấu hình cục bộ</span>
                <span class="tv-avatar">PVN</span>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    with st.form("settings_form"):
        st.markdown(
            clean_html("""
            <div style="font-size:13px; font-weight:800; color:#132238; margin-bottom: 8px;">
                1. Ngưỡng suy luận mô hình
            </div>
            """),
            unsafe_allow_html=True,
        )
        col_c, col_i, col_sz = st.columns(3)
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
        with col_sz:
            imgsz_options = [640, 800, 960, 1024, 1280, 1600]
            curr_imgsz = getattr(current, "imgsz", 1280)
            def_idx = imgsz_options.index(curr_imgsz) if curr_imgsz in imgsz_options else 4
            new_imgsz = st.selectbox(
                "Kích thước ảnh suy luận (imgsz)",
                options=imgsz_options,
                index=def_idx,
                help="Độ phân giải ảnh đưa vào model suy luận (mặc định: 1280). Giá trị cao hơn giúp nhận diện tốt biển báo nhỏ và ở xa.",
            )

        st.markdown(
            clean_html("""
            <div style="font-size:13px; font-weight:800; color:#132238; margin: 16px 0 8px 0;">
                2. Giới hạn dung lượng tải lên
            </div>
            """),
            unsafe_allow_html=True,
        )
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

        st.write("")
        btn_save = st.form_submit_button("💾 Lưu thiết lập", type="primary")

    if btn_save:
        updated = RuntimeSettings(
            confidence=new_conf,
            iou=new_iou,
            imgsz=int(new_imgsz),
            max_image_bytes=int(new_img_mb * 1024 * 1024),
            max_video_bytes=int(new_vid_mb * 1024 * 1024),
        )
        services.settings_store.save(updated)
        st.success(
            "✅ Đã cập nhật và lưu thiết lập thành công! Các giá trị mới sẽ áp dụng cho các phiên tiếp theo."
        )
