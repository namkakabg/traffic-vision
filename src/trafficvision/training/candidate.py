"""Candidate model packaging module for post-training artifacts."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

from trafficvision.domain import ModelManifest
from trafficvision.registry import sha256_file
from trafficvision.training.evaluator import EvaluationMetrics, evaluate_checkpoint
from trafficvision.training.exporter import ExportResult, export_and_verify_onnx

logger = logging.getLogger(__name__)


def finalize_checkpoint(
    run_id: str,
    checkpoint_path: Path | str,
    data_yaml: Path | str,
    runs_dir: Path | str,
    device: str,
    imgsz: int,
) -> Path:
    """Evaluate, export, and package an existing best checkpoint as a Candidate.

    This deliberately operates on a completed run's ``best.pt``.  It lets a
    previously trained model enter Step 4 without starting a new training run.
    """
    checkpoint = Path(checkpoint_path)
    data_config = Path(data_yaml)
    if not checkpoint.is_file():
        raise FileNotFoundError(f"Best checkpoint not found: {checkpoint}")
    if not data_config.is_file():
        raise FileNotFoundError(f"Dataset configuration not found: {data_config}")

    payload = yaml.safe_load(data_config.read_text(encoding="utf-8")) or {}
    class_names = payload.get("names")
    if not isinstance(class_names, (list, dict)) or not class_names:
        raise ValueError(f"Dataset configuration has no usable 'names' mapping: {data_config}")

    evaluation = evaluate_checkpoint(
        model_path=checkpoint,
        data_yaml=data_config,
        split="test",
        device=device,
        verbose=False,
    )
    exported = export_and_verify_onnx(model_path=checkpoint, imgsz=imgsz)
    return package_candidate(
        run_id=run_id,
        weights_path=checkpoint,
        onnx_result=exported,
        eval_metrics=evaluation,
        class_names=class_names,
        runs_dir=runs_dir,
    )


def package_candidate(
    run_id: str,
    weights_path: Path | str,
    onnx_result: ExportResult,
    eval_metrics: EvaluationMetrics,
    class_names: list[str] | dict[int, str],
    runs_dir: Path | str,
) -> Path:
    """Package validated training artifacts into the standard candidate directory.

    Structures candidate artifacts at `runs_dir / run_id / "candidate"`:
    - model.onnx: Exported ONNX weights.
    - manifest.json: Candidate model metadata conforming to ModelManifest.
    - benchmark.json: CPU latency, FPS, and parity verification metrics.
    - test_metrics.json: Full independent test evaluation metrics.

    Args:
        run_id: Unique identifier for the training run.
        weights_path: Path to PyTorch model weights (best.pt).
        onnx_result: ExportResult with ONNX path, parity status, and benchmarks.
        eval_metrics: EvaluationMetrics on the test dataset split.
        class_names: List of class labels or mapping of class index to label.
        runs_dir: Path to directory storing training runs (e.g. artifacts/runs).

    Returns:
        Path to created candidate directory.
    """
    runs_path = Path(runs_dir)
    if runs_path.name == run_id:
        candidate_dir = runs_path / "candidate"
    else:
        candidate_dir = runs_path / run_id / "candidate"

    candidate_dir.mkdir(parents=True, exist_ok=True)

    # 1. Verify source PyTorch weights path
    if weights_path is not None:
        wp = Path(weights_path)
        if not wp.exists():
            logger.warning(
                "Source PyTorch weights file does not exist at %s for candidate run %s",
                wp,
                run_id,
            )

    # 2. Copy ONNX weights into candidate directory
    src_onnx = Path(onnx_result.onnx_path)
    dest_onnx = candidate_dir / "model.onnx"
    shutil.copy2(src_onnx, dest_onnx)

    # 2. Compute SHA-256 checksum of copied ONNX model
    file_hash = sha256_file(dest_onnx)

    # 3. Format class names as contiguous dict[int, str]
    if isinstance(class_names, dict):
        names_dict = {int(k): str(v) for k, v in class_names.items()}
    else:
        names_dict = {int(i): str(name) for i, name in enumerate(class_names)}

    # 4. Generate and write manifest.json
    manifest = ModelManifest(
        schema_version="1.0",
        model_id=f"trafficvision_{run_id}",
        stage="candidate",
        source_model_id=None,
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names=names_dict,
        imgsz=640,
        sha256=file_hash,
        source=f"runs/{run_id}",
        created_at=datetime.now(timezone.utc).isoformat(),
        metrics={
            "precision": eval_metrics.precision,
            "recall": eval_metrics.recall,
            "f1": eval_metrics.f1,
            "map50": eval_metrics.map50,
            "map50_95": eval_metrics.map50_95,
            "cpu_latency_ms": onnx_result.cpu_latency_ms,
            "cpu_fps": onnx_result.cpu_fps,
            "is_parity_valid": onnx_result.is_parity_valid,
            "max_abs_diff": onnx_result.max_abs_diff,
        },
    )
    manifest_file = candidate_dir / "manifest.json"
    manifest_file.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    # 5. Write benchmark.json
    benchmark_data = {
        "cpu_latency_ms": onnx_result.cpu_latency_ms,
        "cpu_fps": onnx_result.cpu_fps,
        "max_abs_diff": onnx_result.max_abs_diff,
        "is_parity_valid": onnx_result.is_parity_valid,
    }
    benchmark_file = candidate_dir / "benchmark.json"
    benchmark_file.write_text(json.dumps(benchmark_data, indent=2), encoding="utf-8")

    # 6. Write test_metrics.json
    test_metrics_file = candidate_dir / "test_metrics.json"
    test_metrics_file.write_text(eval_metrics.model_dump_json(indent=2), encoding="utf-8")

    if not onnx_result.is_parity_valid:
        logger.warning(
            "Candidate packaged for %s but ONNX parity is INVALID (diff=%.6f)",
            run_id,
            onnx_result.max_abs_diff,
        )
    else:
        logger.info("Successfully packaged candidate model at %s", candidate_dir)

    return candidate_dir
