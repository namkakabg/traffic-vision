"""Tests for TrainingState and TrainingEvent model serialization and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from trafficvision.training.state import TrainingEvent, TrainingState


def test_training_state_defaults() -> None:
    state = TrainingState(run_id="run_001")
    assert state.run_id == "run_001"
    assert state.status == "idle"
    assert state.current_epoch == 0
    assert state.total_epochs == 0
    assert state.best_map50 == 0.0
    assert state.metrics == {}
    assert state.elapsed_s == 0.0
    assert state.error_message is None
    assert state.pid is None
    assert state.checkpoint_paths == {}


def test_training_state_valid_statuses() -> None:
    for status in ["idle", "running", "paused", "completed", "failed", "stopped"]:
        state = TrainingState(run_id="run_test", status=status)  # type: ignore[arg-type]
        assert state.status == status


def test_training_state_invalid_status() -> None:
    with pytest.raises(ValidationError, match="status"):
        TrainingState(run_id="run_test", status="invalid_status")  # type: ignore[arg-type]


def test_training_state_file_roundtrip(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    state = TrainingState(
        run_id="run_save_test",
        status="running",
        current_epoch=5,
        total_epochs=50,
        best_map50=0.725,
        metrics={"metrics/mAP50(B)": 0.725, "loss": 0.35},
        elapsed_s=120.4,
        pid=12345,
        checkpoint_paths={"best": "/path/to/best.pt", "last": "/path/to/last.pt"},
    )
    state.to_file(state_file)
    assert state_file.is_file()

    loaded = TrainingState.from_file(state_file)
    assert loaded == state
    assert loaded.run_id == "run_save_test"
    assert loaded.status == "running"
    assert loaded.current_epoch == 5
    assert loaded.best_map50 == 0.725
    assert loaded.pid == 12345
    assert loaded.checkpoint_paths["best"] == "/path/to/best.pt"


def test_training_event_serialization() -> None:
    event = TrainingEvent(
        epoch=3,
        metrics={"mAP50": 0.65, "train_loss": 0.42},
        timestamp="2026-09-29T06:00:00Z",
        elapsed_s=45.2,
    )
    json_line = event.to_json()
    assert isinstance(json_line, str)

    restored = TrainingEvent.from_json(json_line)
    assert restored.epoch == 3
    assert restored.metrics["mAP50"] == 0.65
    assert restored.timestamp == "2026-09-29T06:00:00Z"
    assert restored.elapsed_s == 45.2
