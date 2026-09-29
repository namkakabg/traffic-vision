"""Tests for independent evaluation of YOLO checkpoints."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from trafficvision.training.evaluator import EvaluationMetrics, evaluate_checkpoint


def test_evaluation_metrics_model():
    """Verify EvaluationMetrics serialization and properties."""
    metrics = EvaluationMetrics(
        precision=0.85,
        recall=0.80,
        f1=0.82424,
        map50=0.88,
        map50_95=0.65,
        per_class_ap={"class_0": 0.88, "class_1": 0.82},
        confusion_matrix=[[10, 2], [1, 15]],
    )
    assert metrics.precision == 0.85
    assert metrics.recall == 0.80
    assert metrics.f1 == 0.82424
    assert metrics.map50 == 0.88
    assert metrics.map50_95 == 0.65
    assert metrics.per_class_ap == {"class_0": 0.88, "class_1": 0.82}
    assert metrics.confusion_matrix == [[10, 2], [1, 15]]

    dumped = metrics.model_dump()
    assert dumped["precision"] == 0.85
    assert dumped["confusion_matrix"] == [[10, 2], [1, 15]]


def test_evaluate_checkpoint_extracts_metrics(tmp_path: Path):
    """Verify evaluate_checkpoint wraps model.val and extracts metrics correctly."""
    model_path = tmp_path / "best.pt"
    model_path.write_bytes(b"dummy-weights")
    data_yaml = tmp_path / "dataset.yaml"
    data_yaml.write_text("names: [c0, c1]\n", encoding="utf-8")

    # Setup mock validation results
    mock_results = MagicMock()
    mock_results.results_dict = {
        "metrics/precision(B)": 0.85,
        "metrics/recall(B)": 0.75,
        "metrics/mAP50(B)": 0.82,
        "metrics/mAP50-95(B)": 0.60,
    }
    mock_results.names = {0: "pedestrian_crossing", 1: "speed_limit_50"}
    mock_results.box.maps = [0.84, 0.80]

    mock_cm = MagicMock()
    mock_cm.matrix = [[12, 1], [2, 14]]
    mock_results.confusion_matrix = mock_cm

    mock_yolo_instance = MagicMock()
    mock_yolo_instance.val.return_value = mock_results

    with patch("ultralytics.YOLO", return_value=mock_yolo_instance) as mock_yolo_cls:
        eval_metrics = evaluate_checkpoint(model_path, data_yaml, split="test")

        mock_yolo_cls.assert_called_once_with(str(model_path))
        mock_yolo_instance.val.assert_called_once_with(
            data=str(data_yaml),
            split="test",
            device="cpu",
            verbose=False,
        )

        assert eval_metrics.precision == 0.85
        assert eval_metrics.recall == 0.75
        expected_f1 = 2 * (0.85 * 0.75) / (0.85 + 0.75)
        assert eval_metrics.f1 == pytest.approx(expected_f1, rel=1e-4)
        assert eval_metrics.map50 == 0.82
        assert eval_metrics.map50_95 == 0.60
        assert eval_metrics.per_class_ap == {
            "pedestrian_crossing": 0.84,
            "speed_limit_50": 0.80,
        }
        assert eval_metrics.confusion_matrix == [[12, 1], [2, 14]]


def test_evaluate_checkpoint_zero_division_safety(tmp_path: Path):
    """Verify F1 calculation safely handles zero precision and recall."""
    model_path = tmp_path / "best.pt"
    model_path.write_bytes(b"dummy-weights")
    data_yaml = tmp_path / "dataset.yaml"
    data_yaml.write_text("names: [c0]\n", encoding="utf-8")

    mock_results = MagicMock()
    mock_results.results_dict = {
        "metrics/precision(B)": 0.0,
        "metrics/recall(B)": 0.0,
        "metrics/mAP50(B)": 0.0,
        "metrics/mAP50-95(B)": 0.0,
    }
    mock_results.names = {0: "c0"}
    mock_results.box.maps = [0.0]
    mock_results.confusion_matrix = None

    mock_yolo_instance = MagicMock()
    mock_yolo_instance.val.return_value = mock_results

    with patch("ultralytics.YOLO", return_value=mock_yolo_instance):
        eval_metrics = evaluate_checkpoint(model_path, data_yaml)
        assert eval_metrics.precision == 0.0
        assert eval_metrics.recall == 0.0
        assert eval_metrics.f1 == 0.0
        assert eval_metrics.confusion_matrix == []


def test_evaluate_checkpoint_custom_split(tmp_path: Path):
    """Verify split argument is passed properly to model.val."""
    model_path = tmp_path / "best.pt"
    model_path.write_bytes(b"dummy-weights")
    data_yaml = tmp_path / "dataset.yaml"
    data_yaml.write_text("names: [c0]\n", encoding="utf-8")

    mock_results = MagicMock()
    mock_results.results_dict = {
        "metrics/precision(B)": 0.9,
        "metrics/recall(B)": 0.9,
        "metrics/mAP50(B)": 0.9,
        "metrics/mAP50-95(B)": 0.9,
    }
    mock_results.names = {}
    mock_results.box.maps = []
    mock_results.confusion_matrix = None

    mock_yolo_instance = MagicMock()
    mock_yolo_instance.val.return_value = mock_results

    with patch("ultralytics.YOLO", return_value=mock_yolo_instance):
        evaluate_checkpoint(model_path, data_yaml, split="val")
        mock_yolo_instance.val.assert_called_once_with(
            data=str(data_yaml),
            split="val",
            device="cpu",
            verbose=False,
        )
