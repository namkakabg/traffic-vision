"""Automated Exploratory Data Analysis (EDA) engine for YOLO datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image

from trafficvision.data.catalog import VIETNAM_TRAFFIC_SIGN_CATALOG, SignClass
from trafficvision.data.dataset import DatasetItem

COCO_SMALL_THRESHOLD = 32 * 32  # 1024 px^2
COCO_MEDIUM_THRESHOLD = 96 * 96  # 9216 px^2


@dataclass(frozen=True)
class EDAMetrics:
    """Aggregated exploratory data analysis metrics and distributions."""

    split_summary: dict[str, dict[str, int]]
    class_counts: dict[int, int]
    size_distribution: dict[str, int]
    aspect_ratios: list[float]
    bbox_stats: dict[str, Any]
    sample_image_manifest: list[dict[str, Any]]
    anomalies: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to a JSON-serializable dictionary."""
        return {
            "split_summary": self.split_summary,
            "class_counts": {str(k): v for k, v in self.class_counts.items()},
            "size_distribution": self.size_distribution,
            "aspect_ratios": self.aspect_ratios,
            "bbox_stats": self.bbox_stats,
            "sample_image_manifest": self.sample_image_manifest,
            "anomalies": self.anomalies,
        }


def _compute_stats(values: list[float]) -> dict[str, float]:
    """Compute min, max, mean, and median for a series of numbers."""
    if not values:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0}

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    min_val = float(sorted_vals[0])
    max_val = float(sorted_vals[-1])
    mean_val = float(sum(sorted_vals) / n)

    if n % 2 == 1:
        median_val = float(sorted_vals[n // 2])
    else:
        median_val = float((sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0)

    return {
        "min": round(min_val, 4),
        "max": round(max_val, 4),
        "mean": round(mean_val, 4),
        "median": round(median_val, 4),
    }


def generate_eda_report(
    items: list[DatasetItem],
    output_dir: Path | str | None = None,
    catalog: list[SignClass] | None = None,
    max_manifest_samples: int | None = 100,
) -> EDAMetrics:
    """Analyze scanned dataset items and generate comprehensive EDA metrics.

    Computes:
    1. Image counts and bounding box counts across splits (train, val, test, total).
    2. Class frequency distribution (class_id -> count).
    3. Bounding box sizes categorized by COCO standards:
       - Small: area < 1024 px^2 (32^2)
       - Medium: 1024 <= area <= 9216 px^2 (32^2 to 96^2)
       - Large: area > 9216 px^2 (96^2)
    4. Bounding box coordinates and aspect ratios (min, max, mean, median).
    5. Annotated sample manifest with bounding box details and anomaly flags.

    Args:
        items: List of scanned DatasetItem entries.
        output_dir: Optional directory or file path to save `eda_report.json`.
        catalog: Optional sign class catalog for class names (defaults to 82 classes).
        max_manifest_samples: Maximum number of sample images to include in manifest.
            If None or greater than total items, includes all.

    Returns:
        EDAMetrics containing aggregated analysis.
    """
    if catalog is None:
        catalog = VIETNAM_TRAFFIC_SIGN_CATALOG
    catalog_map = {sc.id: sc.name_vi for sc in catalog}

    split_summary: dict[str, dict[str, int]] = {
        "train": {"images": 0, "boxes": 0},
        "val": {"images": 0, "boxes": 0},
        "test": {"images": 0, "boxes": 0},
    }

    class_counts: dict[int, int] = {}
    size_distribution: dict[str, int] = {"small": 0, "medium": 0, "large": 0}

    all_aspect_ratios: list[float] = []
    x_centers: list[float] = []
    y_centers: list[float] = []
    widths: list[float] = []
    heights: list[float] = []
    areas: list[float] = []

    sample_image_manifest: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []

    total_images = len(items)
    total_boxes = 0

    for idx, item in enumerate(items):
        split = item.split
        if split not in split_summary:
            split_summary[split] = {"images": 0, "boxes": 0}
        split_summary[split]["images"] += 1

        img_width = 0
        img_height = 0
        item_anomalies: list[str] = []

        # Read image dimensions
        try:
            with Image.open(item.image_path) as img:
                img_width, img_height = img.size
        except Exception as exc:
            item_anomalies.append(f"Cannot read image: {exc}")

        # Parse annotations if label exists
        item_boxes: list[dict[str, Any]] = []
        if item.label_path and item.label_path.is_file():
            try:
                content = item.label_path.read_text(encoding="utf-8")
                for line_num, line in enumerate(content.splitlines(), start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    parts = stripped.split()
                    if len(parts) != 5:
                        item_anomalies.append(
                            f"Line {line_num}: expected 5 tokens, got {len(parts)}"
                        )
                        continue
                    try:
                        cls_id = int(parts[0])
                        x_c = float(parts[1])
                        y_c = float(parts[2])
                        w = float(parts[3])
                        h = float(parts[4])
                    except ValueError:
                        item_anomalies.append(f"Line {line_num}: invalid non-numeric values")
                        continue

                    # Class count
                    class_counts[cls_id] = class_counts.get(cls_id, 0) + 1
                    total_boxes += 1
                    split_summary[split]["boxes"] += 1

                    # Pixel dimensions and area
                    pix_w = w * img_width
                    pix_h = h * img_height
                    box_area = pix_w * pix_h

                    # COCO size category
                    if box_area < COCO_SMALL_THRESHOLD:
                        category = "small"
                    elif box_area <= COCO_MEDIUM_THRESHOLD:
                        category = "medium"
                    else:
                        category = "large"

                    size_distribution[category] += 1

                    # Aspect ratio: width / height
                    ar = round(pix_w / pix_h, 4) if pix_h > 0 else 0.0
                    all_aspect_ratios.append(ar)

                    # Accumulate for bbox stats
                    x_centers.append(x_c)
                    y_centers.append(y_c)
                    widths.append(w)
                    heights.append(h)
                    areas.append(box_area)

                    cls_name = catalog_map.get(cls_id, f"Class {cls_id}")
                    item_boxes.append(
                        {
                            "class_id": cls_id,
                            "class_name": cls_name,
                            "x_center": round(x_c, 6),
                            "y_center": round(y_c, 6),
                            "width": round(w, 6),
                            "height": round(h, 6),
                            "pixel_width": round(pix_w, 2),
                            "pixel_height": round(pix_h, 2),
                            "area_px": round(box_area, 2),
                            "aspect_ratio": ar,
                            "size_category": category,
                        }
                    )
            except OSError as exc:
                item_anomalies.append(f"Cannot read label file: {exc}")

        if item_anomalies:
            anomalies.append(
                {
                    "image_path": str(item.image_path),
                    "split": split,
                    "errors": item_anomalies,
                }
            )

        # Decide whether to include in sample manifest
        should_include = max_manifest_samples is None or idx < max_manifest_samples
        if should_include:
            sample_image_manifest.append(
                {
                    "image_path": str(item.image_path),
                    "image_name": item.image_path.name,
                    "split": split,
                    "width": img_width,
                    "height": img_height,
                    "num_boxes": len(item_boxes),
                    "boxes": item_boxes,
                    "is_background": len(item_boxes) == 0,
                    "has_anomaly": bool(item_anomalies),
                }
            )

    split_summary["total"] = {"images": total_images, "boxes": total_boxes}
    sorted_class_counts = dict(sorted(class_counts.items()))

    bbox_stats = {
        "x_center": _compute_stats(x_centers),
        "y_center": _compute_stats(y_centers),
        "width": _compute_stats(widths),
        "height": _compute_stats(heights),
        "aspect_ratio": _compute_stats(all_aspect_ratios),
        "area": _compute_stats(areas),
    }

    eda = EDAMetrics(
        split_summary=split_summary,
        class_counts=sorted_class_counts,
        size_distribution=size_distribution,
        aspect_ratios=all_aspect_ratios,
        bbox_stats=bbox_stats,
        sample_image_manifest=sample_image_manifest,
        anomalies=anomalies,
    )

    if output_dir is not None:
        out_path = Path(output_dir)
        if out_path.suffix == ".json":
            save_eda_summary(eda, out_path)
        else:
            save_eda_summary(eda, out_path / "eda_report.json")

    return eda


def save_eda_summary(eda: EDAMetrics, output_path: Path | str) -> None:
    """Save an EDAMetrics summary report to a JSON file.

    Args:
        eda: The EDAMetrics instance to serialize.
        output_path: Target path (file or directory). If directory or non-.json,
            saves as `eda_report.json` within that directory.
    """
    path = Path(output_path).resolve()
    if path.is_dir() or path.suffix != ".json":
        path.mkdir(parents=True, exist_ok=True)
        target_file = path / "eda_report.json"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        target_file = path

    data = eda.to_dict()
    target_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
