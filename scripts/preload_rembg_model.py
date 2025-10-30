#!/usr/bin/env python3
"""
预下载 rembg 模型文件
解决首次使用时网络超时问题

使用方法：
    python scripts/preload_rembg_model.py
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def preload_rembg_model():
    """预下载 rembg 模型"""
    try:
        logger.info("开始预下载 rembg 模型...")
        from rembg import new_session
        
        # 设置环境变量增加超时时间
        import os
        os.environ.setdefault('REQUESTS_TIMEOUT', '300')
        
        # 创建 session 会触发模型下载
        logger.info("正在下载 u2net 模型（可能需要几分钟）...")
        session = new_session("u2net")
        logger.info("✓ rembg 模型下载成功！")
        logger.info(f"模型位置: {Path.home() / '.u2net'}")
        return True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"✗ rembg 模型下载失败: {error_msg}")
        
        if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            logger.error("")
            logger.error("网络连接失败。建议：")
            logger.error("1. 检查网络连接或使用代理")
            logger.error("2. 手动下载模型文件到 ~/.u2net/u2net.onnx")
            logger.error("3. 或使用 opencv 方法（不需要下载模型）")
        
        return False

if __name__ == "__main__":
    success = preload_rembg_model()
    sys.exit(0 if success else 1)

