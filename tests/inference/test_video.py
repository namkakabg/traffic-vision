from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from trafficvision.domain import Detection, InferenceOptions, VideoProgress
from trafficvision.inference.video import VideoProcessingError, process_video


def create_tiny_synthetic_video(
    path: Path, num_frames: int = 6, width: int = 64, height: int = 48, fps: float = 10.0
) -> Path:
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
    for i in range(num_frames):
        # Create distinct color frames
        frame = np.full((height, width, 3), fill_value=(i * 30 % 255, 100, 150), dtype=np.uint8)
        out.write(frame)
    out.release()
    return path


class FakeVideoPredictor:
    def __init__(self):
        self.call_count = 0

    def predict(
        self,
        image_bgr: np.ndarray,
        *,
        confidence: float,
        iou: float,
    ) -> tuple[Detection, ...]:
        self.call_count += 1
        # Return 1 detection on even frames
        if self.call_count % 2 == 0:
            return (
                Detection(
                    class_id=0,
                    class_name="bien_cam",
                    confidence=0.85,
                    xyxy=(5.0, 5.0, 20.0, 20.0),
                ),
            )
        return ()


def test_process_video_success(tmp_path: Path):
    in_video = create_tiny_synthetic_video(
        tmp_path / "input.mp4", num_frames=6, width=64, height=48, fps=10.0
    )
    out_video = tmp_path / "output.mp4"
    csv_path = tmp_path / "detections.csv"

    progress_reports: list[VideoProgress] = []

    def on_progress(p: VideoProgress):
        progress_reports.append(p)

    predictor = FakeVideoPredictor()
    options = InferenceOptions(confidence=0.25, iou=0.7)

    analysis = process_video(
        input_path=in_video,
        output_path=out_video,
        csv_path=csv_path,
        predictor=predictor,
        options=options,
        on_progress=on_progress,
    )

    assert out_video.is_file()
    assert not (tmp_path / "output.partial.mp4").exists()
    assert analysis.width == 64
    assert analysis.height == 48
    assert analysis.fps == 10.0
    assert analysis.total_frames == 6
    assert analysis.processed_frames == 6
    assert analysis.detection_counts_by_class == {"bien_cam": 3}

    # Verify progress callback
    assert len(progress_reports) == 6
    fractions = [p.fraction for p in progress_reports]
    assert fractions == sorted(fractions)
    assert fractions[-1] == 1.0

    # Verify CSV content
    csv_text = csv_path.read_text(encoding="utf-8-sig")
    lines = csv_text.strip().splitlines()
    assert lines[0] == "source,frame_index,timestamp_s,class_id,class_name,confidence,x1,y1,x2,y2"
    assert len(lines) == 4  # 1 header + 3 detection rows
    for row in lines[1:]:
        cols = row.split(",")
        assert cols[0] == in_video.name
        assert cols[1] in ["1", "3", "5"]  # 0-indexed frame indices
        assert cols[4] == "bien_cam"


def test_process_video_rejects_corrupted_file(tmp_path: Path):
    corrupt_file = tmp_path / "fake.mp4"
    corrupt_file.write_text("plain text, not video")

    out_video = tmp_path / "output.mp4"
    csv_path = tmp_path / "detections.csv"
    predictor = FakeVideoPredictor()
    options = InferenceOptions()

    with pytest.raises(VideoProcessingError, match="Unable to open video"):
        process_video(
            input_path=corrupt_file,
            output_path=out_video,
            csv_path=csv_path,
            predictor=predictor,
            options=options,
        )


def test_process_video_failure_midway_cleans_up_and_reports_frame(tmp_path: Path):
    in_video = create_tiny_synthetic_video(
        tmp_path / "input.mp4", num_frames=6, width=64, height=48, fps=10.0
    )
    out_video = tmp_path / "output.mp4"
    csv_path = tmp_path / "detections.csv"

    class FailingPredictor:
        def __init__(self):
            self.calls = 0

        def predict(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 3:
                raise RuntimeError("Boom at frame 3")
            return ()

    predictor = FailingPredictor()
    options = InferenceOptions()

    with pytest.raises(VideoProcessingError) as exc_info:
        process_video(
            input_path=in_video,
            output_path=out_video,
            csv_path=csv_path,
            predictor=predictor,
            options=options,
        )

    assert "frame 2" in str(exc_info.value).lower() or "frame 3" in str(exc_info.value).lower()
    # Final output must NOT exist
    assert not out_video.exists()


def test_process_video_codec_fallback(tmp_path: Path):
    in_video = create_tiny_synthetic_video(
        tmp_path / "input.mp4", num_frames=3, width=64, height=48, fps=10.0
    )
    out_video = tmp_path / "output.mp4"
    csv_path = tmp_path / "detections.csv"
    predictor = FakeVideoPredictor()
    options = InferenceOptions()

    # Simulate first codec failing to initialize, falling back to mp4v
    real_video_writer = cv2.VideoWriter
    attempt = 0

    def mock_writer(filename, fourcc, fps, frame_size):
        nonlocal attempt
        attempt += 1
        if attempt == 1:
            # First codec fails to open
            bad_writer = MagicMock()
            bad_writer.isOpened.return_value = False
            return bad_writer
        return real_video_writer(filename, fourcc, fps, frame_size)

    with patch("cv2.VideoWriter", side_effect=mock_writer):
        analysis = process_video(
            input_path=in_video,
            output_path=out_video,
            csv_path=csv_path,
            predictor=predictor,
            options=options,
        )
        assert analysis.fallback_codec_used is True
        assert analysis.codec_note is not None
        assert out_video.is_file()
