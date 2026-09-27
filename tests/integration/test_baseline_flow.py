import io
from pathlib import Path

from PIL import Image

from trafficvision.config import AppConfig, AppPaths
from trafficvision.domain import Detection, ModelManifest
from trafficvision.history import AnalysisRepository
from trafficvision.registry import ModelRegistry, sha256_file
from trafficvision.service import AnalysisService
from trafficvision.settings import RuntimeSettingsStore


class IntegrationFakePredictor:
    def predict(self, image_bgr, *, confidence, iou):
        return (
            Detection(
                class_id=0,
                class_name="bien_cam_di_nguoc_chieu",
                confidence=0.89,
                xyxy=(15.0, 20.0, 80.0, 85.0),
            ),
        )


def test_end_to_end_baseline_analysis_flow(tmp_path: Path):
    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    config = AppConfig.load(project_root=tmp_path)

    # 1. Register baseline model
    dummy_onnx = tmp_path / "model.onnx"
    dummy_onnx.write_bytes(b"dummy-onnx-weights")
    digest = sha256_file(dummy_onnx)

    manifest = ModelManifest(
        schema_version="1.0",
        model_id="yolo11n-baseline-test",
        stage="production",
        source_model_id="yolo11n-baseline",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "bien_cam_di_nguoc_chieu"},
        imgsz=640,
        sha256=digest,
        source="test",
        created_at="2026-09-27T21:00:00Z",
    )
    registry = ModelRegistry(paths)
    registry.install_baseline(dummy_onnx, manifest)

    # 2. Wire service components
    repo = AnalysisRepository(paths.db)
    settings_store = RuntimeSettingsStore(paths.state / "settings.json", default_config=config)
    predictor = IntegrationFakePredictor()

    service = AnalysisService(
        config=config,
        registry=registry,
        repository=repo,
        settings_store=settings_store,
        predictor_factory=lambda: predictor,
    )

    # 3. Create test image upload
    img = Image.new("RGB", (200, 200), color=(120, 180, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_data = buf.getvalue()

    artifacts = service.analyze_image_upload(filename="traffic_sign.png", data=raw_data)

    # 4. Assert artifacts
    assert artifacts.annotated_media_path.is_file()
    assert artifacts.csv_path.is_file()

    # Assert annotated output decodes back to original dimensions
    with Image.open(artifacts.annotated_media_path) as out_img:
        assert out_img.size == (200, 200)

    # Assert CSV contains detection
    csv_text = artifacts.csv_path.read_text(encoding="utf-8-sig")
    assert "bien_cam_di_nguoc_chieu" in csv_text
    assert "traffic_sign.png" in csv_text

    # Assert history row committed
    recent = repo.list_recent()
    assert len(recent) == 1
    assert recent[0].record_id == artifacts.record.record_id
    assert recent[0].model_id == "yolo11n-baseline-test"
    assert recent[0].total_detections == 1
    assert recent[0].class_counts == {"bien_cam_di_nguoc_chieu": 1}
