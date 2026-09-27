from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from trafficvision.config import AppConfig
from trafficvision.settings import RuntimeSettings, RuntimeSettingsStore


def test_runtime_settings_defaults_and_roundtrip(tmp_path: Path):
    config = AppConfig.load(project_root=tmp_path)
    settings_path = tmp_path / "settings.json"
    store = RuntimeSettingsStore(settings_path=settings_path, default_config=config)

    # 1. Missing settings returns defaults from config
    s = store.load()
    assert s.confidence == 0.25
    assert s.iou == 0.70
    assert s.max_image_bytes == 20 * 1024 * 1024
    assert s.max_video_bytes == 500 * 1024 * 1024

    # 2. Modify and save
    updated = RuntimeSettings(
        confidence=0.45,
        iou=0.65,
        max_image_bytes=10 * 1024 * 1024,
        max_video_bytes=200 * 1024 * 1024,
    )
    store.save(updated)

    # 3. Reload and assert persistence
    reloaded = store.load()
    assert reloaded == updated


def test_runtime_settings_validation():
    with pytest.raises(ValidationError):
        RuntimeSettings(confidence=1.5)  # > 1.0

    with pytest.raises(ValidationError):
        RuntimeSettings(iou=-0.2)  # < 0.0

    with pytest.raises(ValidationError):
        RuntimeSettings(max_image_bytes=0)  # <= 0


def test_runtime_settings_atomic_save_preserves_on_failure(tmp_path: Path):
    config = AppConfig.load(project_root=tmp_path)
    settings_path = tmp_path / "settings.json"
    store = RuntimeSettingsStore(settings_path=settings_path, default_config=config)

    initial = RuntimeSettings(confidence=0.30, iou=0.50)
    store.save(initial)

    # Inject failure during os.replace
    with patch("os.replace", side_effect=OSError("Disk write failed")):
        with pytest.raises(OSError):
            store.save(RuntimeSettings(confidence=0.99))

    # Previous settings must be preserved intact
    assert store.load().confidence == 0.30
