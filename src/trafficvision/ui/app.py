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
from trafficvision.ui.pages.analysis import render_analysis_page
from trafficvision.ui.theme import apply_theme


@dataclass
class AppServices:
    config: AppConfig
    registry: ModelRegistry
    repository: AnalysisRepository
    settings_store: RuntimeSettingsStore
    analysis_service: AnalysisService

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
        return cls(
            config=config,
            registry=registry,
            repository=repository,
            settings_store=settings_store,
            analysis_service=analysis_service,
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

    # Sidebar Navigation and Metadata
    with st.sidebar:
        st.title("🚦 TrafficVision")
        st.caption("Hệ thống nhận diện biển báo thông minh")

        prod_model = services.get_production_safe()
        if prod_model is not None:
            num_classes = len(prod_model.manifest.class_names)
            stage = prod_model.manifest.stage
            st.markdown(
                f"""
                <div class="tv-card">
                    <span class="tv-badge tv-badge-baseline">Mode: {stage.upper()}</span>
                    <p style="margin-top: 0.5rem; font-size: 0.85rem;">
                        <strong>Mô hình:</strong> {prod_model.manifest.model_id}<br/>
                        <strong>Số lớp:</strong> {num_classes} lớp
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="tv-card">
                    <span class="tv-badge tv-badge-baseline">CHƯA CÀI ĐẶT</span>
                    <p style="margin-top: 0.5rem; font-size: 0.85rem;">
                        Chưa có mô hình production. Chạy bootstrap trước khi suy luận.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()

        pages = [
            "Phân tích",
            "Lịch sử",
            "Thống kê",
            "Huấn luyện AI",
            "Thông tin mô hình",
            "Thiết lập",
        ]
        choice = st.radio("Menu", pages, index=0)

    # Routing
    if choice == "Phân tích":
        render_analysis_page(services)
    elif choice == "Huấn luyện AI":
        from trafficvision.ui.pages.training_placeholder import (
            render_training_placeholder_page,
        )

        render_training_placeholder_page(services)
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
