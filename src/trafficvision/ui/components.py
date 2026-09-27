from __future__ import annotations

import pandas as pd
import streamlit as st

from trafficvision.domain import RegisteredModel


def render_baseline_warning(model: RegisteredModel | None) -> None:
    """Render baseline warning banner if model is baseline or missing."""
    if model is None:
        st.warning(
            "⚠️ Hệ thống chưa được cài đặt mô hình production. "
            "Vui lòng chạy lệnh bootstrap trong terminal: `python scripts/bootstrap_baseline.py`"
        )
    elif model.manifest.stage == "baseline":
        st.warning(
            "⚠️ Baseline — chưa fine-tune biển báo Việt Nam. "
            "Hệ thống đang chạy mô hình gốc YOLO11n ONNX để kiểm chứng ứng dụng."
        )


def render_detection_summary(
    class_counts: dict[str, int],
    total_detections: int,
    elapsed_ms: float,
) -> None:
    """Render metrics and detection counts breakdown table."""
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Tổng số đối tượng", value=total_detections)
    with col2:
        st.metric(label="Thời gian xử lý", value=f"{elapsed_ms:.1f} ms")

    if class_counts:
        st.subheader("Chi tiết theo lớp")
        df = pd.DataFrame([{"Lớp nhận diện": k, "Số lượng": v} for k, v in class_counts.items()])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Không phát hiện đối tượng nào trong tệp tải lên.")


def render_download_buttons(
    annotated_bytes: bytes,
    media_filename: str,
    csv_bytes: bytes,
    csv_filename: str,
    media_mime: str = "image/jpeg",
) -> None:
    """Render download buttons for annotated output media and CSV."""
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            label="📥 Tải tệp kết quả",
            data=annotated_bytes,
            file_name=media_filename,
            mime=media_mime,
            use_container_width=True,
        )
    with c2:
        st.download_button(
            label="📊 Tải bảng CSV",
            data=csv_bytes,
            file_name=csv_filename,
            mime="text/csv",
            use_container_width=True,
        )
