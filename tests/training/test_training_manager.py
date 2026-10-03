"""Tests for TrainingManager background subprocess lifecycle, crash recovery, and state tracking."""

from __future__ import annotations

import sys
from pathlib import Path

from trafficvision.training.config import TrainingConfig
from trafficvision.training.manager import TrainingManager
from trafficvision.training.state import TrainingEvent, TrainingState


def test_start_training_creates_artifacts_and_records_pid(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    # Use a dummy script that sleeps briefly
    dummy_cmd = [sys.executable, "-c", "import time; time.sleep(1)"]
    manager = TrainingManager(runs_dir=runs_dir, runner_cmd=dummy_cmd)

    config = TrainingConfig(
        run_id="run_test_01",
        data_yaml=tmp_path / "data.yaml",
        epochs=10,
        batch=4,
    )

    state = manager.start_training(config)

    assert state.run_id == "run_test_01"
    assert state.status == "running"
    assert state.pid is not None
    assert state.total_epochs == 10

    run_dir = runs_dir / "run_test_01"
    assert run_dir.is_dir()

    # Check run_config.json
    config_file = run_dir / "run_config.json"
    assert config_file.is_file()
    saved_config = TrainingConfig.model_validate_json(config_file.read_text(encoding="utf-8"))
    assert saved_config.run_id == "run_test_01"

    # Check run.pid
    pid_file = run_dir / "run.pid"
    assert pid_file.is_file()
    pid = int(pid_file.read_text(encoding="utf-8").strip())
    assert pid == state.pid

    # Check state.json
    state_file = run_dir / "state.json"
    assert state_file.is_file()
    saved_state = TrainingState.from_file(state_file)
    assert saved_state.status == "running"
    assert saved_state.pid == pid

    # Check train.log exists
    log_file = run_dir / "train.log"
    assert log_file.is_file()


def test_get_state_reads_state_file_and_events(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    manager = TrainingManager(runs_dir=runs_dir)

    run_dir = runs_dir / "run_metrics_test"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Fake an active state with current process PID (so it appears alive)
    import os

    current_pid = os.getpid()
    state = TrainingState(
        run_id="run_metrics_test",
        status="running",
        current_epoch=3,
        total_epochs=20,
        best_map50=0.68,
        metrics={"mAP50": 0.68, "loss": 0.25},
        elapsed_s=42.0,
        pid=current_pid,
    )
    state.to_file(run_dir / "state.json")

    # Add events to events.jsonl
    events_file = run_dir / "events.jsonl"
    e1 = TrainingEvent(
        epoch=1, metrics={"mAP50": 0.50}, timestamp="2026-09-29T00:00:00Z", elapsed_s=14.0
    )
    e2 = TrainingEvent(
        epoch=2, metrics={"mAP50": 0.61}, timestamp="2026-09-29T00:01:00Z", elapsed_s=28.0
    )
    e3 = TrainingEvent(
        epoch=3, metrics={"mAP50": 0.68}, timestamp="2026-09-29T00:02:00Z", elapsed_s=42.0
    )
    events_file.write_text(f"{e1.to_json()}\n{e2.to_json()}\n{e3.to_json()}\n", encoding="utf-8")

    loaded_state = manager.get_state("run_metrics_test")
    assert loaded_state.current_epoch == 3
    assert loaded_state.best_map50 == 0.68
    assert loaded_state.status == "running"

    events = manager.get_events("run_metrics_test")
    assert len(events) == 3
    assert events[1].epoch == 2
    assert events[2].metrics["mAP50"] == 0.68


def test_get_events_skips_partial_or_corrupt_lines(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    manager = TrainingManager(runs_dir=runs_dir)

    run_dir = runs_dir / "run_corrupt_events"
    run_dir.mkdir(parents=True, exist_ok=True)

    events_file = run_dir / "events.jsonl"
    e1 = TrainingEvent(
        epoch=1, metrics={"mAP50": 0.50}, timestamp="2026-09-29T00:00:00Z", elapsed_s=14.0
    )
    # Write one valid event, one half-written / corrupt JSON line, and another valid event
    content = f'{e1.to_json()}\n{{"epoch": 2, "metrics":\n{e1.to_json()}\n'
    events_file.write_text(content, encoding="utf-8")

    events = manager.get_events("run_corrupt_events")
    assert len(events) == 2


def test_stop_training_creates_stop_signal_file(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    manager = TrainingManager(runs_dir=runs_dir)

    run_dir = runs_dir / "run_stop_test"
    run_dir.mkdir(parents=True, exist_ok=True)

    manager.stop_training("run_stop_test")

    signal_file = run_dir / "stop.signal"
    assert signal_file.is_file()


def test_crash_recovery_transitions_dead_process_to_failed(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    manager = TrainingManager(runs_dir=runs_dir)

    run_dir = runs_dir / "run_crashed"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Non-existent dead PID
    dead_pid = 9999999
    initial_state = TrainingState(
        run_id="run_crashed",
        status="running",
        current_epoch=2,
        total_epochs=10,
        pid=dead_pid,
    )
    initial_state.to_file(run_dir / "state.json")

    # get_state should detect PID is dead and transition status to failed
    recovered_state = manager.get_state("run_crashed")
    assert recovered_state.status == "failed"
    assert recovered_state.error_message == "Process terminated unexpectedly"

    # Verify persisted to state.json
    persisted_state = TrainingState.from_file(run_dir / "state.json")
    assert persisted_state.status == "failed"
    assert persisted_state.error_message == "Process terminated unexpectedly"


def test_list_runs_returns_all_runs(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    manager = TrainingManager(runs_dir=runs_dir)

    # Run 1: completed
    r1 = runs_dir / "run_alpha"
    r1.mkdir(parents=True, exist_ok=True)
    TrainingState(
        run_id="run_alpha", status="completed", current_epoch=10, total_epochs=10
    ).to_file(r1 / "state.json")

    # Run 2: stopped
    r2 = runs_dir / "run_beta"
    r2.mkdir(parents=True, exist_ok=True)
    TrainingState(run_id="run_beta", status="stopped", current_epoch=5, total_epochs=10).to_file(
        r2 / "state.json"
    )

    runs = manager.list_runs()
    run_ids = {r.run_id for r in runs}
    assert run_ids == {"run_alpha", "run_beta"}


def test_manager_init_with_app_paths(tmp_path: Path) -> None:
    from trafficvision.config import AppPaths

    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    manager = TrainingManager(paths=paths)
    assert manager.runs_dir == paths.runs
    assert manager.working_dir == tmp_path.resolve()


def test_resume_training_relaunches_failed_run_from_last_checkpoint_with_safe_workers(
    tmp_path: Path,
) -> None:
    """Resume keeps the original run progress but lowers DataLoader concurrency."""
    runs_dir = tmp_path / "runs"
    manager = TrainingManager(
        runs_dir=runs_dir,
        runner_cmd=[sys.executable, "-c", "import time; time.sleep(0.1)"],
    )
    run_id = "run_resume"
    run_dir = runs_dir / run_id
    checkpoint = run_dir / "weights" / "last.pt"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"checkpoint")
    (run_dir / "run_config.json").write_text(
        TrainingConfig(
            run_id=run_id,
            data_yaml=tmp_path / "data.yaml",
            epochs=10,
            batch=2,
            workers=6,
        ).model_dump_json(),
        encoding="utf-8",
    )
    TrainingState(
        run_id=run_id,
        status="failed",
        current_epoch=4,
        total_epochs=10,
        checkpoint_paths={"last": str(checkpoint)},
    ).to_file(run_dir / "state.json")

    resumed = manager.resume_training(run_id)

    saved_config = TrainingConfig.model_validate_json(
        (run_dir / "run_config.json").read_text(encoding="utf-8")
    )
    assert resumed.status == "running"
    assert resumed.current_epoch == 4
    assert resumed.pid is not None
    assert saved_config.resume_checkpoint == checkpoint
    assert saved_config.workers == 0
