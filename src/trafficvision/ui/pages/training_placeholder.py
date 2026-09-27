from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from trafficvision.ui.app import AppServices


def render_training_placeholder_page(services: AppServices) -> None:
    st.title("🧠 Huấn luyện mô hình AI")
    st.caption("Quy trình fine-tuning mô hình nhận diện 82 lớp biển báo giao thông Việt Nam.")

    st.info(
        "ℹ️ **Giai đoạn 2 — chưa kích hoạt.** Phần quản lý dữ liệu và huấn luyện sẽ được mở trong kế hoạch tiếp theo."
    )

    st.markdown(
        """
        ### Lộ trình 4 bước chuẩn bị:

        1. **Dữ liệu:** Tải và quản lý bộ dữ liệu 82 lớp biển báo giao thông Việt Nam (10.157 ảnh).
        2. **Kiểm định:** Chạy bộ lọc Quality Gate (ảnh hỏng, thiếu nhãn, sai class ID, rò rỉ bản sao) và báo cáo EDA.
        3. **Huấn luyện:** Khởi chạy tiến trình huấn luyện YOLO11n trên background job có checkpoint định kỳ và chống tràn VRAM.
        4. **Đánh giá & xuất:** Kiểm thử trên tập test độc lập, xuất định dạng ONNX tối ưu CPU và sao lưu/thay thế production an toàn.

        *Lưu ý: Không có nút bắt đầu huấn luyện trong giai đoạn baseline này.*
        """
    )
