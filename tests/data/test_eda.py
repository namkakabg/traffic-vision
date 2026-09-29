"""Tests for automated EDA (Exploratory Data Analysis) engine."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from tests.fixtures.dataset_fixture import create_synthetic_dataset
from trafficvision.data.catalog import VIETNAM_TRAFFIC_SIGN_CATALOG
from trafficvision.data.dataset import DatasetItem, scan_yolo_dataset
from trafficvision.data.eda import (
    EDAMetrics,
    generate_eda_report,
    save_eda_summary,
)


def test_eda_split_summary(tmp_path: Path) -> None:
    """EDA should correctly aggregate image and bbox counts across train, val, and test splits."""
    ds_dir = create_synthetic_dataset(tmp_path / "dataset", num_samples=10)
    items = scan_yolo_dataset(ds_dir)

    eda = generate_eda_report(items)

    assert isinstance(eda, EDAMetrics)
    assert eda.split_summary["train"]["images"] == 6
    assert eda.split_summary["train"]["boxes"] == 6
    assert eda.split_summary["val"]["images"] == 2
    assert eda.split_summary["val"]["boxes"] == 2
    assert eda.split_summary["test"]["images"] == 2
    assert eda.split_summary["test"]["boxes"] == 2
    assert eda.split_summary["total"]["images"] == 10
    assert eda.split_summary["total"]["boxes"] == 10


def test_eda_class_distribution(tmp_path: Path) -> None:
    """EDA should correctly count occurrences of each class ID."""
    ds_dir = create_synthetic_dataset(tmp_path / "dataset", num_samples=10)
    items = scan_yolo_dataset(ds_dir)

    eda = generate_eda_report(items)

    assert isinstance(eda.class_counts, dict)
    assert sum(eda.class_counts.values()) == 10
    # In synthetic dataset, class_ids are 0 to 9
    for i in range(10):
        assert eda.class_counts[i] == 1


def test_eda_coco_size_distribution(tmp_path: Path) -> None:
    """EDA should categorize bbox sizes into small, medium, and large according to COCO standard."""
    # COCO thresholds:
    # small: area < 32^2 = 1024 px^2
    # medium: 1024 <= area <= 9216 px^2
    # large: area > 96^2 = 9216 px^2
    img_dir = tmp_path / "train" / "images"
    lbl_dir = tmp_path / "train" / "labels"
    img_dir.mkdir(parents=True)
    lbl_dir.mkdir(parents=True)

    # Image 1: 100x100, box 20x20 -> area 400 (small)
    img1 = Image.new("RGB", (100, 100), color="white")
    img1_path = img_dir / "img1.png"
    img1.save(img1_path)
    (lbl_dir / "img1.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    # Image 2: 100x100, box 50x50 -> area 2500 (medium)
    img2 = Image.new("RGB", (100, 100), color="white")
    img2_path = img_dir / "img2.png"
    img2.save(img2_path)
    (lbl_dir / "img2.txt").write_text("1 0.5 0.5 0.5 0.5\n", encoding="utf-8")

    # Image 3: 200x200, box 120x120 -> area 14400 (large)
    img3 = Image.new("RGB", (200, 200), color="white")
    img3_path = img_dir / "img3.png"
    img3.save(img3_path)
    (lbl_dir / "img3.txt").write_text("2 0.5 0.5 0.6 0.6\n", encoding="utf-8")

    items = scan_yolo_dataset(tmp_path)
    eda = generate_eda_report(items)

    assert eda.size_distribution["small"] == 1
    assert eda.size_distribution["medium"] == 1
    assert eda.size_distribution["large"] == 1


def test_eda_bbox_stats_and_aspect_ratios(tmp_path: Path) -> None:
    """EDA should compute min, max, mean, median for center, dimensions, and aspect ratios."""
    img_dir = tmp_path / "train" / "images"
    lbl_dir = tmp_path / "train" / "labels"
    img_dir.mkdir(parents=True)
    lbl_dir.mkdir(parents=True)

    # 100x100 image
    # Box 1: x=0.2, y=0.3, w=0.4, h=0.2 -> pixel w=40, h=20 -> AR = 2.0
    # Box 2: x=0.6, y=0.7, w=0.2, h=0.4 -> pixel w=20, h=40 -> AR = 0.5
    img = Image.new("RGB", (100, 100), color="blue")
    img_path = img_dir / "sample.png"
    img.save(img_path)
    (lbl_dir / "sample.txt").write_text(
        "0 0.200000 0.300000 0.400000 0.200000\n0 0.600000 0.700000 0.200000 0.400000\n",
        encoding="utf-8",
    )

    items = scan_yolo_dataset(tmp_path)
    eda = generate_eda_report(items)

    assert len(eda.aspect_ratios) == 2
    assert 2.0 in eda.aspect_ratios
    assert 0.5 in eda.aspect_ratios

    # Check bbox_stats structure and values
    stats = eda.bbox_stats
    for dim in ("x_center", "y_center", "width", "height", "aspect_ratio", "area"):
        assert dim in stats
        for metric in ("min", "max", "mean", "median"):
            assert metric in stats[dim]

    assert stats["aspect_ratio"]["min"] == 0.5
    assert stats["aspect_ratio"]["max"] == 2.0
    assert stats["aspect_ratio"]["mean"] == 1.25
    assert stats["aspect_ratio"]["median"] == 1.25

    assert stats["x_center"]["min"] == 0.2
    assert stats["x_center"]["max"] == 0.6
    assert stats["x_center"]["mean"] == 0.4


def test_eda_sample_image_manifest(tmp_path: Path) -> None:
    """EDA should generate an annotated sample manifest with box metadata."""
    ds_dir = create_synthetic_dataset(tmp_path / "dataset", num_samples=4)
    items = scan_yolo_dataset(ds_dir)

    eda = generate_eda_report(items, catalog=VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert len(eda.sample_image_manifest) == 4
    sample = eda.sample_image_manifest[0]

    assert "image_path" in sample
    assert "split" in sample
    assert "width" in sample
    assert "height" in sample
    assert sample["width"] == 32
    assert sample["height"] == 32
    assert "boxes" in sample
    assert len(sample["boxes"]) == 1

    box = sample["boxes"][0]
    assert "class_id" in box
    assert "class_name" in box
    assert "x_center" in box
    assert "y_center" in box
    assert "width" in box
    assert "height" in box
    assert "area_px" in box
    assert "size_category" in box
    assert box["size_category"] == "small"


def test_eda_save_and_json_serialization(tmp_path: Path) -> None:
    """EDA report should be serializable to JSON and saved to disk."""
    ds_dir = create_synthetic_dataset(tmp_path / "dataset", num_samples=4)
    items = scan_yolo_dataset(ds_dir)
    out_dir = tmp_path / "eda_output"

    eda = generate_eda_report(items, output_dir=out_dir)

    # 1. Output directory should have eda_report.json
    report_file = out_dir / "eda_report.json"
    assert report_file.is_file()

    # 2. Can load and parse JSON cleanly
    with open(report_file, encoding="utf-8") as f:
        data = json.load(f)

    assert "split_summary" in data
    assert "class_counts" in data
    assert "size_distribution" in data
    assert "aspect_ratios" in data
    assert "bbox_stats" in data
    assert "sample_image_manifest" in data

    # 3. Test save_eda_summary directly with explicit file path
    custom_report_file = tmp_path / "custom" / "summary.json"
    save_eda_summary(eda, custom_report_file)
    assert custom_report_file.is_file()


def test_eda_empty_dataset_and_background_images(tmp_path: Path) -> None:
    """EDA should handle empty datasets and images with zero bounding boxes."""
    # 1. Empty items list
    eda_empty = generate_eda_report([])
    assert eda_empty.split_summary["total"]["images"] == 0
    assert eda_empty.split_summary["total"]["boxes"] == 0
    assert eda_empty.size_distribution == {"small": 0, "medium": 0, "large": 0}
    assert eda_empty.aspect_ratios == []

    # 2. Background image (no boxes)
    img_dir = tmp_path / "train" / "images"
    lbl_dir = tmp_path / "train" / "labels"
    img_dir.mkdir(parents=True)
    lbl_dir.mkdir(parents=True)

    img = Image.new("RGB", (64, 64), color="black")
    img.save(img_dir / "bg.png")
    (lbl_dir / "bg.txt").write_text("", encoding="utf-8")

    items = [
        DatasetItem(image_path=img_dir / "bg.png", label_path=lbl_dir / "bg.txt", split="train")
    ]
    eda_bg = generate_eda_report(items)

    assert eda_bg.split_summary["train"]["images"] == 1
    assert eda_bg.split_summary["train"]["boxes"] == 0
    assert eda_bg.sample_image_manifest[0]["is_background"] is True
    assert len(eda_bg.sample_image_manifest[0]["boxes"]) == 0


def test_eda_corrupt_or_zero_dimension_image_guarded(tmp_path: Path) -> None:
    """EDA should not calculate physical pixel dimensions or increment COCO size distribution if image is invalid."""
    img_dir = tmp_path / "train" / "images"
    lbl_dir = tmp_path / "train" / "labels"
    img_dir.mkdir(parents=True)
    lbl_dir.mkdir(parents=True)

    fake_img = img_dir / "corrupt.png"
    fake_img.write_text("CORRUPT NOT AN IMAGE", encoding="utf-8")
    fake_lbl = lbl_dir / "corrupt.txt"
    fake_lbl.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    items = [DatasetItem(image_path=fake_img, label_path=fake_lbl, split="train")]
    eda = generate_eda_report(items)

    assert eda.size_distribution == {"small": 0, "medium": 0, "large": 0}
    assert eda.bbox_stats["area"]["max"] == 0.0
    box = eda.sample_image_manifest[0]["boxes"][0]
    assert box["pixel_width"] is None
    assert box["pixel_height"] is None
    assert box["area_px"] is None
    assert box["size_category"] is None

