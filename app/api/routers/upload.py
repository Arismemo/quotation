import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image
import io

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["文件上传"])

# 使用配置中的常量
ALLOWED_EXTENSIONS = settings.ALLOWED_IMAGE_EXTENSIONS
ALLOWED_CONTENT_TYPES = settings.ALLOWED_IMAGE_CONTENT_TYPES
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE

# 上传目录（使用绝对路径，基于项目根目录）
# 从当前文件位置向上三级到项目根目录
# upload.py 在 app/api/routers/，所以需要 parents[3]
_BASE_DIR = Path(__file__).resolve().parents[3]
UPLOAD_DIR = _BASE_DIR / "app" / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/image")
async def upload_image(file: UploadFile = File(...)) -> dict[str, str]:
    """上传图片"""

    # 检查文件扩展名
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。仅支持: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 检查Content-Type（如果提供）
    if file.content_type and file.content_type.lower() not in ALLOWED_CONTENT_TYPES:
        # 允许content-type为空（某些客户端可能不发送），但如果不为空则需要验证
        logger.warning(
            f"Content-Type不匹配: {file.content_type}, 文件名: {file.filename}"
        )
        # 不直接拒绝，因为某些客户端可能发送错误的Content-Type，但文件本身是正确的

    # 读取文件内容
    content = await file.read()

    # 检查文件是否为空
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="文件不能为空",
        )

    # 检查文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制({MAX_FILE_SIZE // 1024 // 1024}MB)",
        )

    # 验证图片内容是否有效
    try:
        with Image.open(io.BytesIO(content)) as img:
            # 验证图片可以正常打开和读取（不使用 verify()，因为它会破坏图片对象）
            # 通过尝试读取格式和尺寸来验证图片有效性
            img.format  # 读取格式
            img.size  # 读取尺寸
            # 尝试加载图片（对于某些格式，需要显式加载）
            img.load()
    except Exception as e:
        logger.error(f"图片验证失败: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"文件不是有效的图片格式: {str(e)}",
        )

    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    # 保存文件
    try:
        with open(file_path, "wb") as f:
            f.write(content)

        # 返回相对路径（用于数据库存储和前端访问）
        relative_path = f"/static/uploads/{unique_filename}"
        logger.info(f"上传图片成功: {relative_path} (大小: {len(content)} bytes)")

        return {
            "path": relative_path,
            "filename": unique_filename,
            "size": str(len(content)),
        }

    except PermissionError as e:
        logger.error(f"保存图片失败（权限不足）: {e}, 路径: {file_path}")
        raise HTTPException(
            status_code=500, 
            detail="保存图片失败：权限不足，请检查目录权限"
        ) from e
    except OSError as e:
        logger.error(f"保存图片失败（IO错误）: {e}, 路径: {file_path}")
        raise HTTPException(
            status_code=500, 
            detail=f"保存图片失败：{str(e)}"
        ) from e
    except Exception as e:
        logger.error(f"保存图片失败（未知错误）: {e}, 路径: {file_path}", exc_info=True)
        raise HTTPException(status_code=500, detail="保存图片失败，请重试") from e
