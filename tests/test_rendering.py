import io

import numpy as np
from PIL import Image

from trafficvision.domain import Detection
from trafficvision.rendering import annotate_image, detections_csv


def test_annotate_image_with_vietnamese_labels():
    img_bgr = np.zeros((300, 400, 3), dtype=np.uint8)
    det1 = Detection(
        class_id=0,
        class_name="Cấm đi ngược chiều",
        confidence=0.91,
        xyxy=(20.0, 30.0, 150.0, 160.0),
    )
    det2 = Detection(
        class_id=1,
        class_name="Biển cảnh báo nguy hiểm",
        confidence=0.78,
        xyxy=(200.0, 50.0, 350.0, 200.0),
    )

    annotated_bytes = annotate_image(img_bgr, [det1, det2], format="JPEG")
    assert isinstance(annotated_bytes, bytes)
    assert len(annotated_bytes) > 0

    # Ensure output is a valid decodable image matching input dimensions
    rendered = Image.open(io.BytesIO(annotated_bytes))
    assert rendered.size == (400, 300)
    assert rendered.format == "JPEG"

    # Test WEBP encoding
    webp_bytes = annotate_image(img_bgr, [det1, det2], format="WEBP")
    assert isinstance(webp_bytes, bytes)
    rendered_webp = Image.open(io.BytesIO(webp_bytes))
    assert rendered_webp.size == (400, 300)
    assert rendered_webp.format == "WEBP"


def test_detections_csv_format_and_bom():
    det = Detection(
        class_id=5,
        class_name="Biển cấm đỗ",
        confidence=0.8543,
        xyxy=(10.5, 20.25, 100.0, 150.75),
    )
    csv_bytes = detections_csv([det], source_name="test_photo.jpg")

    # Assert UTF-8 BOM is present
    assert csv_bytes.startswith(b"\xef\xbb\xbf")

    text = csv_bytes.decode("utf-8-sig")
    lines = text.strip().split("\r\n") if "\r\n" in text else text.strip().split("\n")
    assert lines[0] == "source,frame_index,timestamp_s,class_id,class_name,confidence,x1,y1,x2,y2"
    assert len(lines) == 2

    # Check contents of data row
    cols = lines[1].split(",")
    assert cols[0] == "test_photo.jpg"
    assert cols[1] == ""  # frame_index empty for image
    assert cols[2] == ""  # timestamp_s empty for image
    assert cols[3] == "5"
    assert cols[4] == "Biển cấm đỗ"
    assert "0.85" in cols[5]


def test_detections_csv_empty_detections():
    csv_bytes = detections_csv([], source_name="empty.jpg")
    text = csv_bytes.decode("utf-8-sig")
    lines = text.strip().splitlines()
    assert len(lines) == 1
    assert lines[0] == "source,frame_index,timestamp_s,class_id,class_name,confidence,x1,y1,x2,y2"
