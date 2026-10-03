#!/usr/bin/env python3
"""Repair known imported YOLO dataset defects without deleting source files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from trafficvision.config import AppPaths  # noqa: E402
from trafficvision.data.repair import repair_yolo_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--project-root", type=Path, default=repo_root)
    args = parser.parse_args()

    paths = AppPaths.from_root(args.project_root.resolve())
    data_dir = args.data_dir.resolve() if args.data_dir else paths.staging
    report = repair_yolo_dataset(data_dir)
    print(f"Normalized label lines: {report.normalized_label_lines}")
    print(f"Quarantined duplicate images: {report.quarantined_images}")
    print(f"Repair manifest: {report.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
