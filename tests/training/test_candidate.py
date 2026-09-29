"""Tests for packaging candidate artifacts into candidate directory."""

from __future__ import annotations

import json
from pathlib import Path

from trafficvision.domain import ModelManifest
from trafficvision.registry import sha256_file
from trafficvision.training.candidate import package_candidate
from trafficvision.training.evaluator import EvaluationMetrics
from trafficvision.training.exporter import ExportResult


def test_package_candidate_success(tmp_path: Path):
    """Verify package_candidate structures artifacts, computes hash, and writes manifests."""
    runs_dir = tmp_path / "artifacts" / "runs"
    run_id = "run_20260929_120000"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True)

    weights_path = run_dir / "weights" / "best.pt"
    weights_path.parent.mkdir(parents=True)
    weights_path.write_bytes(b"dummy-best-pt")

    onnx_file = run_dir / "weights" / "best.onnx"
    onnx_file.write_bytes(b"dummy-onnx-bytes-content")

    onnx_result = ExportResult(
        onnx_path=onnx_file,
        max_abs_diff=0.0002,
        is_parity_valid=True,
        cpu_latency_ms=22.4,
        cpu_fps=44.6,
    )

    eval_metrics = EvaluationMetrics(
        precision=0.87,
        recall=0.81,
        f1=0.839,
        map50=0.85,
        map50_95=0.62,
        per_class_ap={"pedestrian": 0.86, "speed_limit": 0.84},
        confusion_matrix=[[20, 1], [2, 18]],
    )

    class_names = ["pedestrian", "speed_limit"]

    candidate_dir = package_candidate(
        run_id=run_id,
        weights_path=weights_path,
        onnx_result=onnx_result,
        eval_metrics=eval_metrics,
        class_names=class_names,
        runs_dir=runs_dir,
    )

    expected_candidate_dir = runs_dir / run_id / "candidate"
    assert candidate_dir == expected_candidate_dir
    assert candidate_dir.is_dir()

    # 1. model.onnx check
    target_onnx = candidate_dir / "model.onnx"
    assert target_onnx.is_file()
    assert target_onnx.read_bytes() == b"dummy-onnx-bytes-content"
    computed_sha = sha256_file(target_onnx)

    # 2. manifest.json check
    manifest_file = candidate_dir / "manifest.json"
    assert manifest_file.is_file()
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest = ModelManifest.model_validate(manifest_data)

    assert manifest.stage == "candidate"
    assert manifest.model_id == f"trafficvision_{run_id}"
    assert manifest.backend == "onnx"
    assert manifest.task == "detect"
    assert manifest.imgsz == 640
    assert manifest.class_names == {0: "pedestrian", 1: "speed_limit"}
    assert manifest.sha256 == computed_sha
    assert manifest.source == f"runs/{run_id}"
    assert manifest.metrics is not None
    assert manifest.metrics["map50"] == 0.85
    assert manifest.metrics["is_parity_valid"] is True
    assert manifest.metrics["cpu_fps"] == 44.6

    # 3. benchmark.json check
    benchmark_file = candidate_dir / "benchmark.json"
    assert benchmark_file.is_file()
    benchmark_data = json.loads(benchmark_file.read_text(encoding="utf-8"))
    assert benchmark_data["cpu_latency_ms"] == 22.4
    assert benchmark_data["cpu_fps"] == 44.6
    assert benchmark_data["max_abs_diff"] == 0.0002
    assert benchmark_data["is_parity_valid"] is True

    # 4. test_metrics.json check
    metrics_file = candidate_dir / "test_metrics.json"
    assert metrics_file.is_file()
    saved_metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
    assert saved_metrics["precision"] == 0.87
    assert saved_metrics["recall"] == 0.81
    assert saved_metrics["f1"] == 0.839
    assert saved_metrics["map50"] == 0.85
    assert saved_metrics["per_class_ap"] == {"pedestrian": 0.86, "speed_limit": 0.84}
    assert saved_metrics["confusion_matrix"] == [[20, 1], [2, 18]]


def test_package_candidate_with_parity_failure(tmp_path: Path):
    """Verify package_candidate records parity divergence failure in manifest and benchmark."""
    runs_dir = tmp_path / "artifacts" / "runs"
    run_id = "run_diverged_999"

    weights_path = tmp_path / "best.pt"
    weights_path.write_bytes(b"dummy")

    onnx_file = tmp_path / "best.onnx"
    onnx_file.write_bytes(b"dummy-onnx")

    onnx_result = ExportResult(
        onnx_path=onnx_file,
        max_abs_diff=0.045,
        is_parity_valid=False,
        cpu_latency_ms=19.0,
        cpu_fps=52.6,
    )

    eval_metrics = EvaluationMetrics(
        precision=0.70,
        recall=0.70,
        f1=0.70,
        map50=0.68,
        map50_95=0.45,
        per_class_ap={"class0": 0.68},
        confusion_matrix=[[5]],
    )

    candidate_dir = package_candidate(
        run_id=run_id,
        weights_path=weights_path,
        onnx_result=onnx_result,
        eval_metrics=eval_metrics,
        class_names=["class0"],
        runs_dir=runs_dir,
    )

    manifest_file = candidate_dir / "manifest.json"
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data["metrics"]["is_parity_valid"] is False
    assert manifest_data["metrics"]["max_abs_diff"] == 0.045

    benchmark_file = candidate_dir / "benchmark.json"
    benchmark_data = json.loads(benchmark_file.read_text(encoding="utf-8"))
    assert benchmark_data["is_parity_valid"] is False
    assert benchmark_data["max_abs_diff"] == 0.045


def test_package_candidate_with_dict_class_names(tmp_path: Path):
    """Verify package_candidate supports class_names passed as dict."""
    runs_dir = tmp_path / "artifacts" / "runs"
    run_id = "run_dict_classes"

    weights_path = tmp_path / "best.pt"
    weights_path.write_bytes(b"dummy")

    onnx_file = tmp_path / "best.onnx"
    onnx_file.write_bytes(b"dummy-onnx-content")

    onnx_result = ExportResult(
        onnx_path=onnx_file,
        max_abs_diff=0.0001,
        is_parity_valid=True,
        cpu_latency_ms=10.0,
        cpu_fps=100.0,
    )

    eval_metrics = EvaluationMetrics(
        precision=0.9,
        recall=0.9,
        f1=0.9,
        map50=0.9,
        map50_95=0.7,
        per_class_ap={"c0": 0.9},
        confusion_matrix=[[1]],
    )

    candidate_dir = package_candidate(
        run_id=run_id,
        weights_path=weights_path,
        onnx_result=onnx_result,
        eval_metrics=eval_metrics,
        class_names={0: "c0"},
        runs_dir=runs_dir,
    )

    manifest_file = candidate_dir / "manifest.json"
    manifest = ModelManifest.model_validate_json(manifest_file.read_text(encoding="utf-8"))
    assert manifest.class_names == {0: "c0"}


def test_training_package_reexports():
    """Verify trafficvision.training re-exports all Task 5 interfaces."""
    import trafficvision.training as tv_training

    assert hasattr(tv_training, "EvaluationMetrics")
    assert hasattr(tv_training, "evaluate_checkpoint")
    assert hasattr(tv_training, "ExportResult")
    assert hasattr(tv_training, "export_and_verify_onnx")
    assert hasattr(tv_training, "package_candidate")


def test_package_candidate_warns_on_missing_weights_path(tmp_path: Path, caplog):
    """Verify warning logged when weights_path does not exist."""
    runs_dir = tmp_path / "artifacts" / "runs"
    run_id = "run_missing_weights"

    nonexistent_weights = tmp_path / "nonexistent" / "best.pt"
    onnx_file = tmp_path / "best.onnx"
    onnx_file.write_bytes(b"dummy-onnx-content")

    onnx_result = ExportResult(
        onnx_path=onnx_file,
        max_abs_diff=0.0001,
        is_parity_valid=True,
        cpu_latency_ms=10.0,
        cpu_fps=100.0,
    )

    eval_metrics = EvaluationMetrics(
        precision=0.8,
        recall=0.8,
        f1=0.8,
        map50=0.8,
        map50_95=0.6,
        per_class_ap={"c0": 0.8},
        confusion_matrix=[[1]],
    )

    package_candidate(
        run_id=run_id,
        weights_path=nonexistent_weights,
        onnx_result=onnx_result,
        eval_metrics=eval_metrics,
        class_names=["c0"],
        runs_dir=runs_dir,
    )

    assert "Source PyTorch weights file does not exist" in caplog.text
