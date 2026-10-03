from pathlib import Path
from shutil import copyfile

from PIL import Image

from trafficvision.data import (
    VIETNAM_TRAFFIC_SIGN_CATALOG,
    scan_yolo_dataset,
    validate_dataset,
)
from trafficvision.data.repair import repair_yolo_dataset


def _write_image(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (12, 12), color).save(path)


def _write_label(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_repair_yolo_dataset_normalizes_known_extra_field_and_quarantines_leaks(
    tmp_path: Path,
) -> None:
    root = tmp_path / "dataset"

    # The same bytes in train and test are a cross-split leak. The test copy
    # is retained so the held-out split remains independent of training.
    test_image = root / "test" / "images" / "duplicate.jpg"
    _write_image(test_image, (255, 0, 0))
    _write_label(root / "test" / "labels" / "duplicate.txt", "0 0.5 0.5 0.4 0.4\n")
    train_duplicate = root / "train" / "images" / "duplicate.jpg"
    train_duplicate.parent.mkdir(parents=True, exist_ok=True)
    copyfile(test_image, train_duplicate)
    _write_label(root / "train" / "labels" / "duplicate.txt", "0 0.5 0.5 0.4 0.4\n")

    # This six-field row is the documented extra-zero source format defect.
    _write_image(root / "train" / "images" / "extra-field.jpg", (0, 255, 0))
    malformed_label = root / "train" / "labels" / "extra-field.txt"
    _write_label(malformed_label, "12 0 0.63125 0.53984375 0.025 0.0455078125\n")

    before = validate_dataset(scan_yolo_dataset(root), VIETNAM_TRAFFIC_SIGN_CATALOG)
    assert before.has_blocking

    repaired = repair_yolo_dataset(root)

    assert repaired.normalized_label_lines == 1
    assert repaired.quarantined_images == 1
    assert malformed_label.read_text(encoding="utf-8") == "12 0.63125 0.53984375 0.025 0.0455078125\n"
    assert not train_duplicate.exists()
    assert (root / ".quarantine" / "train" / "images" / "duplicate.jpg").is_file()

    after = validate_dataset(scan_yolo_dataset(root), VIETNAM_TRAFFIC_SIGN_CATALOG)
    assert not after.has_blocking
