"""Unit tests for dataset quality gate validation."""

from pathlib import Path

from PIL import Image

from tests.fixtures.dataset_fixture import create_synthetic_dataset
from trafficvision.data.catalog import VIETNAM_TRAFFIC_SIGN_CATALOG
from trafficvision.data.dataset import scan_yolo_dataset
from trafficvision.data.validator import (
    ValidationErrorItem,
    ValidationReport,
    validate_dataset,
)


def test_validate_clean_dataset(tmp_path: Path) -> None:
    """A clean dataset should pass validation with is_valid=True and no blocking errors."""
    data_dir = create_synthetic_dataset(tmp_path / "clean", num_samples=10)
    items = scan_yolo_dataset(data_dir)

    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert isinstance(report, ValidationReport)
    assert report.is_valid is True
    assert report.has_blocking is False
    assert len(report.blocking_errors) == 0
    assert report.total_images == 10
    assert report.total_labels > 0
    assert len(report.class_distribution) > 0


def test_validate_corrupt_image_zero_bytes(tmp_path: Path) -> None:
    """A zero-byte image file must trigger a blocking CORRUPT_IMAGE error."""
    data_dir = create_synthetic_dataset(
        tmp_path / "corrupt_zero", num_samples=5, invalid_case="corrupt_image"
    )
    items = scan_yolo_dataset(data_dir)

    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is True
    assert report.is_valid is False
    error_codes = [err.code for err in report.blocking_errors]
    assert "CORRUPT_IMAGE" in error_codes

    corrupt_err = next(e for e in report.blocking_errors if e.code == "CORRUPT_IMAGE")
    assert corrupt_err.level == "blocking"
    assert corrupt_err.file_path is not None
    assert corrupt_err.file_path.exists()
    assert corrupt_err.file_path.stat().st_size == 0


def test_validate_corrupt_image_spoofed_extension(tmp_path: Path) -> None:
    """A non-image file with an image extension must trigger a blocking CORRUPT_IMAGE error."""
    data_dir = tmp_path / "spoofed_dataset"
    img_dir = data_dir / "train" / "images"
    lbl_dir = data_dir / "train" / "labels"
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    fake_img = img_dir / "fake.png"
    fake_img.write_text("NOT A REAL PNG FILE - RANDOM TEXT HEADER", encoding="utf-8")
    (lbl_dir / "fake.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    items = scan_yolo_dataset(data_dir)
    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is True
    assert report.is_valid is False
    assert any(e.code == "CORRUPT_IMAGE" for e in report.blocking_errors)


def test_validate_malformed_yolo_line(tmp_path: Path) -> None:
    """A label file with non-5 values on a line must trigger MALFORMED_YOLO_LINE."""
    data_dir = create_synthetic_dataset(
        tmp_path / "malformed", num_samples=5, invalid_case="malformed_line"
    )
    items = scan_yolo_dataset(data_dir)

    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is True
    assert report.is_valid is False
    assert any(e.code == "MALFORMED_YOLO_LINE" for e in report.blocking_errors)
    malformed_err = next(e for e in report.blocking_errors if e.code == "MALFORMED_YOLO_LINE")
    assert malformed_err.level == "blocking"
    assert malformed_err.file_path is not None


def test_validate_class_id_out_of_range(tmp_path: Path) -> None:
    """Class IDs outside [0, 81] must trigger CLASS_ID_OUT_OF_RANGE."""
    data_dir = create_synthetic_dataset(
        tmp_path / "out_of_range", num_samples=5, invalid_case="class_id_out_of_range"
    )
    items = scan_yolo_dataset(data_dir)

    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is True
    assert report.is_valid is False
    assert any(e.code == "CLASS_ID_OUT_OF_RANGE" for e in report.blocking_errors)

    # Also test negative class ID
    neg_dir = tmp_path / "neg_dataset"
    (neg_dir / "train" / "images").mkdir(parents=True, exist_ok=True)
    (neg_dir / "train" / "labels").mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 32)).save(neg_dir / "train" / "images" / "neg.png")
    (neg_dir / "train" / "labels" / "neg.txt").write_text("-1 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    neg_items = scan_yolo_dataset(neg_dir)
    neg_report = validate_dataset(neg_items, VIETNAM_TRAFFIC_SIGN_CATALOG)
    assert neg_report.has_blocking is True
    assert any(e.code == "CLASS_ID_OUT_OF_RANGE" for e in neg_report.blocking_errors)


def test_validate_invalid_coordinates(tmp_path: Path) -> None:
    """Bounding box coordinates < 0, > 1, or width/height <= 0 must trigger INVALID_COORDINATES."""
    data_dir = create_synthetic_dataset(
        tmp_path / "invalid_coords", num_samples=5, invalid_case="invalid_coordinates"
    )
    items = scan_yolo_dataset(data_dir)

    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is True
    assert report.is_valid is False
    assert any(e.code == "INVALID_COORDINATES" for e in report.blocking_errors)

    # Test width <= 0
    zero_w_dir = tmp_path / "zero_w_dataset"
    (zero_w_dir / "train" / "images").mkdir(parents=True, exist_ok=True)
    (zero_w_dir / "train" / "labels").mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 32)).save(zero_w_dir / "train" / "images" / "zero_w.png")
    (zero_w_dir / "train" / "labels" / "zero_w.txt").write_text("0 0.5 0.5 0.0 0.2\n", encoding="utf-8")

    zw_items = scan_yolo_dataset(zero_w_dir)
    zw_report = validate_dataset(zw_items, VIETNAM_TRAFFIC_SIGN_CATALOG)
    assert zw_report.has_blocking is True
    assert any(e.code == "INVALID_COORDINATES" for e in zw_report.blocking_errors)


def test_validate_data_leakage(tmp_path: Path) -> None:
    """Duplicate images across splits (identical SHA-256) must trigger DATA_LEAKAGE."""
    data_dir = create_synthetic_dataset(
        tmp_path / "leak", num_samples=6, invalid_case="data_leakage"
    )
    items = scan_yolo_dataset(data_dir)

    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is True
    assert report.is_valid is False
    assert any(e.code == "DATA_LEAKAGE" for e in report.blocking_errors)
    leak_err = next(e for e in report.blocking_errors if e.code == "DATA_LEAKAGE")
    assert leak_err.level == "blocking"


def test_validate_warnings_class_imbalance(tmp_path: Path) -> None:
    """Class imbalance ratio > 10:1 should produce a warning but NOT block validation."""
    data_dir = create_synthetic_dataset(
        tmp_path / "imbalance", num_samples=25, invalid_case="imbalance"
    )
    items = scan_yolo_dataset(data_dir)

    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    # Crucial requirement: warnings do NOT make has_blocking=True
    assert report.has_blocking is False
    assert report.is_valid is True
    assert len(report.blocking_errors) == 0

    warning_codes = [w.code for w in report.warnings]
    assert "CLASS_IMBALANCE" in warning_codes
    assert all(w.level == "warning" for w in report.warnings)


def test_validate_warnings_low_sample_count(tmp_path: Path) -> None:
    """Classes with fewer than 5 samples should produce a LOW_SAMPLE_COUNT warning."""
    data_dir = tmp_path / "low_sample_dataset"
    (data_dir / "train" / "images").mkdir(parents=True, exist_ok=True)
    (data_dir / "train" / "labels").mkdir(parents=True, exist_ok=True)

    # Class 0 has 2 samples (< 5)
    for i in range(2):
        img_p = data_dir / "train" / "images" / f"sample_{i}.png"
        Image.new("RGB", (32, 32)).save(img_p)
        lbl_p = data_dir / "train" / "labels" / f"sample_{i}.txt"
        lbl_p.write_text("0 0.5 0.5 0.3 0.3\n", encoding="utf-8")

    items = scan_yolo_dataset(data_dir)
    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is False
    assert report.is_valid is True
    assert any(w.code == "LOW_SAMPLE_COUNT" for w in report.warnings)


def test_validate_warnings_small_bbox(tmp_path: Path) -> None:
    """Bounding boxes with extremely small normalized area should produce a SMALL_BBOX warning."""
    data_dir = tmp_path / "small_bbox_dataset"
    (data_dir / "train" / "images").mkdir(parents=True, exist_ok=True)
    (data_dir / "train" / "labels").mkdir(parents=True, exist_ok=True)

    img_p = data_dir / "train" / "images" / "tiny.png"
    Image.new("RGB", (32, 32)).save(img_p)
    lbl_p = data_dir / "train" / "labels" / "tiny.txt"
    # width=0.005, height=0.005 -> area=0.000025
    lbl_p.write_text("0 0.5 0.5 0.005 0.005\n", encoding="utf-8")

    items = scan_yolo_dataset(data_dir)
    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is False
    assert any(w.code == "SMALL_BBOX" for w in report.warnings)


def test_validate_background_and_unlabeled_images(tmp_path: Path) -> None:
    """Empty label files (background images) and unlabeled images are valid non-blocking cases."""
    data_dir = create_synthetic_dataset(
        tmp_path / "empty_lbl", num_samples=3, invalid_case="empty_label"
    )
    items = scan_yolo_dataset(data_dir)

    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    assert report.has_blocking is False
    assert report.is_valid is True
    assert len(report.blocking_errors) == 0


def test_validation_error_item_attributes() -> None:
    """ValidationErrorItem fields and representation."""
    item = ValidationErrorItem(
        level="blocking",
        code="CORRUPT_IMAGE",
        message="Zero byte image",
        file_path=Path("/tmp/test.png"),
    )
    assert item.level == "blocking"
    assert item.code == "CORRUPT_IMAGE"
    assert item.message == "Zero byte image"
    assert item.file_path == Path("/tmp/test.png")
