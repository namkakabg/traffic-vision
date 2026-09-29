"""Independent model evaluation module for YOLO checkpoints."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class EvaluationMetrics(BaseModel):
    """Evaluation metrics extracted from model validation on test split."""

    model_config = ConfigDict(frozen=True)

    precision: float
    recall: float
    f1: float
    map50: float
    map50_95: float
    per_class_ap: dict[str, float] = Field(default_factory=dict)
    confusion_matrix: list[list[int]] = Field(default_factory=list)


def evaluate_checkpoint(
    model_path: Path | str,
    data_yaml: Path | str,
    split: str = "test",
    device: str = "cpu",
    verbose: bool = False,
) -> EvaluationMetrics:
    """Evaluate a YOLO model checkpoint against a dataset split.

    Wraps Ultralytics model validation (`YOLO(model_path).val(...)`), safely
    extracting precision, recall, mAP50, mAP50-95, per-class AP, and confusion matrix,
    and calculating the F1 score.

    Args:
        model_path: Path to model weights (.pt).
        data_yaml: Path to dataset YAML configuration file.
        split: Dataset split to evaluate on ('test' or 'val'). Defaults to 'test'.
        device: Device to use for validation ('cpu', '0', etc.). Defaults to 'cpu'.
        verbose: Verbosity flag for Ultralytics validation.

    Returns:
        EvaluationMetrics instance containing evaluation results.
    """
    from ultralytics import YOLO  # Lazy import

    model = YOLO(str(model_path))
    results = model.val(
        data=str(data_yaml),
        split=split,
        device=device,
        verbose=verbose,
    )

    results_dict = getattr(results, "results_dict", {}) or {}
    box_obj = getattr(results, "box", None)

    def _get_val(key: str, fallback_attr: str | None = None) -> float:
        if key in results_dict and results_dict[key] is not None:
            try:
                return float(results_dict[key])
            except (ValueError, TypeError):
                pass
        if box_obj is not None and fallback_attr is not None:
            val = getattr(box_obj, fallback_attr, None)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
        return 0.0

    precision = _get_val("metrics/precision(B)", "mp")
    recall = _get_val("metrics/recall(B)", "mr")
    map50 = _get_val("metrics/mAP50(B)", "map50")
    map50_95 = _get_val("metrics/mAP50-95(B)", "map")

    # Compute F1: 2 * (P * R) / (P + R + 1e-9)
    if (precision + recall) > 0:
        f1 = float(2 * (precision * recall) / (precision + recall + 1e-9))
    else:
        f1 = 0.0

    # Extract per-class AP
    names = getattr(results, "names", {}) or {}
    maps = getattr(box_obj, "maps", None)
    if maps is None:
        maps = getattr(results, "maps", None)

    per_class_ap: dict[str, float] = {}
    if names and maps is not None:
        items = names.items() if isinstance(names, dict) else enumerate(names)
        for idx, class_name in items:
            try:
                i = int(idx)
                if i < len(maps):
                    per_class_ap[str(class_name)] = round(float(maps[i]), 5)
            except (ValueError, TypeError, IndexError):
                continue

    # Extract confusion matrix
    cm_obj = getattr(results, "confusion_matrix", None)
    matrix = getattr(cm_obj, "matrix", cm_obj)
    confusion_matrix: list[list[int]] = []
    if matrix is not None:
        try:
            for row in matrix:
                confusion_matrix.append([int(round(float(val))) for val in row])
        except (TypeError, ValueError):
            confusion_matrix = []

    metrics = EvaluationMetrics(
        precision=round(precision, 5),
        recall=round(recall, 5),
        f1=round(f1, 5),
        map50=round(map50, 5),
        map50_95=round(map50_95, 5),
        per_class_ap=per_class_ap,
        confusion_matrix=confusion_matrix,
    )
    logger.info(
        "Checkpoint evaluation complete for %s (split=%s): P=%.4f R=%.4f F1=%.4f mAP50=%.4f",
        model_path,
        split,
        metrics.precision,
        metrics.recall,
        metrics.f1,
        metrics.map50,
    )
    return metrics
