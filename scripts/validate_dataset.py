#!/usr/bin/env python3
"""CLI script to scan, validate, and optionally analyze or snapshot a YOLO dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to sys.path so script can run from any working directory
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from trafficvision.config import AppPaths  # noqa: E402
from trafficvision.data import (  # noqa: E402
    VIETNAM_TRAFFIC_SIGN_CATALOG,
    create_dataset_snapshot,
    generate_eda_report,
    scan_yolo_dataset,
    validate_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan and validate YOLO dataset against quality gate rules."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Path to dataset directory. Defaults to artifacts/staging under project root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory to save EDA report (eda_report.json) and snapshots.",
    )
    parser.add_argument(
        "--create-snapshot",
        action="store_true",
        help="Create an immutable dataset snapshot if validation passes.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=repo_root,
        help="Root directory of the project (default: repo root).",
    )

    args = parser.parse_args()
    project_root = args.project_root.resolve()
    paths = AppPaths.from_root(project_root)
    paths.ensure_directories()

    data_dir = args.data_dir.resolve() if args.data_dir else paths.staging
    if not data_dir.is_dir():
        print(f"[!] Error: Dataset directory not found: {data_dir}", file=sys.stderr)
        return 1

    print(f"[*] Scanning YOLO dataset in: {data_dir}")
    try:
        items = scan_yolo_dataset(data_dir)
    except Exception as exc:
        print(f"[!] Error scanning dataset: {exc}", file=sys.stderr)
        return 1

    total_images = len(items)
    splits: dict[str, int] = {}
    for item in items:
        splits[item.split] = splits.get(item.split, 0) + 1

    print(f"[*] Found {total_images} samples across splits: {splits}")

    print("[*] Running Quality Gate validation against Vietnamese sign catalog...")
    report = validate_dataset(items, VIETNAM_TRAFFIC_SIGN_CATALOG)

    # Print summary
    print("\n--- Validation Summary ---")
    status_str = "VALID (Passed)" if report.is_valid else "INVALID (Blocking errors detected)"
    print(f"Status:          {status_str}")
    print(f"Total Images:    {report.total_images}")
    print(f"Total Labels:    {report.total_labels}")
    print(f"Blocking Errors: {len(report.blocking_errors)}")
    print(f"Warnings:        {len(report.warnings)}")

    if report.blocking_errors:
        print("\n[!] BLOCKING ERRORS:")
        for err in report.blocking_errors:
            loc = f" ({err.file_path.name})" if err.file_path else ""
            print(f"    - [{err.code}] {err.message}{loc}", file=sys.stderr)

    if report.warnings:
        print("\n[*] WARNINGS:")
        for warn in report.warnings:
            loc = f" ({warn.file_path.name})" if warn.file_path else ""
            print(f"    - [{warn.code}] {warn.message}{loc}")

    # Generate EDA Report if requested
    if args.output_dir is not None:
        out_dir = args.output_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n[*] Generating EDA metrics report to: {out_dir}")
        try:
            eda_metrics = generate_eda_report(items, output_dir=out_dir)
            print(f"[+] EDA report saved: {out_dir / 'eda_report.json'}")
            print(f"    Total boxes analyzed: {eda_metrics.bbox_stats.get('total_boxes', 0)}")
        except Exception as exc:
            print(f"[!] Failed to generate EDA report: {exc}", file=sys.stderr)

    # Create snapshot if requested and valid
    if args.create_snapshot:
        if report.has_blocking:
            print(
                "\n[!] Cannot create snapshot: dataset has blocking validation errors.",
                file=sys.stderr,
            )
            return 1

        snapshots_dir = (
            args.output_dir.resolve() / "snapshots"
            if args.output_dir
            else paths.root / "artifacts" / "snapshots"
        )
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n[*] Creating immutable snapshot in: {snapshots_dir}")
        try:
            snapshot = create_dataset_snapshot(items, snapshots_dir, report)
            print(f"[+] Snapshot created successfully: {snapshot.snapshot_id}")
            print(f"    Data YAML: {snapshot.data_yaml_path}")
            print(f"    Directory: {snapshot.snapshot_dir}")
        except Exception as exc:
            print(f"[!] Failed to create snapshot: {exc}", file=sys.stderr)
            return 1

    if report.has_blocking:
        return 1

    print("\n[+] Dataset validation PASSED successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
