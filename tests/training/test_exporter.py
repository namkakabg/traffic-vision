"""Tests for ONNX export, parity verification, and CPU benchmarking."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from trafficvision.training.exporter import ExportResult, export_and_verify_onnx


def test_export_result_model(tmp_path: Path):
    """Verify ExportResult fields and types."""
    onnx_file = tmp_path / "model.onnx"
    onnx_file.write_bytes(b"dummy")
    res = ExportResult(
        onnx_path=onnx_file,
        max_abs_diff=0.00012,
        is_parity_valid=True,
        cpu_latency_ms=18.5,
        cpu_fps=54.05,
    )
    assert res.onnx_path == onnx_file
    assert res.max_abs_diff == 0.00012
    assert res.is_parity_valid is True
    assert res.cpu_latency_ms == 18.5
    assert res.cpu_fps == 54.05


def test_export_and_verify_onnx_parity_pass(tmp_path: Path):
    """Verify export_and_verify_onnx succeeds when outputs match within tolerance."""
    model_path = tmp_path / "best.pt"
    model_path.write_bytes(b"dummy-pt-weights")

    onnx_file = tmp_path / "best.onnx"
    onnx_file.write_bytes(b"dummy-onnx-bytes")

    # Deterministic dummy outputs: difference is 1e-4 <= 1e-3
    shape = (1, 84, 8400)
    base_out = np.ones(shape, dtype=np.float32)
    pt_out_np = base_out.copy()
    onnx_out_np = base_out + 0.0001

    mock_yolo_instance = MagicMock()
    mock_yolo_instance.export.return_value = str(onnx_file)

    # Mock PyTorch model forward pass
    mock_torch_tensor = MagicMock()
    mock_torch_tensor.detach.return_value.cpu.return_value.numpy.return_value = pt_out_np
    mock_yolo_instance.model.return_value = (mock_torch_tensor,)

    # Mock ONNX Runtime session
    mock_session = MagicMock()
    mock_input_meta = MagicMock()
    mock_input_meta.name = "images"
    mock_session.get_inputs.return_value = [mock_input_meta]
    mock_session.run.return_value = [onnx_out_np]

    with (
        patch("ultralytics.YOLO", return_value=mock_yolo_instance) as mock_yolo_cls,
        patch("onnxruntime.InferenceSession", return_value=mock_session) as mock_session_cls,
    ):
        result = export_and_verify_onnx(
            model_path,
            imgsz=640,
            tolerance=1e-3,
            warmup_runs=2,
            benchmark_runs=4,
        )

        mock_yolo_cls.assert_called_once_with(str(model_path))
        mock_yolo_instance.export.assert_called_once_with(
            format="onnx",
            imgsz=640,
            batch=1,
            dynamic=False,
            simplify=False,
            device="cpu",
        )
        mock_session_cls.assert_called_once_with(
            str(onnx_file),
            providers=["CPUExecutionProvider"],
        )

        assert result.onnx_path == onnx_file
        assert result.max_abs_diff == pytest.approx(0.0001, abs=1e-6)
        assert result.is_parity_valid is True
        assert result.cpu_latency_ms > 0
        assert result.cpu_fps > 0

        # Verify session.run called for: 1 parity check + 2 warmup + 4 benchmark = 7 calls
        assert mock_session.run.call_count == 7


def test_export_and_verify_onnx_parity_divergence_failure(tmp_path: Path):
    """Verify export_and_verify_onnx flags is_parity_valid=False when outputs diverge."""
    model_path = tmp_path / "best.pt"
    model_path.write_bytes(b"dummy-pt-weights")

    onnx_file = tmp_path / "best.onnx"
    onnx_file.write_bytes(b"dummy-onnx-bytes")

    # Significant output divergence: diff = 0.05 > tolerance 1e-3
    shape = (1, 84, 8400)
    pt_out_np = np.zeros(shape, dtype=np.float32)
    onnx_out_np = np.full(shape, 0.05, dtype=np.float32)

    mock_yolo_instance = MagicMock()
    mock_yolo_instance.export.return_value = str(onnx_file)

    mock_torch_tensor = MagicMock()
    mock_torch_tensor.detach.return_value.cpu.return_value.numpy.return_value = pt_out_np
    mock_yolo_instance.model.return_value = mock_torch_tensor

    mock_session = MagicMock()
    mock_input_meta = MagicMock()
    mock_input_meta.name = "images"
    mock_session.get_inputs.return_value = [mock_input_meta]
    mock_session.run.return_value = [onnx_out_np]

    with (
        patch("ultralytics.YOLO", return_value=mock_yolo_instance),
        patch("onnxruntime.InferenceSession", return_value=mock_session),
    ):
        result = export_and_verify_onnx(
            model_path,
            imgsz=640,
            tolerance=1e-3,
            warmup_runs=1,
            benchmark_runs=2,
        )

        assert result.onnx_path == onnx_file
        assert result.max_abs_diff == pytest.approx(0.05, abs=1e-5)
        assert result.is_parity_valid is False
        assert result.cpu_latency_ms > 0
        assert result.cpu_fps > 0


def test_export_and_verify_missing_onnx_raises(tmp_path: Path):
    """Verify FileNotFoundError is raised if model.export does not create the onnx file."""
    model_path = tmp_path / "best.pt"
    model_path.write_bytes(b"dummy-pt-weights")

    nonexistent_onnx = tmp_path / "missing.onnx"

    mock_yolo_instance = MagicMock()
    mock_yolo_instance.export.return_value = str(nonexistent_onnx)

    with patch("ultralytics.YOLO", return_value=mock_yolo_instance):
        with pytest.raises(FileNotFoundError):
            export_and_verify_onnx(model_path)
