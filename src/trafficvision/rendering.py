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
from trafficvision.ui.components import extract_mini_badge

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
    selected_index: int | None = None,
) -> bytes:
    """Annotate a BGR image with numbered bounding boxes and Vietnamese class labels.

    If selected_index is specified (0-based index of detection):
    - Non-selected boxes are rendered dimmed/subtle.
    - The selected box is highlighted with a vibrant spotlight outline, translucent fill, and target badge.
    """
    height, width = image_bgr.shape[:2]
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(image_rgb).convert("RGBA")

    # Overlay layer for translucent spotlight highlights or dimming
    overlay = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    font = font_resolver(size=14) if callable(font_resolver) else resolve_font(size=14)
    # Larger font for spotlight target badge
    badge_font = font_resolver(size=15) if callable(font_resolver) else resolve_font(size=15)

    has_selection = selected_index is not None and 0 <= selected_index < len(detections)

    # If something is selected, slightly darken the overall image background to emphasize spotlight
    if has_selection:
        overlay_draw.rectangle([(0, 0), (width, height)], fill=(10, 15, 30, 70))

    # Determine order: draw non-selected first, then draw selected on top
    indices = list(range(len(detections)))
    if has_selection:
        indices.sort(key=lambda idx: 1 if idx == selected_index else 0)

    for idx in indices:
        det = detections[idx]
        is_selected = has_selection and idx == selected_index
        item_icon, _ = extract_mini_badge(det.class_name, str(det.class_id))
        prefix_icon = f"{item_icon} " if item_icon else ""

        x1, y1, x2, y2 = det.xyxy
        # Clamp coordinates to image bounds
        x1 = max(0.0, min(float(x1), float(width - 1)))
        y1 = max(0.0, min(float(y1), float(height - 1)))
        x2 = max(0.0, min(float(x2), float(width - 1)))
        y2 = max(0.0, min(float(y2), float(height - 1)))

        base_color = BOX_COLORS[det.class_id % len(BOX_COLORS)]

        if is_selected:
            # Spotlight highlight:
            # 1. Clear the overall dark tint inside this bounding box
            # 2. Add an eye-catching semi-transparent accent fill
            box_fill = (*base_color, 45)
            overlay_draw.rectangle([(x1, y1), (x2, y2)], fill=box_fill)

            # Vibrant primary border (thickness 4)
            border_color = (*base_color, 255)
            box_width = 4
            label_text = f"🎯 {prefix_icon}{det.class_name} {det.confidence:.2f}"
            cur_font = badge_font
            badge_color = (*base_color, 255)
            badge_text_color = (255, 255, 255, 255)
        elif has_selection:
            # Dimmed non-selected boxes
            border_color = (160, 175, 195, 140)
            box_width = 1
            label_text = f"{prefix_icon}{det.class_name}"
            cur_font = font
            badge_color = (70, 85, 105, 180)
            badge_text_color = (225, 230, 240, 200)
        else:
            # Standard rendering when no selection is active
            border_color = (*base_color, 255)
            box_width = 3
            label_text = f"{prefix_icon}{det.class_name} {det.confidence:.2f}"
            cur_font = font
            badge_color = (*base_color, 255)
            badge_text_color = (255, 255, 255, 255)

        # Draw bounding box outline
        overlay_draw.rectangle([(x1, y1), (x2, y2)], outline=border_color, width=box_width)

        # Calculate text bounding box for label badge
        try:
            bbox = overlay_draw.textbbox((x1, y1), label_text, font=cur_font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            text_w, text_h = 90, 18

        # Draw label background badge above box if room, else inside box
        badge_y1 = y1 - text_h - 6 if (y1 - text_h - 6) >= 0 else y1
        badge_y2 = badge_y1 + text_h + 6
        badge_x2 = min(float(width), x1 + text_w + 8)

        overlay_draw.rectangle([(x1, badge_y1), (badge_x2, badge_y2)], fill=badge_color)
        overlay_draw.text((x1 + 4, badge_y1 + 3), label_text, fill=badge_text_color, font=cur_font)

    # Composite overlay onto image
    annotated = Image.alpha_composite(pil_img, overlay).convert("RGB")

    buf = io.BytesIO()
    fmt_upper = format.upper()
    if fmt_upper == "PNG":
        save_format = "PNG"
        save_kwargs: dict[str, Any] = {}
    elif fmt_upper == "WEBP":
        save_format = "WEBP"
        save_kwargs = {"quality": 92}
    else:
        save_format = "JPEG"
        save_kwargs = {"quality": 92}
    annotated.save(buf, format=save_format, **save_kwargs)
    return buf.getvalue()


def crop_detection(
    image_bgr: np.ndarray,
    detection: Detection,
    padding: int = 16,
    format: str = "JPEG",
) -> bytes:
    """Crop the bounding box of a detection from a BGR image with padding, returning encoded bytes."""
    height, width = image_bgr.shape[:2]
    x1, y1, x2, y2 = detection.xyxy

    # Add padding while clamping to image dimensions
    cx1 = max(0, int(round(x1)) - padding)
    cy1 = max(0, int(round(y1)) - padding)
    cx2 = min(width, int(round(x2)) + padding)
    cy2 = min(height, int(round(y2)) + padding)

    # Ensure crop has at least 1x1 dimensions
    if cx2 <= cx1 or cy2 <= cy1:
        cx1, cy1, cx2, cy2 = 0, 0, max(1, width), max(1, height)

    crop_bgr = image_bgr[cy1:cy2, cx1:cx2]
    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    pil_crop = Image.fromarray(crop_rgb)

    buf = io.BytesIO()
    fmt_upper = format.upper()
    if fmt_upper == "PNG":
        pil_crop.save(buf, format="PNG")
    elif fmt_upper == "WEBP":
        pil_crop.save(buf, format="WEBP", quality=92)
    else:
        pil_crop.save(buf, format="JPEG", quality=92)
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
