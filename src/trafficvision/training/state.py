"""State tracking and event log models for background training runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

RunStatus = Literal["idle", "running", "paused", "completed", "failed", "stopped"]


class TrainingEvent(BaseModel):
    """Event record appended to events.jsonl on each epoch completion."""

    epoch: int
    metrics: dict[str, Any] = Field(default_factory=dict)
    timestamp: str
    elapsed_s: float = 0.0

    def to_json(self) -> str:
        """Serialize event to a single JSON line."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> TrainingEvent:
        """Deserialize event from a JSON line."""
        return cls.model_validate_json(data)


class TrainingState(BaseModel):
    """Mutable/serializable state representing current progress of a training run."""

    run_id: str
    status: RunStatus = "idle"
    current_epoch: int = 0
    total_epochs: int = 0
    best_map50: float = 0.0
    metrics: dict[str, Any] = Field(default_factory=dict)
    elapsed_s: float = 0.0
    error_message: str | None = None
    pid: int | None = None
    checkpoint_paths: dict[str, str] = Field(default_factory=dict)

    def to_file(self, path: Path | str) -> None:
        """Serialize training state atomically to a JSON file."""
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = target_path.with_suffix(".tmp")
        temp_path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        temp_path.replace(target_path)

    @classmethod
    def from_file(cls, path: Path | str) -> TrainingState:
        """Deserialize training state from a JSON file."""
        target_path = Path(path)
        return cls.model_validate_json(target_path.read_text(encoding="utf-8"))
