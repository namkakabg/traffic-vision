"""Training manager orchestrating background training subprocesses and state polling."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from trafficvision.config import AppPaths
from trafficvision.training.config import TrainingConfig
from trafficvision.training.state import TrainingEvent, TrainingState


def _is_pid_alive(pid: int) -> bool:
    """Check whether a process with the given PID is currently active."""
    if pid <= 0:
        return False
    try:
        import psutil

        if psutil.pid_exists(pid):
            proc = psutil.Process(pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        return False
    except Exception:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


class TrainingManager:
    """Manages the lifecycle of background training jobs."""

    def __init__(
        self,
        paths: AppPaths | None = None,
        runs_dir: Path | str | None = None,
        python_executable: str | Path | None = None,
        runner_cmd: list[str] | None = None,
        runner_module: str = "trafficvision.training.runner",
    ) -> None:
        if runs_dir is not None:
            self.runs_dir = Path(runs_dir).resolve()
            self.working_dir = Path.cwd().resolve()
        elif isinstance(paths, AppPaths):
            self.runs_dir = paths.runs.resolve()
            self.working_dir = paths.root.resolve()
        elif paths is not None:
            self.runs_dir = Path(paths).resolve()
            self.working_dir = Path.cwd().resolve()
        else:
            self.runs_dir = Path("artifacts/runs").resolve()
            self.working_dir = Path.cwd().resolve()
        self.python_executable = (
            Path(python_executable).resolve() if python_executable else Path(sys.executable)
        )
        self.runner_cmd = runner_cmd
        self.runner_module = runner_module

    def start_training(self, config: TrainingConfig) -> TrainingState:
        """Start a new background training run.

        Writes run_config.json, initializes state.json, launches the subprocess,
        and records the process ID in run.pid.

        Args:
            config: TrainingConfig specifying hyperparameters and paths.

        Returns:
            Initial TrainingState with status 'running' and process PID.
        """
        run_dir = self.runs_dir / config.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "weights").mkdir(parents=True, exist_ok=True)

        # 1. Write run_config.json
        config_path = run_dir / "run_config.json"
        config_path.write_text(config.model_dump_json(indent=2), encoding="utf-8")

        # 2. Write initial state.json
        state_file = run_dir / "state.json"
        state = TrainingState(
            run_id=config.run_id,
            status="running",
            current_epoch=0,
            total_epochs=config.epochs,
        )
        state.to_file(state_file)

        # 3. Form subprocess command
        if self.runner_cmd is not None:
            cmd = list(self.runner_cmd) + ["--config", str(config_path)]
        else:
            cmd = [
                str(self.python_executable),
                "-m",
                self.runner_module,
                "--config",
                str(config_path),
            ]

        # 4. Prepare environment with PYTHONPATH
        env = dict(os.environ)
        src_path = str((self.working_dir / "src").resolve())
        curr_ppath = env.get("PYTHONPATH", "")
        if curr_ppath:
            env["PYTHONPATH"] = f"{src_path}{os.pathsep}{curr_ppath}"
        else:
            env["PYTHONPATH"] = src_path

        # 5. Open train.log and launch background process (closed in parent immediately)
        with open(run_dir / "train.log", "a", encoding="utf-8") as log_file:
            proc = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=str(self.working_dir),
                env=env,
            )

        # 5. Record PID
        pid_file = run_dir / "run.pid"
        pid_file.write_text(str(proc.pid), encoding="utf-8")

        state.pid = proc.pid
        state.to_file(state_file)
        return state

    def get_state(self, run_id: str) -> TrainingState:
        """Retrieve and synchronize the current state of a training run.

        If the run was recorded as 'running' but the underlying process PID is no longer
        alive without having recorded a normal completion, transitions the status to 'failed'.

        Args:
            run_id: Identifier of the run.

        Returns:
            Current, synchronized TrainingState.

        Raises:
            FileNotFoundError: If the run or its state.json does not exist.
        """
        run_dir = self.runs_dir / run_id
        state_file = run_dir / "state.json"
        if not state_file.is_file():
            raise FileNotFoundError(f"State file not found for run_id: '{run_id}'")

        state = TrainingState.from_file(state_file)

        # Crash recovery check: if running, verify PID is still alive
        if state.status == "running":
            pid: int | None = state.pid
            if pid is None:
                pid_file = run_dir / "run.pid"
                if pid_file.is_file():
                    try:
                        pid = int(pid_file.read_text(encoding="utf-8").strip())
                        state.pid = pid
                    except ValueError:
                        pid = None

            if pid is not None:
                is_alive = _is_pid_alive(pid)
                if not is_alive:
                    # Check if file was updated right at process exit
                    latest_state = TrainingState.from_file(state_file)
                    if latest_state.status == "running":
                        state.status = "failed"
                        state.error_message = "Process terminated unexpectedly"
                        state.to_file(state_file)
                    else:
                        state = latest_state
            else:
                state.status = "failed"
                state.error_message = "Process terminated unexpectedly"
                state.to_file(state_file)

        return state

    def stop_training(self, run_id: str) -> None:
        """Request training to stop cleanly after the current epoch by creating stop.signal."""
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        stop_file = run_dir / "stop.signal"
        stop_file.write_text("stop\n", encoding="utf-8")

    def get_events(self, run_id: str) -> list[TrainingEvent]:
        """Read and parse all training event records from events.jsonl."""
        events_file = self.runs_dir / run_id / "events.jsonl"
        if not events_file.is_file():
            return []

        events: list[TrainingEvent] = []
        for line in events_file.read_text(encoding="utf-8").splitlines():
            line_str = line.strip()
            if line_str:
                try:
                    events.append(TrainingEvent.from_json(line_str))
                except Exception:
                    continue
        return events

    def list_runs(self) -> list[TrainingState]:
        """List all training runs found in the runs directory."""
        if not self.runs_dir.is_dir():
            return []

        runs: list[TrainingState] = []
        for run_dir in self.runs_dir.iterdir():
            if run_dir.is_dir() and (run_dir / "state.json").is_file():
                try:
                    state = self.get_state(run_dir.name)
                    runs.append(state)
                except Exception:
                    continue

        return sorted(runs, key=lambda s: s.run_id)
