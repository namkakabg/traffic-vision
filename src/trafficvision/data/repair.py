"""Conservative repairs for known defects in imported YOLO datasets."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

from trafficvision.data.dataset import DatasetItem, scan_yolo_dataset


@dataclass(frozen=True)
class DatasetRepairReport:
    """A record of changes made while preparing a dataset for validation."""

    normalized_label_lines: int
    quarantined_images: int
    manifest_path: Path


_SPLIT_PRIORITY = {"test": 0, "val": 1, "train": 2}


def repair_yolo_dataset(root_dir: Path | str) -> DatasetRepairReport:
    """Repair only documented, deterministic dataset defects.

    A six-field row is normalized only when its second field is exactly ``0``
    and dropping it produces a valid YOLO ``class x y w h`` row. Duplicate
    image bytes are moved (never deleted) to ``.quarantine``. To protect
    independent evaluation, the retained split priority is ``test``, then
    ``val``, then ``train``.
    """
    root = Path(root_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Dataset root directory does not exist: {root}")

    quarantine = root / ".quarantine"
    label_backups = quarantine / "label-backups"
    normalized_label_lines = _normalize_known_extra_zero_labels(root, label_backups)
    quarantined = _quarantine_cross_split_duplicates(root, quarantine)

    manifest_path = quarantine / "repair-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "policy": {
            "label_normalization": "drop a second zero only when the remaining five fields are valid YOLO",
            "split_retention_priority": ["test", "val", "train"],
            "quarantine": "moved, not deleted",
        },
        "normalized_label_lines": normalized_label_lines,
        "quarantined": quarantined,
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    return DatasetRepairReport(
        normalized_label_lines=normalized_label_lines,
        quarantined_images=len(quarantined),
        manifest_path=manifest_path,
    )


def _normalize_known_extra_zero_labels(root: Path, label_backups: Path) -> int:
    normalized_lines = 0
    for split_dir in sorted(root.iterdir()):
        if not split_dir.is_dir() or split_dir.name.startswith("."):
            continue
        labels_dir = split_dir / "labels"
        if not labels_dir.is_dir():
            continue

        for label_path in sorted(labels_dir.glob("*.txt")):
            original = label_path.read_text(encoding="utf-8")
            rewritten: list[str] = []
            changed = False
            for line in original.splitlines():
                parts = line.split()
                if _is_known_extra_zero_line(parts):
                    rewritten.append(" ".join([parts[0], *parts[2:]]))
                    normalized_lines += 1
                    changed = True
                else:
                    rewritten.append(line)

            if changed:
                backup_path = label_backups / label_path.relative_to(root)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path.write_text(original, encoding="utf-8")
                suffix = "\n" if original.endswith("\n") else ""
                label_path.write_text("\n".join(rewritten) + suffix, encoding="utf-8")
    return normalized_lines


def _is_known_extra_zero_line(parts: list[str]) -> bool:
    if len(parts) != 6 or parts[1] != "0":
        return False
    try:
        class_id = int(parts[0])
        x_center, y_center, width, height = (float(value) for value in parts[2:])
    except ValueError:
        return False
    return (
        class_id >= 0
        and all(math.isfinite(value) for value in (x_center, y_center, width, height))
        and 0 <= x_center <= 1
        and 0 <= y_center <= 1
        and 0 < width <= 1
        and 0 < height <= 1
    )


def _quarantine_cross_split_duplicates(root: Path, quarantine: Path) -> list[dict[str, str]]:
    by_hash: dict[str, list[DatasetItem]] = {}
    for item in scan_yolo_dataset(root):
        image_hash = hashlib.sha256(item.image_path.read_bytes()).hexdigest()
        by_hash.setdefault(image_hash, []).append(item)

    quarantined: list[dict[str, str]] = []
    for image_hash, items in sorted(by_hash.items()):
        if len({item.split for item in items}) < 2:
            continue

        ordered_items = sorted(
            items,
            key=lambda item: (_SPLIT_PRIORITY.get(item.split, len(_SPLIT_PRIORITY)), str(item.image_path)),
        )
        kept = ordered_items[0]
        for item in ordered_items[1:]:
            image_destination = quarantine / item.image_path.relative_to(root)
            _move_to_quarantine(item.image_path, image_destination)
            if item.label_path is not None and item.label_path.is_file():
                label_destination = quarantine / item.label_path.relative_to(root)
                _move_to_quarantine(item.label_path, label_destination)
            quarantined.append(
                {
                    "sha256": image_hash,
                    "kept_image": str(kept.image_path.relative_to(root)),
                    "quarantined_image": str(item.image_path.relative_to(root)),
                }
            )
    return quarantined


def _move_to_quarantine(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing quarantine file: {destination}")
    shutil.move(str(source), str(destination))
