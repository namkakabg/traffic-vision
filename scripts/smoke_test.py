#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# Add src to sys.path so script can run from any working directory
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from trafficvision.config import AppConfig, AppPaths  # noqa: E402
from trafficvision.history import AnalysisRepository  # noqa: E402
from trafficvision.registry import (  # noqa: E402
    ModelIntegrityError,
    ModelNotFoundError,
    ModelRegistry,
)
from trafficvision.service import AnalysisService  # noqa: E402
from trafficvision.settings import RuntimeSettingsStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run non-interactive smoke test on a sample image using production model."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=repo_root,
        help="Project root directory (default: repo root)",
    )
    parser.add_argument(
        "--image",
        type=Path,
        default=None,
        help="Path to the test image file (JPEG, PNG, or WEBP). If omitted, a synthetic sample is generated automatically.",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    paths = AppPaths.from_root(project_root)
    paths.ensure_directories()
    config = AppConfig.load(project_root=project_root)

    if args.image is not None:
        image_path = args.image.resolve()
        if not image_path.is_file():
            print(f"[!] Error: Image file not found: {image_path}", file=sys.stderr)
            return 1
    else:
        from PIL import Image, ImageDraw

        image_path = paths.staging / "smoke_sample.jpg"
        img = Image.new("RGB", (640, 640), color=(128, 128, 128))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 300, 300], fill=(200, 50, 50))
        img.save(image_path, format="JPEG")
        print(f"[*] No --image provided; generated synthetic sample image at {image_path}")
    registry = ModelRegistry(paths)

    # 1. Verify production model
    try:
        prod_model = registry.get_production()
    except ModelNotFoundError as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        print("    Run 'python scripts/bootstrap_baseline.py' first.", file=sys.stderr)
        return 1
    except ModelIntegrityError as e:
        print(f"[!] Security/Integrity Error: {e}", file=sys.stderr)
        return 1

    # 2. Wire service
    repo = AnalysisRepository(paths.db)
    settings_store = RuntimeSettingsStore(paths.state / "settings.json", default_config=config)
    service = AnalysisService(
        config=config,
        registry=registry,
        repository=repo,
        settings_store=settings_store,
    )

    # 3. Read image and analyze
    try:
        image_data = image_path.read_bytes()
        artifacts = service.analyze_image_upload(filename=image_path.name, data=image_data)
    except Exception as exc:
        print(f"[!] Error during analysis: {exc}", file=sys.stderr)
        return 1

    print("[+] TrafficVision Smoke Test PASSED:")
    print(f"    Model ID:        {prod_model.manifest.model_id}")
    print(f"    Backend:         {prod_model.manifest.backend}")
    print(f"    Stage:           {prod_model.manifest.stage}")
    print(f"    Detections:      {artifacts.record.total_detections} detected")
    print(f"    Inference time:  {artifacts.record.inference_ms:.1f} ms")
    print(f"    Annotated Image: {artifacts.annotated_media_path}")
    print(f"    Detections CSV:  {artifacts.csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
