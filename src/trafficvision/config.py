from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


@dataclass(frozen=True)
class AppPaths:
    root: Path
    artifacts: Path
    baseline: Path
    production: Path
    backups: Path
    runs: Path
    staging: Path
    outputs: Path
    state: Path
    db: Path

    @classmethod
    def from_root(cls, root: Path) -> AppPaths:
        root_resolved = root.resolve()
        artifacts = root_resolved / "artifacts"
        state = artifacts / "state"
        return cls(
            root=root_resolved,
            artifacts=artifacts,
            baseline=artifacts / "baseline",
            production=artifacts / "production",
            backups=artifacts / "backups",
            runs=artifacts / "runs",
            staging=artifacts / "staging",
            outputs=artifacts / "outputs",
            state=state,
            db=state / "history.db",
        )

    def ensure_directories(self) -> None:
        for p in [
            self.artifacts,
            self.baseline,
            self.production,
            self.backups,
            self.runs,
            self.staging,
            self.outputs,
            self.state,
        ]:
            p.mkdir(parents=True, exist_ok=True)


class InferenceConfig(BaseModel):
    confidence: float = Field(default=0.25, ge=0.0, le=1.0)
    iou: float = Field(default=0.70, ge=0.0, le=1.0)
    imgsz: int = Field(default=640, gt=0)
    device: str = "cpu"
    backend: str = "onnx"

    @field_validator("confidence", "iou")
    @classmethod
    def validate_probabilities(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Value {v} must be between 0.0 and 1.0")
        return v


class MediaConfig(BaseModel):
    max_image_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    max_video_bytes: int = Field(default=500 * 1024 * 1024, gt=0)
    allowed_image_extensions: tuple[str, ...] = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".heic",
        ".heif",
    )
    allowed_video_extensions: tuple[str, ...] = (".mp4", ".avi", ".mov")


class AppConfig(BaseModel):
    paths: AppPaths
    inference: InferenceConfig = Field(default_factory=InferenceConfig)
    media: MediaConfig = Field(default_factory=MediaConfig)

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def load(
        cls,
        path: Path | None = None,
        project_root: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> AppConfig:
        root = project_root if project_root is not None else Path.cwd()
        paths = AppPaths.from_root(root)

        config_path = path or (root / "configs" / "app.yaml")
        raw: dict[str, Any] = {}
        if config_path.is_file():
            with open(config_path, encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    raw = loaded

        inf_data = raw.get("inference", {})
        media_data = raw.get("media", {})

        env_map = env if env is not None else os.environ

        if "TRAFFICVISION_CONFIDENCE" in env_map:
            try:
                inf_data["confidence"] = float(env_map["TRAFFICVISION_CONFIDENCE"])
            except ValueError as e:
                raise ValueError(f"Invalid TRAFFICVISION_CONFIDENCE: {e}") from e

        if "TRAFFICVISION_IOU" in env_map:
            try:
                inf_data["iou"] = float(env_map["TRAFFICVISION_IOU"])
            except ValueError as e:
                raise ValueError(f"Invalid TRAFFICVISION_IOU: {e}") from e

        if "TRAFFICVISION_IMGSZ" in env_map:
            try:
                inf_data["imgsz"] = int(env_map["TRAFFICVISION_IMGSZ"])
            except ValueError as e:
                raise ValueError(f"Invalid TRAFFICVISION_IMGSZ: {e}") from e

        inference = InferenceConfig.model_validate(inf_data)
        media = MediaConfig.model_validate(media_data)

        return cls(paths=paths, inference=inference, media=media)
