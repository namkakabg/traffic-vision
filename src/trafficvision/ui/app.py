from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from trafficvision.config import AppConfig, AppPaths
from trafficvision.domain import RegisteredModel
from trafficvision.history import AnalysisRepository
from trafficvision.registry import ModelRegistry
from trafficvision.service import AnalysisService
from trafficvision.settings import RuntimeSettingsStore
from trafficvision.training.manager import TrainingManager
from trafficvision.ui.pages.analysis import render_analysis_page
from trafficvision.ui.theme import apply_theme, clean_html


@dataclass
class AppServices:
    config: AppConfig
    registry: ModelRegistry
    repository: AnalysisRepository
    settings_store: RuntimeSettingsStore
    analysis_service: AnalysisService
    training_manager: TrainingManager | None = None

    def get_production_safe(self) -> RegisteredModel | None:
        try:
            return self.registry.get_production()
        except Exception:
            return None

    @classmethod
    def create(cls, project_root: Path | None = None) -> AppServices:
        root = project_root or Path.cwd()
        paths = AppPaths.from_root(root)
        paths.ensure_directories()
        config = AppConfig.load(project_root=root)
        registry = ModelRegistry(paths)
        repository = AnalysisRepository(paths.db)
        settings_store = RuntimeSettingsStore(paths.state / "settings.json", default_config=config)
        analysis_service = AnalysisService(
            config=config,
            registry=registry,
            repository=repository,
            settings_store=settings_store,
        )
        training_manager = TrainingManager(paths.runs)
        return cls(
            config=config,
            registry=registry,
            repository=repository,
            settings_store=settings_store,
            analysis_service=analysis_service,
            training_manager=training_manager,
        )


def main() -> None:
    st.set_page_config(
        page_title="TrafficVision - Nhận dạng biển báo giao thông",
        page_icon="🚦",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme(st)

    root_env = os.environ.get("TRAFFICVISION_ROOT")
    project_root = Path(root_env) if root_env else Path.cwd()
    services = AppServices.create(project_root)

    # Sidebar Navigation and Metadata matching mockup
    with st.sidebar:
        st.title("⌁ TrafficVision")
        st.markdown(
            clean_html("""
            <div class="tv-navlabel">Không gian làm việc</div>
            """),
            unsafe_allow_html=True,
        )

        nav_labels = {
            "Phân tích": "◫ &nbsp; Phân tích",
            "Lịch sử": "◷ &nbsp; Lịch sử",
            "Thống kê": "▥ &nbsp; Thống kê",
            "Huấn luyện AI": "◉ &nbsp; Huấn luyện AI",
            "Thông tin mô hình": "◎ &nbsp; Thông tin mô hình",
            "Thiết lập": "⚙ &nbsp; Thiết lập",
        }

        pages = [
            "Phân tích",
            "Lịch sử",
            "Thống kê",
            "Huấn luyện AI",
            "Thông tin mô hình",
            "Thiết lập",
        ]
        choice = st.radio(
            "Menu",
            pages,
            index=0,
            format_func=lambda x: nav_labels.get(x, x),
            label_visibility="collapsed",
        )

        prod_model = services.get_production_safe()
        if prod_model is not None:
            num_classes = len(prod_model.manifest.class_names)
            stage = prod_model.manifest.stage
            is_baseline = (
                stage == "baseline"
                or (
                    prod_model.manifest.source_model_id
                    and "baseline" in prod_model.manifest.source_model_id
                )
                or ("yolo11n" in prod_model.manifest.source.lower() and num_classes != 82)
            )

            pulse_class = "tv-pulse-amber" if is_baseline else "tv-pulse"
            status_text = "Baseline (Chưa fine-tune)" if is_baseline else "Mô hình sẵn sàng"
            class_meta = (
                f"{num_classes} lớp đối tượng" if num_classes != 82 else "82 lớp biển báo Việt Nam"
            )

            st.markdown(
                clean_html(f"""
                <div class="tv-modelcard">
                    <div class="tv-online"><span class="{pulse_class}"></span> {status_text}</div>
                    <div class="tv-modelname">{prod_model.manifest.model_id} · {prod_model.manifest.backend.upper()}</div>
                    <div class="tv-modelmeta">{class_meta}</div>
                </div>
                """),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                clean_html("""
                <div class="tv-modelcard">
                    <div class="tv-online"><span class="tv-pulse-amber"></span> Chưa cài đặt mô hình</div>
                    <div class="tv-modelname">Chưa có Production</div>
                    <div class="tv-modelmeta">Chạy bootstrap để nạp baseline</div>
                </div>
                """),
                unsafe_allow_html=True,
            )

    # Routing
    if choice == "Phân tích":
        render_analysis_page(services)
    elif choice == "Huấn luyện AI":
        from trafficvision.ui.pages.training import (
            render_training_page,
        )

        render_training_page(services)
    elif choice == "Lịch sử":
        from trafficvision.ui.pages.history import render_history_page

        render_history_page(services)
    elif choice == "Thống kê":
        from trafficvision.ui.pages.statistics import render_statistics_page

        render_statistics_page(services)
    elif choice == "Thông tin mô hình":
        from trafficvision.ui.pages.model_info import render_model_info_page

        render_model_info_page(services)
    elif choice == "Thiết lập":
        from trafficvision.ui.pages.settings import render_settings_page

        render_settings_page(services)
