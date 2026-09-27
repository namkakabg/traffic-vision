from pathlib import Path

from streamlit.testing.v1 import AppTest

from trafficvision.config import AppPaths
from trafficvision.domain import ModelManifest
from trafficvision.registry import ModelRegistry, sha256_file


def test_analysis_page_with_baseline_model(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))

    # Setup dummy baseline model in production
    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    dummy_onnx = tmp_path / "model.onnx"
    dummy_onnx.write_bytes(b"dummy-onnx-bytes")
    digest = sha256_file(dummy_onnx)

    manifest = ModelManifest(
        schema_version="1.0",
        model_id="yolo11n-baseline-test",
        stage="production",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "person", 1: "bicycle"},
        imgsz=640,
        sha256=digest,
        source="test",
        created_at="2026-09-27T21:00:00Z",
    )
    registry = ModelRegistry(paths)
    registry.install_baseline(dummy_onnx, manifest)

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()

    assert not at.exception

    # Assert baseline warning banner is visible
    warning_texts = [w.value for w in at.warning]
    assert any("baseline" in w.lower() and "chưa fine-tune" in w.lower() for w in warning_texts)

    # Assert real class count (2 classes)
    all_text = " ".join(
        [m.value for m in at.markdown]
        + [c.value for c in at.caption]
        + [s.value for s in at.sidebar.markdown]
    )
    assert "2" in all_text

    # Assert no fabricated metrics
    assert "mAP" not in all_text
    assert "82 lớp" not in all_text

    # Assert uploaders exist with allowed extensions
    uploaders = at.file_uploader
    assert len(uploaders) >= 1
    # Check that image uploader has valid types
    image_uploader = uploaders[0]
    assert {ext.lstrip(".") for ext in image_uploader.allowed_type} == {"jpg", "jpeg", "png"}
