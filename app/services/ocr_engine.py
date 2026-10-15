"""OCR service for extracting real text and locations from food label images."""

import math
import os

import cv2
import numpy as np

_PADDLE_AVAILABLE = False
_EASYOCR_AVAILABLE = False
_RAPIDOCR_AVAILABLE = False
_paddle_reader = None
_easyocr_reader = None
_rapid_reader = None

try:
    from paddleocr import PaddleOCR
    _PADDLE_AVAILABLE = True
except ImportError:
    PaddleOCR = None

try:
    import easyocr
    _EASYOCR_AVAILABLE = True
except ImportError:
    easyocr = None

try:
    from rapidocr_onnxruntime import RapidOCR
    _RAPIDOCR_AVAILABLE = True
except ImportError:
    RapidOCR = None


class OCREngine:
    """Reads image text using local OCR engines; never invents OCR content."""

    @classmethod
    def get_paddle_reader(cls):
        global _paddle_reader
        if not _PADDLE_AVAILABLE:
            return None
        if _paddle_reader is None:
            _paddle_reader = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        return _paddle_reader

    @classmethod
    def get_easyocr_reader(cls):
        global _easyocr_reader
        if not _EASYOCR_AVAILABLE:
            return None
        if _easyocr_reader is None:
            _easyocr_reader = easyocr.Reader(["en"], gpu=False)
        return _easyocr_reader

    @classmethod
    def get_rapid_reader(cls):
        global _rapid_reader
        if not _RAPIDOCR_AVAILABLE:
            return None
        if _rapid_reader is None:
            _rapid_reader = RapidOCR()
        return _rapid_reader

    @classmethod
    def extract_text(cls, image_path, preferred_engine="auto", preprocessed_path=None):
        """Extract text from the original image and optionally an enhanced variant."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        image_paths = [image_path]
        if preprocessed_path and os.path.exists(preprocessed_path):
            image_paths.append(preprocessed_path)

        engines = []
        if preferred_engine in ("auto", "paddle") and _PADDLE_AVAILABLE:
            engines.append(("PaddleOCR", cls._run_paddle))
        if preferred_engine in ("auto", "easyocr") and _EASYOCR_AVAILABLE:
            engines.append(("EasyOCR", cls._run_easyocr))
        if preferred_engine in ("auto", "rapidocr") and _RAPIDOCR_AVAILABLE:
            engines.append(("RapidOCR", cls._run_rapidocr))

        results = []
        errors = []
        for engine_name, run_engine in engines:
            for candidate_path in image_paths:
                try:
                    result = run_engine(candidate_path)
                    if result["full_text"]:
                        result["engine_used"] = engine_name
                        results.append((result, candidate_path))
                except Exception as error:
                    errors.append(f"{engine_name}: {error}")
                    print(f"[OCR] {engine_name} failed on {candidate_path}: {error}")

        if results:
            best_result, best_path = max(
                results,
                key=lambda item: cls._text_quality(item[0])
            )
            best_result["image_path_used"] = best_path
            return best_result

        if errors:
            message = "; ".join(errors)
            print(f"[OCR] No OCR engine could read the image: {message}")
        return {
            "engine_used": "OCR unavailable",
            "full_text": "",
            "lines": [],
            "bounding_boxes": [],
            "average_confidence": 0.0
        }

    @staticmethod
    def _text_quality(result):
        """Prefer confident OCR while rewarding broader reads with diminishing returns."""
        boxes = result["bounding_boxes"]
        character_count = sum(len(box["text"]) for box in boxes)
        if not character_count:
            return 0.0

        average_confidence = sum(
            len(box["text"]) * box["confidence"] for box in boxes
        ) / character_count
        return average_confidence * math.log1p(character_count)

    @classmethod
    def _run_paddle(cls, image_path):
        reader = cls.get_paddle_reader()
        result = reader.ocr(image_path, cls=True)
        boxes = []
        if result and result[0]:
            for coords, (text, confidence) in result[0]:
                xs = [point[0] for point in coords]
                ys = [point[1] for point in coords]
                boxes.append({
                    "text": str(text).strip(),
                    "confidence": float(confidence),
                    "box": [
                        int(min(xs)), int(min(ys)),
                        int(max(xs) - min(xs)), int(max(ys) - min(ys))
                    ]
                })
        return cls._format_result(boxes, "PaddleOCR")

    @classmethod
    def _run_easyocr(cls, image_path):
        reader = cls.get_easyocr_reader()
        results = reader.readtext(image_path)
        boxes = []
        for coords, text, confidence in results:
            xs = [point[0] for point in coords]
            ys = [point[1] for point in coords]
            boxes.append({
                "text": str(text).strip(),
                "confidence": float(confidence),
                "box": [
                    int(min(xs)), int(min(ys)),
                    int(max(xs) - min(xs)), int(max(ys) - min(ys))
                ]
            })
        return cls._format_result(boxes, "EasyOCR")

    @classmethod
    def _run_rapidocr(cls, image_path):
        reader = cls.get_rapid_reader()
        results, _ = reader(image_path)
        boxes = []
        for coords, text, confidence in results or []:
            points = np.asarray(coords)
            boxes.append({
                "text": str(text).strip(),
                "confidence": float(confidence),
                "box": [
                    int(points[:, 0].min()), int(points[:, 1].min()),
                    int(points[:, 0].max() - points[:, 0].min()),
                    int(points[:, 1].max() - points[:, 1].min())
                ]
            })
        return cls._format_result(boxes, "RapidOCR")

    @staticmethod
    def _format_result(boxes, engine_name):
        normalized = []
        for box in boxes:
            if not box["text"]:
                continue
            normalized.append({
                "id": len(normalized) + 1,
                "text": box["text"],
                "confidence": round(max(0.0, min(1.0, box["confidence"])), 3),
                "box": box["box"]
            })

        return {
            "engine_used": engine_name,
            "full_text": "\n".join(box["text"] for box in normalized),
            "lines": [box["text"] for box in normalized],
            "bounding_boxes": normalized,
            "average_confidence": round(
                sum(box["confidence"] for box in normalized) / len(normalized), 3
            ) if normalized else 0.0
        }

    @staticmethod
    def _fallback_ocr_extractor(image_path):
        """Compatibility entry point; OpenCV alone cannot recognize text."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not decode image at {image_path}")
        return {
            "engine_used": "OCR unavailable",
            "full_text": "",
            "lines": [],
            "bounding_boxes": [],
            "average_confidence": 0.0
        }

    @classmethod
    def draw_annotated_image(cls, image_path, bounding_boxes, output_path):
        """Draw OCR-recognized text boxes over the original image."""
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not decode image at {image_path}")

        for item in bounding_boxes:
            x, y, width, height = item["box"]
            cv2.rectangle(image, (x, y), (x + width, y + height), (0, 200, 0), 2)
            label = f"{item['text'][:30]} ({item['confidence']:.2f})"
            cv2.putText(
                image, label, (x, max(20, y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1
            )

        if not cv2.imwrite(output_path, image):
            raise OSError(f"Could not write annotated image to {output_path}")
        return output_path
