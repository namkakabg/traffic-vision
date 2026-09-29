from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from trafficvision.domain import AnalysisArtifacts, VideoProgress
from trafficvision.ui.components import (
    render_baseline_warning,
    render_detection_summary,
    render_download_buttons,
)
from trafficvision.ui.theme import clean_html

if TYPE_CHECKING:
    from trafficvision.ui.app import AppServices


def render_analysis_page(services: AppServices) -> None:
    """Render the main image/video upload and detection analysis dashboard matching mockup."""
    model = services.get_production_safe()
    if model is None:
        render_baseline_warning(None)
        return

    # Check baseline status and display warning
    render_baseline_warning(model)

    num_classes = len(model.manifest.class_names)
    backend_label = model.manifest.backend.upper()
    stage_label = model.manifest.stage.upper()

    # Top Header matching mockup
    st.markdown(
        clean_html(f"""
        <div class="tv-top">
            <div>
                <div class="tv-eyebrow">AI Traffic Intelligence</div>
                <h1 class="tv-title">Phân tích biển báo</h1>
                <p class="tv-desc">Tải ảnh hoặc video giao thông để phát hiện và nhận dạng tự động.</p>
            </div>
            <div class="tv-top-actions">
                <span class="tv-pill">● {backend_label} · {stage_label}</span>
                <span class="tv-avatar">PVN</span>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    img_exts = [e.lstrip(".").lower() for e in services.config.media.allowed_image_extensions]
    vid_exts = [e.lstrip(".").lower() for e in services.config.media.allowed_video_extensions]

    # Two column layout: Visual panel (Left) and Summary panel (Right)
    col_visual, col_summary = st.columns([1.6, 1.0], gap="medium")

    with col_visual:
        st.markdown(
            clean_html("""
            <div style="font-size:13px; font-weight:800; color:#132238; margin-bottom: 8px;">
                Kết quả trực quan
            </div>
            """),
            unsafe_allow_html=True,
        )
        tab_image, tab_video = st.tabs(["📷 Hình ảnh", "🎥 Video"])

        # --- TAB ẢNH ---
        with tab_image:
            uploaded_image = st.file_uploader(
                "Chọn tệp ảnh giao thông",
                type=img_exts,
                key="analysis_image_uploader",
                help="Hỗ trợ các định dạng JPG, PNG, WEBP",
            )

            if uploaded_image is not None:
                file_size_kb = len(uploaded_image.getvalue()) / 1024.0

                if "image_result" not in st.session_state:
                    st.image(
                        uploaded_image,
                        caption=f"Ảnh gốc: {uploaded_image.name}",
                        use_container_width=True,
                    )
                    btn_analyze = st.button(
                        "🚀 Bắt đầu phân tích ảnh", type="primary", key="btn_run_img"
                    )
                    if btn_analyze:
                        try:
                            with st.spinner("Đang chạy mô hình AI nhận dạng..."):
                                artifacts: AnalysisArtifacts = (
                                    services.analysis_service.analyze_image_upload(
                                        filename=uploaded_image.name,
                                        data=uploaded_image.getvalue(),
                                    )
                                )
                                st.session_state["image_result"] = artifacts
                                st.session_state["active_result_type"] = "image"
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Lỗi khi xử lý ảnh: {exc}")
                else:
                    result: AnalysisArtifacts = st.session_state["image_result"]
                    annotated_data = result.annotated_media_path.read_bytes()
                    st.image(
                        annotated_data,
                        caption=f"Đã phát hiện {result.record.total_detections} biển báo ({result.record.inference_ms:.1f} ms)",
                        use_container_width=True,
                    )

                    # Info bar matching mockup uploadbar
                    st.markdown(
                        clean_html(f"""
                        <div class="tv-uploadbar">
                            <div class="tv-file">
                                <span>📄 <strong>{uploaded_image.name}</strong> · {file_size_kb:.1f} KB</span>
                            </div>
                        </div>
                        """),
                        unsafe_allow_html=True,
                    )

                    if st.button("＋ Phân tích ảnh khác", key="btn_clear_img"):
                        del st.session_state["image_result"]
                        st.rerun()

        # --- TAB VIDEO ---
        with tab_video:
            uploaded_video = st.file_uploader(
                "Chọn tệp video giao thông",
                type=vid_exts,
                key="analysis_video_uploader",
                help="Hỗ trợ MP4, AVI, MOV",
            )

            if uploaded_video is not None:
                vid_size_mb = len(uploaded_video.getvalue()) / (1024 * 1024)

                if "video_result" not in st.session_state:
                    st.info(f"Tệp video: `{uploaded_video.name}` ({vid_size_mb:.2f} MB)")
                    btn_analyze_video = st.button(
                        "🚀 Bắt đầu phân tích video", type="primary", key="btn_run_vid"
                    )

                    if btn_analyze_video:
                        progress_bar = st.progress(0.0, text="Đang chuẩn bị xử lý video...")

                        def update_progress(prog: VideoProgress) -> None:
                            percent = int(prog.fraction * 100)
                            progress_bar.progress(
                                prog.fraction,
                                text=f"Đang xử lý khung hình {prog.current_frame}/{prog.total_frames} ({percent}%)",
                            )

                        try:
                            with st.spinner("Đang nhận diện theo từng khung hình video..."):
                                vid_artifacts: AnalysisArtifacts = (
                                    services.analysis_service.analyze_video_upload(
                                        filename=uploaded_video.name,
                                        data=uploaded_video.getvalue(),
                                        on_progress=update_progress,
                                    )
                                )
                                st.session_state["video_result"] = vid_artifacts
                                st.session_state["active_result_type"] = "video"
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Lỗi khi xử lý video: {exc}")
                else:
                    vid_res: AnalysisArtifacts = st.session_state["video_result"]
                    vid_bytes = vid_res.annotated_media_path.read_bytes()
                    st.video(vid_bytes)

                    st.markdown(
                        clean_html(f"""
                        <div class="tv-uploadbar">
                            <div class="tv-file">
                                <span>🎥 <strong>{uploaded_video.name}</strong> · {vid_size_mb:.2f} MB</span>
                            </div>
                        </div>
                        """),
                        unsafe_allow_html=True,
                    )

                    if st.button("＋ Phân tích video khác", key="btn_clear_vid"):
                        del st.session_state["video_result"]
                        st.rerun()

    # --- SUMMARY PANEL (Right Column) ---
    with col_summary:
        active_type = st.session_state.get("active_result_type")
        current_result: AnalysisArtifacts | None = None

        if active_type == "video" and "video_result" in st.session_state:
            current_result = st.session_state["video_result"]
        elif "image_result" in st.session_state:
            current_result = st.session_state["image_result"]
        elif "video_result" in st.session_state:
            current_result = st.session_state["video_result"]

        if current_result is not None:
            csv_bytes = current_result.csv_path.read_bytes()
            annotated_bytes = current_result.annotated_media_path.read_bytes()
            mime_type = "video/mp4" if current_result.record.media_type == "video" else "image/jpeg"

            render_detection_summary(
                class_counts=current_result.record.class_counts,
                total_detections=current_result.record.total_detections,
                elapsed_ms=current_result.record.inference_ms,
                num_classes=num_classes,
                csv_bytes=csv_bytes,
            )

            render_download_buttons(
                annotated_bytes=annotated_bytes,
                media_filename=f"annotated_{current_result.record.original_filename}",
                csv_bytes=csv_bytes,
                csv_filename=f"detections_{current_result.record.record_id[:8]}.csv",
                media_mime=mime_type,
            )
        else:
            # Placeholder summary card waiting for user action
            st.markdown(
                clean_html(f"""
                <div class="tv-panel">
                    <div class="tv-panelhead">
                        <span class="tv-paneltitle">Tóm tắt phân tích</span>
                        <span style="color:#7a8798; font-size:10px; font-weight:800; letter-spacing:0.06em;">CHỜ DỮ LIỆU</span>
                    </div>
                    <div class="tv-panelcontent">
                        <div class="tv-stats">
                            <div class="tv-stat">
                                <div class="tv-statnum">--</div>
                                <div class="tv-statlabel">Biển báo phát hiện</div>
                            </div>
                            <div class="tv-stat">
                                <div class="tv-statnum">--</div>
                                <div class="tv-statlabel">Độ tin cậy cao nhất</div>
                            </div>
                            <div class="tv-stat">
                                <div class="tv-statnum">--<span style="font-size:11px; font-weight:600; color:#7a8798;"> ms</span></div>
                                <div class="tv-statlabel">Thời gian suy luận</div>
                            </div>
                            <div class="tv-stat">
                                <div class="tv-statnum">{num_classes}</div>
                                <div class="tv-statlabel">Lớp được hỗ trợ</div>
                            </div>
                        </div>
                        <div class="tv-notice" style="background:#f4f6fa; border-color:#e0e7ef; color:#5c6c80;">
                            <span>ⓘ</span>
                            <span>Tải ảnh hoặc video và bấm nút phân tích để xem khung bao, độ tin cậy và tóm tắt thống kê.</span>
                        </div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )
