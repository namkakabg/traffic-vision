"""Immutable dataset snapshot generator for Ultralytics YOLO training."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from trafficvision.data.catalog import VIETNAM_TRAFFIC_SIGN_CATALOG
from trafficvision.data.dataset import DatasetItem
from trafficvision.data.validator import ValidationReport


@dataclass(frozen=True)
class DatasetSnapshot:
    """Represents an immutable, validated dataset snapshot ready for training."""

    snapshot_id: str
    snapshot_dir: Path
    data_yaml_path: Path
    manifest: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_dir", Path(self.snapshot_dir))
        object.__setattr__(self, "data_yaml_path", Path(self.data_yaml_path))


def create_dataset_snapshot(
    items: list[DatasetItem],
    output_dir: Path | str,
    validation_report: ValidationReport,
    seed: int = 42,
    snapshot_id: str | None = None,
) -> DatasetSnapshot:
    """Create an immutable snapshot of validated dataset items.

    Refuses creation if the validation report contains blocking errors.
    Organizes images and labels by split, generates a YOLO `data.yaml` configuration
    with 82 Vietnamese sign classes, and saves a cryptographically hashed `manifest.json`.

    Args:
        items: List of validated DatasetItem instances to snapshot.
        output_dir: Directory where the snapshot folder will be created.
        validation_report: ValidationReport verifying dataset quality.
        seed: Random seed or configuration version integer.
        snapshot_id: Optional custom snapshot identifier. If None, auto-generated
            using UTC timestamp (e.g. 'snapshot_20260929_063000').

    Returns:
        DatasetSnapshot with paths to root folder, data.yaml, and manifest metadata.

    Raises:
        ValueError: If validation_report.has_blocking is True.
    """
    if validation_report.has_blocking:
        error_count = len(validation_report.blocking_errors)
        error_codes = {err.code for err in validation_report.blocking_errors}
        raise ValueError(
            f"Cannot create snapshot: validation report contains {error_count} "
            f"blocking error(s) ({', '.join(sorted(error_codes))})."
        )

    if snapshot_id is None:
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        snapshot_id = f"snapshot_{timestamp_str}"

    base_out = Path(output_dir).resolve()
    snapshot_dir = (base_out / snapshot_id).resolve()
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    files_to_hash: list[Path] = []

    # 1. Copy images and labels into split directories
    for item in items:
        split_img_dir = snapshot_dir / item.split / "images"
        split_lbl_dir = snapshot_dir / item.split / "labels"
        split_img_dir.mkdir(parents=True, exist_ok=True)
        split_lbl_dir.mkdir(parents=True, exist_ok=True)

        dest_img = split_img_dir / item.image_path.name
        shutil.copy2(item.image_path, dest_img)
        files_to_hash.append(dest_img)

        if item.label_path and item.label_path.is_file():
            dest_lbl = split_lbl_dir / item.label_path.name
            shutil.copy2(item.label_path, dest_lbl)
            files_to_hash.append(dest_lbl)

    # 2. Generate data.yaml configuration
    splits_present = {item.split for item in items}
    data_yaml_path = snapshot_dir / "data.yaml"

    yaml_dict: dict[str, Any] = {
        "path": str(snapshot_dir),
    }

    if "train" in splits_present:
        yaml_dict["train"] = "train/images"
    if "val" in splits_present:
        yaml_dict["val"] = "val/images"
    if "test" in splits_present:
        yaml_dict["test"] = "test/images"

    yaml_dict["nc"] = len(VIETNAM_TRAFFIC_SIGN_CATALOG)
    yaml_dict["names"] = {sc.id: sc.name_vi for sc in VIETNAM_TRAFFIC_SIGN_CATALOG}

    with open(data_yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(yaml_dict, f, allow_unicode=True, sort_keys=False)

    files_to_hash.append(data_yaml_path)

    # 3. Compute SHA-256 for all files to generate manifest
    manifest_files: dict[str, str] = {}
    for file_path in sorted(files_to_hash):
        rel_posix = file_path.relative_to(snapshot_dir).as_posix()
        hasher = hashlib.sha256()
        hasher.update(file_path.read_bytes())
        manifest_files[rel_posix] = hasher.hexdigest()

    manifest: dict[str, Any] = {
        "snapshot_id": snapshot_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "total_files": len(manifest_files),
        "total_images": len(items),
        "total_labels": validation_report.total_labels,
        "files": manifest_files,
        "checksums": manifest_files,
    }

    # Write manifest.json and snapshot_manifest.json
    manifest_json_path = snapshot_dir / "manifest.json"
    manifest_json_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (snapshot_dir / "snapshot_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return DatasetSnapshot(
        snapshot_id=snapshot_id,
        snapshot_dir=snapshot_dir,
        data_yaml_path=data_yaml_path,
        manifest=manifest,
    )
