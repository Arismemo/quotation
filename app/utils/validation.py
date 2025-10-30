"""Validation utilities."""

import os
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile


def validate_file_upload(
    file: UploadFile, allowed_extensions: list[str], max_size_mb: int = 10
) -> None:
    """验证文件上传"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 检查文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。仅支持: {', '.join(allowed_extensions)}",
        )

    # 检查文件大小
    if hasattr(file, "size") and file.size:
        max_size_bytes = max_size_mb * 1024 * 1024
        if file.size > max_size_bytes:
            raise HTTPException(
                status_code=400, detail=f"文件大小超过限制。最大允许: {max_size_mb}MB"
            )


def validate_image_path(image_path: str) -> Path:
    """验证图片路径并返回Path对象"""
    if not image_path.startswith("/static/"):
        raise ValueError("非法路径")

    rel_path = image_path[len("/static/") :]
    abs_path = Path("app/static") / rel_path

    if not abs_path.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    return abs_path


def validate_pagination_params(
    offset: int = 0, limit: int = 20, max_limit: int = 100
) -> tuple[int, int]:
    """验证分页参数"""
    if offset < 0:
        raise ValueError("offset 不能为负数")

    if limit < 1:
        raise ValueError("limit 必须大于 0")

    if limit > max_limit:
        raise ValueError(f"limit 不能超过 {max_limit}")

    return offset, limit


def validate_required_fields(data: dict[str, Any], required_fields: list[str]) -> None:
    """验证必需字段"""
    missing_fields = [
        field for field in required_fields if field not in data or data[field] is None
    ]
    if missing_fields:
        raise ValueError(f"缺少必需字段: {', '.join(missing_fields)}")


def validate_numeric_range(
    value: float, min_val: float, max_val: float, field_name: str
) -> None:
    """验证数值范围"""
    if value < min_val or value > max_val:
        raise ValueError(f"{field_name} 必须在 {min_val} 到 {max_val} 之间")
