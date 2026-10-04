"""YOLO dataset scanning, indexing, and summarization."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from trafficvision.config import AppPaths

VALID_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff",
    ".heic",
    ".heif",
}


@dataclass(frozen=True)
class DatasetItem:
    """Represents a single image-label pair in a YOLO dataset."""

    image_path: Path
    label_path: Path | None
    split: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "image_path", Path(self.image_path))
        if self.label_path is not None:
            object.__setattr__(self, "label_path", Path(self.label_path))


@dataclass(frozen=True)
class DatasetSummary:
    """Statistical summary of a scanned dataset."""

    total_images: int
    split_counts: dict[str, int] = field(default_factory=dict)
    classes_present: set[int] = field(default_factory=set)


def scan_yolo_dataset(root_dir: AppPaths | Path | str) -> list[DatasetItem]:
    """Scan a directory for YOLO-format dataset splits and image-label pairs.

    Supports both standard split-grouped structure (`<split>/images/`, `<split>/labels/`)
    and type-grouped structure (`images/<split>/`, `labels/<split>/`).

    Args:
        root_dir: Root dataset directory path or AppPaths instance (uses staging).

    Returns:
        List of DatasetItem entries sorted deterministically.

    Raises:
        FileNotFoundError: If root_dir does not exist.
    """
    if isinstance(root_dir, AppPaths):
        root = root_dir.staging.resolve()
    else:
        root = Path(root_dir).resolve()

    if not root.exists():
        raise FileNotFoundError(f"Dataset root directory does not exist: {root}")

    items: list[DatasetItem] = []
    scanned_splits: set[tuple[Path, str]] = set()

    # Case A: Structure grouped by split (<root>/<split>/images/)
    for split_dir in sorted(root.iterdir()):
        if split_dir.is_dir() and not split_dir.name.startswith("."):
            images_dir = split_dir / "images"
            if images_dir.is_dir():
                labels_dir = split_dir / "labels"
                scanned_splits.add((images_dir, split_dir.name))
                _scan_split_directory(images_dir, labels_dir, split_dir.name, items)

    # Case B: Structure grouped by type (<root>/images/<split>/)
    root_images = root / "images"
    if root_images.is_dir():
        for split_dir in sorted(root_images.iterdir()):
            if split_dir.is_dir() and not split_dir.name.startswith("."):
                if (split_dir, split_dir.name) not in scanned_splits:
                    labels_dir = root / "labels" / split_dir.name
                    scanned_splits.add((split_dir, split_dir.name))
                    _scan_split_directory(split_dir, labels_dir, split_dir.name, items)

    # Sort deterministically by split, then image filename
    items.sort(key=lambda it: (it.split, it.image_path.name))
    return items


def _scan_split_directory(
    images_dir: Path,
    labels_dir: Path,
    split_name: str,
    items: list[DatasetItem],
) -> None:
    """Helper to scan image files in a split directory and associate labels."""
    has_labels_dir = labels_dir.is_dir()

    for file_path in sorted(images_dir.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in VALID_IMAGE_EXTENSIONS:
            label_path: Path | None = None
            if has_labels_dir:
                candidate = labels_dir / f"{file_path.stem}.txt"
                if candidate.is_file():
                    label_path = candidate

            items.append(
                DatasetItem(
                    image_path=file_path,
                    label_path=label_path,
                    split=split_name,
                )
            )


def summarize_dataset(items: list[DatasetItem]) -> DatasetSummary:
    """Compute summary statistics for a collection of DatasetItem instances.

    Args:
        items: List of scanned DatasetItem entries.

    Returns:
        DatasetSummary with total image count, split distribution, and classes present.
    """
    split_counts: dict[str, int] = {}
    classes_present: set[int] = set()

    for item in items:
        split_counts[item.split] = split_counts.get(item.split, 0) + 1

        if item.label_path and item.label_path.is_file():
            try:
                content = item.label_path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    parts = stripped.split()
                    if parts:
                        classes_present.add(int(parts[0]))
            except (ValueError, OSError):
                continue

    return DatasetSummary(
        total_images=len(items),
        split_counts=split_counts,
        classes_present=classes_present,
    )
