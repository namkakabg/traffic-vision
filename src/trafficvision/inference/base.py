from __future__ import annotations

from typing import Protocol

import numpy as np

from trafficvision.domain import Detection


class PredictionContractError(Exception):
    """Raised when inference results violate domain contract (e.g. unknown class ID)."""


class Predictor(Protocol):
    def predict(
        self,
        image_bgr: np.ndarray,
        *,
        confidence: float,
        iou: float,
    ) -> tuple[Detection, ...]:
        """Run object detection inference on a BGR image array."""
        ...
