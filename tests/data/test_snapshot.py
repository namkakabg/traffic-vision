"""Unit tests for immutable dataset snapshot creation."""

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from tests.fixtures.dataset_fixture import create_synthetic_dataset
from trafficvision.data.catalog import VIETNAM_TRAFFIC_SIGN_CATALOG, get_class_names
from trafficvision.data.dataset import scan_yolo_dataset
from trafficvision.data.snapshot import DatasetSnapshot, create_dataset_snapshot
from trafficvision.data.validator import (
    validate_dataset,
)


def _compute_sha256(path: Path) -> str:
    """Compute sha256 hex digest for a file."""
    hasher = hashlib.sha256()
    hasher.update(path.read_bytes())
    return hasher.hexdigest()


def test_snapshot_refuses_blocking_errors(tmp_path: Path) -> None:
    """create_dataset_snapshot must raise ValueError when validation report has blocking errors."""
    data_dir = create_synthetic_dataset(
        tmp_path / "corrupt_data", num_samples=4, invalid_case="corrupt_image"
    )
    items = scan_yolo_dataset(data_dir)
    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is True

    output_dir = tmp_path / "snapshots"
    with pytest.raises(ValueError, match="blocking error"):
        create_dataset_snapshot(items, output_dir, report)

    # Ensure no snapshot directory was created
    assert not output_dir.exists() or len(list(output_dir.iterdir())) == 0


def test_snapshot_creation_success(tmp_path: Path) -> None:
    """Valid dataset should create an immutable snapshot with data.yaml, manifest, and split files."""
    data_dir = create_synthetic_dataset(tmp_path / "clean_data", num_samples=6)
    items = scan_yolo_dataset(data_dir)
    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is False

    output_dir = tmp_path / "snapshots"
    snapshot = create_dataset_snapshot(items, output_dir, report, seed=42)

    assert isinstance(snapshot, DatasetSnapshot)
    assert snapshot.snapshot_dir.is_dir()
    assert snapshot.snapshot_dir.parent == output_dir.resolve()
    assert snapshot.data_yaml_path.is_file()
    assert snapshot.data_yaml_path == snapshot.snapshot_dir / "data.yaml"

    # Verify split directories and copied items
    for split in ["train", "val", "test"]:
        img_dir = snapshot.snapshot_dir / split / "images"
        lbl_dir = snapshot.snapshot_dir / split / "labels"
        assert img_dir.is_dir()
        assert lbl_dir.is_dir()
        assert len(list(img_dir.glob("*.png"))) > 0
        assert len(list(lbl_dir.glob("*.txt"))) > 0

    # Verify data.yaml content
    with open(snapshot.data_yaml_path, encoding="utf-8") as f:
        yaml_content = yaml.safe_load(f)

    assert "path" in yaml_content
    assert Path(yaml_content["path"]).resolve() == snapshot.snapshot_dir.resolve()
    assert yaml_content["train"] == "train/images"
    assert yaml_content["val"] == "val/images"
    assert yaml_content["test"] == "test/images"
    assert "names" in yaml_content

    # Verify 82 Vietnamese class names in data.yaml
    expected_names = get_class_names()
    assert len(yaml_content["names"]) == 82
    if isinstance(yaml_content["names"], dict):
        for idx, name in enumerate(expected_names):
            assert yaml_content["names"][idx] == name
    else:
        assert yaml_content["names"] == expected_names

    # Verify manifest.json exists and contains correct file checksums
    manifest_path = snapshot.snapshot_dir / "manifest.json"
    assert manifest_path.is_file()

    with open(manifest_path, encoding="utf-8") as f:
        manifest_data = json.load(f)

    assert manifest_data["snapshot_id"] == snapshot.snapshot_id
    assert manifest_data["total_files"] > 0
    assert "files" in manifest_data

    # Verify checksums of every recorded file match disk
    for rel_path_str, expected_hash in manifest_data["files"].items():
        actual_file = snapshot.snapshot_dir / rel_path_str
        assert actual_file.is_file(), f"Manifest lists {rel_path_str} but it doesn't exist"
        assert _compute_sha256(actual_file) == expected_hash

    # Verify snapshot.manifest dict matches manifest.json
    assert snapshot.manifest["snapshot_id"] == snapshot.snapshot_id
    assert snapshot.manifest["files"] == manifest_data["files"]


def test_snapshot_creation_with_warnings_allowed(tmp_path: Path) -> None:
    """Snapshot creation succeeds when validation report contains non-blocking warnings."""
    data_dir = create_synthetic_dataset(
        tmp_path / "imbalanced_data", num_samples=25, invalid_case="imbalance"
    )
    items = scan_yolo_dataset(data_dir)
    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is False
    assert len(report.warnings) > 0

    output_dir = tmp_path / "snapshots"
    snapshot = create_dataset_snapshot(items, output_dir, report)

    assert snapshot.snapshot_dir.is_dir()
    assert (snapshot.snapshot_dir / "data.yaml").is_file()
    assert (snapshot.snapshot_dir / "manifest.json").is_file()


def test_snapshot_custom_snapshot_id(tmp_path: Path) -> None:
    """create_dataset_snapshot accepts an explicit snapshot_id."""
    data_dir = create_synthetic_dataset(tmp_path / "clean_data", num_samples=3)
    items = scan_yolo_dataset(data_dir)
    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    output_dir = tmp_path / "snapshots"
    snapshot = create_dataset_snapshot(
        items, output_dir, report, snapshot_id="snapshot_custom_001"
    )

    assert snapshot.snapshot_id == "snapshot_custom_001"
    assert snapshot.snapshot_dir.name == "snapshot_custom_001"
    assert snapshot.snapshot_dir.is_dir()
