from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
import streamlit as st

from trafficvision.data.catalog import VIETNAM_TRAFFIC_SIGN_CATALOG
from trafficvision.data.dataset import DatasetItem, scan_yolo_dataset, summarize_dataset
from trafficvision.data.eda import generate_eda_report
from trafficvision.data.snapshot import DatasetSnapshot, create_dataset_snapshot
from trafficvision.data.synthetic import create_synthetic_dataset
from trafficvision.data.validator import ValidationReport, validate_dataset
from trafficvision.training.config import TrainingConfig
from trafficvision.training.state import TrainingState
from trafficvision.ui.theme import clean_html

if TYPE_CHECKING:
    from trafficvision.ui.app import AppServices


def _get_hardware_status() -> tuple[bool, str]:
    """Detect available accelerator hardware (CUDA GPU or CPU fallback)."""
    try:
        import torch

        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            return True, f"● CUDA khả dụng · {name}"
    except Exception:
        pass
    return False, "● Chế độ CPU · Huấn luyện nền độc lập"


def _format_seconds(seconds: float) -> str:
    """Format duration in seconds into human-readable string."""
    s = int(seconds)
    hours, remainder = divmod(s, 3600)
    minutes, sec = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {sec}s"
    return f"{sec}s"


def _find_candidates(runs_dir: Path) -> list[tuple[str, Path]]:
    """Scan runs directory for packaged candidate models."""
    candidates: list[tuple[str, Path]] = []
    if not runs_dir.is_dir():
        return candidates

    for run_dir in runs_dir.iterdir():
        if run_dir.is_dir():
            cand_dir = run_dir / "candidate"
            if cand_dir.is_dir() and (cand_dir / "manifest.json").is_file():
                candidates.append((run_dir.name, cand_dir))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates


def render_training_page(services: AppServices) -> None:
    """Render the active 4-step AI Experiment Lab interface matching training-interface.html."""
    has_cuda, gpu_badge = _get_hardware_status()
    paths = services.config.paths
    runs_dir = paths.runs
    training_mgr = services.training_manager

    # Top Header matching mockup
    st.markdown(
        clean_html(f"""
        <div class="tv-top">
            <div>
                <div class="tv-eyebrow">AI Experiment Lab</div>
                <h1 class="tv-title">Huấn luyện mô hình</h1>
                <p class="tv-desc">Cấu hình, theo dõi và quản lý toàn bộ thí nghiệm từ một nơi.</p>
            </div>
            <div>
                <span class="tv-gpu">{gpu_badge}</span>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # Resolve active step classes for visual stepper
    dataset_items: list[DatasetItem] | None = st.session_state.get("dataset_items")
    validation_report: ValidationReport | None = st.session_state.get("validation_report")
    dataset_snapshot: DatasetSnapshot | None = st.session_state.get("dataset_snapshot")
    current_run_id: str | None = st.session_state.get("current_run_id")

    # If current_run_id is not set, pick the latest run if available
    if current_run_id is None and training_mgr is not None:
        runs = training_mgr.list_runs()
        if runs:
            current_run_id = runs[-1].run_id
            st.session_state["current_run_id"] = current_run_id

    # Determine state of each step
    step1_done = dataset_items is not None and len(dataset_items) > 0
    step2_done = validation_report is not None and not validation_report.has_blocking
    step3_done = False
    step4_done = False

    prod_model = services.get_production_safe()
    if prod_model is not None and len(prod_model.manifest.class_names) == 82:
        step4_done = True

    current_state: TrainingState | None = None
    if training_mgr is not None and current_run_id:
        try:
            current_state = training_mgr.get_state(current_run_id)
            if current_state.status == "completed":
                step3_done = True
        except Exception:
            current_state = None

    candidates = _find_candidates(runs_dir)
    if candidates:
        step3_done = True

    def _step_cls(is_done: bool, is_active: bool, num: str) -> str:
        if is_done:
            return f'<div class="tv-step done"><b>✓</b>{num}</div>'
        if is_active:
            return f'<div class="tv-step active"><b>{num}</b>{num}</div>'
        return f'<div class="tv-step"><b>{num}</b>{num}</div>'

    # Render Visual Stepper matching mockup
    c1 = "done" if step1_done else "active"
    b1 = "✓" if step1_done else "1"
    c2 = "done" if step2_done else ("active" if step1_done else "")
    b2 = "✓" if step2_done else "2"
    c3 = "done" if step3_done else ("active" if step2_done else "")
    b3 = "✓" if step3_done else "3"
    c4 = "done" if step4_done else ("active" if step3_done else "")
    b4 = "✓" if step4_done else "4"

    st.markdown(
        clean_html(f"""
        <div class="tv-steps">
            <div class="tv-step {c1}"><b>{b1}</b> Dữ liệu</div>
            <div class="tv-step {c2}"><b>{b2}</b> Kiểm định</div>
            <div class="tv-step {c3}"><b>{b3}</b> Huấn luyện</div>
            <div class="tv-step {c4}"><b>{b4}</b> Đánh giá &amp; xuất</div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # 4 Interactive Step Tabs
    tab_data, tab_val, tab_train, tab_eval = st.tabs(
        ["1. Dữ liệu", "2. Kiểm định", "3. Huấn luyện", "4. Đánh giá & xuất"]
    )

    # =========================================================================
    # STEP 1: DỮ LIỆU
    # =========================================================================
    with tab_data:
        st.subheader("1. Nạp và kiểm tra cấu trúc dữ liệu")

        default_data_dir = st.session_state.get("training_data_dir", str(paths.staging.resolve()))
        data_dir_input = st.text_input(
            "Đường dẫn thư mục dữ liệu (YOLO dataset)",
            value=default_data_dir,
            key="input_training_data_dir",
            help="Thư mục chứa các tập train/val/test với cấu trúc images/ và labels/",
        )
        st.session_state["training_data_dir"] = data_dir_input
        target_path = Path(data_dir_input)

        col_d1, col_d2 = st.columns([1, 1], gap="small")
        with col_d1:
            btn_scan = st.button(
                "🔍 Quét dữ liệu", key="btn_scan_dataset", use_container_width=True
            )
        with col_d2:
            btn_gen_demo = st.button(
                "🎲 Tạo dữ liệu mẫu (Synthetic Demo Dataset)",
                key="btn_generate_synthetic_demo",
                use_container_width=True,
            )

        if btn_gen_demo:
            try:
                create_synthetic_dataset(target_path, num_samples=10)
                st.success(f"Đã tạo thành công bộ dữ liệu mẫu 82 lớp tại: `{target_path}`")
                scanned_items = scan_yolo_dataset(target_path)
                st.session_state["dataset_items"] = scanned_items
                dataset_items = scanned_items
                val_rep = validate_dataset(scanned_items, VIETNAM_TRAFFIC_SIGN_CATALOG)
                st.session_state["validation_report"] = val_rep
                validation_report = val_rep
            except Exception as exc:
                st.error(f"Lỗi khi tạo dữ liệu mẫu: {exc}")

        if btn_scan:
            if not target_path.exists():
                st.error(f"Thư mục không tồn tại: `{target_path}`")
            else:
                try:
                    scanned_items = scan_yolo_dataset(target_path)
                    st.session_state["dataset_items"] = scanned_items
                    dataset_items = scanned_items
                    val_rep = validate_dataset(scanned_items, VIETNAM_TRAFFIC_SIGN_CATALOG)
                    st.session_state["validation_report"] = val_rep
                    validation_report = val_rep
                    st.success(f"Đã quét thành công {len(scanned_items)} ảnh từ `{target_path}`.")
                except Exception as exc:
                    st.error(f"Lỗi quét dữ liệu: {exc}")

        # Display Dataset Summary if items are loaded
        if dataset_items is not None and len(dataset_items) > 0:
            summary = summarize_dataset(dataset_items)
            st.markdown(
                clean_html(f"""
                <div class="tv-stats" style="margin-top:14px;">
                    <div class="tv-stat">
                        <div class="tv-statnum">{summary.total_images}</div>
                        <div class="tv-statlabel">Tổng số ảnh (Samples)</div>
                    </div>
                    <div class="tv-stat">
                        <div class="tv-statnum">{len(summary.classes_present)}/82</div>
                        <div class="tv-statlabel">Số lớp đối tượng hiện diện</div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )

            splits_str = " · ".join(
                f"{k.upper()}: {v} ảnh" for k, v in sorted(summary.split_counts.items())
            )
            st.info(f"📊 **Phân bổ tập chia:** {splits_str}")
        elif target_path.exists() and not btn_scan and not btn_gen_demo:
            try:
                scanned_items = scan_yolo_dataset(target_path)
                if scanned_items:
                    st.session_state["dataset_items"] = scanned_items
                    dataset_items = scanned_items
                    summary = summarize_dataset(scanned_items)
                    st.info(
                        f"📁 Đã tự động phát hiện {summary.total_images} ảnh từ `{target_path}`."
                    )
            except Exception:
                pass

        # HuggingFace & Instructions Box
        with st.expander(
            "📥 Hướng dẫn tải toàn bộ dữ liệu chính thức (HuggingFace)", expanded=False
        ):
            st.markdown(
                """
                Để huấn luyện mô hình chuẩn 82 lớp biển báo Việt Nam với đầy đủ hơn 10.000 ảnh:

                ```bash
                # Tải trực tiếp qua huggingface-cli về thư mục staging
                huggingface-cli download TrafficVision/vietnam-traffic-signs --local-dir artifacts/staging
                ```
                Cấu trúc chuẩn yêu cầu:
                ```
                artifacts/staging/
                ├── train/
                │   ├── images/ (*.png, *.jpg)
                │   └── labels/ (*.txt định dạng YOLO)
                ├── val/
                │   ├── images/
                │   └── labels/
                └── test/
                    ├── images/
                    └── labels/
                ```
                """
            )

    # =========================================================================
    # STEP 2: KIỂM ĐỊNH (VALIDATION & EDA)
    # =========================================================================
    with tab_val:
        st.subheader("2. Kiểm định chất lượng (Quality Gate) & Phân tích EDA")

        col_v1, col_v2 = st.columns([1, 1], gap="small")
        with col_v1:
            btn_validate = st.button(
                "🛡️ Kiểm định dữ liệu", key="btn_run_validation", use_container_width=True
            )
        with col_v2:
            snapshot_disabled = (
                dataset_items is None
                or len(dataset_items) == 0
                or (validation_report is not None and validation_report.has_blocking)
            )
            btn_snapshot = st.button(
                "📦 Tạo snapshot bất biến (Immutable Snapshot)",
                key="btn_create_dataset_snapshot",
                disabled=snapshot_disabled,
                use_container_width=True,
            )

        if btn_validate:
            if not target_path.exists():
                st.error(f"Thư mục dữ liệu không tồn tại: `{target_path}`")
            else:
                try:
                    scanned_items = scan_yolo_dataset(target_path)
                    st.session_state["dataset_items"] = scanned_items
                    dataset_items = scanned_items
                    val_rep = validate_dataset(scanned_items, VIETNAM_TRAFFIC_SIGN_CATALOG)
                    st.session_state["validation_report"] = val_rep
                    validation_report = val_rep
                except Exception as exc:
                    st.error(f"Lỗi kiểm định: {exc}")

        # Handle Snapshot Creation
        if btn_snapshot:
            if dataset_items and validation_report and not validation_report.has_blocking:
                try:
                    snapshots_dir = paths.root / "artifacts" / "snapshots"
                    snapshot = create_dataset_snapshot(
                        items=dataset_items,
                        output_dir=snapshots_dir,
                        validation_report=validation_report,
                    )
                    st.session_state["dataset_snapshot"] = snapshot
                    dataset_snapshot = snapshot
                    st.success(
                        f"Đã tạo thành công Snapshot bất biến: `{snapshot.snapshot_id}` "
                        f"(data.yaml: `{snapshot.data_yaml_path.name}`)."
                    )
                except Exception as exc:
                    st.error(f"Lỗi tạo snapshot: {exc}")

        # Render Validation Report findings
        if validation_report is not None:
            if validation_report.has_blocking:
                st.error(
                    f"❌ **Phát hiện {len(validation_report.blocking_errors)} lỗi nghiêm trọng (Blocking errors)!** "
                    "Nút bắt đầu huấn luyện sẽ bị vô hiệu hóa cho đến khi các lỗi này được khắc phục."
                )
                for err in validation_report.blocking_errors:
                    st.markdown(
                        f"- <span style='color:#dc2626; font-weight:700;'>[{err.code}]</span> {err.message} "
                        f"(`{err.file_path.name if err.file_path else 'N/A'}`)",
                        unsafe_allow_html=True,
                    )
            else:
                st.success(
                    "✅ **Dữ liệu hợp lệ! Đạt tiêu chuẩn chất lượng (Quality Gate Passed).** "
                    "Không phát hiện lỗi blocking nào trong các file ảnh và nhãn."
                )

            if validation_report.warnings:
                st.warning(
                    f"⚠️ **Có {len(validation_report.warnings)} cảnh báo chất lượng dữ liệu (Non-blocking):**"
                )
                for w in validation_report.warnings:
                    st.markdown(f"- **`{w.code}`**: {w.message}")

            # EDA Summary
            if dataset_items and not validation_report.has_blocking:
                st.markdown("#### 📈 Phân tích Exploratory Data Analysis (EDA)")
                eda = generate_eda_report(dataset_items)

                c_eda1, c_eda2, c_eda3 = st.columns(3)
                with c_eda1:
                    st.metric("Tổng số nhãn (Bounding Boxes)", validation_report.total_labels)
                with c_eda2:
                    st.metric(
                        "Hộp kích thước nhỏ (COCO Small)", eda.size_distribution.get("small", 0)
                    )
                with c_eda3:
                    st.metric(
                        "Hộp kích thước vừa / lớn",
                        eda.size_distribution.get("medium", 0)
                        + eda.size_distribution.get("large", 0),
                    )

                if eda.class_counts:
                    df_classes = pd.DataFrame(
                        [
                            {
                                "Class ID": k,
                                "Tên lớp": VIETNAM_TRAFFIC_SIGN_CATALOG[k].name_vi
                                if k < len(VIETNAM_TRAFFIC_SIGN_CATALOG)
                                else f"Lớp {k}",
                                "Số lượng": v,
                            }
                            for k, v in eda.class_counts.items()
                        ]
                    )
                    st.dataframe(df_classes, use_container_width=True, hide_index=True)

        elif dataset_items is None:
            st.info("Vui lòng nạp hoặc quét dữ liệu ở Bước 1 trước khi tiến hành kiểm định.")

    # =========================================================================
    # STEP 3: HUẤN LUYỆN (TRAINING LAB)
    # =========================================================================
    with tab_train:
        col_cfg, col_prog = st.columns([1.1, 1.7], gap="medium")

        with col_cfg:
            st.markdown(
                clean_html("""
                <div class="tv-panel">
                    <div class="tv-panelhead">
                        <span class="tv-paneltitle">Cấu hình thí nghiệm</span>
                        <span style="color:#79879a; font-size:12px;">⚙</span>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )

            base_model = st.selectbox(
                "Mô hình nền (Pretrained)",
                ["yolo11n.pt", "yolo11s.pt", "yolo11m.pt"],
                index=0,
                key="train_base_model",
            )

            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                cfg_epochs = st.number_input(
                    "Epochs", min_value=1, max_value=500, value=50, key="cfg_epochs"
                )
                cfg_imgsz = st.selectbox(
                    "Kích thước ảnh", [640, 320, 1280], index=0, key="cfg_imgsz"
                )
            with col_sub2:
                cfg_batch = st.number_input(
                    "Batch size", min_value=1, max_value=128, value=4, key="cfg_batch"
                )
                cfg_patience = st.number_input(
                    "Patience", min_value=0, max_value=100, value=10, key="cfg_patience"
                )

            cfg_amp = st.checkbox("Mixed precision (AMP)", value=True, key="cfg_amp")
            st.checkbox("Lưu checkpoint mỗi epoch", value=True, key="cfg_save_ckpt")

            device_choice = "0" if has_cuda else "cpu"

            # Check if training can start
            is_running = current_state is not None and current_state.status == "running"
            has_blocking_err = validation_report is not None and validation_report.has_blocking

            # Resolve data.yaml path
            active_data_yaml: Path | None = None
            if dataset_snapshot is not None and dataset_snapshot.data_yaml_path.is_file():
                active_data_yaml = dataset_snapshot.data_yaml_path
            elif (target_path / "data.yaml").is_file():
                active_data_yaml = target_path / "data.yaml"

            # If no data.yaml yet but clean items exist, create snapshot automatically or warn
            can_start = (
                not is_running
                and not has_blocking_err
                and (
                    active_data_yaml is not None
                    or (
                        dataset_items is not None
                        and validation_report is not None
                        and not validation_report.has_blocking
                    )
                )
            )

            btn_start_disabled = not can_start

            btn_col1, btn_col2 = st.columns(2, gap="small")
            with btn_col1:
                btn_start = st.button(
                    "🚀 Bắt đầu huấn luyện",
                    key="btn_start_training",
                    disabled=btn_start_disabled,
                    type="primary",
                    use_container_width=True,
                )
            with btn_col2:
                btn_stop = st.button(
                    "⏹ Dừng huấn luyện",
                    key="btn_stop_training",
                    disabled=not is_running,
                    use_container_width=True,
                )

            if btn_start and training_mgr is not None:
                try:
                    # Auto-create snapshot if not explicitly done
                    if active_data_yaml is None:
                        snapshots_dir = paths.root / "artifacts" / "snapshots"
                        snap = create_dataset_snapshot(
                            items=dataset_items,
                            output_dir=snapshots_dir,
                            validation_report=validation_report,
                        )
                        st.session_state["dataset_snapshot"] = snap
                        active_data_yaml = snap.data_yaml_path

                    run_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    train_cfg = TrainingConfig(
                        run_id=run_id,
                        data_yaml=active_data_yaml,
                        base_model=base_model,
                        epochs=int(cfg_epochs),
                        batch=int(cfg_batch),
                        imgsz=int(cfg_imgsz),
                        patience=int(cfg_patience),
                        amp=cfg_amp,
                        device=device_choice,
                    )
                    init_state = training_mgr.start_training(train_cfg)
                    st.session_state["current_run_id"] = run_id
                    current_state = init_state
                    st.success(
                        f"Đã khởi động tiến trình huấn luyện nền: `{run_id}` (PID {init_state.pid})"
                    )
                except Exception as exc:
                    st.error(f"Lỗi khởi động huấn luyện: {exc}")

            if btn_stop and current_run_id and training_mgr is not None:
                try:
                    training_mgr.stop_training(current_run_id)
                    st.info(
                        "Đã gửi tín hiệu dừng (stop.signal). Tiến trình sẽ dừng lại sau epoch hiện tại."
                    )
                except Exception as exc:
                    st.error(f"Lỗi gửi tín hiệu dừng: {exc}")

            if has_blocking_err:
                st.caption("⚠️ Không thể bắt đầu: dữ liệu có lỗi blocking tại Bước 2.")

        # Right column: Live Progress & Polling
        with col_prog:
            # Determine display metrics
            if current_state is not None:
                disp_epoch = f"{current_state.current_epoch}/{current_state.total_epochs}"
                disp_map50 = f"{current_state.best_map50:.3f}"
                val_loss = current_state.metrics.get(
                    "val/loss", current_state.metrics.get("loss", 0.0)
                )
                disp_loss = (
                    f"{val_loss:.3f}" if isinstance(val_loss, (int, float)) else str(val_loss)
                )
                disp_time = _format_seconds(current_state.elapsed_s)
                status_label = current_state.status.upper()
                if current_state.status == "running":
                    status_badge = '<span style="color:#168561; font-weight:850; font-size:10px;">● ĐANG HUẤN LUYỆN</span>'
                elif current_state.status == "completed":
                    status_badge = '<span style="color:#2563eb; font-weight:850; font-size:10px;">● HOÀN THÀNH</span>'
                elif current_state.status in ("failed", "stopped"):
                    status_badge = f'<span style="color:#dc2626; font-weight:850; font-size:10px;">● {status_label}</span>'
                else:
                    status_badge = f'<span style="color:#718096; font-weight:850; font-size:10px;">● {status_label}</span>'
                progress_val = min(
                    1.0, current_state.current_epoch / max(1, current_state.total_epochs)
                )
            else:
                disp_epoch = "0/50"
                disp_map50 = "0.000"
                disp_loss = "0.000"
                disp_time = "0s"
                status_badge = '<span style="color:#718096; font-weight:850; font-size:10px;">● CHỜ KHỞI CHẠY</span>'
                progress_val = 0.0

            st.markdown(
                clean_html(f"""
                <div class="tv-panel">
                    <div class="tv-panelhead">
                        <span class="tv-paneltitle">Tiến trình trực tiếp</span>
                        {status_badge}
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )

            # Metric Cards Row matching mockup
            st.markdown(
                clean_html(f"""
                <div class="tv-metricrow">
                    <div class="tv-metric">
                        <div class="tv-num">{disp_epoch}</div>
                        <div class="tv-label">Epoch hiện tại</div>
                    </div>
                    <div class="tv-metric">
                        <div class="tv-num">{disp_map50}</div>
                        <div class="tv-label">Best mAP@50</div>
                    </div>
                    <div class="tv-metric">
                        <div class="tv-num">{disp_loss}</div>
                        <div class="tv-label">Validation loss</div>
                    </div>
                    <div class="tv-metric">
                        <div class="tv-num">{disp_time}</div>
                        <div class="tv-label">Thời gian chạy</div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )

            # Progress Bar
            pct = int(progress_val * 100)
            st.progress(progress_val)
            st.caption(
                f"Tiến độ hoàn thành: {pct}% · Thí nghiệm: `{current_run_id or 'Chưa khởi chạy'}`"
            )

            # Training Events Chart
            events = (
                training_mgr.get_events(current_run_id) if (training_mgr and current_run_id) else []
            )
            if events:
                chart_data = []
                for ev in events:
                    row = {"Epoch": ev.epoch}
                    if "metrics/mAP50(B)" in ev.metrics:
                        row["mAP@50"] = ev.metrics["metrics/mAP50(B)"]
                    elif "map50" in ev.metrics:
                        row["mAP@50"] = ev.metrics["map50"]
                    if "val/loss" in ev.metrics:
                        row["Val Loss"] = ev.metrics["val/loss"]
                    chart_data.append(row)
                if chart_data:
                    df_chart = pd.DataFrame(chart_data).set_index("Epoch")
                    st.line_chart(df_chart, height=180)

            # Terminal Log Console matching mockup
            log_lines: list[str] = []
            if current_run_id and (runs_dir / current_run_id / "train.log").is_file():
                try:
                    all_lines = (
                        (runs_dir / current_run_id / "train.log")
                        .read_text(encoding="utf-8")
                        .splitlines()
                    )
                    log_lines = all_lines[-6:]
                except Exception:
                    log_lines = []

            if not log_lines:
                log_content = "<strong>Trạng thái:</strong> Sẵn sàng. Nhấn 'Bắt đầu huấn luyện' để khởi tạo tiến trình nền."
            else:
                log_content = "<br/>".join(
                    line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    for line in log_lines
                )

            st.markdown(
                clean_html(f"""
                <div class="tv-log">
                    {log_content}
                </div>
                """),
                unsafe_allow_html=True,
            )

        # Footer Grid matching mockup
        st.markdown(
            clean_html("""
            <div class="tv-footergrid">
                <div class="tv-smallbox">
                    <div>
                        <div class="tv-smalltitle">Checkpoint tốt nhất</div>
                        <div class="tv-smalltext">best.pt · tự động lưu và kiểm định mô hình</div>
                    </div>
                    <span class="tv-tag">SẴN SÀNG</span>
                </div>
                <div class="tv-smallbox">
                    <div>
                        <div class="tv-smalltitle">Báo cáo thí nghiệm</div>
                        <div class="tv-smalltext">Biểu đồ hàm mất mát, confusion matrix và test metrics</div>
                    </div>
                    <span class="tv-tag">TỰ ĐỘNG</span>
                </div>
            </div>
            """),
            unsafe_allow_html=True,
        )

    # =========================================================================
    # STEP 4: ĐÁNH GIÁ & XUẤT (EVALUATION & PROMOTION)
    # =========================================================================
    with tab_eval:
        st.subheader("4. Đánh giá chất lượng độc lập & Thăng cấp mô hình (Promotion)")

        if not candidates:
            st.info(
                "Chưa có mô hình ứng viên (Candidate) nào hoàn tất. "
                "Sau khi tiến trình huấn luyện ở Bước 3 kết thúc, mô hình sẽ được đóng gói ứng viên tại đây."
            )
        else:
            cand_names = [c[0] for c in candidates]
            default_cand_idx = 0
            if current_run_id in cand_names:
                default_cand_idx = cand_names.index(current_run_id)

            selected_cand_name = st.selectbox(
                "Chọn mô hình ứng viên (Candidate Run):",
                cand_names,
                index=default_cand_idx,
                key="select_candidate_model",
            )
            cand_dir = dict(candidates)[selected_cand_name]

            # Read candidate manifest, test_metrics, and benchmark
            cand_test_metrics_file = cand_dir / "test_metrics.json"
            cand_benchmark_file = cand_dir / "benchmark.json"

            cand_metrics: dict[str, Any] = {}
            cand_benchmark: dict[str, Any] = {}

            if cand_test_metrics_file.is_file():
                try:
                    cand_metrics = json.loads(cand_test_metrics_file.read_text(encoding="utf-8"))
                except Exception:
                    pass

            if cand_benchmark_file.is_file():
                try:
                    cand_benchmark = json.loads(cand_benchmark_file.read_text(encoding="utf-8"))
                except Exception:
                    pass

            # Display Test Set Metrics Cards
            map50_val = cand_metrics.get("map50", cand_metrics.get("mAP50", 0.0))
            map50_95_val = cand_metrics.get("map50_95", cand_metrics.get("mAP50-95", 0.0))
            prec_val = cand_metrics.get("precision", 0.0)
            rec_val = cand_metrics.get("recall", 0.0)
            f1_val = cand_metrics.get("f1", 0.0)

            st.markdown(
                clean_html(f"""
                <div class="tv-metricrow">
                    <div class="tv-metric">
                        <div class="tv-num">{map50_val:.3f}</div>
                        <div class="tv-label">Test mAP@50</div>
                    </div>
                    <div class="tv-metric">
                        <div class="tv-num">{map50_95_val:.3f}</div>
                        <div class="tv-label">Test mAP@50-95</div>
                    </div>
                    <div class="tv-metric">
                        <div class="tv-num">{prec_val:.3f} / {rec_val:.3f}</div>
                        <div class="tv-label">Precision / Recall</div>
                    </div>
                    <div class="tv-metric">
                        <div class="tv-num">{f1_val:.3f}</div>
                        <div class="tv-label">F1-Score</div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )

            # CPU Benchmark
            cpu_latency = cand_benchmark.get("cpu_latency_ms", "N/A")
            cpu_fps = cand_benchmark.get("cpu_fps", "N/A")
            is_parity = cand_benchmark.get("is_parity_valid", True)
            parity_text = (
                "Đạt chuẩn ONNX (Parity Valid)" if is_parity else "Cảnh báo sai lệch PyTorch-ONNX"
            )

            st.markdown(
                clean_html(f"""
                <div class="tv-smallbox" style="margin-bottom:16px;">
                    <div>
                        <div class="tv-smalltitle">Hiệu năng suy luận CPU &amp; Kiểm tra tương đương (Parity)</div>
                        <div class="tv-smalltext">Độ trễ trung bình: <strong>{cpu_latency} ms</strong> · Tốc độ: <strong>{cpu_fps} FPS</strong> · {parity_text}</div>
                    </div>
                    <span class="tv-tag">82 LỚP VIỆT NAM</span>
                </div>
                """),
                unsafe_allow_html=True,
            )

            # One-click Promote to Production Button
            btn_promote = st.button(
                "🚀 Chuyển lên Production (82 lớp)",
                key="btn_promote_to_production",
                type="primary",
                use_container_width=True,
            )

            if btn_promote:
                try:
                    promoted = services.registry.promote_candidate(cand_dir)
                    st.success(
                        f"🎉 Mô hình `{promoted.manifest.model_id}` đã được thăng cấp lên Production thành công! "
                        f"Hệ thống hiện phục vụ suy luận đầy đủ 82 lớp biển báo Việt Nam."
                    )
                except Exception as exc:
                    st.error(f"Lỗi khi thăng cấp mô hình lên Production: {exc}")
