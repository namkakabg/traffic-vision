from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from trafficvision.domain import Detection

# Approved color palette for detection boxes and tags
BOX_COLORS = [
    (2, 132, 199),  # #0284c7 Primary blue
    (13, 148, 136),  # #0d9488 Teal
    (225, 29, 72),  # #e11d48 Rose
    (217, 119, 6),  # #d97706 Amber
    (79, 70, 229),  # #4f46e5 Indigo
    (5, 150, 105),  # #059669 Emerald
    (147, 51, 234),  # #9333ea Purple
]


def resolve_font(custom_path: Path | str | None = None, size: int = 14) -> ImageFont.ImageFont:
    """Resolve a Unicode-compatible TrueType font, checking project font, OS fonts, and fallback."""
    candidates: list[str | Path] = []
    if custom_path:
        candidates.append(custom_path)

    # macOS candidates
    candidates.extend(
        [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    )
    # Windows candidates
    candidates.extend(
        [
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\segoeui.ttf",
        ]
    )
    # Linux candidates
    candidates.extend(
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
    )

    for path in candidates:
        p = Path(path)
        if p.is_file():
            try:
                return ImageFont.truetype(str(p), size=size)
            except Exception:
                continue

    # Fallback to PIL default font
    return ImageFont.load_default()


def annotate_image(
    image_bgr: np.ndarray,
    detections: Sequence[Detection],
    font_resolver: Any = None,
    format: str = "JPEG",
) -> bytes:
    """Annotate a BGR image with bounding boxes and Vietnamese class labels, returning encoded bytes."""
    height, width = image_bgr.shape[:2]
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(image_rgb)
    draw = ImageDraw.Draw(pil_img)

    font = font_resolver(size=14) if callable(font_resolver) else resolve_font(size=14)

    for det in detections:
        x1, y1, x2, y2 = det.xyxy
        # Clamp coordinates to image bounds
        x1 = max(0.0, min(float(x1), float(width - 1)))
        y1 = max(0.0, min(float(y1), float(height - 1)))
        x2 = max(0.0, min(float(x2), float(width - 1)))
        y2 = max(0.0, min(float(y2), float(height - 1)))

        color = BOX_COLORS[det.class_id % len(BOX_COLORS)]
        # Draw bounding box
        draw.rectangle([(x1, y1), (x2, y2)], outline=color, width=3)

        label_text = f"{det.class_name} {det.confidence:.2f}"

        # Calculate text bounding box for label badge
        try:
            bbox = draw.textbbox((x1, y1), label_text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            text_w, text_h = 80, 16

        # Draw label background badge above box if room, else inside box
        badge_y1 = y1 - text_h - 4 if (y1 - text_h - 4) >= 0 else y1
        badge_y2 = badge_y1 + text_h + 4
        badge_x2 = min(float(width), x1 + text_w + 6)

        draw.rectangle([(x1, badge_y1), (badge_x2, badge_y2)], fill=color)
        draw.text((x1 + 3, badge_y1 + 2), label_text, fill=(255, 255, 255), font=font)

    buf = io.BytesIO()
    save_format = "PNG" if format.upper() == "PNG" else "JPEG"
    pil_img.save(buf, format=save_format, quality=92 if save_format == "JPEG" else None)
    return buf.getvalue()


def detections_csv(
    detections: Sequence[Detection],
    source_name: str,
    frame_index: int | None = None,
    timestamp_s: float | None = None,
) -> bytes:
    """Serialize detections to CSV bytes prefixed with UTF-8 BOM for Excel compatibility."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")

    headers = [
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
    writer.writerow(headers)

    f_idx_str = str(frame_index) if frame_index is not None else ""
    ts_str = f"{timestamp_s:.3f}" if timestamp_s is not None else ""

    for det in detections:
        writer.writerow(
            [
                source_name,
                f_idx_str,
                ts_str,
                det.class_id,
                det.class_name,
                f"{det.confidence:.4f}",
                f"{det.xyxy[0]:.2f}",
                f"{det.xyxy[1]:.2f}",
                f"{det.xyxy[2]:.2f}",
                f"{det.xyxy[3]:.2f}",
            ]
        )

    # Encode with UTF-8 BOM
    return b"\xef\xbb\xbf" + out.getvalue().encode("utf-8")
