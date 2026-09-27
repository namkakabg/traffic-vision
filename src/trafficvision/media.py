from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from PIL import Image

from trafficvision.config import AppConfig, AppPaths
from trafficvision.domain import StagedMedia


class MediaValidationError(Exception):
    """Raised when uploaded media is invalid, corrupt, or exceeds limits."""


def stage_upload(
    filename: str,
    data: bytes,
    media_type: Literal["image", "video"],
    paths: AppPaths,
    config: AppConfig,
) -> StagedMedia:
    """Safely validate and stage an uploaded file under paths.staging using a UUID."""
    paths.staging.mkdir(parents=True, exist_ok=True)
    size = len(data)

    # 1. Size checks
    if media_type == "image":
        max_bytes = config.media.max_image_bytes
        if size > max_bytes:
            raise MediaValidationError(
                f"Image size ({size} bytes) exceeds maximum allowed ({max_bytes} bytes)"
            )
        allowed_exts = config.media.allowed_image_extensions
    elif media_type == "video":
        max_bytes = config.media.max_video_bytes
        if size > max_bytes:
            raise MediaValidationError(
                f"Video size ({size} bytes) exceeds maximum allowed ({max_bytes} bytes)"
            )
        allowed_exts = config.media.allowed_video_extensions
    else:
        raise MediaValidationError(f"Unsupported media type: {media_type}")

    # 2. Extension check
    raw_suffix = Path(filename).suffix.lower()
    if raw_suffix not in allowed_exts:
        raise MediaValidationError(
            f"File extension '{raw_suffix}' is not permitted for {media_type}. "
            f"Allowed extensions: {allowed_exts}"
        )

    # 3. Content validation
    if media_type == "image":
        try:
            buf = io.BytesIO(data)
            with Image.open(buf) as img:
                img.verify()
        except Exception as e:
            raise MediaValidationError(f"Invalid or unreadable image content: {e}") from e

    # 4. Safe write using UUID (never use raw filename in path)
    media_id = str(uuid.uuid4())
    safe_path = paths.staging / f"{media_id}{raw_suffix}"
    safe_path.write_bytes(data)

    return StagedMedia(
        media_id=media_id,
        original_filename=filename,
        staged_path=safe_path,
        media_type=media_type,
        size_bytes=size,
    )


def decode_image(media: StagedMedia) -> np.ndarray:
    """Decode staged image into a BGR uint8 numpy array."""
    if not media.staged_path.is_file():
        raise FileNotFoundError(f"Staged file not found: {media.staged_path}")

    # Using Pillow then converting to BGR guarantees consistent cross-platform decoding
    try:
        with Image.open(media.staged_path) as img:
            rgb = np.array(img.convert("RGB"))
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception as e:
        raise MediaValidationError(f"Failed to decode image from {media.staged_path}: {e}") from e
