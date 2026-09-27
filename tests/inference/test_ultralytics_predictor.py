from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from trafficvision.domain import ModelManifest, RegisteredModel
from trafficvision.inference.base import PredictionContractError
from trafficvision.inference.ultralytics import UltralyticsOnnxPredictor
from trafficvision.registry import ModelIntegrityError, sha256_file


@pytest.fixture
def sample_registered_model(tmp_path: Path) -> RegisteredModel:
    model_file = tmp_path / "model.onnx"
    model_file.write_bytes(b"dummy-model-onnx-bytes")
    manifest_file = tmp_path / "manifest.json"
    digest = sha256_file(model_file)

    manifest = ModelManifest(
        schema_version="1.0",
        model_id="test-model-v1",
        stage="production",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "bien_cam", 1: "bien_nguy_hiem"},
        imgsz=640,
        sha256=digest,
        source="unit-test",
        created_at="2026-09-27T21:00:00Z",
    )
    manifest_file.write_text(manifest.model_dump_json())
    return RegisteredModel(
        manifest=manifest,
        model_path=model_file,
        manifest_path=manifest_file,
    )


def test_predictor_converts_boxes_using_manifest_names(sample_registered_model: RegisteredModel):
    fake_img = np.zeros((480, 640, 3), dtype=np.uint8)

    # Mock Ultralytics box tensors
    box1 = MagicMock()
    box1.xyxy = [MagicMock(cpu=lambda: MagicMock(tolist=lambda: [10.0, 20.0, 100.0, 200.0]))]
    box1.conf = [MagicMock(cpu=lambda: MagicMock(item=lambda: 0.88))]
    box1.cls = [MagicMock(cpu=lambda: MagicMock(item=lambda: 0))]

    fake_result = MagicMock()
    fake_result.boxes = [box1]
    # Intentionally set result.names differently to prove name comes from manifest, NOT result.names
    fake_result.names = {0: "wrong_coco_name"}

    mock_yolo_instance = MagicMock()
    mock_yolo_instance.return_value = [fake_result]

    with patch("ultralytics.YOLO", return_value=mock_yolo_instance):
        predictor = UltralyticsOnnxPredictor.from_registered(sample_registered_model)
        detections = predictor.predict(fake_img, confidence=0.5, iou=0.45)

        assert len(detections) == 1
        d = detections[0]
        assert d.class_id == 0
        assert d.class_name == "bien_cam"  # From manifest
        assert d.confidence == 0.88
        assert d.xyxy == (10.0, 20.0, 100.0, 200.0)

        # Verify call arguments
        mock_yolo_instance.assert_called_once_with(
            fake_img,
            conf=0.5,
            iou=0.45,
            imgsz=640,
            device="cpu",
            verbose=False,
        )


def test_predictor_handles_empty_detections(sample_registered_model: RegisteredModel):
    fake_img = np.zeros((480, 640, 3), dtype=np.uint8)
    fake_result = MagicMock()
    fake_result.boxes = []

    mock_yolo_instance = MagicMock()
    mock_yolo_instance.return_value = [fake_result]

    with patch("ultralytics.YOLO", return_value=mock_yolo_instance):
        predictor = UltralyticsOnnxPredictor.from_registered(sample_registered_model)
        detections = predictor.predict(fake_img, confidence=0.25, iou=0.7)
        assert detections == ()


def test_predictor_rejects_class_id_absent_from_manifest(sample_registered_model: RegisteredModel):
    fake_img = np.zeros((480, 640, 3), dtype=np.uint8)

    box_bad = MagicMock()
    box_bad.xyxy = [MagicMock(cpu=lambda: MagicMock(tolist=lambda: [5.0, 5.0, 50.0, 50.0]))]
    box_bad.conf = [MagicMock(cpu=lambda: MagicMock(item=lambda: 0.95))]
    box_bad.cls = [MagicMock(cpu=lambda: MagicMock(item=lambda: 99))]  # 99 not in manifest

    fake_result = MagicMock()
    fake_result.boxes = [box_bad]

    mock_yolo_instance = MagicMock()
    mock_yolo_instance.return_value = [fake_result]

    with patch("ultralytics.YOLO", return_value=mock_yolo_instance):
        predictor = UltralyticsOnnxPredictor.from_registered(sample_registered_model)
        with pytest.raises(PredictionContractError):
            predictor.predict(fake_img, confidence=0.25, iou=0.7)


def test_predictor_validates_checksum_before_yolo_factory(sample_registered_model: RegisteredModel):
    # Tamper with the model file before lazy load
    sample_registered_model.model_path.write_bytes(b"tampered-onnx-bytes")

    with patch("ultralytics.YOLO") as mock_yolo_cls:
        predictor = UltralyticsOnnxPredictor.from_registered(sample_registered_model)
        fake_img = np.zeros((100, 100, 3), dtype=np.uint8)

        with pytest.raises(ModelIntegrityError):
            predictor.predict(fake_img, confidence=0.25, iou=0.7)

        # Ultralytics must NEVER be called if integrity failed
        mock_yolo_cls.assert_not_called()
