"""Synthetic YOLO dataset generator for tests and fixtures."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def create_synthetic_dataset(
    target_dir: Path | str,
    num_samples: int = 10,
    invalid_case: str | None = None,
) -> Path:
    """Generate a synthetic YOLO format dataset.

    Args:
        target_dir: Root directory for the dataset.
        num_samples: Total number of samples across splits.
        invalid_case: Optional failure condition to inject for validation testing.
            Supported: "corrupt_image", "malformed_line", "class_id_out_of_range",
            "invalid_coordinates", "data_leakage", "unlabeled_image", "empty_label",
            "imbalance".

    Returns:
        Path to the root dataset directory.
    """
    root = Path(target_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)

    # Compute split counts
    if num_samples <= 1:
        splits = {"train": num_samples, "val": 0, "test": 0}
    elif num_samples == 2:
        splits = {"train": 1, "val": 1, "test": 0}
    else:
        val_count = max(1, num_samples // 5)
        test_count = max(1, num_samples // 5)
        train_count = num_samples - val_count - test_count
        splits = {"train": train_count, "val": val_count, "test": test_count}

    global_idx = 0
    leak_image_path: Path | None = None

    for split_name, count in splits.items():
        img_dir = root / split_name / "images"
        lbl_dir = root / split_name / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for i in range(count):
            sample_name = f"{split_name}_{i:04d}"
            img_path = img_dir / f"{sample_name}.png"
            lbl_path = lbl_dir / f"{sample_name}.txt"

            # Create image
            color = ((global_idx * 37) % 256, (global_idx * 67) % 256, (global_idx * 97) % 256)
            img = Image.new("RGB", (32, 32), color=color)
            img.save(img_path, format="PNG")

            # Label generation
            class_id = global_idx % 82
            if invalid_case == "imbalance":
                class_id = 0 if global_idx < (num_samples - 1) else 1

            lbl_content = f"{class_id} 0.500000 0.500000 0.300000 0.300000\n"

            # Apply specific invalid cases to first sample of train or relevant split
            if global_idx == 0:
                if invalid_case == "corrupt_image":
                    # Truncate to 0 bytes
                    img_path.write_bytes(b"")
                elif invalid_case == "malformed_line":
                    lbl_content = f"{class_id} 0.5 0.5 0.3\n"  # Only 4 values
                elif invalid_case == "class_id_out_of_range":
                    lbl_content = "82 0.5 0.5 0.3 0.3\n"
                elif invalid_case == "invalid_coordinates":
                    lbl_content = f"{class_id} 1.5 0.5 0.3 0.3\n"
                elif invalid_case == "unlabeled_image":
                    lbl_content = ""  # Will skip creating label file below
                elif invalid_case == "empty_label":
                    lbl_content = ""  # Creates empty file (background image)
                elif invalid_case == "data_leakage":
                    leak_image_path = img_path

            if invalid_case == "unlabeled_image" and global_idx == 0:
                pass  # Do not write label file
            else:
                lbl_path.write_text(lbl_content, encoding="utf-8")

            global_idx += 1

    # Inject data leakage if requested (copy train sample into val)
    if invalid_case == "data_leakage" and leak_image_path and splits.get("val", 0) > 0:
        val_leak_img = root / "val" / "images" / f"val_leak_{leak_image_path.name}"
        val_leak_lbl = root / "val" / "labels" / f"val_leak_{leak_image_path.stem}.txt"
        val_leak_img.write_bytes(leak_image_path.read_bytes())
        val_leak_lbl.write_text("0 0.5 0.5 0.3 0.3\n", encoding="utf-8")

    return root
