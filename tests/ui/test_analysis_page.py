import io
from pathlib import Path
from unittest.mock import MagicMock

from PIL import Image
from streamlit.testing.v1 import AppTest

from trafficvision.config import AppPaths
from trafficvision.domain import AnalysisArtifacts, AnalysisRecord, ModelManifest
from trafficvision.registry import ModelRegistry, sha256_file
from trafficvision.service import AnalysisService


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
    assert {ext.lstrip(".") for ext in image_uploader.allowed_type} == {
        "jpg",
        "jpeg",
        "png",
        "webp",
        "heic",
        "heif",
    }


def test_analysis_page_clears_old_results_on_new_upload(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))

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

    old_annotated = tmp_path / "old_annotated.jpg"
    old_annotated.write_bytes(b"jpeg-bytes")
    old_csv = tmp_path / "old.csv"
    old_csv.write_bytes(b"class_id,name\n0,person\n")

    dummy_record = AnalysisRecord(
        record_id="dummy-1",
        media_type="image",
        original_filename="old_sign.jpg",
        model_id="yolo11n-baseline-test",
        model_stage="production",
        confidence_threshold=0.25,
        iou_threshold=0.7,
        total_detections=3,
        class_counts={"person": 3},
        inference_ms=45.0,
        created_at="2026-09-27T21:00:00Z",
        annotated_path=old_annotated,
        csv_path=old_csv,
    )

    dummy_artifacts = AnalysisArtifacts(
        record=dummy_record,
        annotated_media_path=old_annotated,
        csv_path=old_csv,
    )
    at.session_state["image_result"] = dummy_artifacts
    at.session_state["last_uploaded_image_sig"] = "old_sign.jpg_oldid_100"
    at.session_state["active_result_type"] = "image"

    # Now upload a new image
    new_img_buf = io.BytesIO()
    Image.new("RGB", (32, 32), color=(255, 0, 0)).save(new_img_buf, format="PNG")
    at.file_uploader[0].upload("new_sign.png", new_img_buf.getvalue()).run()
    assert not at.exception

    # The previous result must be automatically cleared
    assert "image_result" not in at.session_state
    assert at.session_state.get("active_result_type") != "image"


def test_analysis_page_auto_analyzes_image_on_upload(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))

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

    annotated_out = tmp_path / "auto_annotated.jpg"
    buf_ann = io.BytesIO()
    Image.new("RGB", (64, 64), color=(0, 0, 255)).save(buf_ann, format="JPEG")
    annotated_out.write_bytes(buf_ann.getvalue())
    csv_out = tmp_path / "auto_detections.csv"
    csv_out.write_bytes(b"class_id,class_name\n0,person\n")

    mock_artifacts = AnalysisArtifacts(
        record=AnalysisRecord(
            record_id="auto-rec-1",
            media_type="image",
            original_filename="test_auto.jpg",
            model_id="yolo11n-baseline-test",
            model_stage="production",
            confidence_threshold=0.25,
            iou_threshold=0.7,
            total_detections=1,
            class_counts={"person": 1},
            inference_ms=18.5,
            created_at="2026-10-04T00:00:00Z",
            annotated_path=annotated_out,
            csv_path=csv_out,
        ),
        annotated_media_path=annotated_out,
        csv_path=csv_out,
    )

    mock_analyze = MagicMock(return_value=mock_artifacts)
    monkeypatch.setattr(AnalysisService, "analyze_image_upload", mock_analyze)

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    assert not at.exception

    # Initially before upload, analyze has not been called
    assert mock_analyze.call_count == 0

    # Upload image
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color=(0, 255, 0)).save(buf, format="JPEG")
    at.file_uploader[0].upload("test_auto.jpg", buf.getvalue()).run()
    assert not at.exception

    # Verify that analysis was called automatically!
    assert mock_analyze.call_count >= 1
    assert "image_result" in at.session_state
    assert at.session_state["image_result"] == mock_artifacts

    # Verify that "Phân tích lại" button is available
    reanalyze_btns = [b for b in at.button if b.key == "btn_reanalyze_img"]
    assert len(reanalyze_btns) == 1

    # Clicking re-analyze should trigger analysis again
    prev_calls = mock_analyze.call_count
    reanalyze_btns[0].click().run()
    assert not at.exception
    assert mock_analyze.call_count == prev_calls + 1


def test_analysis_page_detection_row_selection_spotlight(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))

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

    # Prepare staged original image and annotated image
    staged_img_path = tmp_path / "staged.jpg"
    annotated_out = tmp_path / "annotated.jpg"
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(128, 128, 128)).save(buf, format="JPEG")
    staged_img_path.write_bytes(buf.getvalue())
    annotated_out.write_bytes(buf.getvalue())

    csv_out = tmp_path / "detections.csv"
    csv_out.write_bytes(b"class_id,class_name,confidence\n0,person,0.88\n1,bicycle,0.75\n")

    from trafficvision.domain import Detection

    det1 = Detection(class_id=0, class_name="person", confidence=0.88, xyxy=(10.0, 10.0, 50.0, 50.0))
    det2 = Detection(class_id=1, class_name="bicycle", confidence=0.75, xyxy=(55.0, 20.0, 90.0, 80.0))

    mock_artifacts = AnalysisArtifacts(
        record=AnalysisRecord(
            record_id="spotlight-rec-1",
            media_type="image",
            original_filename="spotlight_test.jpg",
            model_id="yolo11n-baseline-test",
            model_stage="production",
            confidence_threshold=0.25,
            iou_threshold=0.7,
            total_detections=2,
            class_counts={"person": 1, "bicycle": 1},
            inference_ms=22.0,
            created_at="2026-10-04T00:00:00Z",
            annotated_path=annotated_out,
            csv_path=csv_out,
        ),
        annotated_media_path=annotated_out,
        csv_path=csv_out,
        detections=(det1, det2),
        staged_media_path=staged_img_path,
    )

    mock_analyze = MagicMock(return_value=mock_artifacts)
    monkeypatch.setattr(AnalysisService, "analyze_image_upload", mock_analyze)

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    assert not at.exception

    # Upload test image
    at.file_uploader[0].upload("spotlight_test.jpg", buf.getvalue()).run()
    assert not at.exception

    # Selection buttons should be rendered for each detection
    det_btn_0 = [b for b in at.button if b.key == "det_row_select_0"]
    det_btn_1 = [b for b in at.button if b.key == "det_row_select_1"]
    assert len(det_btn_0) == 1
    assert len(det_btn_1) == 1

    # Initially, no selection is active
    assert at.session_state.get("selected_detection_idx") is None

    # Click on the first detection row
    det_btn_0[0].click().run()
    assert not at.exception
    assert at.session_state.get("selected_detection_idx") == 0

    # Deselect button should appear
    clear_btn = [b for b in at.button if b.key == "btn_clear_selection"]
    assert len(clear_btn) == 1

    # Click clear selection button
    clear_btn[0].click().run()
    assert not at.exception
    assert at.session_state.get("selected_detection_idx") is None


