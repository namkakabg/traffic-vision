from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import onnx
import pytest
from onnx import TensorProto, helper

from trafficvision.config import AppPaths
from trafficvision.domain import ModelManifest
from trafficvision.registry import (
    BackupInfo,
    ModelIntegrityError,
    ModelNotFoundError,
    ModelPromotionError,
    ModelRegistry,
    ModelSecurityError,
    sha256_file,
)


@pytest.fixture
def test_paths(tmp_path: Path) -> AppPaths:
    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    return paths


def create_valid_onnx(path: Path) -> None:
    """Create a minimal, valid ONNX model file."""
    node = helper.make_node("Identity", ["X"], ["Y"])
    graph = helper.make_graph(
        [node],
        "test",
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


def create_candidate(
    candidate_dir: Path,
    *,
    num_classes: int = 82,
    corrupt_hash: bool = False,
    corrupt_onnx: bool = False,
    model_id: str = "candidate-model-82",
    missing_manifest: bool = False,
    missing_model: bool = False,
    custom_artifact_filename: str = "model.onnx",
) -> Path:
    candidate_dir.mkdir(parents=True, exist_ok=True)
    model_file = candidate_dir / custom_artifact_filename

    if not missing_model:
        if corrupt_onnx:
            model_file.write_bytes(b"corrupt-non-onnx-bytes-data")
        else:
            create_valid_onnx(model_file)

    if missing_manifest:
        return candidate_dir

    actual_hash = sha256_file(model_file) if model_file.is_file() else "0" * 64
    manifest_hash = "a" * 64 if corrupt_hash else actual_hash

    class_names = {i: f"traffic_sign_{i}" for i in range(num_classes)}
    manifest = ModelManifest(
        schema_version="1.0",
        model_id=model_id,
        stage="candidate",
        artifact_filename=custom_artifact_filename,
        backend="onnx",
        task="detect",
        class_names=class_names,
        imgsz=640,
        sha256=manifest_hash,
        source="runs/run_test",
        created_at=datetime.now(timezone.utc).isoformat(),
        metrics={"map50": 0.88, "f1": 0.85},
    )
    manifest_file = candidate_dir / "manifest.json"
    manifest_file.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return candidate_dir


def setup_initial_production(registry: ModelRegistry, tmp_path: Path, model_id: str = "baseline-test") -> None:
    model_src = tmp_path / f"{model_id}.onnx"
    create_valid_onnx(model_src)
    digest = sha256_file(model_src)
    manifest = ModelManifest(
        schema_version="1.0",
        model_id=model_id,
        stage="baseline",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "car", 1: "sign"},
        imgsz=640,
        sha256=digest,
        source="baseline-source",
        created_at="2026-09-27T10:00:00Z",
    )
    registry.install_baseline(model_src, manifest)


def test_promote_candidate_valid_creates_backup_and_sets_production(test_paths: AppPaths, tmp_path: Path):
    """Test valid candidate promotion creates automated backup of old prod and promotes candidate to 82 classes."""
    registry = ModelRegistry(test_paths)
    setup_initial_production(registry, tmp_path, model_id="baseline-v1")
    old_prod = registry.get_production()
    assert old_prod.manifest.model_id == "baseline-v1"

    candidate_dir = tmp_path / "runs" / "candidate"
    create_candidate(candidate_dir, num_classes=82, model_id="candidate-vn-82")

    promoted = registry.promote_candidate(candidate_dir)
    assert promoted.manifest.model_id == "candidate-vn-82"
    assert promoted.manifest.stage == "production"
    assert promoted.manifest.source_model_id == "candidate-vn-82"
    assert len(promoted.manifest.class_names) == 82
    assert promoted.model_path.is_file()
    assert promoted.manifest_path.is_file()

    # Verify current production via get_production
    current_prod = registry.get_production()
    assert current_prod.manifest.model_id == "candidate-vn-82"
    assert len(current_prod.manifest.class_names) == 82

    # Verify automated backup was created in artifacts/backups
    backups = registry.list_backups()
    assert len(backups) == 1
    backup = backups[0]
    assert isinstance(backup, BackupInfo)
    assert backup.model_id == "baseline-v1"
    assert backup.backup_dir.is_dir()
    assert (backup.backup_dir / "model.onnx").is_file()
    assert (backup.backup_dir / "manifest.json").is_file()
    assert backup.manifest.model_id == "baseline-v1"


def test_promote_candidate_when_no_prior_production(test_paths: AppPaths, tmp_path: Path):
    """Test candidate promotion succeeds without backup when no prior production model exists."""
    registry = ModelRegistry(test_paths)
    with pytest.raises(ModelNotFoundError):
        registry.get_production()

    candidate_dir = tmp_path / "candidate_first"
    create_candidate(candidate_dir, num_classes=82, model_id="initial-candidate")

    promoted = registry.promote_candidate(candidate_dir)
    assert promoted.manifest.model_id == "initial-candidate"
    assert promoted.manifest.stage == "production"
    assert len(promoted.manifest.class_names) == 82

    # No backup should have been made
    assert len(registry.list_backups()) == 0


def test_promote_candidate_rejects_missing_manifest_or_model(test_paths: AppPaths, tmp_path: Path):
    """Test candidate promotion rejected if manifest.json or model.onnx is missing."""
    registry = ModelRegistry(test_paths)

    # Missing candidate directory completely
    with pytest.raises(ModelNotFoundError):
        registry.promote_candidate(tmp_path / "nonexistent")

    # Missing manifest.json
    cand1 = tmp_path / "cand_no_manifest"
    create_candidate(cand1, missing_manifest=True)
    with pytest.raises(ModelNotFoundError):
        registry.promote_candidate(cand1)

    # Missing model.onnx
    cand2 = tmp_path / "cand_no_model"
    create_candidate(cand2, missing_model=True)
    with pytest.raises(ModelNotFoundError):
        registry.promote_candidate(cand2)


def test_promote_candidate_rejects_corrupted_checksum(test_paths: AppPaths, tmp_path: Path):
    """Test candidate promotion rejected when checksum in manifest does not match actual file."""
    registry = ModelRegistry(test_paths)
    setup_initial_production(registry, tmp_path, model_id="baseline-prod")

    candidate_dir = tmp_path / "cand_bad_sha"
    create_candidate(candidate_dir, corrupt_hash=True, model_id="bad-sha-cand")

    with pytest.raises(ModelIntegrityError):
        registry.promote_candidate(candidate_dir)

    # Production remains baseline-prod and untouched
    prod = registry.get_production()
    assert prod.manifest.model_id == "baseline-prod"
    assert len(registry.list_backups()) == 0


def test_promote_candidate_rejects_wrong_class_count(test_paths: AppPaths, tmp_path: Path):
    """Test candidate promotion rejected when number of classes is not exactly 82."""
    registry = ModelRegistry(test_paths)
    setup_initial_production(registry, tmp_path, model_id="baseline-prod")

    # 80 classes instead of 82
    cand_80 = tmp_path / "cand_80"
    create_candidate(cand_80, num_classes=80, model_id="cand-80")
    with pytest.raises(ModelPromotionError):
        registry.promote_candidate(cand_80)

    # 1 class instead of 82
    cand_1 = tmp_path / "cand_1"
    create_candidate(cand_1, num_classes=1, model_id="cand-1")
    with pytest.raises(ModelPromotionError):
        registry.promote_candidate(cand_1)

    # Production remains baseline-prod
    prod = registry.get_production()
    assert prod.manifest.model_id == "baseline-prod"
    assert len(registry.list_backups()) == 0


def test_promote_candidate_rejects_corrupt_onnx_smoke_test(test_paths: AppPaths, tmp_path: Path):
    """Test candidate promotion rejected when ONNX smoke test fails despite matching checksum."""
    registry = ModelRegistry(test_paths)
    setup_initial_production(registry, tmp_path, model_id="baseline-prod")

    candidate_dir = tmp_path / "cand_corrupt_onnx"
    create_candidate(candidate_dir, corrupt_onnx=True, model_id="corrupt-onnx-cand")

    with pytest.raises(ModelIntegrityError):
        registry.promote_candidate(candidate_dir)

    # Production remains baseline-prod
    prod = registry.get_production()
    assert prod.manifest.model_id == "baseline-prod"
    assert len(registry.list_backups()) == 0


def test_promote_candidate_atomic_rollback_on_post_verification_failure(test_paths: AppPaths, tmp_path: Path):
    """Test that if an error occurs after backup during promotion, production is automatically rolled back."""
    registry = ModelRegistry(test_paths)
    setup_initial_production(registry, tmp_path, model_id="orig-prod")
    original_prod = registry.get_production()
    assert original_prod.manifest.model_id == "orig-prod"

    candidate_dir = tmp_path / "cand_verify_fail"
    create_candidate(candidate_dir, num_classes=82, model_id="failing-candidate")

    # Mock verify to fail when verifying candidate production model
    orig_verify = registry.verify
    calls = []

    def mock_verify(model):
        calls.append(model.manifest.model_id)
        if model.manifest.model_id == "failing-candidate":
            raise ModelIntegrityError("Simulated post-promotion verification failure")
        return orig_verify(model)

    with patch.object(registry, "verify", side_effect=mock_verify):
        with pytest.raises(ModelIntegrityError):
            registry.promote_candidate(candidate_dir)

    # Production model must be restored to original "orig-prod"
    restored_prod = registry.get_production()
    assert restored_prod.manifest.model_id == "orig-prod"


def test_promote_candidate_path_traversal_rejection(test_paths: AppPaths, tmp_path: Path):
    """Test candidate promotion rejects path traversal in artifact_filename."""
    registry = ModelRegistry(test_paths)
    candidate_dir = tmp_path / "cand_traversal"
    create_candidate(
        candidate_dir,
        num_classes=82,
        custom_artifact_filename="../escaped.onnx",
    )

    with pytest.raises(ModelSecurityError):
        registry.promote_candidate(candidate_dir)


def test_manual_rollback_to_backup_latest_and_by_id(test_paths: AppPaths, tmp_path: Path):
    """Test manual rollback to latest backup or specific backup ID."""
    registry = ModelRegistry(test_paths)
    setup_initial_production(registry, tmp_path, model_id="model-A")

    # Promote model B
    cand_b = tmp_path / "cand_b"
    create_candidate(cand_b, num_classes=82, model_id="model-B")
    registry.promote_candidate(cand_b)
    assert registry.get_production().manifest.model_id == "model-B"

    # Promote model C
    cand_c = tmp_path / "cand_c"
    create_candidate(cand_c, num_classes=82, model_id="model-C")
    registry.promote_candidate(cand_c)
    assert registry.get_production().manifest.model_id == "model-C"

    # We now have 2 backups: model-B and model-A
    backups = registry.list_backups()
    assert len(backups) == 2
    assert backups[0].model_id == "model-B"
    assert backups[1].model_id == "model-A"

    backup_id_a = backups[1].backup_id
    backup_id_b = backups[0].backup_id
    assert backup_id_b == backups[0].backup_id

    # 1. Rollback to default (latest backup = model-B)
    restored = registry.rollback_to_backup()
    assert restored.manifest.model_id == "model-B"
    assert restored.manifest.stage == "production"
    assert registry.get_production().manifest.model_id == "model-B"

    # 2. Rollback to specific backup (model-A)
    restored_a = registry.rollback_to_backup(backup_id_a)
    assert restored_a.manifest.model_id == "model-A"
    assert restored_a.manifest.stage == "production"
    assert registry.get_production().manifest.model_id == "model-A"


def test_rollback_to_backup_error_cases(test_paths: AppPaths, tmp_path: Path):
    """Test rollback error handling for empty backups, unknown backup_id, and corrupted backup file."""
    registry = ModelRegistry(test_paths)

    # No backups exist
    with pytest.raises(ModelNotFoundError):
        registry.rollback_to_backup()

    # Specific backup does not exist
    with pytest.raises(ModelNotFoundError):
        registry.rollback_to_backup("nonexistent_backup_id")

    # Corrupted backup model
    setup_initial_production(registry, tmp_path, model_id="model-to-backup")
    cand = tmp_path / "cand"
    create_candidate(cand, num_classes=82, model_id="model-new")
    registry.promote_candidate(cand)

    backups = registry.list_backups()
    assert len(backups) == 1
    backup_file = backups[0].backup_dir / backups[0].manifest.artifact_filename
    # Corrupt the backed up model file
    backup_file.write_bytes(b"tampered-backup-file-bytes")

    with pytest.raises(ModelIntegrityError):
        registry.rollback_to_backup(backups[0].backup_id)


def test_list_backups_sorted_descending(test_paths: AppPaths, tmp_path: Path):
    """Test list_backups correctly parses directories and sorts by timestamp descending."""
    registry = ModelRegistry(test_paths)
    backups_dir = test_paths.backups

    for ts, m_id in [
        ("20260928_100000", "model-old"),
        ("20260929_150000", "model-newest"),
        ("20260929_120000", "model-middle"),
    ]:
        b_dir = backups_dir / f"{ts}_{m_id}"
        b_dir.mkdir(parents=True)
        m = ModelManifest(
            schema_version="1.0",
            model_id=m_id,
            stage="backup",
            artifact_filename="model.onnx",
            backend="onnx",
            task="detect",
            class_names={0: "c0"},
            imgsz=640,
            sha256="0" * 64,
            source="test",
            created_at=ts,
        )
        (b_dir / "manifest.json").write_text(m.model_dump_json(), encoding="utf-8")

    backups = registry.list_backups()
    assert len(backups) == 3
    assert [b.model_id for b in backups] == ["model-newest", "model-middle", "model-old"]
    assert [b.timestamp for b in backups] == ["20260929_150000", "20260929_120000", "20260928_100000"]
