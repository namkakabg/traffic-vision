from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from trafficvision.domain import AnalysisRecord


class AnalysisRepository:
    """SQLite repository for persisting and querying analysis history."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_history (
                    record_id TEXT PRIMARY KEY,
                    media_type TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    model_stage TEXT NOT NULL,
                    confidence_threshold REAL NOT NULL,
                    iou_threshold REAL NOT NULL,
                    total_detections INTEGER NOT NULL,
                    class_counts TEXT NOT NULL,
                    inference_ms REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    annotated_path TEXT NOT NULL,
                    csv_path TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add(self, record: AnalysisRecord) -> None:
        """Insert a completed analysis record."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO analysis_history (
                    record_id, media_type, original_filename, model_id, model_stage,
                    confidence_threshold, iou_threshold, total_detections, class_counts,
                    inference_ms, created_at, annotated_path, csv_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    record.media_type,
                    record.original_filename,
                    record.model_id,
                    record.model_stage,
                    record.confidence_threshold,
                    record.iou_threshold,
                    record.total_detections,
                    json.dumps(record.class_counts, ensure_ascii=False),
                    record.inference_ms,
                    record.created_at,
                    str(record.annotated_path),
                    str(record.csv_path),
                ),
            )
            conn.commit()

    def list_recent(self, limit: int = 50) -> list[AnalysisRecord]:
        """Return newest analysis records up to limit."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM analysis_history
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        records: list[AnalysisRecord] = []
        for r in rows:
            counts: dict[str, int] = json.loads(r["class_counts"])
            rec = AnalysisRecord(
                record_id=r["record_id"],
                media_type=r["media_type"],
                original_filename=r["original_filename"],
                model_id=r["model_id"],
                model_stage=r["model_stage"],
                confidence_threshold=float(r["confidence_threshold"]),
                iou_threshold=float(r["iou_threshold"]),
                total_detections=int(r["total_detections"]),
                class_counts=counts,
                inference_ms=float(r["inference_ms"]),
                created_at=r["created_at"],
                annotated_path=Path(r["annotated_path"]),
                csv_path=Path(r["csv_path"]),
            )
            records.append(rec)
        return records

    def class_totals(self) -> dict[str, int]:
        """Aggregate total detections by class across all analysis records."""
        totals: dict[str, int] = {}
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT class_counts FROM analysis_history")
            rows = cursor.fetchall()

        for r in rows:
            counts: dict[str, int] = json.loads(r["class_counts"])
            for cls_name, count in counts.items():
                totals[cls_name] = totals.get(cls_name, 0) + int(count)

        return totals
