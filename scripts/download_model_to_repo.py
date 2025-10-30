#!/usr/bin/env python3
"""
下载 rembg 模型文件到本地 models 目录
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_model_to_repo():
    """下载模型到仓库的 models 目录"""
    try:
        # 获取项目根目录
        repo_root = Path(__file__).resolve().parents[1]
        models_dir = repo_root / "models"
        models_dir.mkdir(exist_ok=True)
        
        logger.info(f"模型将保存到: {models_dir}")
        
        # 导入 rembg
        from rembg import new_session
        import os
        
        # 设置 U2NET_HOME 环境变量指向本地目录
        os.environ['U2NET_HOME'] = str(models_dir)
        logger.info(f"设置 U2NET_HOME={models_dir}")
        
        # 下载模型（会保存到指定目录）
        logger.info("正在下载 u2net 模型（可能需要几分钟）...")
        session = new_session("u2net")
        
        # 验证文件是否下载成功
        model_file = models_dir / "u2net.onnx"
        if model_file.exists():
            file_size = model_file.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✓ 模型下载成功！")
            logger.info(f"  文件位置: {model_file}")
            logger.info(f"  文件大小: {file_size:.2f} MB")
            return True
        else:
            logger.error("✗ 模型文件未找到")
            return False
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"✗ 模型下载失败: {error_msg}")
        
        if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            logger.error("")
            logger.error("网络连接失败。建议：")
            logger.error("1. 检查网络连接")
            logger.error("2. 使用代理：export HTTP_PROXY=...")
            logger.error("3. 手动下载：")
            logger.error(f"   curl -L https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx -o {models_dir}/u2net.onnx")
        
        return False

if __name__ == "__main__":
    success = download_model_to_repo()
    sys.exit(0 if success else 1)

