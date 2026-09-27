from pathlib import Path
from unittest.mock import MagicMock, patch

from trafficvision.bootstrap import bootstrap_baseline
from trafficvision.config import AppPaths
from trafficvision.registry import ModelRegistry


def test_isolated_bootstrap_baseline(tmp_path: Path):
    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    registry = ModelRegistry(paths)

    fake_onnx = tmp_path / "mock_exported.onnx"
    fake_onnx.write_bytes(b"mock-onnx-content")

    mock_yolo_instance = MagicMock()
    mock_yolo_instance.names = {0: "person", 1: "bicycle", 2: "car"}

    def fake_export(**kwargs):
        assert kwargs.get("format") == "onnx"
        assert kwargs.get("imgsz") == 640
        assert kwargs.get("batch") == 1
        assert kwargs.get("dynamic") is False
        assert kwargs.get("simplify") is False
        assert kwargs.get("device") == "cpu"
        return str(fake_onnx)

    mock_yolo_instance.export = fake_export

    with patch("ultralytics.YOLO", return_value=mock_yolo_instance) as mock_yolo_cls:
        registered = bootstrap_baseline(registry, model_name="yolo11n.pt")

        mock_yolo_cls.assert_called_once_with("yolo11n.pt")
        assert registered.manifest.stage == "production"
        assert registered.manifest.class_names == {0: "person", 1: "bicycle", 2: "car"}
        assert registered.manifest.source_model_id is not None
        assert "yolo11n" in registered.manifest.source_model_id

        # Verify registry has production ready
        prod = registry.get_production()
        assert prod.manifest.model_id == registered.manifest.model_id
        assert prod.model_path.is_file()
