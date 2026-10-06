from __future__ import annotations

import csv
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw

from trafficvision.domain import InferenceOptions, VideoAnalysis, VideoProgress
from trafficvision.inference.base import Predictor
from trafficvision.rendering import BOX_COLORS, resolve_font


class VideoProcessingError(Exception):
    """Raised when video intake, decoding, inference, or encoding fails."""


def _draw_detections_bgr(
    frame_bgr: np.ndarray,
    detections: tuple,
    font: Any,
) -> np.ndarray:
    """Draw bounding boxes and Vietnamese label badges onto a BGR frame array."""
    if not detections:
        return frame_bgr

    height, width = frame_bgr.shape[:2]
    image_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(image_rgb)
    draw = ImageDraw.Draw(pil_img)

    for det in detections:
        x1, y1, x2, y2 = det.xyxy
        x1 = max(0.0, min(float(x1), float(width - 1)))
        y1 = max(0.0, min(float(y1), float(height - 1)))
        x2 = max(0.0, min(float(x2), float(width - 1)))
        y2 = max(0.0, min(float(y2), float(height - 1)))

        color = BOX_COLORS[det.class_id % len(BOX_COLORS)]
        draw.rectangle([(x1, y1), (x2, y2)], outline=color, width=3)

        label_text = f"{det.class_name} {det.confidence:.2f}"
        try:
            bbox = draw.textbbox((x1, y1), label_text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            text_w, text_h = 80, 16

        badge_y1 = y1 - text_h - 4 if (y1 - text_h - 4) >= 0 else y1
        badge_y2 = badge_y1 + text_h + 4
        badge_x2 = min(float(width), x1 + text_w + 6)

        draw.rectangle([(x1, badge_y1), (badge_x2, badge_y2)], fill=color)
        draw.text((x1 + 3, badge_y1 + 2), label_text, fill=(255, 255, 255), font=font)

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def process_video(
    input_path: Path,
    output_path: Path,
    csv_path: Path,
    predictor: Predictor,
    options: InferenceOptions,
    on_progress: Callable[[VideoProgress], None] | None = None,
) -> VideoAnalysis:
    """Streamingly process video frame-by-frame with bounded memory usage."""
    if not input_path.is_file():
        raise VideoProcessingError(f"Input video file not found: {input_path}")

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise VideoProcessingError(f"Unable to open video file at {input_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if width <= 0 or height <= 0:
        cap.release()
        raise VideoProcessingError(f"Invalid video dimensions: {width}x{height}")
    if fps <= 0.0 or np.isnan(fps):
        fps = 25.0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    partial_output = output_path.with_name(f"{output_path.stem}.partial{output_path.suffix}")
    if partial_output.exists():
        partial_output.unlink()

    # Codec negotiation: prefer H.264 (avc1), fallback to MP4V
    codecs_to_try = [
        ("avc1", "H.264 (avc1)"),
        ("mp4v", "MPEG-4 (mp4v)"),
    ]

    writer = None
    chosen_codec_desc = ""
    fallback_used = False

    for idx, (codec_code, codec_desc) in enumerate(codecs_to_try):
        fourcc = cv2.VideoWriter_fourcc(*codec_code)
        w = cv2.VideoWriter(str(partial_output), fourcc, fps, (width, height))
        if w.isOpened():
            writer = w
            chosen_codec_desc = codec_desc
            if idx > 0:
                fallback_used = True
            break
        w.release()

    if writer is None or not writer.isOpened():
        cap.release()
        raise VideoProcessingError("Failed to initialize video writer with supported codecs")

    font = resolve_font(size=14)
    detection_counts: dict[str, int] = {}
    total_inf_ms = 0.0
    processed_frames = 0
    current_frame_idx = 0

    import inspect
    sig = inspect.signature(predictor.predict)
    has_imgsz = "imgsz" in sig.parameters

    try:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as csv_file:
            csv_writer = csv.writer(csv_file, lineterminator="\r\n")
            csv_writer.writerow(
                [
                    "source",
                    "frame_index",
                    "timestamp_s",
                    "class_id",
                    "class_name",
                    "confidence",
                    "x1",
                    "y1",
                    "x2",
                    "y2",
                ]
            )

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                current_frame_idx = processed_frames
                timestamp_s = current_frame_idx / fps if fps > 0 else 0.0

                start_t = time.perf_counter()
                if has_imgsz:
                    detections = predictor.predict(
                        frame,
                        confidence=options.confidence,
                        iou=options.iou,
                        imgsz=getattr(options, "imgsz", None),
                    )
                else:
                    detections = predictor.predict(
                        frame,
                        confidence=options.confidence,
                        iou=options.iou,
                    )
                total_inf_ms += (time.perf_counter() - start_t) * 1000.0

                for det in detections:
                    detection_counts[det.class_name] = detection_counts.get(det.class_name, 0) + 1
                    csv_writer.writerow(
                        [
                            input_path.name,
                            current_frame_idx,
                            f"{timestamp_s:.3f}",
                            det.class_id,
                            det.class_name,
                            f"{det.confidence:.4f}",
                            f"{det.xyxy[0]:.2f}",
                            f"{det.xyxy[1]:.2f}",
                            f"{det.xyxy[2]:.2f}",
                            f"{det.xyxy[3]:.2f}",
                        ]
                    )

                annotated_frame = _draw_detections_bgr(frame, detections, font)
                writer.write(annotated_frame)
                processed_frames += 1

                if on_progress:
                    denom = max(total_frames, processed_frames)
                    frac = min(1.0, processed_frames / denom)
                    on_progress(
                        VideoProgress(
                            current_frame=processed_frames,
                            total_frames=denom,
                            fraction=frac,
                            fps=fps,
                        )
                    )

    except Exception as exc:
        if partial_output.exists():
            try:
                partial_output.unlink()
            except Exception:
                pass
        raise VideoProcessingError(
            f"Video processing error at frame {current_frame_idx}: {exc}"
        ) from exc
    finally:
        cap.release()
        writer.release()

    # Verify output file
    if not partial_output.exists() or partial_output.stat().st_size == 0:
        raise VideoProcessingError("Output video file was not generated properly")

    # Atomic move
    os.replace(partial_output, output_path)

    codec_note = (
        f"Codec: {chosen_codec_desc}" if not fallback_used else f"Fallback to {chosen_codec_desc}"
    )

    return VideoAnalysis(
        width=width,
        height=height,
        fps=fps,
        total_frames=total_frames if total_frames > 0 else processed_frames,
        processed_frames=processed_frames,
        detection_counts_by_class=detection_counts,
        inference_ms=total_inf_ms,
        fallback_codec_used=fallback_used,
        codec_note=codec_note,
    )
