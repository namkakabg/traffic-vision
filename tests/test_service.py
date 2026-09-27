import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from trafficvision.config import AppConfig, AppPaths
from trafficvision.domain import Detection, ModelManifest
from trafficvision.history import AnalysisRepository
from trafficvision.inference.video import VideoProcessingError
from trafficvision.media import MediaValidationError
from trafficvision.registry import ModelRegistry, sha256_file
from trafficvision.service import AnalysisService
from trafficvision.settings import RuntimeSettingsStore


@pytest.fixture
def service_env(tmp_path: Path):
    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    config = AppConfig.load(project_root=tmp_path)

    # Set up dummy registered model in production
    dummy_onnx = tmp_path / "model.onnx"
    dummy_onnx.write_bytes(b"dummy-model-bytes")
    digest = sha256_file(dummy_onnx)
    manifest = ModelManifest(
        schema_version="1.0",
        model_id="yolo11n-test",
        stage="production",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "bien_cam", 1: "bien_nguy_hiem"},
        imgsz=640,
        sha256=digest,
        source="test",
        created_at="2026-09-27T21:00:00Z",
    )
    registry = ModelRegistry(paths)
    registry.install_baseline(dummy_onnx, manifest)

    repo = AnalysisRepository(paths.db)
    settings_store = RuntimeSettingsStore(paths.state / "settings.json", default_config=config)

    fake_predictor = MagicMock()
    fake_predictor.predict.return_value = (
        Detection(
            class_id=0, class_name="bien_cam", confidence=0.88, xyxy=(10.0, 10.0, 50.0, 50.0)
        ),
    )

    service = AnalysisService(
        config=config,
        registry=registry,
        repository=repo,
        settings_store=settings_store,
        predictor_factory=lambda: fake_predictor,
    )
    return service, repo, paths


def test_analyze_image_upload_commits_history_after_files_exist(service_env):
    service, repo, paths = service_env

    # Create sample image
    img = Image.new("RGB", (100, 100), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    data = buf.getvalue()

    artifacts = service.analyze_image_upload(filename="test.jpg", data=data)

    # Verify files exist
    assert artifacts.annotated_media_path.is_file()
    assert artifacts.csv_path.is_file()
    assert artifacts.record.total_detections == 1

    # Verify history is committed
    recent = repo.list_recent()
    assert len(recent) == 1
    assert recent[0].record_id == artifacts.record.record_id
    assert recent[0].annotated_path == artifacts.annotated_media_path


def test_analyze_video_failure_leaves_no_history_or_partial_file(service_env):
    service, repo, paths = service_env

    # Corrupt video bytes
    bad_data = b"bad-video-bytes"

    with pytest.raises((VideoProcessingError, MediaValidationError)):
        service.analyze_video_upload(filename="corrupt.mp4", data=bad_data)

    # No history row should be committed
    assert repo.list_recent() == []

    # No partial output should remain
    partial_files = list(paths.outputs.glob("*.partial*"))
    assert len(partial_files) == 0
