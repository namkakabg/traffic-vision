from __future__ import annotations

from typing import Any

import numpy as np

from trafficvision.domain import Detection, RegisteredModel
from trafficvision.inference.base import PredictionContractError
from trafficvision.registry import ModelIntegrityError, sha256_file


class UltralyticsOnnxPredictor:
    """Predictor adapter running ONNX Runtime on CPU via Ultralytics."""

    def __init__(self, model: RegisteredModel) -> None:
        self.model = model
        self._yolo: Any | None = None

    @classmethod
    def from_registered(cls, model: RegisteredModel) -> UltralyticsOnnxPredictor:
        return cls(model=model)

    def _ensure_loaded(self) -> None:
        # Check integrity before loading model
        if not self.model.model_path.is_file():
            raise ModelIntegrityError(f"Model file {self.model.model_path} does not exist")

        actual_sha = sha256_file(self.model.model_path)
        if actual_sha != self.model.manifest.sha256.lower():
            raise ModelIntegrityError(
                f"Model integrity violation for {self.model.manifest.model_id}: "
                f"expected {self.model.manifest.sha256}, got {actual_sha}"
            )

        if self._yolo is None:
            try:
                from ultralytics import YOLO
            except ImportError as e:
                raise RuntimeError("Ultralytics package is required for inference.") from e

            self._yolo = YOLO(str(self.model.model_path), task="detect")

    def predict(
        self,
        image_bgr: np.ndarray,
        *,
        confidence: float,
        iou: float,
    ) -> tuple[Detection, ...]:
        self._ensure_loaded()
        assert self._yolo is not None

        results = self._yolo(
            image_bgr,
            conf=confidence,
            iou=iou,
            imgsz=self.model.manifest.imgsz,
            device="cpu",
            verbose=False,
        )

        detections: list[Detection] = []
        for res in results:
            boxes = getattr(res, "boxes", None)
            if boxes is None or len(boxes) == 0:
                continue

            for box in boxes:
                raw_xyxy = box.xyxy[0].cpu().tolist()
                conf_val = float(box.conf[0].cpu().item())
                cls_id = int(box.cls[0].cpu().item())

                if cls_id not in self.model.manifest.class_names:
                    raise PredictionContractError(
                        f"Model returned class ID {cls_id} which is not declared in manifest "
                        f"for model {self.model.manifest.model_id}"
                    )

                class_name = self.model.manifest.class_names[cls_id]
                detection = Detection(
                    class_id=cls_id,
                    class_name=class_name,
                    confidence=conf_val,
                    xyxy=(
                        float(raw_xyxy[0]),
                        float(raw_xyxy[1]),
                        float(raw_xyxy[2]),
                        float(raw_xyxy[3]),
                    ),
                )
                detections.append(detection)

        return tuple(detections)
