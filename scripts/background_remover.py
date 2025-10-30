from io import BytesIO
from typing import Literal, Optional
import logging
from pathlib import Path
import os

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# 延迟导入 rembg，避免在不需要时加载
_rembg_remove = None
_rembg_session = None

def _get_repo_model_path():
    """获取仓库中的模型路径"""
    # 从当前文件位置向上两级到项目根目录
    repo_root = Path(__file__).resolve().parents[1]
    models_dir = repo_root / "models"
    model_file = models_dir / "u2net.onnx"
    return model_file if model_file.exists() else None

def _get_rembg_remove():
    """延迟加载 rembg，优先使用本地模型文件"""
    global _rembg_remove, _rembg_session
    
    if _rembg_remove is None:
        try:
            from rembg import remove as _remove
            from rembg import new_session
            import os
            
            # 优先使用仓库中的模型文件
            repo_model_path = _get_repo_model_path()
            if repo_model_path:
                logger.info(f"使用仓库中的模型文件: {repo_model_path}")
                # 设置 U2NET_HOME 环境变量指向 models 目录
                models_dir = repo_model_path.parent
                os.environ['U2NET_HOME'] = str(models_dir)
            else:
                logger.info("仓库中未找到模型文件，将使用默认路径（可能需要下载）")
            
            # 设置环境变量增加超时时间（如果支持）
            os.environ.setdefault('REQUESTS_TIMEOUT', '300')
            
            # 尝试预加载模型（如果失败会抛出异常）
            logger.info("正在加载 rembg 模型...")
            try:
                # 预创建 session 以便提前下载模型（如果本地没有）
                _rembg_session = new_session("u2net")
                logger.info("rembg 模型加载成功")
            except Exception as e:
                logger.warning(f"rembg 模型预加载失败: {e}，将在使用时重试")
            
            _rembg_remove = _remove
        except ImportError:
            raise ImportError("rembg 模块未安装，请安装: pip install rembg")
    return _rembg_remove


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

    def rembg_mask_and_rgb(self, image_bytes: bytes) -> tuple[np.ndarray, np.ndarray]:
        """使用 rembg 进行背景移除"""
        try:
            remove_func = _get_rembg_remove()
            logger.info("调用 rembg.remove() 处理图片...")
            result_bytes = remove_func(image_bytes)
            logger.info("rembg 处理完成")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"rembg 处理失败: {error_msg}")
            
            # 检查是否是网络相关错误
            if "timeout" in error_msg.lower() or "connection" in error_msg.lower() or "github.com" in error_msg.lower():
                raise RuntimeError(
                    "rembg 模型下载失败（网络超时）。"
                    "解决方案：1) 确保服务器可以访问 GitHub；"
                    "2) 或在构建时预下载模型；"
                    "3) 或使用 opencv 方法替代。"
                ) from e
            raise
        
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

    def opencv_mask_and_rgb(
        self, image_bgr: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
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

    def get_mask_and_rgb(
        self,
        *,
        method: Literal["rembg", "opencv"],
        image_bgr: Optional[np.ndarray],
        image_bytes: Optional[bytes],
    ) -> tuple[np.ndarray, np.ndarray]:
        if method == "rembg":
            if image_bytes is None:
                raise ValueError("rembg 需要 image_bytes")
            return self.rembg_mask_and_rgb(image_bytes)
        if method == "opencv":
            if image_bgr is None:
                raise ValueError("opencv 需要 image_bgr")
            return self.opencv_mask_and_rgb(image_bgr)
        raise ValueError("不支持的抠图方法")
