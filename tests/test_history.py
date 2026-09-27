from pathlib import Path

from trafficvision.domain import AnalysisRecord
from trafficvision.history import AnalysisRepository


def test_history_repository_operations(tmp_path: Path):
    db_path = tmp_path / "test_history.db"
    repo = AnalysisRepository(db_path)

    # Initially empty
    assert repo.list_recent() == []
    assert repo.class_totals() == {}

    # Insert 3 records
    for i in range(3):
        rec = AnalysisRecord(
            record_id=f"rec-{i}",
            media_type="image",
            original_filename=f"ảnh_giao_thông_{i}.jpg",
            model_id="yolo11n",
            model_stage="baseline",
            confidence_threshold=0.25,
            iou_threshold=0.70,
            total_detections=i + 1,
            class_counts={"bien_cam": i, "bien_nguy_hiem": 1},
            inference_ms=10.0 + i,
            created_at=f"2026-09-27T21:0{i}:00Z",
            annotated_path=tmp_path / f"annotated_{i}.jpg",
            csv_path=tmp_path / f"results_{i}.csv",
        )
        repo.add(rec)

    # Test list_recent ordering (newest first)
    recent = repo.list_recent(limit=2)
    assert len(recent) == 2
    assert recent[0].record_id == "rec-2"
    assert recent[1].record_id == "rec-1"
    assert recent[0].original_filename == "ảnh_giao_thông_2.jpg"

    # Test class totals aggregate
    totals = repo.class_totals()
    # bien_cam: 0 + 1 + 2 = 3
    # bien_nguy_hiem: 1 + 1 + 1 = 3
    assert totals == {"bien_cam": 3, "bien_nguy_hiem": 3}
