from pathlib import Path

import pytest
from pydantic import ValidationError

from trafficvision.domain import (
    AnalysisArtifacts,
    AnalysisRecord,
    Detection,
    ImageAnalysis,
    InferenceOptions,
    ModelManifest,
    RegisteredModel,
    StagedMedia,
    VideoAnalysis,
    VideoProgress,
)


def test_model_manifest_dynamic_classes_and_json_roundtrip():
    manifest_data = {
        "schema_version": "1.0",
        "model_id": "yolo11n-baseline-20260927",
        "stage": "baseline",
        "source_model_id": None,
        "artifact_filename": "model.onnx",
        "backend": "onnx",
        "task": "detect",
        "class_names": {0: "person", 1: "bicycle", 2: "car"},
        "imgsz": 640,
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "source": "ultralytics-yolo11n",
        "created_at": "2026-09-27T21:00:00Z",
        "metrics": None,
    }
    manifest = ModelManifest.model_validate(manifest_data)
    assert manifest.class_names[0] == "person"
    assert manifest.class_names[2] == "car"
    assert len(manifest.class_names) == 3

    json_str = manifest.model_dump_json()
    reloaded = ModelManifest.model_validate_json(json_str)
    assert reloaded == manifest


def test_model_manifest_rejects_empty_classes_or_invalid_sha256():
    base_data = {
        "schema_version": "1.0",
        "model_id": "test-model",
        "stage": "baseline",
        "artifact_filename": "model.onnx",
        "backend": "onnx",
        "task": "detect",
        "class_names": {},
        "imgsz": 640,
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "source": "test",
        "created_at": "2026-09-27T21:00:00Z",
    }
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(base_data)

    invalid_sha = base_data.copy()
    invalid_sha["class_names"] = {0: "test"}
    invalid_sha["sha256"] = "invalid-sha-too-short"
    with pytest.raises(ValidationError):
        ModelManifest.model_validate(invalid_sha)


def test_detection_validates_confidence_and_bounds():
    valid = Detection(
        class_id=0,
        class_name="person",
        confidence=0.85,
        xyxy=(10.0, 20.0, 100.0, 200.0),
    )
    assert valid.confidence == 0.85

    with pytest.raises(ValidationError):
        Detection(
            class_id=0,
            class_name="person",
            confidence=1.5,
            xyxy=(10.0, 20.0, 100.0, 200.0),
        )

    with pytest.raises(ValidationError):
        Detection(
            class_id=0,
            class_name="person",
            confidence=-0.1,
            xyxy=(10.0, 20.0, 100.0, 200.0),
        )

    with pytest.raises(ValidationError):
        Detection(
            class_id=0,
            class_name="person",
            confidence=0.9,
            xyxy=(100.0, 20.0, 50.0, 200.0),  # x2 < x1
        )

    with pytest.raises(ValidationError):
        Detection(
            class_id=0,
            class_name="person",
            confidence=0.9,
            xyxy=(10.0, 200.0, 100.0, 50.0),  # y2 < y1
        )


def test_domain_models_instantiation(tmp_path: Path):
    opts = InferenceOptions(confidence=0.3, iou=0.5)
    assert opts.confidence == 0.3

    staged = StagedMedia(
        media_id="abc-123",
        original_filename="sample.jpg",
        staged_path=tmp_path / "sample.jpg",
        media_type="image",
        size_bytes=1024,
    )
    assert staged.media_id == "abc-123"

    prog = VideoProgress(
        current_frame=10,
        total_frames=100,
        fraction=0.1,
        fps=25.0,
    )
    assert prog.fraction == 0.1

    det = Detection(
        class_id=0,
        class_name="person",
        confidence=0.9,
        xyxy=(1.0, 2.0, 3.0, 4.0),
    )
    img_analysis = ImageAnalysis(
        width=640,
        height=480,
        detections=(det,),
        inference_ms=12.5,
    )
    assert len(img_analysis.detections) == 1

    vid_analysis = VideoAnalysis(
        width=1280,
        height=720,
        fps=30.0,
        total_frames=100,
        processed_frames=100,
        detection_counts_by_class={"person": 5},
        inference_ms=1200.0,
    )
    assert vid_analysis.total_frames == 100

    rec = AnalysisRecord(
        record_id="rec-1",
        media_type="image",
        original_filename="sample.jpg",
        model_id="yolo11n",
        model_stage="baseline",
        confidence_threshold=0.25,
        iou_threshold=0.70,
        total_detections=1,
        class_counts={"person": 1},
        inference_ms=12.5,
        created_at="2026-09-27T21:00:00Z",
        annotated_path=tmp_path / "annotated.jpg",
        csv_path=tmp_path / "results.csv",
    )
    artifacts = AnalysisArtifacts(
        record=rec,
        annotated_media_path=tmp_path / "annotated.jpg",
        csv_path=tmp_path / "results.csv",
    )
    assert artifacts.record.record_id == "rec-1"

    manifest = ModelManifest(
        schema_version="1.0",
        model_id="test",
        stage="baseline",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "c0"},
        imgsz=640,
        sha256="a" * 64,
        source="unit-test",
        created_at="2026-09-27T21:00:00Z",
    )
    reg_model = RegisteredModel(
        manifest=manifest,
        model_path=tmp_path / "model.onnx",
        manifest_path=tmp_path / "manifest.json",
    )
    assert reg_model.manifest.model_id == "test"
