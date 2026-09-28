"""TrafficVision training package for background YOLO training, state tracking, and process lifecycle."""

from __future__ import annotations

from typing import Any

from trafficvision.training.config import TrainingConfig
from trafficvision.training.manager import TrainingManager
from trafficvision.training.state import TrainingEvent, TrainingState

__all__ = [
    "TrainingConfig",
    "TrainingEvent",
    "TrainingManager",
    "TrainingState",
    "run_training_subprocess",
]


def __getattr__(name: str) -> Any:
    if name == "run_training_subprocess":
        from trafficvision.training.runner import run_training_subprocess

        return run_training_subprocess
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
