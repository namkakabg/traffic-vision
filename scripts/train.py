#!/usr/bin/env python3
"""CLI operator script for initiating and monitoring YOLO training runs."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add src to sys.path so script can run from any working directory
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from trafficvision.config import AppPaths  # noqa: E402
from trafficvision.training.config import TrainingConfig  # noqa: E402
from trafficvision.training.manager import TrainingManager  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run YOLO traffic sign detection training pipeline."
    )
    parser.add_argument(
        "--data-yaml",
        type=Path,
        required=True,
        help="Path to data.yaml dataset configuration file.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Total training epochs (default: 50).",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=4,
        help="Batch size (default: 4).",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Input image resolution in pixels, multiple of 32 (default: 640).",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=10,
        help="Early stopping patience in epochs (default: 10).",
    )
    parser.add_argument(
        "--amp",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable automatic mixed precision (default: True).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Computation device ('cpu', '0', 'mps', default: 'cpu').",
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="yolo11n.pt",
        help="Base pretrained YOLO checkpoint (default: yolo11n.pt).",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Custom run ID (default: auto-generated timestamp).",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Start background training subprocess and exit without waiting for completion.",
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

    data_yaml_path = args.data_yaml.resolve()
    if not data_yaml_path.is_file():
        print(f"[!] Error: data.yaml file not found: {data_yaml_path}", file=sys.stderr)
        return 1

    run_id = args.run_id or f"train_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    try:
        config = TrainingConfig(
            run_id=run_id,
            data_yaml=data_yaml_path,
            base_model=args.base_model,
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            patience=args.patience,
            amp=args.amp,
            device=args.device,
        )
    except Exception as exc:
        print(f"[!] Invalid training configuration: {exc}", file=sys.stderr)
        return 1

    manager = TrainingManager(paths=paths)

    print(f"[*] Initializing training run '{run_id}'...")
    print(f"    Data YAML:   {config.data_yaml}")
    print(f"    Base Model:  {config.base_model}")
    print(f"    Epochs:      {config.epochs}")
    print(f"    Batch Size:  {config.batch}")
    print(f"    Image Size:  {config.imgsz}")
    print(f"    Device:      {config.device}")
    print(f"    AMP:         {config.amp}")

    try:
        initial_state = manager.start_training(config)
    except Exception as exc:
        print(f"[!] Failed to start training process: {exc}", file=sys.stderr)
        return 1

    run_dir = paths.runs / run_id
    print(f"[+] Training run launched with PID {initial_state.pid}")
    print(f"    Run Directory: {run_dir}")
    print(f"    Log File:      {run_dir / 'train.log'}")

    if args.no_wait:
        print("[*] Running in background (--no-wait specified).")
        return 0

    print("\n[*] Monitoring training progress (Ctrl+C to stop)...")
    last_epoch = -1
    try:
        while True:
            time.sleep(1.0)
            state = manager.get_state(run_id)

            if state.current_epoch != last_epoch:
                last_epoch = state.current_epoch
                metrics_summary = ""
                if state.metrics:
                    metrics_summary = f" | {state.metrics}"
                print(
                    f"    Epoch {state.current_epoch}/{state.total_epochs} "
                    f"[Best mAP50: {state.best_map50:.4f}]{metrics_summary}"
                )

            if state.status == "completed":
                print(f"\n[+] Training COMPLETED successfully in {state.elapsed_s:.1f}s!")
                if state.checkpoint_paths:
                    print("    Checkpoints:")
                    for name, cp_path in state.checkpoint_paths.items():
                        print(f"      - {name}: {cp_path}")
                return 0

            if state.status == "failed":
                print(f"\n[!] Training FAILED: {state.error_message}", file=sys.stderr)
                print(f"    Check logs for details: {run_dir / 'train.log'}", file=sys.stderr)
                return 1

            if state.status == "stopped":
                print(f"\n[*] Training STOPPED early after {state.elapsed_s:.1f}s.")
                return 0

    except KeyboardInterrupt:
        print("\n[*] Received interrupt. Requesting training stop...")
        manager.stop_training(run_id)
        print("[*] Training run signaled to stop.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
