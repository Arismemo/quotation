import logging
import sys
import uuid
from io import BytesIO
from pathlib import Path
from typing import Literal, Optional

import cv2
import numpy as np
from PIL import Image
from rembg import remove

STATIC_DIR = Path("app/static")
UPLOADS_DIR = STATIC_DIR / "uploads"
ANALYSIS_DIR = UPLOADS_DIR / "analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


def _ensure_uint8(image: np.ndarray) -> np.ndarray:
    if image.dtype == np.uint8:
        return image
    image = np.clip(image, 0, 255)
    return image.astype(np.uint8)


def _find_largest_contour(binary_mask: np.ndarray) -> Optional[np.ndarray]:
    contours, _ = cv2.findContours(
        binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) <= 0:
        return None
    return largest


def _compute_ratio_from_contour(
    contour: np.ndarray,
) -> tuple[float, tuple[np.ndarray, tuple[float, float], float]]:
    area = float(cv2.contourArea(contour))
    rect = cv2.minAreaRect(contour)  # ((cx,cy),(w,h),angle)
    (w, h) = rect[1]
    rect_area = float(max(w, 0.0) * max(h, 0.0))
    if rect_area <= 0.0:
        return 0.0, rect
    return max(0.0, min(1.0, area / rect_area)), rect


def _draw_preview(base_bgr: np.ndarray, contour: np.ndarray, rect) -> np.ndarray:
    preview = base_bgr.copy()
    # draw contour
    cv2.drawContours(preview, [contour], -1, (0, 255, 0), 2)
    # draw rotated rect
    box = cv2.boxPoints(rect)
    box = np.intp(box)
    cv2.polylines(preview, [box], True, (0, 0, 255), 2)
    return preview


def analyze_with_opencv(image_bgr: np.ndarray) -> tuple[float, np.ndarray]:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Try OTSU both polarities and pick better one by largest contour area
    _, thr1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, thr2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    def postprocess(mask: np.ndarray) -> np.ndarray:
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        return mask

    thr1 = postprocess(thr1)
    thr2 = postprocess(thr2)

    c1 = _find_largest_contour(thr1)
    c2 = _find_largest_contour(thr2)

    def contour_score(c: Optional[np.ndarray]) -> float:
        return 0.0 if c is None else float(cv2.contourArea(c))

    contour = c1 if contour_score(c1) >= contour_score(c2) else c2
    if contour is None:
        # fallback: Canny + dilation
        edges = cv2.Canny(gray, 50, 150)
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        contour = _find_largest_contour(edges)
        if contour is None:
            raise ValueError("未能检测到有效前景轮廓")

    ratio, rect = _compute_ratio_from_contour(contour)
    preview = _draw_preview(image_bgr, contour, rect)
    return ratio, preview


def analyze_with_rembg(image_bytes: bytes) -> tuple[float, np.ndarray]:
    # Remove background to RGBA bytes
    result_bytes = remove(image_bytes)
    rgba = Image.open(BytesIO(result_bytes)).convert("RGBA")
    # alpha to mask
    alpha = np.array(rgba.split()[-1])  # HxW uint8
    _, mask = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contour = _find_largest_contour(mask)
    if contour is None:
        raise ValueError("未能从抠图结果中检测到有效前景轮廓")

    ratio, rect = _compute_ratio_from_contour(contour)
    # Compose preview on white background for visibility
    rgb = np.array(rgba.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    preview = _draw_preview(bgr, contour, rect)
    return ratio, preview


def save_preview(preview_bgr: np.ndarray) -> str:
    filename = f"analysis_{uuid.uuid4().hex}.png"
    out_path = ANALYSIS_DIR / filename
    cv2.imwrite(str(out_path), _ensure_uint8(preview_bgr))
    # return relative static path
    return f"/static/uploads/analysis/{filename}"


def load_image_bgr_from_path(static_path: str) -> tuple[np.ndarray, bytes]:
    # static_path like "/static/uploads/xxx.png"
    if not static_path.startswith("/static/"):
        raise ValueError("非法路径")
    rel = static_path[len("/static/") :]
    abs_path = STATIC_DIR / rel
    if not abs_path.exists():
        raise FileNotFoundError("图片不存在")
    data = abs_path.read_bytes()
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法读取图片内容")
    return img, data


def analyze_area_ratio(
    static_path: str, method: Literal["opencv", "rembg"]
) -> tuple[float, str]:
    # 使用新模块进行抠图与面积计算
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from area_ratio_calculator import AreaRatioCalculator  # type: ignore
    from background_remover import BackgroundRemover  # type: ignore

    image_bgr, image_bytes = load_image_bgr_from_path(static_path)
    remover = BackgroundRemover()
    mask, rgb = remover.get_mask_and_rgb(
        method=method,
        image_bgr=image_bgr if method == "opencv" else None,
        image_bytes=image_bytes if method == "rembg" else None,
    )
    # 预览需要BGR底图
    base_bgr = image_bgr if method == "opencv" else cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    ratio, preview = AreaRatioCalculator().compute(mask=mask, base_bgr=base_bgr)
    preview_path = save_preview(preview)
    return ratio, preview_path


def analyze_colors(static_path: str) -> dict[str, object]:
    """统计主体颜色数量与调色板（改为使用 color_counter 模块）。"""
    # 解析文件绝对路径
    if not static_path.startswith("/static/"):
        raise ValueError("非法路径")
    rel = static_path[len("/static/") :]
    abs_path = STATIC_DIR / rel
    if not abs_path.exists():
        raise FileNotFoundError("图片不存在")
    logger.info("[colors] analyze start path=%s abs=%s", static_path, str(abs_path))

    # 导入 color_counter 并调用
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    try:
        from color_counter import count_product_colors_from_mask_rgb  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.exception("[colors] failed to import color_counter: %s", e)
        raise ImportError("无法导入 color_counter 模块") from e

    # 复用我们已有抠图流程，避免重复IO
    image_bgr, image_bytes = load_image_bgr_from_path(static_path)
    from background_remover import BackgroundRemover  # type: ignore

    remover = BackgroundRemover()
    # 默认用 rembg 抠图获得 mask 和 rgb（白底合成）
    mask, rgb = remover.get_mask_and_rgb(
        method="rembg", image_bgr=None, image_bytes=image_bytes
    )
    try:
        logger.info(
            "[colors] mask pixels=%d rgb_shape=%s",
            int((mask > 0).sum()),
            str(rgb.shape),
        )
    except Exception:
        logger.warning("[colors] failed to log mask/rgb shape")

    # 用兼容方法直接基于 mask+rgb 统计颜色
    try:
        num_colors, colors, percentages = count_product_colors_from_mask_rgb(
            mask, rgb, k_range=(2, 10), min_percentage=5.0
        )
        logger.info(
            "[colors] clustering done num_colors=%s colors_len=%s pct_len=%s",
            str(num_colors),
            str(len(colors) if colors else 0),
            str(len(percentages) if percentages else 0),
        )
    except Exception as e:
        logger.exception("[colors] clustering error: %s", e)
        raise

    if num_colors is None:
        raise ValueError("颜色统计失败")

    # 构造统一返回结构
    palette = []
    if colors and percentages:
        for rgb, pct in zip(colors, percentages):
            palette.append(
                {
                    "rgb": [int(rgb[0]), int(rgb[1]), int(rgb[2])],
                    "count": 0,  # 外部不需要像素计数，保留字段
                    "ratio": round(float(pct) / 100.0, 6),
                }
            )

    return {"color_count": int(num_colors), "palette": palette}
