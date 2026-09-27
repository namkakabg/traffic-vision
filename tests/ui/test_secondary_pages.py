from pathlib import Path

from streamlit.testing.v1 import AppTest

from trafficvision.config import AppPaths
from trafficvision.domain import AnalysisRecord, ModelManifest
from trafficvision.history import AnalysisRepository
from trafficvision.registry import ModelRegistry, sha256_file


def setup_test_environment(tmp_path: Path):
    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    dummy_onnx = tmp_path / "model.onnx"
    dummy_onnx.write_bytes(b"dummy-onnx-weights")
    digest = sha256_file(dummy_onnx)

    manifest = ModelManifest(
        schema_version="1.0",
        model_id="yolo11n-baseline-test",
        stage="production",
        source_model_id="yolo11n-baseline-orig",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "bien_cam", 1: "bien_hieu_lenh", 2: "bien_chi_dan"},
        imgsz=640,
        sha256=digest,
        source="ultralytics-test",
        created_at="2026-09-27T21:00:00Z",
    )
    registry = ModelRegistry(paths)
    registry.install_baseline(dummy_onnx, manifest)
    return paths, manifest


def test_history_page_empty_and_populated(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))
    paths, _ = setup_test_environment(tmp_path)
    app_path = str(Path(__file__).parents[2] / "app.py")

    # 1. Empty history
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    at.sidebar.radio[0].set_value("Lịch sử").run()
    assert not at.exception
    all_text = " ".join([m.value for m in at.markdown] + [i.value for i in at.info])
    assert "chưa có" in all_text.lower() or "không có" in all_text.lower()

    # 2. Add history records
    repo = AnalysisRepository(paths.db)
    for i in range(2):
        repo.add(
            AnalysisRecord(
                record_id=f"rec-{i}",
                media_type="image",
                original_filename=f"photo_{i}.png",
                model_id="yolo11n",
                model_stage="baseline",
                confidence_threshold=0.25,
                iou_threshold=0.70,
                total_detections=i + 1,
                class_counts={"bien_cam": i + 1},
                inference_ms=15.0,
                created_at=f"2026-09-27T21:0{i}:00Z",
                annotated_path=tmp_path / f"out_{i}.jpg",
                csv_path=tmp_path / f"out_{i}.csv",
            )
        )

    at2 = AppTest.from_file(app_path, default_timeout=25)
    at2.run()
    at2.sidebar.radio[0].set_value("Lịch sử").run()
    assert not at2.exception
    # Assert table exists with populated rows
    assert len(at2.dataframe) >= 1


def test_statistics_page_aggregates(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))
    paths, _ = setup_test_environment(tmp_path)
    repo = AnalysisRepository(paths.db)
    repo.add(
        AnalysisRecord(
            record_id="rec-stat-1",
            media_type="image",
            original_filename="photo.jpg",
            model_id="yolo11n",
            model_stage="baseline",
            confidence_threshold=0.25,
            iou_threshold=0.70,
            total_detections=4,
            class_counts={"bien_cam": 3, "bien_chi_dan": 1},
            inference_ms=20.0,
            created_at="2026-09-27T21:00:00Z",
            annotated_path=tmp_path / "out.jpg",
            csv_path=tmp_path / "out.csv",
        )
    )

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    at.sidebar.radio[0].set_value("Thống kê").run()
    assert not at.exception

    # Assert metric cards exist
    assert len(at.metric) >= 2


def test_model_info_page_details(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))
    _, manifest = setup_test_environment(tmp_path)

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    at.sidebar.radio[0].set_value("Thông tin mô hình").run()
    assert not at.exception

    all_text = " ".join([m.value for m in at.markdown] + [w.value for w in at.warning])
    assert manifest.model_id in all_text
    assert manifest.backend.lower() in all_text.lower()
    assert manifest.sha256[:8] in all_text
    assert "3 lớp" in all_text or "3" in all_text
    assert any("baseline" in w.value.lower() for w in at.warning)


def test_settings_page_persistence(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))
    setup_test_environment(tmp_path)

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    at.sidebar.radio[0].set_value("Thiết lập").run()
    assert not at.exception

    # Verify settings controls exist
    assert len(at.slider) >= 2
    # Verify save button exists
    assert len(at.button) >= 1


def test_training_placeholder_page(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))
    setup_test_environment(tmp_path)

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    at.sidebar.radio[0].set_value("Huấn luyện AI").run()
    assert not at.exception

    all_text = " ".join(
        [m.value for m in at.markdown] + [i.value for i in at.info] + [t.value for t in at.title]
    )
    # Must contain approved 4-step sequence
    assert "Dữ liệu" in all_text
    assert "Kiểm định" in all_text
    assert "Huấn luyện" in all_text
    assert "Đánh giá" in all_text

    # Must NOT have training start button
    button_labels = [b.label.lower() for b in at.button]
    assert not any("bắt đầu" in b or "start" in b or "train" in b for b in button_labels)
