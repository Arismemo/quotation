import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.db.models import User  # 保留导入以兼容可能的类型引用

logger = logging.getLogger(__name__)

router = APIRouter(tags=["文件上传"])

# 允许的图片格式
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB，与前端一致

# 上传目录
UPLOAD_DIR = Path("app/static/uploads")
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

    # 读取文件内容
    content = await file.read()

    # 检查文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制({MAX_FILE_SIZE // 1024 // 1024}MB)",
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
        # 尽力记录，但上传允许匿名
        try:
            logger.info(f"上传图片: {relative_path}")
        except Exception:
            pass

        return {
            "path": relative_path,
            "filename": unique_filename,
            "size": str(len(content)),
        }

    except Exception as e:
        logger.error(f"保存图片失败: {e}")
        raise HTTPException(status_code=500, detail="保存图片失败") from e
