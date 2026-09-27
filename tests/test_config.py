from pathlib import Path

import pytest

from trafficvision.config import AppConfig


def test_load_defaults_are_cross_platform(tmp_path: Path):
    config = AppConfig.load(project_root=tmp_path)
    assert config.inference.confidence == 0.25
    assert config.inference.iou == 0.70
    assert config.inference.imgsz == 640
    assert config.media.max_image_bytes == 20 * 1024 * 1024
    assert config.media.max_video_bytes == 500 * 1024 * 1024
    assert ".webp" in config.media.allowed_image_extensions

    paths = config.paths
    for attr in ["artifacts", "baseline", "production", "backups", "staging", "outputs", "state"]:
        path_val: Path = getattr(paths, attr)
        assert tmp_path in path_val.parents or path_val == tmp_path


def test_environment_overrides_thresholds(tmp_path: Path):
    env = {
        "TRAFFICVISION_CONFIDENCE": "0.45",
        "TRAFFICVISION_IOU": "0.65",
    }
    config = AppConfig.load(project_root=tmp_path, env=env)
    assert config.inference.confidence == 0.45
    assert config.inference.iou == 0.65


def test_invalid_threshold_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        AppConfig.load(project_root=tmp_path, env={"TRAFFICVISION_CONFIDENCE": "1.5"})

    with pytest.raises(ValueError):
        AppConfig.load(project_root=tmp_path, env={"TRAFFICVISION_IOU": "-0.1"})
