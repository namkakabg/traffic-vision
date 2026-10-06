"""ONNX export, parity verification, and CPU benchmark module."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class ExportResult(BaseModel):
    """Result of ONNX model export, parity check, and CPU benchmark."""

    model_config = ConfigDict(frozen=True)

    onnx_path: Path
    max_abs_diff: float
    is_parity_valid: bool
    cpu_latency_ms: float
    cpu_fps: float


def export_and_verify_onnx(
    model_path: Path | str,
    imgsz: int = 640,
    tolerance: float = 1e-3,
    warmup_runs: int = 10,
    benchmark_runs: int = 30,
    dynamic: bool = True,
) -> ExportResult:
    """Export PyTorch YOLO weights to ONNX, verify numerical parity, and benchmark CPU inference.

    Args:
        model_path: Path to PyTorch model weights (.pt).
        imgsz: Image input resolution for exported ONNX model.
        tolerance: Maximum acceptable absolute difference between PyTorch and ONNX outputs.
        warmup_runs: Number of unmeasured warmup inference runs (default 10).
        benchmark_runs: Number of timed inference iterations for latency/FPS calculation (default 30).
        dynamic: Whether to export ONNX with dynamic input axes (default True).

    Returns:
        ExportResult containing path to ONNX model, max absolute difference, parity status,
        and latency/FPS metrics.

    Raises:
        FileNotFoundError: If the exported ONNX model file does not exist after export.
    """
    from ultralytics import YOLO  # Lazy import

    model_file = Path(model_path)
    model = YOLO(str(model_file))

    # 1. Export model to ONNX with dynamic or fixed dimensions
    exported_str = model.export(
        format="onnx",
        imgsz=imgsz,
        batch=1,
        dynamic=dynamic,
        simplify=False,
        device="cpu",
    )
    onnx_path = Path(exported_str)
    if not onnx_path.is_file():
        raise FileNotFoundError(f"Exported ONNX model file not found at {onnx_path}")

    # 2. Prepare dummy input tensor for parity and benchmark
    rng = np.random.default_rng(seed=42)
    dummy_input_np = rng.uniform(0.0, 1.0, size=(1, 3, imgsz, imgsz)).astype(np.float32)

    # 3. PyTorch inference (ensure CPU placement and eval mode)
    import torch  # Lazy import

    torch_input = torch.from_numpy(dummy_input_np)
    pt_module = getattr(model, "model", model)
    if hasattr(pt_module, "to") and callable(pt_module.to):
        pt_module.to("cpu")
    if hasattr(pt_module, "eval") and callable(pt_module.eval):
        pt_module.eval()

    with torch.no_grad():
        if callable(pt_module):
            pt_raw = pt_module(torch_input)
        else:
            pt_raw = model(torch_input)

    if isinstance(pt_raw, (list, tuple)):
        pt_tensor = pt_raw[0]
    else:
        pt_tensor = pt_raw

    if hasattr(pt_tensor, "detach"):
        pt_out = pt_tensor.detach().cpu().numpy()
    elif isinstance(pt_tensor, np.ndarray):
        pt_out = pt_tensor
    else:
        pt_out = np.asarray(pt_tensor, dtype=np.float32)

    # 4. ONNX Runtime inference
    import onnxruntime  # Lazy import

    session = onnxruntime.InferenceSession(
        str(onnx_path),
        providers=["CPUExecutionProvider"],
    )
    input_name = session.get_inputs()[0].name
    onnx_outs = session.run(None, {input_name: dummy_input_np})
    onnx_out = onnx_outs[0]

    if hasattr(onnx_out, "detach"):
        onnx_out = onnx_out.detach().cpu().numpy()
    elif not isinstance(onnx_out, np.ndarray):
        onnx_out = np.asarray(onnx_out, dtype=np.float32)

    # 5. Numerical parity comparison (defensive against shape mismatch)
    if pt_out.shape != onnx_out.shape:
        logger.error(
            "ONNX parity shape mismatch for %s: PyTorch shape %s vs ONNX shape %s",
            onnx_path,
            pt_out.shape,
            onnx_out.shape,
        )
        max_abs_diff = float("inf")
        is_parity_valid = False
    else:
        max_abs_diff = float(np.max(np.abs(pt_out - onnx_out)))
        is_parity_valid = bool(max_abs_diff <= tolerance)

        if not is_parity_valid:
            logger.warning(
                "ONNX numerical parity check failed for %s: max_abs_diff=%.6f > tolerance=%.6f",
                onnx_path,
                max_abs_diff,
                tolerance,
            )
        else:
            logger.info(
                "ONNX parity verified for %s: max_abs_diff=%.6f <= tolerance=%.6f",
                onnx_path,
                max_abs_diff,
                tolerance,
            )

    # 6. CPU Latency and FPS Benchmark
    for _ in range(warmup_runs):
        session.run(None, {input_name: dummy_input_np})

    start_time = time.perf_counter()
    for _ in range(benchmark_runs):
        session.run(None, {input_name: dummy_input_np})
    elapsed = time.perf_counter() - start_time

    if benchmark_runs > 0 and elapsed > 0:
        cpu_latency_ms = (elapsed / benchmark_runs) * 1000.0
        cpu_fps = benchmark_runs / elapsed
    else:
        cpu_latency_ms = 0.0
        cpu_fps = 0.0

    return ExportResult(
        onnx_path=onnx_path,
        max_abs_diff=round(max_abs_diff, 6),
        is_parity_valid=is_parity_valid,
        cpu_latency_ms=round(cpu_latency_ms, 4),
        cpu_fps=round(cpu_fps, 2),
    )
