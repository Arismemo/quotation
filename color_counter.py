import cv2
import matplotlib.pyplot as plt
import numpy as np
from rembg import remove
from sklearn.cluster import KMeans


class ColorAnalyzer:
    """
    一个用于分析图片中产品主颜色的面向对象的工具。

    这个类封装了从背景移除到颜色聚类、过滤和可视化的整个流程。
    """

    def __init__(self, k_range=(2, 10), min_percentage=1.0, sample_size=20000):
        """
        初始化颜色分析器。

        :param k_range: 用于肘部法则的K值范围。
        :param min_percentage: 一种颜色被视为“主要颜色”所需的最小像素百分比。
        :param sample_size: 用于加速肘部法则计算的像素采样数量。
        """
        # --- 配置参数 ---
        self.k_range = k_range
        self.min_percentage = min_percentage
        self.sample_size = sample_size

        # --- 分析结果 (初始化为空) ---
        self.image_path = None
        self.dominant_colors = None
        self.percentages = None
        self.analyzed_k = None

    def _remove_background(self, image):
        """私有方法：移除图片背景。"""
        print("正在进行背景移除...")
        return remove(image, alpha=True)

    def _extract_pixels_in_lab(self, foreground_rgba):
        """私有方法：提取前景像素并转换为LAB颜色空间。"""
        mask = foreground_rgba[:, :, 3] > 128
        if not np.any(mask):
            return None

        foreground_bgr = foreground_rgba[:, :, :3][mask]
        foreground_lab = cv2.cvtColor(
            foreground_bgr.reshape(1, -1, 3), cv2.COLOR_BGR2Lab
        ).reshape(-1, 3)
        return foreground_lab

    def _find_best_k(self, pixels):
        """私有方法：使用肘部法则找到最佳的K值。"""
        print("正在使用肘部法则寻找最佳K值...")

        # 如果像素总数少于采样数，则直接使用所有像素
        if len(pixels) > self.sample_size:
            pixels_sample = pixels[
                np.random.choice(len(pixels), self.sample_size, replace=False)
            ]
        else:
            pixels_sample = pixels

        sse = []
        k_values = range(self.k_range[0], self.k_range[1] + 1)
        for k in k_values:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
            kmeans.fit(pixels_sample)
            sse.append(kmeans.inertia_)

        points = np.array([list(k_values), sse]).T
        p1, p2 = points[0], points[-1]
        distances = np.abs(np.cross(p2 - p1, p1 - points)) / np.linalg.norm(p2 - p1)
        best_k = k_values[np.argmax(distances)]
        print(f"肘部法则推荐的最佳K值为: {best_k}")
        self.analyzed_k = best_k
        return best_k

    def _filter_and_convert_colors(self, kmeans):
        """私有方法：根据像素占比过滤颜色，并将结果从LAB转换回RGB。"""
        print(f"正在过滤掉占比小于 {self.min_percentage}% 的颜色...")
        total_pixels = len(kmeans.labels_)
        counts = np.bincount(kmeans.labels_)

        filtered_colors_lab = []
        filtered_percentages = []

        for i, count in enumerate(counts):
            percentage = (count / total_pixels) * 100
            if percentage >= self.min_percentage:
                filtered_colors_lab.append(kmeans.cluster_centers_[i])
                filtered_percentages.append(percentage)

        if not filtered_colors_lab:
            return [], []

        lab_array = np.uint8(np.array(filtered_colors_lab).reshape(1, -1, 3))
        rgb_array = cv2.cvtColor(lab_array, cv2.COLOR_LAB2RGB).reshape(-1, 3)
        filtered_colors_rgb = [tuple(color) for color in rgb_array]

        return filtered_colors_rgb, filtered_percentages

    def analyze(self, image_path):
        """
        公开方法：执行完整的颜色分析流程。

        :param image_path: 要分析的图片路径。
        :return: (颜色数量, 颜色列表, 百分比列表)
        """
        self.image_path = image_path
        input_image = cv2.imread(image_path)
        if input_image is None:
            print("图片无法读取!")
            return None, None, None

        # 步骤 1: 移除背景
        foreground_rgba = self._remove_background(input_image)

        # 步骤 2: 提取像素
        all_pixels_lab = self._extract_pixels_in_lab(foreground_rgba)
        if all_pixels_lab is None:
            print("未检测到前景对象！")
            return 0, [], []

        # 步骤 3: 寻找最佳K
        best_k = self._find_best_k(all_pixels_lab)

        # 步骤 4: 执行最终聚类
        print(f"使用 K={best_k} 进行最终颜色聚类...")
        kmeans = KMeans(n_clusters=best_k, random_state=42, n_init="auto")
        kmeans.fit(all_pixels_lab)

        # 步骤 5: 过滤并存储结果
        self.dominant_colors, self.percentages = self._filter_and_convert_colors(kmeans)

        print("\n--- 分析完成 ---")
        return len(self.dominant_colors), self.dominant_colors, self.percentages


# ========== 兼容方法：复用现有流程，支持不同的图像传入方式 ==========
def _cluster_lab_pixels(
    pixels_lab: np.ndarray, k_range=(2, 10), min_percentage: float = 5.0
):
    if pixels_lab is None or len(pixels_lab) == 0:
        return 0, [], []
    # 肘部法
    if len(pixels_lab) > 20000:
        pixels_sample = pixels_lab[
            np.random.choice(len(pixels_lab), 20000, replace=False)
        ]
    else:
        pixels_sample = pixels_lab
    sse = []
    k_values = range(k_range[0], k_range[1] + 1)
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
        kmeans.fit(pixels_sample)
        sse.append(kmeans.inertia_)
    points = np.array([list(k_values), sse]).T
    p1, p2 = points[0], points[-1]
    distances = np.abs(np.cross(p2 - p1, p1 - points)) / np.linalg.norm(p2 - p1)
    best_k = k_values[np.argmax(distances)]
    # 全量聚类
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init="auto")
    kmeans.fit(pixels_lab)
    # 过滤并转回RGB
    total_pixels = len(kmeans.labels_)
    counts = np.bincount(kmeans.labels_)
    filtered_colors_lab = []
    filtered_percentages = []
    for i, count in enumerate(counts):
        percentage = (count / total_pixels) * 100
        if percentage >= min_percentage:
            filtered_colors_lab.append(kmeans.cluster_centers_[i])
            filtered_percentages.append(percentage)
    if not filtered_colors_lab:
        return 0, [], []
    lab_array = np.uint8(np.array(filtered_colors_lab).reshape(1, -1, 3))
    rgb_array = cv2.cvtColor(lab_array, cv2.COLOR_LAB2RGB).reshape(-1, 3)
    filtered_colors_rgb = [tuple(color) for color in rgb_array]
    return len(filtered_colors_rgb), filtered_colors_rgb, filtered_percentages


def count_product_colors_from_bgr(
    image_bgr: np.ndarray, k_range=(2, 10), min_percentage: float = 5.0
):
    """直接接收BGR图像，内部调用rembg抠图再聚类。"""
    if image_bgr is None:
        return None, None, None
    foreground_rgba = remove(image_bgr, alpha=True)
    mask = foreground_rgba[:, :, 3] > 128
    if not np.any(mask):
        return 0, [], []
    foreground_bgr = foreground_rgba[:, :, :3][mask]
    pixels_lab = cv2.cvtColor(
        foreground_bgr.reshape(1, -1, 3), cv2.COLOR_BGR2Lab
    ).reshape(-1, 3)
    return _cluster_lab_pixels(
        pixels_lab, k_range=k_range, min_percentage=min_percentage
    )


def count_product_colors_from_mask_rgb(
    mask: np.ndarray, rgb: np.ndarray, k_range=(2, 10), min_percentage: float = 5.0
):
    """接收我们已有流程产出的 mask 与 RGB（前景合成白底后），跳过rembg。"""
    if mask is None or rgb is None:
        return None, None, None
    m = mask > 0
    if not np.any(m):
        return 0, [], []
    # 注意 rgb 可能为 RGB，需要转 BGR->Lab 或直接 RGB->Lab
    # 这里先转到 BGR 再到 Lab，与主流程保持一致性
    # 将选中的像素转为 BGR 排列
    sel_rgb = rgb[m]
    sel_bgr = sel_rgb[:, ::-1]
    pixels_lab = cv2.cvtColor(sel_bgr.reshape(1, -1, 3), cv2.COLOR_BGR2Lab).reshape(
        -1, 3
    )
    return _cluster_lab_pixels(
        pixels_lab, k_range=k_range, min_percentage=min_percentage
    )

    def get_results_string(self):
        """以格式化的字符串形式返回分析结果。"""
        if self.dominant_colors is None:
            return "分析尚未运行，请先调用 analyze() 方法。"

        header = f"图片 '{self.image_path}' 上的产品共有 {len(self.dominant_colors)} 种主要颜色。\n"
        details = "颜色详情 (RGB值 | 占比):\n"

        sorted_results = sorted(
            zip(self.dominant_colors, self.percentages),
            key=lambda x: x[1],
            reverse=True,
        )

        lines = []
        for color, percentage in sorted_results:
            lines.append(f"- RGB: {color} | 占比: {percentage:.2f}%")

        return header + details + "\n".join(lines)

    def plot_results(self):
        """可视化分析出的主颜色及其占比。"""
        if not self.dominant_colors:
            print("没有可供显示的颜色。请先成功运行 analyze() 方法。")
            return

        total_width = 400
        bar_height = 80
        bar = np.zeros((bar_height, total_width, 3), dtype="uint8")

        start_x = 0
        sorted_data = sorted(
            zip(self.dominant_colors, self.percentages),
            key=lambda x: x[1],
            reverse=True,
        )

        for color_rgb, percentage in sorted_data:
            bar_width = int(total_width * (percentage / 100))
            end_x = start_x + bar_width
            color_bgr = (int(color_rgb[2]), int(color_rgb[1]), int(color_rgb[0]))
            cv2.rectangle(bar, (start_x, 0), (end_x, bar_height), color_bgr, -1)
            start_x = end_x

        bar_rgb = cv2.cvtColor(bar, cv2.COLOR_BGR2RGB)

        plt.figure()
        plt.axis("off")
        plt.imshow(bar_rgb)
        plt.title("识别出的主颜色 (按占比显示)")
        plt.show()


if __name__ == "__main__":
    # --- 使用方法 ---

    # 1. 创建一个 ColorAnalyzer 实例
    # 你可以在这里传入自定义的配置参数
    analyzer = ColorAnalyzer(min_percentage=2.0)

    # 2. 对指定的图片执行分析
    # analyze 方法会返回结果，同时也将结果保存在 analyzer 对象内部
    num_colors, colors, percentages = analyzer.analyze("test3.jpg")

    # 3. 打印分析结果
    if num_colors is not None:
        # 你可以使用对象内的方法来获取格式化好的字符串
        print(analyzer.get_results_string())

        # 4. 显示可视化图表
        analyzer.plot_results()
