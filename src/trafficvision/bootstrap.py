from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from trafficvision.domain import ModelManifest, RegisteredModel
from trafficvision.registry import ModelRegistry, sha256_file


def bootstrap_baseline(
    registry: ModelRegistry,
    model_name: str = "yolo11n.pt",
) -> RegisteredModel:
    """Download, export, and register the baseline pretrained YOLO model as ONNX."""
    os.environ["YOLO_AUTOINSTALL"] = "False"

    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise RuntimeError("Ultralytics package is required for bootstrap.") from e

    model = YOLO(model_name)

    # Extract class names mapping from model metadata
    raw_names = model.names
    if isinstance(raw_names, (list, tuple)):
        class_names = {i: str(name) for i, name in enumerate(raw_names)}
    elif isinstance(raw_names, dict):
        class_names = {int(k): str(v) for k, v in raw_names.items()}
    else:
        raise ValueError(f"Unexpected model.names format: {type(raw_names)}")

    # Export fixed-shape ONNX without simplification-time autoinstall
    exported_str = model.export(
        format="onnx",
        imgsz=640,
        batch=1,
        dynamic=False,
        simplify=False,
        device="cpu",
    )
    exported_path = Path(exported_str)
    if not exported_path.is_file():
        raise FileNotFoundError(f"Exported ONNX model file not found at {exported_path}")

    file_hash = sha256_file(exported_path)
    stem = Path(model_name).stem
    model_id = f"{stem}-baseline-{file_hash[:8]}"

    manifest = ModelManifest(
        schema_version="1.0",
        model_id=model_id,
        stage="baseline",
        source_model_id=None,
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names=class_names,
        imgsz=640,
        sha256=file_hash,
        source=f"ultralytics-{model_name}",
        created_at=datetime.now(timezone.utc).isoformat(),
        metrics=None,
    )

    return registry.install_baseline(exported_path, manifest)
