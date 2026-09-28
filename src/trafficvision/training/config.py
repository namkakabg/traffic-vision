"""Configuration model for YOLO training runs."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class TrainingConfig(BaseModel):
    """Pydantic model specifying hyper-parameters and paths for a training run."""

    run_id: str
    data_yaml: Path
    base_model: str = "yolo11n.pt"
    epochs: int = Field(default=50, ge=1)
    batch: int = Field(default=4, ge=1)
    imgsz: int = Field(default=640, gt=0)
    patience: int = Field(default=10, ge=0)
    amp: bool = True
    device: str = "cpu"
    seed: int = 42

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("batch")
    @classmethod
    def validate_batch(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"batch must be at least 1, got {v}")
        return v

    @field_validator("epochs")
    @classmethod
    def validate_epochs(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"epochs must be at least 1, got {v}")
        return v

    @field_validator("imgsz")
    @classmethod
    def validate_imgsz(cls, v: int) -> int:
        if v <= 0 or v % 32 != 0:
            raise ValueError(f"imgsz must be a positive multiple of 32, got {v}")
        return v
