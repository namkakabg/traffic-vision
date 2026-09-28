"""Quality gate validation for YOLO traffic sign datasets."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image

from trafficvision.data.catalog import VIETNAM_TRAFFIC_SIGN_CATALOG, SignClass
from trafficvision.data.dataset import DatasetItem


@dataclass(frozen=True)
class ValidationErrorItem:
    """Represents a single validation error or warning."""

    level: Literal["blocking", "warning"]
    code: str
    message: str
    file_path: Path | None = None


@dataclass(frozen=True)
class ValidationReport:
    """Aggregated validation findings and statistical summary for a dataset."""

    is_valid: bool
    has_blocking: bool
    blocking_errors: list[ValidationErrorItem]
    warnings: list[ValidationErrorItem]
    total_images: int
    total_labels: int
    class_distribution: dict[int, int]


def validate_dataset(
    items: list[DatasetItem],
    catalog: list[SignClass] | None = None,
) -> ValidationReport:
    """Validate a collection of DatasetItem instances against quality gate rules.

    Checks for:
    - Blocking errors:
      1. CORRUPT_IMAGE: 0-byte or unreadable/corrupted/spoofed image files.
      2. MALFORMED_YOLO_LINE: label lines with non-5 values or non-numeric tokens.
      3. CLASS_ID_OUT_OF_RANGE: class IDs outside [0, len(catalog) - 1].
      4. INVALID_COORDINATES: box coordinates < 0, > 1, or width/height <= 0.
      5. DATA_LEAKAGE: duplicate images (identical SHA-256) across splits.
    - Warnings (non-blocking):
      1. LOW_SAMPLE_COUNT: classes with fewer than 5 instances.
      2. CLASS_IMBALANCE: ratio between max and min class counts > 10:1.
      3. SMALL_BBOX: normalized box area < 0.0001 or width/height < 0.01.

    Args:
        items: List of DatasetItem instances to validate.
        catalog: Optional sign class catalog (defaults to VIETNAM_TRAFFIC_SIGN_CATALOG).

    Returns:
        ValidationReport containing is_valid, has_blocking, errors, warnings, and distribution.
    """
    if catalog is None:
        catalog = VIETNAM_TRAFFIC_SIGN_CATALOG

    num_classes = len(catalog)
    blocking_errors: list[ValidationErrorItem] = []
    warnings: list[ValidationErrorItem] = []
    class_distribution: dict[int, int] = {}
    total_labels = 0

    # Map image SHA-256 to list of items to detect cross-split data leakage
    hash_to_items: dict[str, list[DatasetItem]] = {}

    for item in items:
        # 1. Check image integrity
        image_valid = False
        if not item.image_path.is_file() or item.image_path.stat().st_size == 0:
            blocking_errors.append(
                ValidationErrorItem(
                    level="blocking",
                    code="CORRUPT_IMAGE",
                    message=f"Image file is missing or 0 bytes: {item.image_path}",
                    file_path=item.image_path,
                )
            )
        else:
            try:
                with Image.open(item.image_path) as img:
                    img.verify()
                image_valid = True
            except Exception as exc:
                blocking_errors.append(
                    ValidationErrorItem(
                        level="blocking",
                        code="CORRUPT_IMAGE",
                        message=f"Corrupt or invalid image ({exc}): {item.image_path}",
                        file_path=item.image_path,
                    )
                )

        # Compute hash for readable images to check cross-split leakage
        if image_valid:
            try:
                img_bytes = item.image_path.read_bytes()
                img_hash = hashlib.sha256(img_bytes).hexdigest()
                hash_to_items.setdefault(img_hash, []).append(item)
            except OSError:
                pass

        # 2. Check label file if present
        if item.label_path and item.label_path.is_file():
            try:
                content = item.label_path.read_text(encoding="utf-8")
            except Exception as exc:
                blocking_errors.append(
                    ValidationErrorItem(
                        level="blocking",
                        code="MALFORMED_YOLO_LINE",
                        message=f"Failed to read label file: {exc}",
                        file_path=item.label_path,
                    )
                )
                continue

            for line_idx, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if not stripped:
                    continue

                parts = stripped.split()
                if len(parts) != 5:
                    blocking_errors.append(
                        ValidationErrorItem(
                            level="blocking",
                            code="MALFORMED_YOLO_LINE",
                            message=(
                                f"Expected 5 values per line (class_id x_center y_center width height), "
                                f"found {len(parts)} at line {line_idx}: '{stripped}'"
                            ),
                            file_path=item.label_path,
                        )
                    )
                    continue

                try:
                    cls_id = int(parts[0])
                    x_c = float(parts[1])
                    y_c = float(parts[2])
                    w = float(parts[3])
                    h = float(parts[4])
                except ValueError:
                    blocking_errors.append(
                        ValidationErrorItem(
                            level="blocking",
                            code="MALFORMED_YOLO_LINE",
                            message=f"Non-numeric tokens in label at line {line_idx}: '{stripped}'",
                            file_path=item.label_path,
                        )
                    )
                    continue

                # Check class ID range
                if cls_id < 0 or cls_id >= num_classes:
                    blocking_errors.append(
                        ValidationErrorItem(
                            level="blocking",
                            code="CLASS_ID_OUT_OF_RANGE",
                            message=(
                                f"Class ID {cls_id} out of range [0, {num_classes - 1}] "
                                f"at line {line_idx}"
                            ),
                            file_path=item.label_path,
                        )
                    )
                    total_labels += 1
                    continue

                # Check normalized coordinates
                if (
                    x_c < 0.0
                    or x_c > 1.0
                    or y_c < 0.0
                    or y_c > 1.0
                    or w <= 0.0
                    or w > 1.0
                    or h <= 0.0
                    or h > 1.0
                ):
                    blocking_errors.append(
                        ValidationErrorItem(
                            level="blocking",
                            code="INVALID_COORDINATES",
                            message=(
                                f"Invalid coordinates (x={x_c}, y={y_c}, w={w}, h={h}) "
                                f"at line {line_idx}"
                            ),
                            file_path=item.label_path,
                        )
                    )
                    total_labels += 1
                    continue

                # Valid label annotation
                total_labels += 1
                class_distribution[cls_id] = class_distribution.get(cls_id, 0) + 1

                # Small bounding box warning
                if (w * h) < 0.0001 or w < 0.01 or h < 0.01:
                    warnings.append(
                        ValidationErrorItem(
                            level="warning",
                            code="SMALL_BBOX",
                            message=(
                                f"Small bounding box detected (w={w:.4f}, h={h:.4f}) "
                                f"at line {line_idx}"
                            ),
                            file_path=item.label_path,
                        )
                    )

    # 3. Check for cross-split data leakage
    for img_hash, hashed_items in hash_to_items.items():
        distinct_splits = {it.split for it in hashed_items}
        if len(distinct_splits) > 1:
            for it in hashed_items:
                blocking_errors.append(
                    ValidationErrorItem(
                        level="blocking",
                        code="DATA_LEAKAGE",
                        message=(
                            f"Identical image SHA-256 ({img_hash[:8]}...) leaked across "
                            f"splits: {', '.join(sorted(distinct_splits))}"
                        ),
                        file_path=it.image_path,
                    )
                )

    # 4. Check class distribution warnings
    if class_distribution:
        # Warning: classes with fewer than 5 samples
        for cls_id, count in sorted(class_distribution.items()):
            if count < 5:
                warnings.append(
                    ValidationErrorItem(
                        level="warning",
                        code="LOW_SAMPLE_COUNT",
                        message=(
                            f"Class {cls_id} has only {count} sample(s), "
                            "less than the recommended minimum of 5."
                        ),
                    )
                )

        # Warning: class imbalance ratio > 10:1
        counts = list(class_distribution.values())
        max_count = max(counts)
        min_count = min(counts)
        if min_count > 0:
            ratio = max_count / min_count
            if ratio > 10.0:
                warnings.append(
                    ValidationErrorItem(
                        level="warning",
                        code="CLASS_IMBALANCE",
                        message=(
                            f"Class imbalance ratio is {ratio:.1f}:1 "
                            f"(max: {max_count}, min: {min_count}), exceeding 10:1."
                        ),
                    )
                )

    has_blocking = len(blocking_errors) > 0
    is_valid = not has_blocking

    return ValidationReport(
        is_valid=is_valid,
        has_blocking=has_blocking,
        blocking_errors=blocking_errors,
        warnings=warnings,
        total_images=len(items),
        total_labels=total_labels,
        class_distribution=class_distribution,
    )
