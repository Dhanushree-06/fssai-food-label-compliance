"""
Unit Tests for OpenCV Image Preprocessing Service
"""

import os
import shutil
import tempfile
import cv2
import numpy as np
from app.services import ocr_engine
from app.services.image_processing import ImagePreprocessor
from app.services.ocr_engine import OCREngine


SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "static", "sample_images"
)


def test_deskew_image_synthetic():
    """Verify deskew function handles synthetic test image without errors."""
    dummy_img = np.ones((300, 300, 3), dtype=np.uint8) * 255
    cv2.putText(dummy_img, "FSSAI TEST LABEL", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    rotated, angle = ImagePreprocessor.deskew_image(dummy_img)
    assert rotated.shape == dummy_img.shape
    assert isinstance(angle, float)


def test_enhance_contrast():
    """Verify CLAHE contrast enhancement."""
    gray = np.ones((200, 200), dtype=np.uint8) * 128
    enhanced = ImagePreprocessor.enhance_contrast(gray)
    assert enhanced.shape == gray.shape


def test_preprocess_pipeline_on_sample():
    """Verify the enhanced preview preserves grayscale detail for reading."""
    sample_path = os.path.join(SAMPLE_DIR, "sample_snack_pack.png")
    if os.path.exists(sample_path):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = os.path.join(temp_dir, "label.png")
            shutil.copyfile(sample_path, image_path)
            res = ImagePreprocessor.preprocess_pipeline(image_path)
            assert "processed_path" in res
            assert os.path.exists(res["processed_path"])
            assert "deskew_angle" in res
            assert res["original_shape"][0] > 0
            processed = cv2.imread(res["processed_path"], cv2.IMREAD_GRAYSCALE)
            assert processed.shape == res["original_shape"]
            assert len(np.unique(processed)) > 2


def test_detect_veg_symbol():
    """Verify green veg circle detection on sample."""
    sample_path = os.path.join(SAMPLE_DIR, "sample_snack_pack.png")
    if os.path.exists(sample_path):
        res = ImagePreprocessor.detect_veg_nonveg_symbol(sample_path)
        assert "detected" in res
        assert res["detected"] is True
        assert res["type"] == "VEGETARIAN"

    defective_path = os.path.join(SAMPLE_DIR, "sample_defective_label.png")
    if os.path.exists(defective_path):
        res = ImagePreprocessor.detect_veg_nonveg_symbol(defective_path)
        assert res["detected"] is False


def test_ocr_reads_image_content_instead_of_filename():
    """OCR output must come from visible image text, not the image's name."""
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = os.path.join(temp_dir, "sample_snack_pack.png")
        image = np.full((220, 1400, 3), 255, dtype=np.uint8)
        cv2.putText(
            image, "FSSAI LICENSE 10012345678901", (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX, 1.7, (0, 0, 0), 3, cv2.LINE_AA
        )
        cv2.putText(
            image, "INGREDIENTS: WHEAT FLOUR, SUGAR", (30, 165),
            cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 0), 3, cv2.LINE_AA
        )
        assert cv2.imwrite(image_path, image)

        result = OCREngine.extract_text(image_path)

    assert result["engine_used"] == "RapidOCR"
    assert "10012345678901" in result["full_text"]
    assert "WHEAT FLOUR" in result["full_text"]
    assert "CRISP KRAFT" not in result["full_text"]


def test_ocr_uses_best_complete_image_read(monkeypatch):
    """Select one OCR variant so conflicting text and bounding boxes are not combined."""
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = os.path.join(temp_dir, "label.png")
        preprocessed_path = os.path.join(temp_dir, "preprocessed.png")
        for path in (image_path, preprocessed_path):
            with open(path, "wb") as image_file:
                image_file.write(b"test")

        results = {
            image_path: OCREngine._format_result(
                [{"text": "Ingredients:", "confidence": 0.75, "box": [10, 10, 200, 30]}],
                "RapidOCR"
            ),
            preprocessed_path: OCREngine._format_result(
                [
                    {"text": "Ingredients", "confidence": 0.95, "box": [10, 10, 200, 30]},
                    {"text": "Wheat flour, sugar", "confidence": 0.90, "box": [10, 50, 220, 30]}
                ],
                "RapidOCR"
            )
        }
        monkeypatch.setattr(ocr_engine, "_RAPIDOCR_AVAILABLE", True)
        monkeypatch.setattr(OCREngine, "_run_rapidocr", lambda path: results[path])

        result = OCREngine.extract_text(
            image_path,
            preprocessed_path=preprocessed_path
        )

    assert result["full_text"].count("Ingredients") == 1
    assert result["full_text"] == "Ingredients\nWheat flour, sugar"
    assert result["image_path_used"] == preprocessed_path


def test_ocr_prefers_confident_read_over_longer_noisy_read(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = os.path.join(temp_dir, "label.png")
        preprocessed_path = os.path.join(temp_dir, "preprocessed.png")
        for path in (image_path, preprocessed_path):
            with open(path, "wb") as image_file:
                image_file.write(b"test")

        results = {
            image_path: OCREngine._format_result(
                [{
                    "text": "Clear ingredients and nutrition details",
                    "confidence": 0.9,
                    "box": [10, 10, 200, 30]
                }],
                "RapidOCR"
            ),
            preprocessed_path: OCREngine._format_result(
                [{
                    "text": "Unclear " * 12,
                    "confidence": 0.45,
                    "box": [10, 10, 400, 30]
                }],
                "RapidOCR"
            )
        }
        monkeypatch.setattr(ocr_engine, "_RAPIDOCR_AVAILABLE", True)
        monkeypatch.setattr(OCREngine, "_run_rapidocr", lambda path: results[path])

        result = OCREngine.extract_text(
            image_path,
            preprocessed_path=preprocessed_path
        )

    assert result["full_text"] == "Clear ingredients and nutrition details"
    assert result["image_path_used"] == image_path


def test_unavailable_opencv_fallback_does_not_invent_label_text():
    """The no-OCR fallback must return no text rather than synthetic declarations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = os.path.join(temp_dir, "sample_snack_pack.png")
        assert cv2.imwrite(image_path, np.full((80, 240, 3), 255, dtype=np.uint8))

        result = OCREngine._fallback_ocr_extractor(image_path)

    assert result["full_text"] == ""
    assert result["bounding_boxes"] == []
    assert result["average_confidence"] == 0.0
