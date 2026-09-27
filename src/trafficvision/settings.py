from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field

from trafficvision.config import AppConfig


class RuntimeSettings(BaseModel):
    confidence: float = Field(default=0.25, ge=0.0, le=1.0)
    iou: float = Field(default=0.70, ge=0.0, le=1.0)
    max_image_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    max_video_bytes: int = Field(default=500 * 1024 * 1024, gt=0)


class RuntimeSettingsStore:
    """Atomic local persistence for user runtime settings under artifacts/state/settings.json."""

    def __init__(self, settings_path: Path, default_config: AppConfig) -> None:
        self.settings_path = settings_path
        self.default_config = default_config

    def load(self) -> RuntimeSettings:
        if not self.settings_path.is_file():
            return RuntimeSettings(
                confidence=self.default_config.inference.confidence,
                iou=self.default_config.inference.iou,
                max_image_bytes=self.default_config.media.max_image_bytes,
                max_video_bytes=self.default_config.media.max_video_bytes,
            )

        try:
            content = self.settings_path.read_text(encoding="utf-8")
            data = json.loads(content)
            return RuntimeSettings.model_validate(data)
        except Exception:
            return RuntimeSettings(
                confidence=self.default_config.inference.confidence,
                iou=self.default_config.inference.iou,
                max_image_bytes=self.default_config.media.max_image_bytes,
                max_video_bytes=self.default_config.media.max_video_bytes,
            )

    def save(self, settings: RuntimeSettings) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        data = settings.model_dump_json(indent=2).encode("utf-8")

        with tempfile.NamedTemporaryFile(dir=self.settings_path.parent, delete=False) as tf:
            tf.write(data)
            temp_name = tf.name

        os.replace(temp_name, self.settings_path)
