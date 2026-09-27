import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from trafficvision.config import AppConfig, AppPaths
from trafficvision.media import MediaValidationError, decode_image, stage_upload


@pytest.fixture
def app_config(tmp_path: Path) -> AppConfig:
    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    return AppConfig.load(project_root=tmp_path)


def create_sample_jpeg_bytes(width=100, height=100, color=(255, 0, 0)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_stage_upload_safe_filename_and_path_traversal(app_config: AppConfig):
    data = create_sample_jpeg_bytes()

    # Traversal attempts and Unicode
    dangerous_names = [
        "../secret.jpg",
        "..\\windows_secret.jpg",
        "C:\\Users\\admin\\secret.jpg",
        "/etc/passwd.jpg",
        "biển_báo_giao_thông_2026.png",
    ]

    for name in dangerous_names:
        staged = stage_upload(
            filename=name,
            data=data,
            media_type="image",
            paths=app_config.paths,
            config=app_config,
        )
        assert staged.staged_path.parent == app_config.paths.staging
        assert staged.staged_path.exists()
        assert staged.original_filename == name
        # Staged file basename must not contain traversal characters
        assert ".." not in staged.staged_path.name
        assert "/" not in staged.staged_path.name
        assert "\\" not in staged.staged_path.name


def test_stage_upload_rejects_oversized_file(app_config: AppConfig):
    # Set limit low
    app_config.media.max_image_bytes = 100
    big_data = b"x" * 200

    with pytest.raises(MediaValidationError, match="exceeds maximum allowed"):
        stage_upload(
            filename="big.jpg",
            data=big_data,
            media_type="image",
            paths=app_config.paths,
            config=app_config,
        )


def test_stage_upload_and_decode_validates_image_content(app_config: AppConfig):
    # Text content renamed as jpg
    corrupt_data = b"This is not a real image file, just plain text."
    with pytest.raises(MediaValidationError, match="Invalid or unreadable image"):
        stage_upload(
            filename="fake.jpg",
            data=corrupt_data,
            media_type="image",
            paths=app_config.paths,
            config=app_config,
        )

    # Valid image stages and decodes to BGR numpy array
    valid_data = create_sample_jpeg_bytes(width=64, height=48, color=(10, 20, 30))
    staged = stage_upload(
        filename="test.jpg",
        data=valid_data,
        media_type="image",
        paths=app_config.paths,
        config=app_config,
    )
    bgr = decode_image(staged)
    assert isinstance(bgr, np.ndarray)
    assert bgr.shape == (48, 64, 3)
    assert bgr.dtype == np.uint8


def test_stage_upload_rejects_corrupted_video_content(app_config: AppConfig):
    corrupt_video_data = b"This is plain text with an .mp4 extension, not real video."
    with pytest.raises(MediaValidationError, match="Invalid or unreadable video"):
        stage_upload(
            filename="fake.mp4",
            data=corrupt_video_data,
            media_type="video",
            paths=app_config.paths,
            config=app_config,
        )
