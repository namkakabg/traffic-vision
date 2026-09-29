"""End-to-end integration tests for Phase 2 dataset, training, promotion, and CLI scripts."""

from __future__ import annotations

import io
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import onnx
from onnx import TensorProto, helper
from PIL import Image

from trafficvision.config import AppConfig, AppPaths
from trafficvision.data import (
    VIETNAM_TRAFFIC_SIGN_CATALOG,
    create_dataset_snapshot,
    create_synthetic_dataset,
    scan_yolo_dataset,
    validate_dataset,
)
from trafficvision.domain import ModelManifest
from trafficvision.history import AnalysisRepository
from trafficvision.registry import ModelRegistry, sha256_file
from trafficvision.service import AnalysisService
from trafficvision.settings import RuntimeSettingsStore
from trafficvision.training.candidate import package_candidate
from trafficvision.training.evaluator import EvaluationMetrics
from trafficvision.training.exporter import ExportResult


def _create_minimal_onnx(path: Path) -> None:
    """Create a minimal valid ONNX file for tests."""
    node = helper.make_node("Identity", ["X"], ["Y"])
    graph = helper.make_graph(
        [node],
        "test_graph",
        [helper.make_tensor_value_info("X", TensorProto.FLOAT, [1, 3, 640, 640])],
        [helper.make_tensor_value_info("Y", TensorProto.FLOAT, [1, 3, 640, 640])],
    )
    model = helper.make_model(
        graph,
        producer_name="test",
        ir_version=9,
        opset_imports=[helper.make_operatorsetid("", 17)],
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def test_phase2_full_lifecycle(tmp_path: Path):
    """Verify complete Phase 2 lifecycle:

    1. Generate synthetic dataset with 82 classes.
    2. Run validate_dataset (assert no blocking errors).
    3. Run create_dataset_snapshot (assert immutable snapshot + data.yaml created).
    4. Package candidate model with ONNX and 82 classes manifest.
    5. Call ModelRegistry.promote_candidate: assert stage is 'production', class count is 82, backup created.
    6. Analyze an image with AnalysisService: assert inference uses promoted model and returns Vietnamese labels.
    7. Call ModelRegistry.rollback_to_backup: assert production restores to original baseline.
    """
    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    config = AppConfig.load(project_root=tmp_path)

    # 0. Setup initial baseline production model (2 classes)
    baseline_onnx = tmp_path / "baseline_model.onnx"
    _create_minimal_onnx(baseline_onnx)
    baseline_digest = sha256_file(baseline_onnx)

    baseline_manifest = ModelManifest(
        schema_version="1.0",
        model_id="baseline-v1-test",
        stage="production",
        source_model_id="yolo11n-baseline",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "car", 1: "sign"},
        imgsz=640,
        sha256=baseline_digest,
        source="test-init",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    registry = ModelRegistry(paths)
    registry.install_baseline(baseline_onnx, baseline_manifest)

    init_prod = registry.get_production()
    assert init_prod.manifest.model_id == "baseline-v1-test"
    assert len(init_prod.manifest.class_names) == 2

    # 1. Generate synthetic dataset with 82 classes
    dataset_dir = create_synthetic_dataset(tmp_path / "raw_dataset", num_samples=100)
    items = scan_yolo_dataset(dataset_dir)
    assert len(items) == 100

    # 2. Run validate_dataset (assert no blocking errors)
    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)
    assert report.is_valid
    assert not report.has_blocking
    assert len(report.blocking_errors) == 0

    # 3. Run create_dataset_snapshot
    snapshots_dir = tmp_path / "artifacts" / "snapshots"
    snapshot = create_dataset_snapshot(items, snapshots_dir, report)
    assert snapshot.data_yaml_path.is_file()
    assert (snapshot.snapshot_dir / "manifest.json").is_file()
    assert snapshot.manifest["total_images"] == 100

    # 4. Package candidate model with ONNX and 82 classes manifest
    run_id = "phase2_run_001"
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    weights_path = run_dir / "weights" / "best.pt"
    weights_path.parent.mkdir(parents=True, exist_ok=True)
    weights_path.write_bytes(b"dummy-weights-best")

    candidate_onnx = run_dir / "model.onnx"
    _create_minimal_onnx(candidate_onnx)

    onnx_result = ExportResult(
        onnx_path=candidate_onnx,
        max_abs_diff=0.0001,
        is_parity_valid=True,
        cpu_latency_ms=15.0,
        cpu_fps=66.7,
    )
    eval_metrics = EvaluationMetrics(
        precision=0.91,
        recall=0.87,
        f1=0.89,
        map50=0.90,
        map50_95=0.65,
    )
    class_names = {sc.id: sc.name_vi for sc in VIETNAM_TRAFFIC_SIGN_CATALOG}
    candidate_dir = package_candidate(
        run_id=run_id,
        weights_path=weights_path,
        onnx_result=onnx_result,
        eval_metrics=eval_metrics,
        class_names=class_names,
        runs_dir=tmp_path / "artifacts" / "runs",
    )
    assert (candidate_dir / "manifest.json").is_file()
    assert (candidate_dir / "model.onnx").is_file()

    # 5. Call ModelRegistry.promote_candidate
    promoted = registry.promote_candidate(candidate_dir)
    assert promoted.manifest.stage == "production"
    assert len(promoted.manifest.class_names) == 82
    assert promoted.manifest.model_id == f"trafficvision_{run_id}"

    # Verify backup was created
    backups = registry.list_backups()
    assert len(backups) == 1
    assert backups[0].model_id == "baseline-v1-test"

    # 6. Analyze an image with AnalysisService.analyze_image_upload
    repo = AnalysisRepository(paths.db)
    settings_store = RuntimeSettingsStore(paths.state / "settings.json", default_config=config)
    service = AnalysisService(
        config=config,
        registry=registry,
        repository=repo,
        settings_store=settings_store,
    )

    test_img = Image.new("RGB", (300, 300), color=(100, 150, 200))
    buf = io.BytesIO()
    test_img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    # Mock Ultralytics inference to output class 0 ("Cấm đi ngược chiều")
    box_mock = MagicMock()
    box_mock.xyxy = [MagicMock(cpu=lambda: MagicMock(tolist=lambda: [20.0, 30.0, 120.0, 150.0]))]
    box_mock.conf = [MagicMock(cpu=lambda: MagicMock(item=lambda: 0.94))]
    box_mock.cls = [MagicMock(cpu=lambda: MagicMock(item=lambda: 0))]

    fake_result = MagicMock()
    fake_result.boxes = [box_mock]
    fake_yolo = MagicMock()
    fake_yolo.return_value = [fake_result]

    with patch("ultralytics.YOLO", return_value=fake_yolo):
        artifacts = service.analyze_image_upload(filename="test_sign.jpg", data=img_bytes)

    assert artifacts.record.total_detections == 1
    assert "Cấm đi ngược chiều" in artifacts.record.class_counts
    assert artifacts.record.class_counts["Cấm đi ngược chiều"] == 1
    assert artifacts.record.model_id == f"trafficvision_{run_id}"

    # Verify CSV contains Vietnamese sign class label
    csv_text = artifacts.csv_path.read_text(encoding="utf-8-sig")
    assert "Cấm đi ngược chiều" in csv_text

    # 7. Call ModelRegistry.rollback_to_backup: assert production restores to original baseline
    restored = registry.rollback_to_backup()
    assert restored.manifest.model_id == "baseline-v1-test"
    assert len(restored.manifest.class_names) == 2
    assert restored.manifest.stage == "production"

    current_prod = registry.get_production()
    assert current_prod.manifest.model_id == "baseline-v1-test"
    assert len(current_prod.manifest.class_names) == 2


def test_cli_validate_dataset_script(tmp_path: Path):
    """Test scripts/validate_dataset.py CLI flags and exit codes."""
    script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "validate_dataset.py"
    assert script_path.is_file(), f"{script_path} should exist"

    # 1. Valid dataset test
    valid_dir = create_synthetic_dataset(tmp_path / "valid_data", num_samples=20)
    out_dir = tmp_path / "output_eda"

    cmd = [
        sys.executable,
        str(script_path),
        "--data-dir",
        str(valid_dir),
        "--output-dir",
        str(out_dir),
        "--create-snapshot",
        "--project-root",
        str(tmp_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Expected 0, stderr: {res.stderr}\nstdout: {res.stdout}"
    assert "VALID" in res.stdout or "Valid" in res.stdout
    assert (out_dir / "eda_report.json").is_file()

    # 2. Invalid dataset test (corrupt image)
    invalid_dir = create_synthetic_dataset(
        tmp_path / "invalid_data", num_samples=10, invalid_case="corrupt_image"
    )
    cmd_invalid = [
        sys.executable,
        str(script_path),
        "--data-dir",
        str(invalid_dir),
        "--project-root",
        str(tmp_path),
    ]
    res_inv = subprocess.run(cmd_invalid, capture_output=True, text=True)
    assert res_inv.returncode == 1
    assert "BLOCKING" in res_inv.stdout or "Error" in res_inv.stdout or "blocking" in res_inv.stderr


def test_cli_promote_model_script(tmp_path: Path):
    """Test scripts/promote_model.py CLI flags (--candidate-dir, --list-backups, --rollback)."""
    script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "promote_model.py"
    assert script_path.is_file(), f"{script_path} should exist"

    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    registry = ModelRegistry(paths)

    # Initial baseline model
    base_onnx = tmp_path / "base.onnx"
    _create_minimal_onnx(base_onnx)
    base_manifest = ModelManifest(
        schema_version="1.0",
        model_id="prod-baseline",
        stage="production",
        source_model_id="baseline",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "sign"},
        imgsz=640,
        sha256=sha256_file(base_onnx),
        source="test",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    registry.install_baseline(base_onnx, base_manifest)

    # Create candidate
    candidate_dir = tmp_path / "cand"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    cand_onnx = candidate_dir / "model.onnx"
    _create_minimal_onnx(cand_onnx)
    cand_manifest = ModelManifest(
        schema_version="1.0",
        model_id="cand-model-vn",
        stage="candidate",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={i: f"sign_{i}" for i in range(82)},
        imgsz=640,
        sha256=sha256_file(cand_onnx),
        source="test",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    (candidate_dir / "manifest.json").write_text(cand_manifest.model_dump_json())

    # 1. Promote candidate via CLI
    cmd_promote = [
        sys.executable,
        str(script_path),
        "--candidate-dir",
        str(candidate_dir),
        "--project-root",
        str(tmp_path),
    ]
    res_promote = subprocess.run(cmd_promote, capture_output=True, text=True)
    assert res_promote.returncode == 0, f"Promote failed: {res_promote.stderr}"
    assert registry.get_production().manifest.model_id == "cand-model-vn"

    # 2. List backups via CLI
    cmd_list = [
        sys.executable,
        str(script_path),
        "--list-backups",
        "--project-root",
        str(tmp_path),
    ]
    res_list = subprocess.run(cmd_list, capture_output=True, text=True)
    assert res_list.returncode == 0
    assert "prod-baseline" in res_list.stdout

    # 3. Rollback via CLI
    cmd_rollback = [
        sys.executable,
        str(script_path),
        "--rollback",
        "--project-root",
        str(tmp_path),
    ]
    res_rollback = subprocess.run(cmd_rollback, capture_output=True, text=True)
    assert res_rollback.returncode == 0, f"Rollback failed: {res_rollback.stderr}"
    assert registry.get_production().manifest.model_id == "prod-baseline"


def test_cli_train_script_help_and_execution(tmp_path: Path):
    """Test scripts/train.py CLI help and basic argument parsing/execution."""
    script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "train.py"
    assert script_path.is_file(), f"{script_path} should exist"

    # Test --help flag
    res_help = subprocess.run(
        [sys.executable, str(script_path), "--help"], capture_output=True, text=True
    )
    assert res_help.returncode == 0
    assert "--data-yaml" in res_help.stdout
    assert "--epochs" in res_help.stdout
    assert "--batch" in res_help.stdout
    assert "--imgsz" in res_help.stdout
    assert "--patience" in res_help.stdout
    assert "--amp" in res_help.stdout
    assert "--device" in res_help.stdout
    assert "--project-root" in res_help.stdout
    assert "--base-model" in res_help.stdout

    # Test missing data.yaml
    res_missing = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--data-yaml",
            str(tmp_path / "nonexistent.yaml"),
            "--project-root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert res_missing.returncode == 1
    assert "not found" in res_missing.stderr or "not found" in res_missing.stdout

    # Test invalid configuration (batch < 1)
    dummy_yaml = tmp_path / "data.yaml"
    dummy_yaml.write_text("names: ['a']\n", encoding="utf-8")
    res_inv = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--data-yaml",
            str(dummy_yaml),
            "--batch",
            "0",
            "--project-root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert res_inv.returncode == 1

    # Test --no-wait launch
    res_nowait = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--data-yaml",
            str(dummy_yaml),
            "--epochs",
            "1",
            "--no-wait",
            "--project-root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert res_nowait.returncode == 0
    assert "Training run launched" in res_nowait.stdout
