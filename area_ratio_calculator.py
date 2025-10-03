from typing import Tuple

import cv2
import numpy as np


class AreaRatioCalculator:
    """根据前景mask计算占用面积比例并绘制预览。"""

    @staticmethod
    def _ensure_uint8(image: np.ndarray) -> np.ndarray:
        if image.dtype == np.uint8:
            return image
        image = np.clip(image, 0, 255)
        return image.astype(np.uint8)

    @staticmethod
    def _find_largest_contour(binary_mask: np.ndarray):
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) <= 0:
            return None
        return largest

    @staticmethod
    def _compute_ratio_from_contour(contour: np.ndarray):
        area = float(cv2.contourArea(contour))
        rect = cv2.minAreaRect(contour)
        (w, h) = rect[1]
        rect_area = float(max(w, 0.0) * max(h, 0.0))
        if rect_area <= 0.0:
            return 0.0, rect
        return max(0.0, min(1.0, area / rect_area)), rect

    @staticmethod
    def _draw_preview(base_bgr: np.ndarray, contour: np.ndarray, rect) -> np.ndarray:
        preview = base_bgr.copy()
        cv2.drawContours(preview, [contour], -1, (0, 255, 0), 2)
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        cv2.polylines(preview, [box], True, (0, 0, 255), 2)
        return preview

    def compute(self, *, mask: np.ndarray, base_bgr: np.ndarray) -> Tuple[float, np.ndarray]:
        contour = self._find_largest_contour((mask > 0).astype(np.uint8))
        if contour is None:
            raise ValueError("未能检测到有效前景轮廓")
        ratio, rect = self._compute_ratio_from_contour(contour)
        preview = self._draw_preview(base_bgr, contour, rect)
        return ratio, self._ensure_uint8(preview)


