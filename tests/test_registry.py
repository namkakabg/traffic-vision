from pathlib import Path

import pytest

from trafficvision.config import AppPaths
from trafficvision.domain import ModelManifest
from trafficvision.registry import (
    ModelIntegrityError,
    ModelNotFoundError,
    ModelRegistry,
    ModelSecurityError,
    sha256_file,
)


@pytest.fixture
def test_paths(tmp_path: Path) -> AppPaths:
    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    return paths


def test_sha256_file(tmp_path: Path):
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"hello trafficvision")
    expected = "b463d592d7139f7a8a86beb8a2b4068dcf5f968ac754637c2356d2b031232321"
    assert sha256_file(sample) == expected


def test_atomic_install_baseline_and_production_resolution(test_paths: AppPaths, tmp_path: Path):
    registry = ModelRegistry(test_paths)

    # Initially no production model
    with pytest.raises(ModelNotFoundError):
        registry.get_production()

    model_src = tmp_path / "yolo11n.onnx"
    model_bytes = b"fake-onnx-bytes-for-testing"
    model_src.write_bytes(model_bytes)
    digest = sha256_file(model_src)

    manifest = ModelManifest(
        schema_version="1.0",
        model_id="yolo11n-baseline-test",
        stage="baseline",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "car", 1: "sign"},
        imgsz=640,
        sha256=digest,
        source="test-source",
        created_at="2026-09-27T21:00:00Z",
    )

    registered = registry.install_baseline(model_src, manifest)
    assert registered.manifest.model_id == "yolo11n-baseline-test"
    assert registered.model_path.exists()
    assert registered.manifest_path.exists()

    # Verify baseline directory exists
    baseline_dir = test_paths.baseline / "yolo11n-baseline-test"
    assert (baseline_dir / "model.onnx").is_file()
    assert (baseline_dir / "manifest.json").is_file()

    # Verify production model
    prod = registry.get_production()
    assert prod.manifest.stage == "production"
    assert prod.manifest.source_model_id == "yolo11n-baseline-test"
    assert prod.manifest.sha256 == digest
    assert prod.model_path.is_file()
    assert prod.manifest_path.is_file()


def test_registry_verifies_checksum_and_catches_tampering(test_paths: AppPaths, tmp_path: Path):
    registry = ModelRegistry(test_paths)
    model_src = tmp_path / "valid.onnx"
    model_src.write_bytes(b"initial-valid-content")
    digest = sha256_file(model_src)

    manifest = ModelManifest(
        schema_version="1.0",
        model_id="tamper-test",
        stage="baseline",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "c0"},
        imgsz=640,
        sha256=digest,
        source="unit-test",
        created_at="2026-09-27T21:00:00Z",
    )
    registry.install_baseline(model_src, manifest)
    prod = registry.get_production()
    registry.verify(prod)  # passes

    # Tamper with 1 byte of the production ONNX file
    prod.model_path.write_bytes(b"corrupt-valid-content")

    # verify() must raise ModelIntegrityError
    with pytest.raises(ModelIntegrityError):
        registry.verify(prod)

    # get_production() must also fail with ModelIntegrityError before returning
    with pytest.raises(ModelIntegrityError):
        registry.get_production()


def test_registry_rejects_path_traversal_in_manifest(test_paths: AppPaths, tmp_path: Path):
    registry = ModelRegistry(test_paths)
    # Write a malicious manifest pointing outside production
    prod_manifest = test_paths.production / "manifest.json"
    prod_manifest.write_text(
        """{
        "schema_version": "1.0",
        "model_id": "malicious",
        "stage": "production",
        "artifact_filename": "../../../etc/passwd",
        "backend": "onnx",
        "task": "detect",
        "class_names": {"0": "c0"},
        "imgsz": 640,
        "sha256": "%s",
        "source": "evil",
        "created_at": "2026-09-27T21:00:00Z"
    }"""
        % ("0" * 64)
    )

    with pytest.raises(ModelSecurityError):
        registry.get_production()


def test_rollback_empty_or_whitespace_backup_id_raises(test_paths: AppPaths):
    registry = ModelRegistry(test_paths)
    with pytest.raises(ModelNotFoundError, match="empty or whitespace"):
        registry.rollback_to_backup("")

    with pytest.raises(ModelNotFoundError, match="empty or whitespace"):
        registry.rollback_to_backup("   \t  ")


def test_promote_candidate_logs_critical_when_rollback_fails(
    test_paths: AppPaths, tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
):
    import logging

    registry = ModelRegistry(test_paths)

    # 1. Setup existing production model so a backup is created during promotion
    model_src = tmp_path / "baseline.onnx"
    model_src.write_bytes(b"baseline-onnx-bytes")
    manifest = ModelManifest(
        schema_version="1.0",
        model_id="base-001",
        stage="baseline",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={i: f"c{i}" for i in range(82)},
        imgsz=640,
        sha256=sha256_file(model_src),
        source="test",
        created_at="2026-09-27T21:00:00Z",
    )
    registry.install_baseline(model_src, manifest)

    # 2. Setup candidate dir with valid ONNX structure
    cand_dir = tmp_path / "candidate"
    cand_dir.mkdir(parents=True)
    cand_model = cand_dir / "model.onnx"
    cand_model.write_bytes(b"cand-onnx-bytes")
    cand_manifest = ModelManifest(
        schema_version="1.0",
        model_id="cand-001",
        stage="candidate",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={i: f"c{i}" for i in range(82)},
        imgsz=640,
        sha256=sha256_file(cand_model),
        source="test",
        created_at="2026-09-27T21:00:00Z",
    )
    (cand_dir / "manifest.json").write_text(cand_manifest.model_dump_json(), encoding="utf-8")

    # Mock onnx checker to pass
    monkeypatch.setattr("onnx.checker.check_model", lambda path: None)

    # Force verification of newly promoted model to fail, triggering rollback
    def _fail_verify(self, model):
        raise ModelIntegrityError("Simulated post-promotion failure")

    # Force rollback to fail
    def _fail_restore(self, backup_dir):
        raise RuntimeError("Simulated rollback disk error")

    monkeypatch.setattr(ModelRegistry, "verify", _fail_verify)
    monkeypatch.setattr(ModelRegistry, "_restore_from_backup_dir", _fail_restore)

    with caplog.at_level(logging.CRITICAL):
        with pytest.raises(ModelIntegrityError, match="Simulated post-promotion failure"):
            registry.promote_candidate(cand_dir)

    assert "Failed to rollback to backup" in caplog.text

