"""Tests for runner.py execution, callback handling, stop signals, and checkpoint packaging."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from trafficvision.training.config import TrainingConfig
from trafficvision.training.runner import run_training_subprocess
from trafficvision.training.state import TrainingEvent, TrainingState


def test_runner_executes_with_custom_train_fn(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_test_runner"
    run_dir.mkdir(parents=True, exist_ok=True)

    config = TrainingConfig(
        run_id="run_test_runner",
        data_yaml=tmp_path / "data.yaml",
        epochs=3,
        batch=4,
    )
    config_file = run_dir / "run_config.json"
    config_file.write_text(config.model_dump_json(), encoding="utf-8")

    def mock_train_fn(
        config: TrainingConfig,
        run_dir: Path,
        state: TrainingState,
        state_file: Path,
        events_file: Path,
        stop_file: Path,
        weights_dir: Path,
    ) -> None:
        for epoch in range(1, config.epochs + 1):
            state.current_epoch = epoch
            state.metrics = {"mAP50": 0.5 + 0.1 * epoch, "loss": 0.5 - 0.1 * epoch}
            state.best_map50 = max(state.best_map50, state.metrics["mAP50"])
            state.to_file(state_file)

            event = TrainingEvent(
                epoch=epoch,
                metrics=state.metrics,
                timestamp="2026-09-29T00:00:00Z",
                elapsed_s=float(epoch),
            )
            with open(events_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")

        # Create dummy weights
        (weights_dir / "best.pt").write_bytes(b"dummy_best")
        (weights_dir / "last.pt").write_bytes(b"dummy_last")

    final_state = run_training_subprocess(config_file, train_fn=mock_train_fn)

    assert final_state.status == "completed"
    assert final_state.current_epoch == 3
    assert final_state.best_map50 == 0.8
    assert "best" in final_state.checkpoint_paths
    assert "last" in final_state.checkpoint_paths
    assert Path(final_state.checkpoint_paths["best"]).is_file()

    # Check events file
    events_lines = (run_dir / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(events_lines) == 3


def test_runner_stops_early_on_stop_signal(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_stop_runner"
    run_dir.mkdir(parents=True, exist_ok=True)

    config = TrainingConfig(
        run_id="run_stop_runner",
        data_yaml=tmp_path / "data.yaml",
        epochs=10,
        batch=4,
    )
    config_file = run_dir / "run_config.json"
    config_file.write_text(config.model_dump_json(), encoding="utf-8")

    def mock_train_fn_with_stop(
        config: TrainingConfig,
        run_dir: Path,
        state: TrainingState,
        state_file: Path,
        events_file: Path,
        stop_file: Path,
        weights_dir: Path,
    ) -> None:
        for epoch in range(1, config.epochs + 1):
            if epoch == 2:
                # Trigger stop signal
                stop_file.write_text("stop\n", encoding="utf-8")

            if stop_file.exists():
                break

            state.current_epoch = epoch
            state.to_file(state_file)

    final_state = run_training_subprocess(config_file, train_fn=mock_train_fn_with_stop)
    assert final_state.status == "stopped"
    assert final_state.current_epoch == 1


def test_runner_handles_exception_and_marks_failed(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_error_runner"
    run_dir.mkdir(parents=True, exist_ok=True)

    config = TrainingConfig(
        run_id="run_error_runner",
        data_yaml=tmp_path / "data.yaml",
        epochs=5,
        batch=4,
    )
    config_file = run_dir / "run_config.json"
    config_file.write_text(config.model_dump_json(), encoding="utf-8")

    def mock_failing_train_fn(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Simulated GPU out of memory")

    with pytest.raises(RuntimeError, match="Simulated GPU out of memory"):
        run_training_subprocess(config_file, train_fn=mock_failing_train_fn)

    saved_state = TrainingState.from_file(run_dir / "state.json")
    assert saved_state.status == "failed"
    assert "Simulated GPU out of memory" in (saved_state.error_message or "")
