from __future__ import annotations

import time

import numpy as np

from trafficvision.domain import ImageAnalysis
from trafficvision.inference.base import Predictor


def analyze_image(
    image_bgr: np.ndarray,
    predictor: Predictor,
    confidence: float,
    iou: float,
) -> ImageAnalysis:
    """Run detection on a single BGR image and return immutable ImageAnalysis."""
    height, width = image_bgr.shape[:2]

    start = time.perf_counter()
    detections = predictor.predict(
        image_bgr,
        confidence=confidence,
        iou=iou,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    return ImageAnalysis(
        width=width,
        height=height,
        detections=tuple(detections),
        inference_ms=elapsed_ms,
    )
