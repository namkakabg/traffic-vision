"""Tests for TrainingConfig validation and serialization."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from trafficvision.training.config import TrainingConfig


def test_training_config_defaults(tmp_path: Path) -> None:
    data_yaml = tmp_path / "data.yaml"
    data_yaml.write_text("names: [c0]\n", encoding="utf-8")

    config = TrainingConfig(run_id="run_001", data_yaml=data_yaml)

    assert config.run_id == "run_001"
    assert config.data_yaml == data_yaml
    assert config.base_model == "yolo11n.pt"
    assert config.epochs == 50
    assert config.batch == 4
    assert config.imgsz == 640
    assert config.patience == 10
    assert config.amp is True
    assert config.device == "cpu"
    assert config.seed == 42


def test_training_config_custom_values(tmp_path: Path) -> None:
    data_yaml = tmp_path / "custom_data.yaml"
    config = TrainingConfig(
        run_id="run_custom",
        data_yaml=data_yaml,
        base_model="yolo11s.pt",
        epochs=100,
        batch=16,
        imgsz=320,
        patience=15,
        amp=False,
        device="cuda",
        seed=123,
    )
    assert config.base_model == "yolo11s.pt"
    assert config.epochs == 100
    assert config.batch == 16
    assert config.imgsz == 320
    assert config.patience == 15
    assert config.amp is False
    assert config.device == "cuda"
    assert config.seed == 123


def test_training_config_string_data_yaml_conversion(tmp_path: Path) -> None:
    data_yaml_str = str(tmp_path / "data.yaml")
    config = TrainingConfig(run_id="run_str_path", data_yaml=data_yaml_str)  # type: ignore[arg-type]
    assert isinstance(config.data_yaml, Path)
    assert config.data_yaml == Path(data_yaml_str)


@pytest.mark.parametrize("invalid_batch", [0, -1, -10])
def test_training_config_invalid_batch(tmp_path: Path, invalid_batch: int) -> None:
    with pytest.raises(ValidationError, match="batch"):
        TrainingConfig(run_id="run_inv", data_yaml=tmp_path / "data.yaml", batch=invalid_batch)


@pytest.mark.parametrize("invalid_epochs", [0, -1, -50])
def test_training_config_invalid_epochs(tmp_path: Path, invalid_epochs: int) -> None:
    with pytest.raises(ValidationError, match="epochs"):
        TrainingConfig(run_id="run_inv", data_yaml=tmp_path / "data.yaml", epochs=invalid_epochs)


@pytest.mark.parametrize("invalid_imgsz", [0, -32, 641, 500, 100])
def test_training_config_invalid_imgsz(tmp_path: Path, invalid_imgsz: int) -> None:
    with pytest.raises(ValidationError, match="imgsz"):
        TrainingConfig(run_id="run_inv", data_yaml=tmp_path / "data.yaml", imgsz=invalid_imgsz)


@pytest.mark.parametrize("valid_imgsz", [32, 320, 640, 1280])
def test_training_config_valid_imgsz(tmp_path: Path, valid_imgsz: int) -> None:
    config = TrainingConfig(run_id="run_ok", data_yaml=tmp_path / "data.yaml", imgsz=valid_imgsz)
    assert config.imgsz == valid_imgsz


def test_training_config_roundtrip_json(tmp_path: Path) -> None:
    data_yaml = tmp_path / "data.yaml"
    config = TrainingConfig(run_id="run_roundtrip", data_yaml=data_yaml, epochs=20, batch=8)
    json_str = config.model_dump_json()

    restored = TrainingConfig.model_validate_json(json_str)
    assert restored.run_id == config.run_id
    assert restored.data_yaml == config.data_yaml
    assert restored.epochs == config.epochs
    assert restored.batch == config.batch
