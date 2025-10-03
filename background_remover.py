from io import BytesIO
from typing import Literal, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from rembg import remove


class BackgroundRemover:
    """前景抠图与RGB合成。

    输出统一为: (mask_uint8, rgb_uint8)
    - mask: 1表示前景, 0表示背景
    - rgb: 用于颜色分析/预览的RGB图，rembg流程会以白底合成
    """

    @staticmethod
    def _refine_mask(mask: np.ndarray) -> np.ndarray:
        k3 = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k3, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k3, iterations=2)
        mask = cv2.erode(mask, k3, iterations=1)
        return mask

    def rembg_mask_and_rgb(self, image_bytes: bytes) -> Tuple[np.ndarray, np.ndarray]:
        result_bytes = remove(image_bytes)
        rgba = Image.open(BytesIO(result_bytes)).convert("RGBA")
        rgba_np = np.array(rgba)
        alpha = rgba_np[..., 3]
        mask = (alpha > 0).astype(np.uint8)
        mask = self._refine_mask(mask)
        rgb_fg = rgba_np[..., :3].astype(np.float32)
        a = (alpha.astype(np.float32) / 255.0)[..., None]
        white_bg = np.full_like(rgb_fg, 255.0, dtype=np.float32)
        rgb = (rgb_fg * a + white_bg * (1.0 - a)).astype(np.uint8)
        rgb = cv2.GaussianBlur(rgb, (3, 3), 0)
        return mask, rgb

    def opencv_mask_and_rgb(self, image_bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        bgr = image_bgr
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thr1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, thr2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        c1 = np.count_nonzero(thr1)
        c2 = np.count_nonzero(thr2)
        mask = thr1 if c1 >= c2 else thr2
        mask = (mask > 0).astype(np.uint8)
        mask = self._refine_mask(mask)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        rgb = cv2.GaussianBlur(rgb, (3, 3), 0)
        return mask, rgb

    def get_mask_and_rgb(self, *, method: Literal["rembg", "opencv"], image_bgr: Optional[np.ndarray], image_bytes: Optional[bytes]) -> Tuple[np.ndarray, np.ndarray]:
        if method == "rembg":
            if image_bytes is None:
                raise ValueError("rembg 需要 image_bytes")
            return self.rembg_mask_and_rgb(image_bytes)
        if method == "opencv":
            if image_bgr is None:
                raise ValueError("opencv 需要 image_bgr")
            return self.opencv_mask_and_rgb(image_bgr)
        raise ValueError("不支持的抠图方法")


