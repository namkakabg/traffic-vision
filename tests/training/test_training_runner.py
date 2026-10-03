"""Tests for runner.py execution, callback handling, stop signals, and checkpoint packaging."""

from __future__ import annotations

import sys
import types
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


def test_runner_syncs_checkpoints_mid_run_and_preserves_on_crash(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_crash_checkpoint"
    run_dir.mkdir(parents=True, exist_ok=True)

    config = TrainingConfig(
        run_id="run_crash_checkpoint",
        data_yaml=tmp_path / "data.yaml",
        epochs=5,
        batch=4,
    )
    config_file = run_dir / "run_config.json"
    config_file.write_text(config.model_dump_json(), encoding="utf-8")

    def mock_train_crash_at_epoch_2(
        config: TrainingConfig,
        run_dir: Path,
        state: TrainingState,
        state_file: Path,
        events_file: Path,
        stop_file: Path,
        weights_dir: Path,
    ) -> None:
        # Simulate epoch 1 completing and saving checkpoint
        (weights_dir / "last.pt").write_bytes(b"epoch1_weights")
        (weights_dir / "best.pt").write_bytes(b"epoch1_weights")
        state.checkpoint_paths["last"] = str((weights_dir / "last.pt").resolve())
        state.checkpoint_paths["best"] = str((weights_dir / "best.pt").resolve())
        state.current_epoch = 1
        state.to_file(state_file)

        # Crash during epoch 2
        raise RuntimeError("Crash on epoch 2")

    with pytest.raises(RuntimeError, match="Crash on epoch 2"):
        run_training_subprocess(config_file, train_fn=mock_train_crash_at_epoch_2)

    # Checkpoint from epoch 1 must remain intact on disk
    assert (run_dir / "weights" / "last.pt").is_file()
    assert (run_dir / "weights" / "best.pt").is_file()
    assert (run_dir / "weights" / "last.pt").read_bytes() == b"epoch1_weights"

    saved_state = TrainingState.from_file(run_dir / "state.json")
    assert saved_state.status == "failed"
    assert "last" in saved_state.checkpoint_paths


def test_runner_resumes_checkpoint_with_configured_safe_worker_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A restart must pass the saved checkpoint and worker limit to Ultralytics."""
    run_dir = tmp_path / "run_resume"
    weights_dir = run_dir / "weights"
    weights_dir.mkdir(parents=True)
    checkpoint = weights_dir / "last.pt"
    checkpoint.write_bytes(b"checkpoint")
    captured: dict[str, Any] = {}

    class FakeYOLO:
        trainer = None

        def __init__(self, model_path: str) -> None:
            captured["model_path"] = model_path

        def add_callback(self, event: str, callback: Any) -> None:
            captured["callback_event"] = event

        def train(self, **kwargs: Any) -> None:
            captured["train_kwargs"] = kwargs

    monkeypatch.setitem(sys.modules, "ultralytics", types.SimpleNamespace(YOLO=FakeYOLO))
    config = TrainingConfig(
        run_id="run_resume",
        data_yaml=tmp_path / "data.yaml",
        epochs=10,
        batch=2,
        workers=0,
        resume_checkpoint=checkpoint,
    )
    config_file = run_dir / "run_config.json"
    config_file.write_text(config.model_dump_json(), encoding="utf-8")

    final_state = run_training_subprocess(config_file)

    assert final_state.status == "completed"
    assert captured["model_path"] == str(checkpoint)
    assert captured["train_kwargs"]["resume"] is True
    assert captured["train_kwargs"]["workers"] == 0


def test_runner_finalizes_completed_default_training_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A normal completed run must create a Candidate without requiring a UI retry."""
    from trafficvision.training import candidate

    run_dir = tmp_path / "run_finalize"
    run_dir.mkdir()
    data_yaml = tmp_path / "data.yaml"
    data_yaml.write_text("names:\n  0: Stop\n", encoding="utf-8")
    captured: dict[str, Any] = {}

    class FakeYOLO:
        trainer = None

        def __init__(self, model_path: str) -> None:
            captured["model_path"] = model_path

        def add_callback(self, event: str, callback: Any) -> None:
            captured["callback_event"] = event

        def train(self, **kwargs: Any) -> None:
            weights = Path(kwargs["project"]) / kwargs["name"] / "weights"
            weights.mkdir(parents=True)
            (weights / "best.pt").write_bytes(b"best")
            (weights / "last.pt").write_bytes(b"last")

    def fake_finalize(**kwargs: Any) -> Path:
        captured["finalize_kwargs"] = kwargs
        candidate_dir = run_dir / "candidate"
        candidate_dir.mkdir()
        (candidate_dir / "manifest.json").write_text("{}", encoding="utf-8")
        return candidate_dir

    monkeypatch.setitem(sys.modules, "ultralytics", types.SimpleNamespace(YOLO=FakeYOLO))
    monkeypatch.setattr(candidate, "finalize_checkpoint", fake_finalize)
    config = TrainingConfig(
        run_id="run_finalize",
        data_yaml=data_yaml,
        epochs=1,
        batch=1,
        device="cpu",
        imgsz=640,
    )
    config_file = run_dir / "run_config.json"
    config_file.write_text(config.model_dump_json(), encoding="utf-8")

    final_state = run_training_subprocess(config_file)

    assert final_state.status == "completed"
    assert (run_dir / "candidate" / "manifest.json").is_file()
    assert captured["finalize_kwargs"]["checkpoint_path"] == run_dir / "weights" / "best.pt"
    assert captured["finalize_kwargs"]["device"] == "cpu"
