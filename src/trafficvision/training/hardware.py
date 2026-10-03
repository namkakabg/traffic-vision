"""Runtime detection for training devices that Ultralytics can actually use."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TrainingDevice:
    """One selectable compute target for a training run."""

    value: str
    label: str
    is_cuda: bool


def detect_training_devices(torch_module: Any | None = None) -> list[TrainingDevice]:
    """Return verified CUDA devices followed by the always-available CPU option."""
    if torch_module is None:
        try:
            import torch

            torch_module = torch
        except Exception:
            return [TrainingDevice(value="cpu", label="CPU", is_cuda=False)]

    devices: list[TrainingDevice] = []
    try:
        if torch_module.cuda.is_available():
            for index in range(torch_module.cuda.device_count()):
                name = torch_module.cuda.get_device_name(index)
                devices.append(
                    TrainingDevice(
                        value=str(index),
                        label=f"GPU {index} - {name}",
                        is_cuda=True,
                    )
                )
    except Exception:
        pass

    devices.append(TrainingDevice(value="cpu", label="CPU", is_cuda=False))
    return devices
