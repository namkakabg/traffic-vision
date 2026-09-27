from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SHA256_REGEX = re.compile(r"^[0-9a-fA-F]{64}$")


class ModelManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0"
    model_id: str
    stage: Literal["baseline", "candidate", "production", "backup"]
    source_model_id: str | None = None
    artifact_filename: str = "model.onnx"
    backend: Literal["onnx", "pt"] = "onnx"
    task: str = "detect"
    class_names: dict[int, str]
    imgsz: int = 640
    sha256: str
    source: str
    created_at: str
    metrics: dict[str, Any] | None = None

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        if not SHA256_REGEX.match(v):
            raise ValueError(f"Invalid SHA-256 hash: {v}")
        return v.lower()

    @field_validator("class_names")
    @classmethod
    def validate_class_names(cls, v: dict[int, str]) -> dict[int, str]:
        if not v:
            raise ValueError("class_names cannot be empty")
        sorted_keys = sorted(v.keys())
        expected_keys = list(range(len(sorted_keys)))
        if sorted_keys != expected_keys:
            raise ValueError(
                f"class_names keys must be contiguous integers starting from 0, got {sorted_keys}"
            )
        return v


class RegisteredModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    manifest: ModelManifest
    model_path: Path
    manifest_path: Path


class Detection(BaseModel):
    model_config = ConfigDict(frozen=True)

    class_id: int
    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    xyxy: tuple[float, float, float, float]

    @model_validator(mode="after")
    def validate_bounds(self) -> Detection:
        x1, y1, x2, y2 = self.xyxy
        if x2 < x1:
            raise ValueError(f"Invalid coordinates: x2 ({x2}) < x1 ({x1})")
        if y2 < y1:
            raise ValueError(f"Invalid coordinates: y2 ({y2}) < y1 ({y1})")
        return self


class InferenceOptions(BaseModel):
    model_config = ConfigDict(frozen=True)

    confidence: float = Field(default=0.25, ge=0.0, le=1.0)
    iou: float = Field(default=0.70, ge=0.0, le=1.0)


class StagedMedia(BaseModel):
    model_config = ConfigDict(frozen=True)

    media_id: str
    original_filename: str
    staged_path: Path
    media_type: Literal["image", "video"]
    size_bytes: int


class VideoProgress(BaseModel):
    model_config = ConfigDict(frozen=True)

    current_frame: int
    total_frames: int
    fraction: float
    fps: float


class ImageAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    width: int
    height: int
    detections: tuple[Detection, ...]
    inference_ms: float


class VideoAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    width: int
    height: int
    fps: float
    total_frames: int
    processed_frames: int
    detection_counts_by_class: dict[str, int]
    inference_ms: float
    fallback_codec_used: bool = False
    codec_note: str | None = None


class AnalysisRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    record_id: str
    media_type: Literal["image", "video"]
    original_filename: str
    model_id: str
    model_stage: str
    confidence_threshold: float
    iou_threshold: float
    total_detections: int
    class_counts: dict[str, int]
    inference_ms: float
    created_at: str
    annotated_path: Path
    csv_path: Path


class AnalysisArtifacts(BaseModel):
    model_config = ConfigDict(frozen=True)

    record: AnalysisRecord
    annotated_media_path: Path
    csv_path: Path
