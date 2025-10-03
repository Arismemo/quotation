import argparse
from io import BytesIO
from pathlib import Path
from typing import Literal, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from rembg import remove
from skimage import color as skcolor


class Analyzer:
    """图像占用面积识别（rembg / OpenCV）。

    面积比例定义为：前景区域面积 / 其最小外接旋转矩形面积，范围 [0,1]。
    """

    @staticmethod
    def _ensure_uint8(image: np.ndarray) -> np.ndarray:
        if image.dtype == np.uint8:
            return image
        image = np.clip(image, 0, 255)
        return image.astype(np.uint8)

    @staticmethod
    def _find_largest_contour(binary_mask: np.ndarray) -> Optional[np.ndarray]:
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) <= 0:
            return None
        return largest

    @staticmethod
    def _compute_ratio_from_contour(contour: np.ndarray) -> Tuple[float, Tuple[np.ndarray, Tuple[float, float], float]]:
        area = float(cv2.contourArea(contour))
        rect = cv2.minAreaRect(contour)  # ((cx,cy),(w,h),angle)
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

    def analyze_opencv(self, image_bgr: np.ndarray) -> Tuple[float, np.ndarray]:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

        # OTSU 两种极性
        _, thr1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, thr2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        def post(mask: np.ndarray) -> np.ndarray:
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            return mask

        thr1 = post(thr1)
        thr2 = post(thr2)

        c1 = self._find_largest_contour(thr1)
        c2 = self._find_largest_contour(thr2)
        contour = c1 if (0.0 if c1 is None else cv2.contourArea(c1)) >= (0.0 if c2 is None else cv2.contourArea(c2)) else c2

        if contour is None:
            # 兜底：Canny
            edges = cv2.Canny(gray, 50, 150)
            kernel = np.ones((3, 3), np.uint8)
            edges = cv2.dilate(edges, kernel, iterations=1)
            contour = self._find_largest_contour(edges)
            if contour is None:
                raise ValueError("未能检测到有效前景轮廓")

        ratio, rect = self._compute_ratio_from_contour(contour)
        preview = self._draw_preview(image_bgr, contour, rect)
        return ratio, preview

    def analyze_rembg(self, image_bytes: bytes) -> Tuple[float, np.ndarray]:
        result_bytes = remove(image_bytes)
        rgba = Image.open(BytesIO(result_bytes)).convert("RGBA")
        alpha = np.array(rgba.split()[-1])
        _, mask = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contour = self._find_largest_contour(mask)
        if contour is None:
            raise ValueError("未能从抠图结果中检测到有效前景轮廓")

        ratio, rect = self._compute_ratio_from_contour(contour)
        rgb = np.array(rgba.convert("RGB"))
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        preview = self._draw_preview(bgr, contour, rect)
        return ratio, preview

    def analyze(self, *, image_bgr: Optional[np.ndarray], image_bytes: Optional[bytes], method: Literal["opencv", "rembg"]) -> Tuple[float, np.ndarray]:
        if method == "opencv":
            if image_bgr is None:
                raise ValueError("analyze(opencv) 需要 image_bgr")
            return self.analyze_opencv(image_bgr)
        if method == "rembg":
            if image_bytes is None:
                raise ValueError("analyze(rembg) 需要 image_bytes")
            return self.analyze_rembg(image_bytes)
        raise ValueError("不支持的算法方法")

    # ===================== 主体颜色统计 =====================
    @staticmethod
    def _rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
        # rgb uint8 -> float [0,1] -> Lab
        return skcolor.rgb2lab(rgb.astype(np.float32) / 255.0)

    @staticmethod
    def _lab_delta_e(a: np.ndarray, b: np.ndarray) -> float:
        # a,b: shape (3,) Lab
        de = skcolor.deltaE_ciede2000(a[np.newaxis, :], b[np.newaxis, :])
        de_arr = np.asarray(de).reshape(-1)
        return float(de_arr[0])

    def _kmeans_palette(self, pixels_rgb: np.ndarray, max_k: int = 12) -> Tuple[np.ndarray, np.ndarray]:
        # pixels_rgb: N x 3 uint8
        Z = pixels_rgb.reshape((-1, 3)).astype(np.float32)
        # criteria: type, max_iter, epsilon
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        K = max(2, min(max_k, max(2, int(np.clip(Z.shape[0] / 2000, 2, max_k)))))
        # fallback if very small
        if Z.shape[0] < 1000:
            K = min(6, max_k)
        compactness, labels, centers = cv2.kmeans(Z, K, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
        centers = centers.astype(np.uint8)
        return centers, labels.reshape(-1)

    def _merge_by_delta_e(self, centers_rgb: np.ndarray, counts: np.ndarray, delta_e_thresh: float = 8.0) -> Tuple[np.ndarray, np.ndarray]:
        # 多轮合并：每轮合并所有阈值内的近邻
        centers = centers_rgb.astype(np.uint8)
        cnts = counts.astype(np.int64)
        changed = True
        while changed and centers.shape[0] > 1:
            changed = False
            lab = self._rgb_to_lab(centers)
            N = centers.shape[0]
            # 计算上三角距离矩阵最小对
            min_d = 1e9
            min_i = -1
            min_j = -1
            for i in range(N):
                di = skcolor.deltaE_ciede2000(lab[i][None, :], lab[i+1:]) if i+1 < N else []
                if isinstance(di, list):
                    continue
                arr = np.asarray(di).reshape(-1)
                if arr.size == 0:
                    continue
                j_rel = int(np.argmin(arr))
                d = float(arr[j_rel])
                if d < min_d:
                    min_d = d
                    min_i = i
                    min_j = i + 1 + j_rel
            if min_i >= 0 and min_d <= delta_e_thresh:
                # 合并 min_i 与 min_j
                wi = int(cnts[min_i])
                wj = int(cnts[min_j])
                merged_rgb = ((centers[min_i].astype(np.float32) * wi + centers[min_j].astype(np.float32) * wj) / float(wi + wj)).astype(np.uint8)
                centers = np.delete(centers, min_j, axis=0)
                cnts = np.delete(cnts, min_j, axis=0)
                centers[min_i] = merged_rgb
                cnts[min_i] = wi + wj
                changed = True
        return centers, cnts

    def analyze_colors(self, *, image_bgr: Optional[np.ndarray], image_bytes: Optional[bytes], method: Literal["opencv", "rembg"], max_k: int = 6, min_ratio: float = 0.05, delta_e_thresh: float = 32.0, max_output_colors: int = 18, target_max_colors: int = 6) -> Tuple[int, np.ndarray, np.ndarray]:
        # 生成主体掩码和 RGB 像素
        if method == "rembg":
            if image_bytes is None:
                raise ValueError("analyze_colors(rembg) 需要 image_bytes")
            result_bytes = remove(image_bytes)
            rgba = Image.open(BytesIO(result_bytes)).convert("RGBA")
            rgba_np = np.array(rgba)
            alpha = rgba_np[..., 3]
            mask = (alpha > 0).astype(np.uint8)
            # 精细化主体掩码，弱化边缘噪声
            k3 = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k3, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k3, iterations=2)
            mask = cv2.erode(mask, k3, iterations=1)
            # 以白底进行 alpha 合成，避免透明区合成到黑色造成黑色占比偏大
            rgb_fg = rgba_np[..., :3].astype(np.float32)
            a = (alpha.astype(np.float32) / 255.0)[..., None]
            white_bg = np.full_like(rgb_fg, 255.0, dtype=np.float32)
            rgb = (rgb_fg * a + white_bg * (1.0 - a)).astype(np.uint8)
            # 轻度平滑以减少微小色噪（仅用于后续聚类输入，不改变掩码）
            rgb = cv2.GaussianBlur(rgb, (3, 3), 0)
        elif method == "opencv":
            if image_bgr is None:
                raise ValueError("analyze_colors(opencv) 需要 image_bgr")
            bgr = image_bgr
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thr1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            _, thr2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            # choose better by larger foreground area
            c1 = np.count_nonzero(thr1)
            c2 = np.count_nonzero(thr2)
            mask = thr1 if c1 >= c2 else thr2
            mask = (mask > 0).astype(np.uint8)
            # 精细化主体掩码
            k3 = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k3, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k3, iterations=2)
            mask = cv2.erode(mask, k3, iterations=1)
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            rgb = cv2.GaussianBlur(rgb, (3, 3), 0)
        else:
            raise ValueError("不支持的算法方法")

        # 提取主体像素
        ys, xs = np.where(mask > 0)
        if ys.size == 0:
            raise ValueError("未检测到主体像素")
        pixels = rgb[ys, xs, :]

        # ========== Lab 空间 + 肘部法选择最佳 K，再做全量聚类 ==========
        rgb_f = pixels.astype(np.float32) / 255.0
        lab = skcolor.rgb2lab(rgb_f.reshape(-1, 1, 3)).reshape(-1, 3)

        # 抽样用于肘部法评估
        sample = lab
        if sample.shape[0] > 20000:
            idx = np.random.choice(sample.shape[0], 20000, replace=False)
            sample = sample[idx]

        def kmeans_cv2(data: np.ndarray, k: int) -> Tuple[float, np.ndarray, np.ndarray]:
            Z = data.astype(np.float32)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            compactness, labels, centers = cv2.kmeans(Z, k, None, criteria, 5, cv2.KMEANS_PP_CENTERS)
            return float(compactness), labels.reshape(-1), centers

        k_min, k_max = 2, 10
        sse_list = []
        for k in range(k_min, k_max + 1):
            sse, _, _ = kmeans_cv2(sample, k)
            sse_list.append(sse)
        ks = np.arange(k_min, k_max + 1, dtype=np.float32)
        sse_arr = np.array(sse_list, dtype=np.float32)
        # 远点法：端点直线到各点距离最大
        p1 = np.array([ks[0], sse_arr[0]], dtype=np.float32)
        p2 = np.array([ks[-1], sse_arr[-1]], dtype=np.float32)
        vec = p2 - p1
        den = np.linalg.norm(vec) + 1e-6
        dists = np.abs(np.cross(vec, np.stack([ks, sse_arr], axis=1) - p1)) / den
        best_k = int(ks[int(np.argmax(dists))])

        # 全量聚类（在 Lab 上）
        _, labels_full, centers_lab = kmeans_cv2(lab, best_k)
        counts = np.bincount(labels_full, minlength=centers_lab.shape[0]).astype(np.int64)
        # 转回 RGB 作为代表色
        rep_rgb = (skcolor.lab2rgb(centers_lab.reshape(-1, 1, 3)).reshape(-1, 3) * 255.0).clip(0, 255).astype(np.uint8)
        centers_rgb = rep_rgb

        # 基于 ΔE 合并近似颜色
        merged_centers, merged_counts = self._merge_by_delta_e(centers_rgb, counts, delta_e_thresh=delta_e_thresh)

        # ========== 中性色折叠（将灰度系统一并减少“灰/黑”重复计数） ==========
        if merged_centers.shape[0] > 0:
            centers_f01 = merged_centers.astype(np.float32) / 255.0
            centers_lab = skcolor.rgb2lab(centers_f01.reshape(-1, 1, 3)).reshape(-1, 3)
            a_vals = centers_lab[:, 1]
            b_vals = centers_lab[:, 2]
            chroma = np.sqrt(a_vals * a_vals + b_vals * b_vals)
            neutral_mask = chroma < 8.0  # 放宽中性判断，更多灰黑白并入
            if np.any(neutral_mask):
                L_vals = centers_lab[:, 0]
                # L 分为黑与白两档
                black_mask = neutral_mask & (L_vals < 50.0)
                white_mask = neutral_mask & (L_vals >= 50.0)
                keep_mask = ~neutral_mask

                kept_centers = merged_centers[keep_mask]
                kept_counts = merged_counts[keep_mask]

                add_centers = []
                add_counts = []
                if np.any(black_mask):
                    w = merged_counts[black_mask].astype(np.float64)
                    c = merged_centers[black_mask].astype(np.float64)
                    avg = (c * w[:, None]).sum(axis=0) / w.sum()
                    add_centers.append(avg.astype(np.uint8))
                    add_counts.append(w.sum().astype(np.int64))
                if np.any(white_mask):
                    w = merged_counts[white_mask].astype(np.float64)
                    c = merged_centers[white_mask].astype(np.float64)
                    avg = (c * w[:, None]).sum(axis=0) / w.sum()
                    add_centers.append(avg.astype(np.uint8))
                    add_counts.append(w.sum().astype(np.int64))

                if len(add_centers) > 0:
                    merged_centers = np.vstack([kept_centers] + [np.asarray(x)[None, :] for x in add_centers]) if kept_centers.size else np.vstack([np.asarray(x)[None, :] for x in add_centers])
                    merged_counts = np.concatenate([kept_counts] + [np.asarray(x, dtype=np.int64).reshape(1) for x in add_counts]) if kept_counts.size else np.concatenate([np.asarray(x, dtype=np.int64).reshape(1) for x in add_counts])

                # 再做一次 ΔE 合并，避免中性合并后与彩色靠得很近
                merged_centers, merged_counts = self._merge_by_delta_e(merged_centers, merged_counts, delta_e_thresh=delta_e_thresh)

        # 自适应合并：在 ΔE 基础上逐步增大阈值，直至颜色数不超过目标上限
        cur_thresh = float(delta_e_thresh)
        prev_n = merged_centers.shape[0]
        while merged_centers.shape[0] > target_max_colors and cur_thresh <= 50.0:
            c_before = merged_centers.shape[0]
            merged_centers, merged_counts = self._merge_by_delta_e(merged_centers, merged_counts, delta_e_thresh=cur_thresh)
            c_after = merged_centers.shape[0]
            if c_after >= c_before:
                cur_thresh += 4.0
            else:
                prev_n = c_after

        # 硬性上限：若仍超过目标上限，按最相近 ΔE 贪心合并直到满足
        if merged_centers.shape[0] > target_max_colors:
            # 计算 ΔE 距离矩阵
            c01 = merged_centers.astype(np.float32) / 255.0
            lab = skcolor.rgb2lab(c01.reshape(-1, 1, 3)).reshape(-1, 3)
            while lab.shape[0] > target_max_colors:
                # 找最近的一对
                n = lab.shape[0]
                dmin = 1e9
                pair = (0, 1)
                for i in range(n):
                    for j in range(i + 1, n):
                        d = delta_e_ciede2000(lab[i], lab[j])
                        if d < dmin:
                            dmin = d
                            pair = (i, j)
                i, j = pair
                # 按权重合并
                w_i = float(merged_counts[i])
                w_j = float(merged_counts[j])
                wi = w_i / (w_i + w_j)
                wj = 1.0 - wi
                new_lab = wi * lab[i] + wj * lab[j]
                new_count = merged_counts[i] + merged_counts[j]
                # 更新集合
                mask = np.ones(n, dtype=bool)
                mask[[i, j]] = False
                lab = np.vstack([lab[mask], new_lab[None, :]])
                merged_counts = np.concatenate([merged_counts[mask], np.array([new_count], dtype=np.int64)])
                # 颜色中心同步转换
                rgb_mask = np.ones(n, dtype=bool)
                rgb_mask[[i, j]] = False
                kept = merged_centers[rgb_mask]
                new_rgb = (skcolor.lab2rgb(new_lab.reshape(1, 1, 3)).reshape(1, 3) * 255.0).clip(0, 255).astype(np.uint8)
                merged_centers = np.vstack([kept, new_rgb])

        # 过滤小簇
        total = int(merged_counts.sum())
        keep = merged_counts / max(1, total) >= min_ratio
        merged_centers = merged_centers[keep]
        merged_counts = merged_counts[keep]

        # 按占比降序
        order = np.argsort(-merged_counts)
        merged_centers = merged_centers[order]
        merged_counts = merged_counts[order]

        # 限制输出颜色数，并将尾部颜色合并到最接近的主色
        if merged_centers.shape[0] > max_output_colors:
            keep_centers = merged_centers[:max_output_colors]
            keep_counts = merged_counts[:max_output_colors].astype(np.int64)
            tail_centers = merged_centers[max_output_colors:]
            tail_counts = merged_counts[max_output_colors:].astype(np.int64)
            # 将尾部按 Lab 距离分配到最近主色
            keep_lab = self._rgb_to_lab(keep_centers)
            tail_lab = self._rgb_to_lab(tail_centers)
            for idx in range(tail_centers.shape[0]):
                dists = skcolor.deltaE_ciede2000(keep_lab, tail_lab[idx][None, :])
                nearest = int(np.argmin(np.asarray(dists).reshape(-1)))
                keep_counts[nearest] += int(tail_counts[idx])
            merged_centers = keep_centers
            merged_counts = keep_counts

        return int(merged_centers.shape[0]), merged_centers, merged_counts


def _cli():
    parser = argparse.ArgumentParser(description="占用面积识别（rembg / OpenCV）")
    parser.add_argument("--image", required=True, help="输入图片路径")
    parser.add_argument("--method", choices=["rembg", "opencv"], default="rembg", help="识别算法")
    parser.add_argument("--out", default="preview.png", help="结果预览输出路径")
    args = parser.parse_args()

    path = Path(args.image)
    if not path.exists():
        raise SystemExit("图片不存在")

    data = path.read_bytes()
    arr = np.frombuffer(data, dtype=np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise SystemExit("无法读取图片内容")

    analyzer = Analyzer()
    ratio, preview = analyzer.analyze(
        image_bgr=img_bgr if args.method == "opencv" else None,
        image_bytes=data if args.method == "rembg" else None,
        method=args.method,
    )
    cv2.imwrite(args.out, Analyzer._ensure_uint8(preview))
    print(f"area_ratio={ratio:.4f}")
    print(f"preview_path={args.out}")


if __name__ == "__main__":
    _cli()


