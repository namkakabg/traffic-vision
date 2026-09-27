import numpy as np

from trafficvision.domain import Detection
from trafficvision.inference.image import analyze_image


class FakePredictor:
    def __init__(self, detections: tuple[Detection, ...] = ()):
        self.detections = detections
        self.last_confidence: float | None = None
        self.last_iou: float | None = None

    def predict(
        self,
        image_bgr: np.ndarray,
        *,
        confidence: float,
        iou: float,
    ) -> tuple[Detection, ...]:
        self.last_confidence = confidence
        self.last_iou = iou
        return self.detections


def test_analyze_image_success():
    img_bgr = np.zeros((300, 400, 3), dtype=np.uint8)
    expected_det = Detection(
        class_id=1,
        class_name="bien_nguy_hiem",
        confidence=0.82,
        xyxy=(10.0, 20.0, 100.0, 200.0),
    )
    predictor = FakePredictor(detections=(expected_det,))

    analysis = analyze_image(img_bgr, predictor, confidence=0.35, iou=0.55)

    assert predictor.last_confidence == 0.35
    assert predictor.last_iou == 0.55
    assert analysis.width == 400
    assert analysis.height == 300
    assert analysis.inference_ms >= 0.0
    assert len(analysis.detections) == 1
    assert analysis.detections[0] == expected_det
    assert isinstance(analysis.detections, tuple)


def test_analyze_image_no_detections():
    img_bgr = np.zeros((200, 200, 3), dtype=np.uint8)
    predictor = FakePredictor(detections=())

    analysis = analyze_image(img_bgr, predictor, confidence=0.5, iou=0.5)

    assert analysis.width == 200
    assert analysis.height == 200
    assert analysis.inference_ms >= 0.0
    assert analysis.detections == ()
