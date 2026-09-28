"""Unit tests for YOLO dataset scanning, indexing, and synthetic fixtures."""

from pathlib import Path

import pytest
from PIL import Image

from tests.fixtures.dataset_fixture import create_synthetic_dataset
from trafficvision.data.dataset import (
    DatasetItem,
    DatasetSummary,
    scan_yolo_dataset,
    summarize_dataset,
)


def test_create_synthetic_dataset_structure(tmp_path: Path) -> None:
    """Synthetic dataset generator should build train, val, and test splits with images and labels."""
    dataset_dir = create_synthetic_dataset(tmp_path / "synthetic", num_samples=6)
    assert dataset_dir.is_dir()

    for split in ["train", "val", "test"]:
        images_dir = dataset_dir / split / "images"
        labels_dir = dataset_dir / split / "labels"
        assert images_dir.is_dir()
        assert labels_dir.is_dir()

        images = list(images_dir.glob("*.png"))
        assert len(images) > 0

        for img_path in images:
            with Image.open(img_path) as img:
                assert img.size == (32, 32)

            lbl_path = labels_dir / f"{img_path.stem}.txt"
            assert lbl_path.is_file()
            lines = lbl_path.read_text(encoding="utf-8").strip().splitlines()
            assert len(lines) > 0
            for line in lines:
                parts = line.strip().split()
                assert len(parts) == 5
                cls_id = int(parts[0])
                assert 0 <= cls_id < 82
                box = [float(p) for p in parts[1:]]
                for coord in box:
                    assert 0.0 <= coord <= 1.0


def test_scan_yolo_dataset_structure_a(tmp_path: Path) -> None:
    """scan_yolo_dataset handles grouped structure <split>/images/ and <split>/labels/."""
    dataset_dir = create_synthetic_dataset(tmp_path / "dataset_a", num_samples=6)
    items = scan_yolo_dataset(dataset_dir)

    assert len(items) == 6
    splits = {item.split for item in items}
    assert splits == {"train", "val", "test"}

    for item in items:
        assert isinstance(item, DatasetItem)
        assert item.image_path.exists()
        assert item.image_path.suffix.lower() in {".png", ".jpg", ".jpeg"}
        assert item.label_path is not None
        assert item.label_path.exists()


def test_scan_yolo_dataset_structure_b(tmp_path: Path) -> None:
    """scan_yolo_dataset handles flat/inverted structure images/<split>/ and labels/<split>/."""
    root = tmp_path / "dataset_b"
    for split in ["train", "val"]:
        img_dir = root / "images" / split
        lbl_dir = root / "labels" / split
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for i in range(2):
            img_file = img_dir / f"{split}_{i}.png"
            Image.new("RGB", (32, 32), color=(i * 50, 100, 150)).save(img_file)
            lbl_file = lbl_dir / f"{split}_{i}.txt"
            lbl_file.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    items = scan_yolo_dataset(root)
    assert len(items) == 4
    splits = {item.split for item in items}
    assert splits == {"train", "val"}
    for item in items:
        assert item.label_path is not None
        assert item.label_path.is_file()


def test_scan_yolo_dataset_unlabeled_images(tmp_path: Path) -> None:
    """scan_yolo_dataset correctly sets label_path=None when label file is missing."""
    dataset_dir = tmp_path / "dataset_unlabeled"
    img_dir = dataset_dir / "train" / "images"
    lbl_dir = dataset_dir / "train" / "labels"
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    img1 = img_dir / "labeled.png"
    Image.new("RGB", (32, 32)).save(img1)
    (lbl_dir / "labeled.txt").write_text("1 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    img2 = img_dir / "unlabeled.png"
    Image.new("RGB", (32, 32)).save(img2)

    items = scan_yolo_dataset(dataset_dir)
    assert len(items) == 2

    labeled_item = next(it for it in items if it.image_path.stem == "labeled")
    unlabeled_item = next(it for it in items if it.image_path.stem == "unlabeled")

    assert labeled_item.label_path is not None
    assert labeled_item.label_path.is_file()
    assert unlabeled_item.label_path is None


def test_scan_yolo_dataset_nonexistent_directory() -> None:
    """Non-existent directory should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        scan_yolo_dataset(Path("/nonexistent/path/for/trafficvision/test"))


def test_scan_yolo_dataset_empty_directory(tmp_path: Path) -> None:
    """Empty directory should return an empty list."""
    empty_dir = tmp_path / "empty_dataset"
    empty_dir.mkdir()
    items = scan_yolo_dataset(empty_dir)
    assert items == []


def test_summarize_dataset(tmp_path: Path) -> None:
    """summarize_dataset should compute total images, split counts, and classes present."""
    dataset_dir = create_synthetic_dataset(tmp_path / "synthetic_summary", num_samples=9)
    items = scan_yolo_dataset(dataset_dir)

    summary = summarize_dataset(items)
    assert isinstance(summary, DatasetSummary)
    assert summary.total_images == 9
    assert sum(summary.split_counts.values()) == 9
    assert "train" in summary.split_counts
    assert "val" in summary.split_counts
    assert "test" in summary.split_counts
    assert len(summary.classes_present) > 0
    assert all(0 <= cid < 82 for cid in summary.classes_present)


def test_synthetic_dataset_invalid_cases(tmp_path: Path) -> None:
    """Synthetic dataset generator supports specific invalid cases for test fixtures."""
    # Corrupt image case
    corrupt_dir = create_synthetic_dataset(
        tmp_path / "corrupt", num_samples=3, invalid_case="corrupt_image"
    )
    items_corrupt = scan_yolo_dataset(corrupt_dir)
    assert any(it.image_path.stat().st_size == 0 for it in items_corrupt)

    # Malformed line case
    malformed_dir = create_synthetic_dataset(
        tmp_path / "malformed", num_samples=3, invalid_case="malformed_line"
    )
    items_malformed = scan_yolo_dataset(malformed_dir)
    has_malformed = False
    for it in items_malformed:
        if it.label_path and it.label_path.exists():
            text = it.label_path.read_text(encoding="utf-8")
            if any(len(line.split()) != 5 for line in text.splitlines() if line.strip()):
                has_malformed = True
                break
    assert has_malformed

    # Class ID out of range case
    out_of_range_dir = create_synthetic_dataset(
        tmp_path / "out_of_range", num_samples=3, invalid_case="class_id_out_of_range"
    )
    items_oor = scan_yolo_dataset(out_of_range_dir)
    found_oor = False
    for it in items_oor:
        if it.label_path and it.label_path.exists():
            for line in it.label_path.read_text(encoding="utf-8").splitlines():
                if line.strip() and int(line.split()[0]) >= 82:
                    found_oor = True
                    break
    assert found_oor

    # Invalid coordinates case
    invalid_coords_dir = create_synthetic_dataset(
        tmp_path / "invalid_coords", num_samples=3, invalid_case="invalid_coordinates"
    )
    items_coords = scan_yolo_dataset(invalid_coords_dir)
    found_invalid_coords = False
    for it in items_coords:
        if it.label_path and it.label_path.exists():
            for line in it.label_path.read_text(encoding="utf-8").splitlines():
                parts = line.strip().split()
                if len(parts) == 5:
                    box = [float(p) for p in parts[1:]]
                    if any(c < 0.0 or c > 1.0 for c in box):
                        found_invalid_coords = True
                        break
    assert found_invalid_coords

    # Data leakage case (identical file in train and val)
    leak_dir = create_synthetic_dataset(
        tmp_path / "leak", num_samples=5, invalid_case="data_leakage"
    )
    items_leak = scan_yolo_dataset(leak_dir)
    train_bytes = {it.image_path.read_bytes() for it in items_leak if it.split == "train"}
    val_bytes = {it.image_path.read_bytes() for it in items_leak if it.split == "val"}
    assert len(train_bytes.intersection(val_bytes)) > 0

    # Unlabeled image case
    unlabeled_dir = create_synthetic_dataset(
        tmp_path / "unlabeled_case", num_samples=3, invalid_case="unlabeled_image"
    )
    items_unlabeled = scan_yolo_dataset(unlabeled_dir)
    assert any(it.label_path is None for it in items_unlabeled)

    # Empty label case (background image)
    empty_lbl_dir = create_synthetic_dataset(
        tmp_path / "empty_lbl", num_samples=3, invalid_case="empty_label"
    )
    items_empty = scan_yolo_dataset(empty_lbl_dir)
    assert any(
        it.label_path is not None and it.label_path.stat().st_size == 0
        for it in items_empty
    )


def test_scan_yolo_dataset_with_app_paths(tmp_path: Path) -> None:
    """scan_yolo_dataset should accept an AppPaths instance and scan its staging directory."""
    from trafficvision.config import AppPaths

    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    create_synthetic_dataset(paths.staging, num_samples=4)

    items = scan_yolo_dataset(paths)
    assert len(items) == 4
    for it in items:
        assert str(paths.staging) in str(it.image_path)
