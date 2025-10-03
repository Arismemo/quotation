from typing import Tuple

import cv2
import numpy as np
from skimage import color as skcolor


class ColorAnalyzer:
    def __init__(self, *, target_max_colors: int = 4, min_ratio: float = 0.05):
        self.target_max_colors = target_max_colors
        self.min_ratio = min_ratio

    @staticmethod
    def _rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
        return skcolor.rgb2lab(rgb.astype(np.float32) / 255.0)

    @staticmethod
    def _merge_by_delta_e(centers_rgb: np.ndarray, counts: np.ndarray, delta_e_thresh: float) -> Tuple[np.ndarray, np.ndarray]:
        centers = centers_rgb.astype(np.uint8)
        cnts = counts.astype(np.int64)
        changed = True
        while changed and centers.shape[0] > 1:
            changed = False
            lab = ColorAnalyzer._rgb_to_lab(centers)
            N = centers.shape[0]
            min_d, min_i, min_j = 1e9, -1, -1
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
                    min_d, min_i, min_j = d, i, i + 1 + j_rel
            if min_i >= 0 and min_d <= delta_e_thresh:
                wi, wj = int(cnts[min_i]), int(cnts[min_j])
                merged_rgb = ((centers[min_i].astype(np.float32) * wi + centers[min_j].astype(np.float32) * wj) / float(wi + wj)).astype(np.uint8)
                centers = np.delete(centers, min_j, axis=0)
                cnts = np.delete(cnts, min_j, axis=0)
                centers[min_i] = merged_rgb
                cnts[min_i] = wi + wj
                changed = True
        return centers, cnts

    def analyze(self, *, mask: np.ndarray, rgb: np.ndarray) -> Tuple[int, np.ndarray, np.ndarray]:
        ys, xs = np.where(mask > 0)
        if ys.size == 0:
            raise ValueError("未检测到主体像素")
        pixels = rgb[ys, xs, :]

        # RGB->Lab
        rgb_f = pixels.astype(np.float32) / 255.0
        lab = skcolor.rgb2lab(rgb_f.reshape(-1, 1, 3)).reshape(-1, 3)

        # 肘部法
        sample = lab
        if sample.shape[0] > 20000:
            idx = np.random.choice(sample.shape[0], 20000, replace=False)
            sample = sample[idx]

        def kmeans_cv2(data: np.ndarray, k: int):
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
        p1 = np.array([ks[0], sse_arr[0]], dtype=np.float32)
        p2 = np.array([ks[-1], sse_arr[-1]], dtype=np.float32)
        den = np.linalg.norm(p2 - p1) + 1e-6
        dists = np.abs(np.cross(p2 - p1, np.stack([ks, sse_arr], axis=1) - p1)) / den
        best_k = int(ks[int(np.argmax(dists))])

        # 全量聚类
        _, labels_full, centers_lab = kmeans_cv2(lab, best_k)
        counts = np.bincount(labels_full, minlength=centers_lab.shape[0]).astype(np.int64)
        centers_rgb = (skcolor.lab2rgb(centers_lab.reshape(-1, 1, 3)).reshape(-1, 3) * 255.0).clip(0, 255).astype(np.uint8)

        # 中性色折叠
        if centers_rgb.shape[0] > 0:
            centers_f01 = centers_rgb.astype(np.float32) / 255.0
            centers_lab = skcolor.rgb2lab(centers_f01.reshape(-1, 1, 3)).reshape(-1, 3)
            a_vals, b_vals = centers_lab[:, 1], centers_lab[:, 2]
            chroma = np.sqrt(a_vals * a_vals + b_vals * b_vals)
            neutral_mask = chroma < 8.0
            if np.any(neutral_mask):
                L_vals = centers_lab[:, 0]
                black_mask = neutral_mask & (L_vals < 50.0)
                white_mask = neutral_mask & (L_vals >= 85.0)
                keep_mask = ~neutral_mask
                kept_centers, kept_counts = centers_rgb[keep_mask], counts[keep_mask]
                add_centers, add_counts = [], []
                if np.any(black_mask):
                    w = counts[black_mask].astype(np.float64)
                    c = centers_rgb[black_mask].astype(np.float64)
                    add_centers.append(((c * w[:, None]).sum(axis=0) / w.sum()).astype(np.uint8))
                    add_counts.append(w.sum().astype(np.int64))
                if np.any(white_mask):
                    w = counts[white_mask].astype(np.float64)
                    c = centers_rgb[white_mask].astype(np.float64)
                    add_centers.append(((c * w[:, None]).sum(axis=0) / w.sum()).astype(np.uint8))
                    add_counts.append(w.sum().astype(np.int64))
                if len(add_centers) > 0:
                    centers_rgb = np.vstack([kept_centers] + [np.asarray(x)[None, :] for x in add_centers]) if kept_centers.size else np.vstack([np.asarray(x)[None, :] for x in add_centers])
                    counts = np.concatenate([kept_counts] + [np.asarray(x, dtype=np.int64).reshape(1) for x in add_counts]) if kept_counts.size else np.concatenate([np.asarray(x, dtype=np.int64).reshape(1) for x in add_counts])

        # ΔE 合并 + 自适应
        centers_rgb, counts = self._merge_by_delta_e(centers_rgb, counts, delta_e_thresh=24.0)
        cur = 24.0
        while centers_rgb.shape[0] > self.target_max_colors and cur <= 40.0:
            before = centers_rgb.shape[0]
            centers_rgb, counts = self._merge_by_delta_e(centers_rgb, counts, delta_e_thresh=cur)
            after = centers_rgb.shape[0]
            if after >= before:
                cur += 4.0

        if centers_rgb.shape[0] > self.target_max_colors:
            c01 = centers_rgb.astype(np.float32) / 255.0
            lab_c = skcolor.rgb2lab(c01.reshape(-1, 1, 3)).reshape(-1, 3)
            while lab_c.shape[0] > self.target_max_colors:
                n = lab_c.shape[0]
                dmin, pair = 1e9, (0, 1)
                for i in range(n):
                    for j in range(i + 1, n):
                        d = skcolor.deltaE_ciede2000(lab_c[i][None, :], lab_c[j][None, :])
                        d = float(np.asarray(d).reshape(-1)[0])
                        if d < dmin:
                            dmin, pair = d, (i, j)
                i, j = pair
                wi, wj = float(counts[i]), float(counts[j])
                new_lab = (wi * lab_c[i] + wj * lab_c[j]) / (wi + wj)
                new_count = counts[i] + counts[j]
                mask = np.ones(n, dtype=bool)
                mask[[i, j]] = False
                lab_c = np.vstack([lab_c[mask], new_lab[None, :]])
                counts = np.concatenate([counts[mask], np.array([new_count], dtype=np.int64)])
                rgb_keep = centers_rgb[mask]
                new_rgb = (skcolor.lab2rgb(new_lab.reshape(1, 1, 3)).reshape(1, 3) * 255.0).clip(0, 255).astype(np.uint8)
                centers_rgb = np.vstack([rgb_keep, new_rgb])

        # 最小占比过滤
        total = int(counts.sum())
        keep = counts / max(1, total) >= self.min_ratio
        centers_rgb = centers_rgb[keep]
        counts = counts[keep]

        # 排序
        order = np.argsort(-counts)
        centers_rgb = centers_rgb[order]
        counts = counts[order]

        return int(centers_rgb.shape[0]), centers_rgb, counts


