#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# Add src to sys.path so script can run from repo root
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from trafficvision.bootstrap import bootstrap_baseline  # noqa: E402
from trafficvision.config import AppPaths  # noqa: E402
from trafficvision.registry import ModelRegistry  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap and register the baseline pretrained YOLO ONNX model."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=repo_root,
        help="Root directory of the project (default: current repository root)",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="yolo11n.pt",
        help="Ultralytics pretrained model name/checkpoint (default: yolo11n.pt)",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    print(f"[*] Bootstrapping baseline model '{args.model_name}' in: {project_root}")

    paths = AppPaths.from_root(project_root)
    paths.ensure_directories()
    registry = ModelRegistry(paths)

    try:
        registered = bootstrap_baseline(registry, model_name=args.model_name)
    except Exception as exc:
        print(f"[!] ERROR: Failed to bootstrap baseline model: {exc}", file=sys.stderr)
        return 1

    print("[+] Baseline model registered successfully:")
    print(f"    Model ID:    {registered.manifest.model_id}")
    print(f"    Backend:     {registered.manifest.backend}")
    print(f"    Stage:       {registered.manifest.stage}")
    print(f"    Classes:     {len(registered.manifest.class_names)} classes")
    print(f"    SHA-256:     {registered.manifest.sha256}")
    print(f"    Model Path:  {registered.model_path}")
    print(f"    Manifest:    {registered.manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
