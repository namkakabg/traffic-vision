from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from trafficvision.domain import AnalysisArtifacts, VideoProgress
from trafficvision.ui.components import (
    render_detection_summary,
    render_download_buttons,
)

if TYPE_CHECKING:
    from trafficvision.ui.app import AppServices


def render_analysis_page(services: AppServices) -> None:
    """Render the main image/video upload and detection analysis dashboard."""
    st.title("🚦 Phân tích biển báo giao thông")

    model = services.get_production_safe()
    if model is None:
        st.warning(
            "⚠️ Hệ thống chưa được cài đặt mô hình production. "
            "Vui lòng chạy lệnh bootstrap trong terminal: `python scripts/bootstrap_baseline.py`"
        )
        return

    # Check if baseline
    is_baseline = (
        model.manifest.stage == "baseline"
        or (model.manifest.source_model_id and "baseline" in model.manifest.source_model_id)
        or ("yolo11n" in model.manifest.source.lower() and len(model.manifest.class_names) != 82)
    )
    if is_baseline:
        st.warning(
            "⚠️ Baseline — chưa fine-tune biển báo Việt Nam. "
            "Hệ thống đang chạy mô hình gốc YOLO11n ONNX để kiểm chứng ứng dụng."
        )

    tab_image, tab_video = st.tabs(["📷 Phân tích ảnh", "🎥 Phân tích video"])

    img_exts = [e.lstrip(".").lower() for e in services.config.media.allowed_image_extensions]
    vid_exts = [e.lstrip(".").lower() for e in services.config.media.allowed_video_extensions]

    # --- TAB ẢNH ---
    with tab_image:
        st.write("Tải lên hình ảnh chụp biển báo giao thông để nhận diện và định vị.")
        uploaded_image = st.file_uploader(
            "Chọn tệp ảnh",
            type=img_exts,
            key="analysis_image_uploader",
        )

        if uploaded_image is not None:
            col_preview, col_action = st.columns([1, 1])
            with col_preview:
                st.image(uploaded_image, caption="Ảnh gốc tải lên", use_container_width=True)

            with col_action:
                st.info(
                    f"Tệp: `{uploaded_image.name}` ({len(uploaded_image.getvalue()) / 1024:.1f} KB)"
                )
                btn_analyze_image = st.button(
                    "🚀 Phân tích ảnh", type="primary", key="btn_analyze_img"
                )

            if btn_analyze_image:
                try:
                    with st.spinner("Đang chạy mô hình AI nhận dạng..."):
                        artifacts: AnalysisArtifacts = (
                            services.analysis_service.analyze_image_upload(
                                filename=uploaded_image.name,
                                data=uploaded_image.getvalue(),
                            )
                        )
                        st.session_state["image_result"] = artifacts
                    st.success("Nhận dạng ảnh thành công!")
                except Exception as exc:
                    st.error(f"Lỗi khi xử lý ảnh: {exc}")

        if "image_result" in st.session_state:
            result: AnalysisArtifacts = st.session_state["image_result"]
            st.divider()
            st.subheader("🖼️ Kết quả nhận dạng")

            annotated_data = result.annotated_media_path.read_bytes()
            csv_data = result.csv_path.read_bytes()

            c_img1, c_img2 = st.columns(2)
            with c_img1:
                st.image(
                    annotated_data,
                    caption="Ảnh đã khoanh vùng và gắn nhãn",
                    use_container_width=True,
                )
            with c_img2:
                render_detection_summary(
                    class_counts=result.record.class_counts,
                    total_detections=result.record.total_detections,
                    elapsed_ms=result.record.inference_ms,
                )

            st.write("---")
            render_download_buttons(
                annotated_bytes=annotated_data,
                media_filename=f"annotated_{result.record.original_filename}",
                csv_bytes=csv_data,
                csv_filename=f"detections_{result.record.record_id[:8]}.csv",
                media_mime="image/jpeg",
            )

    # --- TAB VIDEO ---
    with tab_video:
        st.write("Tải lên video giao thông để xử lý và khoanh vùng biển báo theo từng khung hình.")
        uploaded_video = st.file_uploader(
            "Chọn tệp video",
            type=vid_exts,
            key="analysis_video_uploader",
        )

        if uploaded_video is not None:
            st.info(
                f"Tệp: `{uploaded_video.name}` ({len(uploaded_video.getvalue()) / (1024 * 1024):.2f} MB)"
            )
            btn_analyze_video = st.button(
                "🚀 Phân tích video", type="primary", key="btn_analyze_vid"
            )

            if btn_analyze_video:
                progress_bar = st.progress(0.0, text="Đang bắt đầu xử lý video...")

                def update_progress(prog: VideoProgress):
                    percent = int(prog.fraction * 100)
                    progress_bar.progress(
                        prog.fraction,
                        text=f"Đang xử lý khung hình {prog.current_frame}/{prog.total_frames} ({percent}%)",
                    )

                try:
                    with st.spinner("Đang xử lý tuần tự từng khung hình video..."):
                        vid_artifacts: AnalysisArtifacts = (
                            services.analysis_service.analyze_video_upload(
                                filename=uploaded_video.name,
                                data=uploaded_video.getvalue(),
                                on_progress=update_progress,
                            )
                        )
                        st.session_state["video_result"] = vid_artifacts
                    st.success("Xử lý video hoàn tất!")
                except Exception as exc:
                    st.error(f"Lỗi khi xử lý video: {exc}")

        if "video_result" in st.session_state:
            vid_res: AnalysisArtifacts = st.session_state["video_result"]
            st.divider()
            st.subheader("🎬 Kết quả xử lý video")

            render_detection_summary(
                class_counts=vid_res.record.class_counts,
                total_detections=vid_res.record.total_detections,
                elapsed_ms=vid_res.record.inference_ms,
            )

            vid_bytes = vid_res.annotated_media_path.read_bytes()
            vid_csv = vid_res.csv_path.read_bytes()

            st.write("---")
            render_download_buttons(
                annotated_bytes=vid_bytes,
                media_filename=f"annotated_{vid_res.record.original_filename}",
                csv_bytes=vid_csv,
                csv_filename=f"video_detections_{vid_res.record.record_id[:8]}.csv",
                media_mime="video/mp4",
            )
