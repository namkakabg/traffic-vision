from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from trafficvision.config import AppConfig
from trafficvision.domain import (
    AnalysisArtifacts,
    AnalysisRecord,
    InferenceOptions,
    VideoProgress,
)
from trafficvision.history import AnalysisRepository
from trafficvision.inference.base import Predictor
from trafficvision.inference.image import analyze_image
from trafficvision.inference.ultralytics import UltralyticsOnnxPredictor
from trafficvision.inference.video import process_video
from trafficvision.media import decode_image, stage_upload
from trafficvision.registry import ModelRegistry
from trafficvision.rendering import annotate_image, detections_csv
from trafficvision.settings import RuntimeSettingsStore


class AnalysisService:
    """Application-level image/video analysis service and history transaction boundary."""

    def __init__(
        self,
        config: AppConfig,
        registry: ModelRegistry,
        repository: AnalysisRepository,
        settings_store: RuntimeSettingsStore,
        predictor_factory: Callable[[], Predictor] | None = None,
    ) -> None:
        self.config = config
        self.registry = registry
        self.repository = repository
        self.settings_store = settings_store
        self.predictor_factory = predictor_factory

    def _get_predictor(self) -> Predictor:
        if self.predictor_factory is not None:
            return self.predictor_factory()
        prod = self.registry.get_production()
        return UltralyticsOnnxPredictor.from_registered(prod)

    def analyze_image_upload(self, filename: str, data: bytes) -> AnalysisArtifacts:
        settings = self.settings_store.load()
        staged = stage_upload(
            filename=filename,
            data=data,
            media_type="image",
            paths=self.config.paths,
            config=self.config,
        )

        image_bgr = decode_image(staged)
        predictor = self._get_predictor()
        prod = self.registry.get_production()

        analysis = analyze_image(
            image_bgr=image_bgr,
            predictor=predictor,
            confidence=settings.confidence,
            iou=settings.iou,
        )

        annotated_bytes = annotate_image(image_bgr, analysis.detections, format="JPEG")
        csv_bytes = detections_csv(analysis.detections, source_name=filename)

        record_id = str(uuid.uuid4())
        self.config.paths.outputs.mkdir(parents=True, exist_ok=True)
        annotated_path = self.config.paths.outputs / f"{record_id}_annotated.jpg"
        csv_path = self.config.paths.outputs / f"{record_id}_detections.csv"

        annotated_path.write_bytes(annotated_bytes)
        csv_path.write_bytes(csv_bytes)

        class_counts: dict[str, int] = {}
        for d in analysis.detections:
            class_counts[d.class_name] = class_counts.get(d.class_name, 0) + 1

        record = AnalysisRecord(
            record_id=record_id,
            media_type="image",
            original_filename=filename,
            model_id=prod.manifest.model_id,
            model_stage=prod.manifest.stage,
            confidence_threshold=settings.confidence,
            iou_threshold=settings.iou,
            total_detections=len(analysis.detections),
            class_counts=class_counts,
            inference_ms=analysis.inference_ms,
            created_at=datetime.now(timezone.utc).isoformat(),
            annotated_path=annotated_path,
            csv_path=csv_path,
        )

        self.repository.add(record)

        return AnalysisArtifacts(
            record=record,
            annotated_media_path=annotated_path,
            csv_path=csv_path,
        )

    def analyze_video_upload(
        self,
        filename: str,
        data: bytes,
        on_progress: Callable[[VideoProgress], None] | None = None,
    ) -> AnalysisArtifacts:
        settings = self.settings_store.load()
        staged = stage_upload(
            filename=filename,
            data=data,
            media_type="video",
            paths=self.config.paths,
            config=self.config,
        )

        predictor = self._get_predictor()
        prod = self.registry.get_production()

        record_id = str(uuid.uuid4())
        self.config.paths.outputs.mkdir(parents=True, exist_ok=True)
        ext = Path(filename).suffix.lower() or ".mp4"
        annotated_path = self.config.paths.outputs / f"{record_id}_annotated{ext}"
        csv_path = self.config.paths.outputs / f"{record_id}_detections.csv"

        options = InferenceOptions(confidence=settings.confidence, iou=settings.iou)

        video_analysis = process_video(
            input_path=staged.staged_path,
            output_path=annotated_path,
            csv_path=csv_path,
            predictor=predictor,
            options=options,
            on_progress=on_progress,
        )

        total_dets = sum(video_analysis.detection_counts_by_class.values())

        record = AnalysisRecord(
            record_id=record_id,
            media_type="video",
            original_filename=filename,
            model_id=prod.manifest.model_id,
            model_stage=prod.manifest.stage,
            confidence_threshold=settings.confidence,
            iou_threshold=settings.iou,
            total_detections=total_dets,
            class_counts=video_analysis.detection_counts_by_class,
            inference_ms=video_analysis.inference_ms,
            created_at=datetime.now(timezone.utc).isoformat(),
            annotated_path=annotated_path,
            csv_path=csv_path,
        )

        self.repository.add(record)

        return AnalysisArtifacts(
            record=record,
            annotated_media_path=annotated_path,
            csv_path=csv_path,
        )
