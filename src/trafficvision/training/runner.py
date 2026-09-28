"""Subprocess runner executing YOLO training in the background."""

from __future__ import annotations

import argparse
import os
import shutil
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trafficvision.training.config import TrainingConfig
from trafficvision.training.state import TrainingEvent, TrainingState


def run_training_subprocess(
    config_path: Path | str,
    train_fn: Callable[..., Any] | None = None,
) -> TrainingState:
    """Execute training run inside background subprocess.

    Loads run configuration, binds callbacks to track epoch-by-epoch metrics,
    appends events to events.jsonl, watches for stop.signal, and stores checkpoints.

    Args:
        config_path: Path to run_config.json.
        train_fn: Optional custom/mock training function used for testing.

    Returns:
        Final TrainingState reflecting completion, stop, or failure.
    """
    config_file = Path(config_path).resolve()
    config = TrainingConfig.model_validate_json(config_file.read_text(encoding="utf-8"))

    run_dir = config_file.parent
    state_file = run_dir / "state.json"
    events_file = run_dir / "events.jsonl"
    stop_file = run_dir / "stop.signal"
    weights_dir = run_dir / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)

    if state_file.is_file():
        state = TrainingState.from_file(state_file)
    else:
        state = TrainingState(run_id=config.run_id, total_epochs=config.epochs)

    state.status = "running"
    state.pid = os.getpid()
    state.total_epochs = config.epochs
    state.to_file(state_file)

    start_time = time.time()
    stopped_early = False

    if train_fn is not None:
        try:
            train_fn(
                config=config,
                run_dir=run_dir,
                state=state,
                state_file=state_file,
                events_file=events_file,
                stop_file=stop_file,
                weights_dir=weights_dir,
            )
        except Exception as exc:
            state.status = "failed"
            state.error_message = str(exc)
            state.elapsed_s = round(time.time() - start_time, 2)
            state.to_file(state_file)
            raise
    else:
        # Default Ultralytics YOLO training execution
        from ultralytics import YOLO  # lazy import

        model = YOLO(config.base_model)

        def on_fit_epoch_end(trainer: Any) -> None:
            nonlocal stopped_early
            epoch = int(getattr(trainer, "epoch", 0)) + 1
            elapsed = round(time.time() - start_time, 2)
            raw_metrics = getattr(trainer, "metrics", {}) or {}
            clean_metrics: dict[str, float] = {}
            for k, v in raw_metrics.items():
                try:
                    clean_metrics[str(k)] = round(float(v), 5)
                except (TypeError, ValueError):
                    continue

            map50 = clean_metrics.get("metrics/mAP50(B)", 0.0)
            if map50 > state.best_map50:
                state.best_map50 = map50

            state.current_epoch = epoch
            state.metrics = clean_metrics
            state.elapsed_s = elapsed

            if stop_file.exists():
                stopped_early = True
                trainer.stop = True

            state.to_file(state_file)

            event = TrainingEvent(
                epoch=epoch,
                metrics=clean_metrics,
                timestamp=datetime.now(timezone.utc).isoformat(),
                elapsed_s=elapsed,
            )
            with open(events_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
                f.flush()

        model.add_callback("on_fit_epoch_end", on_fit_epoch_end)

        try:
            model.train(
                data=str(config.data_yaml),
                epochs=config.epochs,
                batch=config.batch,
                imgsz=config.imgsz,
                patience=config.patience,
                amp=config.amp,
                device=config.device,
                seed=config.seed,
                project=str(run_dir),
                name="yolo_train",
                exist_ok=True,
                verbose=False,
            )
        except Exception as exc:
            state.status = "failed"
            state.error_message = str(exc)
            state.elapsed_s = round(time.time() - start_time, 2)
            state.to_file(state_file)
            raise

    # Copy checkpoints if produced in ultralytics run subfolder
    yolo_weights = run_dir / "yolo_train" / "weights"
    if yolo_weights.is_dir():
        if (yolo_weights / "best.pt").is_file():
            shutil.copy2(yolo_weights / "best.pt", weights_dir / "best.pt")
        if (yolo_weights / "last.pt").is_file():
            shutil.copy2(yolo_weights / "last.pt", weights_dir / "last.pt")

    if (weights_dir / "best.pt").is_file():
        state.checkpoint_paths["best"] = str((weights_dir / "best.pt").resolve())
    if (weights_dir / "last.pt").is_file():
        state.checkpoint_paths["last"] = str((weights_dir / "last.pt").resolve())

    if stopped_early or stop_file.exists():
        state.status = "stopped"
    elif state.status != "failed":
        state.status = "completed"

    state.elapsed_s = round(time.time() - start_time, 2)
    state.to_file(state_file)
    return state


def main() -> None:
    """CLI entry point for running training in a subprocess."""
    parser = argparse.ArgumentParser(description="TrafficVision Background Training Subprocess")
    parser.add_argument("--config", type=Path, required=True, help="Path to run_config.json")
    args = parser.parse_args()
    run_training_subprocess(args.config)


if __name__ == "__main__":
    main()
