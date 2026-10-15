"""
OpenCV Image Preprocessing and Computer Vision Service
AI-Based Food Label Compliance Verification Platform
"""

import os
import cv2
import numpy as np


class ImagePreprocessor:
    """Provides OpenCV image transformations and symbol detection for food labels."""

    @staticmethod
    def deskew_image(image):
        """Detects text skew angle and rotates the image to upright orientation."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # Find coordinates of all foreground pixels
            coords = np.column_stack(np.where(thresh > 0))
            if len(coords) < 50:
                return image, 0.0

            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            # Clamp extreme or spurious angles to avoid flipping valid labels
            if abs(angle) > 30.0 or abs(angle) < 0.5:
                return image, 0.0

            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                image, rot_mat, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            return rotated, round(float(angle), 2)
        except Exception as e:
            print(f"[OpenCV] Deskew error: {e}")
            return image, 0.0

    @staticmethod
    def enhance_contrast(gray_image):
        """Applies CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray_image)

    @classmethod
    def preprocess_pipeline(cls, image_path, options=None):
        """Deskew and improve local contrast without discarding fine print."""
        options = options or {}

        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Could not load image at {image_path}")

        orig_h, orig_w = img.shape[:2]
        deskew_angle = 0.0

        # Step 1: Deskew
        if options.get("enable_deskew", True):
            img, deskew_angle = cls.deskew_image(img)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if options.get("enable_clahe", True):
            enhanced = cls.enhance_contrast(gray)
        else:
            enhanced = gray

        if options.get("enable_sharpen", True):
            blurred = cv2.GaussianBlur(enhanced, (0, 0), 1.2)
            enhanced = cv2.addWeighted(enhanced, 1.35, blurred, -0.35, 0)

        dir_name = os.path.dirname(image_path)
        base_name = os.path.basename(image_path)
        processed_filename = f"preproc_{base_name}"
        processed_path = os.path.join(dir_name, processed_filename)
        if not cv2.imwrite(processed_path, enhanced):
            raise OSError(f"Could not write preprocessed image to {processed_path}")

        return {
            "original_shape": (orig_h, orig_w),
            "deskew_angle": deskew_angle,
            "processed_path": processed_path,
            "processed_filename": processed_filename,
            "processed_image": enhanced
        }

    @staticmethod
    def detect_veg_nonveg_symbol(image_path):
        """
        Analyzes the image for FSSAI Vegetarian (Green circle in square)
        or Non-Vegetarian (Brown triangle in square) logos.
        """
        img = cv2.imread(image_path)
        if img is None:
            return {"detected": False, "type": "UNKNOWN", "confidence": 0.0, "details": "Image load failed"}

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, w = img.shape[:2]
        total_pixels = h * w

        # Green HSV range for Vegetarian Logo
        lower_green = np.array([35, 60, 60])
        upper_green = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)

        # Brown/Red HSV range for Non-Vegetarian Logo
        lower_brown = np.array([5, 70, 40])
        upper_brown = np.array([20, 255, 200])
        brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)

        # Also lower red
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        nonveg_mask = cv2.bitwise_or(brown_mask, red_mask)

        # Require a green circular mark nested inside a separate square outline.
        green_contours, green_hierarchy = cv2.findContours(
            green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        for index, cnt in enumerate(green_contours):
            area = cv2.contourArea(cnt)
            if 150 < area < (total_pixels * 0.15):
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect_ratio = float(cw) / max(ch, 1)
                polygon = cv2.approxPolyDP(
                    cnt, 0.04 * cv2.arcLength(cnt, True), True
                )
                if 0.75 <= aspect_ratio <= 1.35 and len(polygon) == 4:
                    outer_center = (x + cw / 2, y + ch / 2)
                    for circle_index, circle in enumerate(green_contours):
                        circle_area = cv2.contourArea(circle)
                        if not 0 < circle_area < area:
                            continue
                        circle_x, circle_y, circle_w, circle_h = cv2.boundingRect(circle)
                        circle_ratio = circle_w / max(circle_h, 1)
                        circle_center = (
                            circle_x + circle_w / 2,
                            circle_y + circle_h / 2
                        )
                        if (
                            abs(circle_center[0] - outer_center[0]) > cw * 0.2
                            or abs(circle_center[1] - outer_center[1]) > ch * 0.2
                            or not 0.75 <= circle_ratio <= 1.25
                        ):
                            continue

                        parent_index = green_hierarchy[0][circle_index][3]
                        nested_in_square = False
                        while parent_index != -1:
                            if parent_index == index:
                                nested_in_square = True
                                break
                            parent_index = green_hierarchy[0][parent_index][3]
                        if not nested_in_square:
                            continue

                        perimeter = cv2.arcLength(circle, True)
                        circularity = (
                            4 * np.pi * circle_area / (perimeter * perimeter)
                            if perimeter > 0 else 0
                        )
                        if circularity > 0.60 and 0.15 < circle_area / area < 0.80:
                            return {
                                "detected": True,
                                "type": "VEGETARIAN",
                                "confidence": round(min(0.95, circularity), 2),
                                "box": [int(x), int(y), int(cw), int(ch)],
                                "details": "Centered green circle nested within a green square outline"
                            }

        # Analyze Non-Veg Contours
        nonveg_contours, _ = cv2.findContours(nonveg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in nonveg_contours:
            area = cv2.contourArea(cnt)
            if 150 < area < (total_pixels * 0.15):
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect_ratio = float(cw) / max(ch, 1)
                if 0.7 <= aspect_ratio <= 1.4:
                    # Check triangularity via contour approximation
                    approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
                    if len(approx) == 3:
                        return {
                            "detected": True,
                            "type": "NON_VEGETARIAN",
                            "confidence": 0.88,
                            "box": [int(x), int(y), int(cw), int(ch)],
                            "details": "Brown/Red triangle emblem detected via OpenCV HSV contour analysis"
                        }

        return {
            "detected": False,
            "type": "NOT_DETECTED",
            "confidence": 0.0,
            "box": None,
            "details": "No distinct green circle or brown triangle contour isolated"
        }

    @staticmethod
    def draw_annotated_image(image_path, bounding_boxes, output_path):
        """Draws bounding boxes and labels onto the image for web visualization."""
        img = cv2.imread(image_path)
        if img is None:
            return None

        h, w = img.shape[:2]
        for box_info in bounding_boxes:
            box = box_info.get("box", [])
            text = box_info.get("text", "")
            conf = box_info.get("confidence", 0.0)
            if len(box) == 4:
                x, y, bw, bh = box
                # Clamp within image bounds
                x = max(0, min(x, w - 1))
                y = max(0, min(y, h - 1))
                bw = min(bw, w - x)
                bh = min(bh, h - y)

                cv2.rectangle(img, (x, y), (x + bw, y + bh), (30, 180, 70), 2)
                # Label background
                label = f"{text[:18]}.. ({int(conf*100)}%)" if len(text) > 18 else f"{text} ({int(conf*100)}%)"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                cv2.rectangle(img, (x, max(0, y - 18)), (x + tw + 6, y), (30, 180, 70), -1)
                cv2.putText(
                    img, label, (x + 3, max(12, y - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA
                )

        cv2.imwrite(output_path, img)
        return output_path
