"""Security utilities for input validation and sanitization."""

import re
from typing import Any

from fastapi import HTTPException


def validate_password_strength(password: str) -> None:
    """验证密码强度"""
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="密码长度至少8位")

    if len(password) > 128:
        raise HTTPException(status_code=400, detail="密码长度不能超过128位")

    # 检查是否包含至少一个字母和一个数字
    if not re.search(r"[A-Za-z]", password):
        raise HTTPException(status_code=400, detail="密码必须包含至少一个字母")

    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="密码必须包含至少一个数字")


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除危险字符"""
    # 移除路径分隔符和其他危险字符
    dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(dangerous_chars, "_", filename)

    # 限制长度
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit(".", 1) if "." in sanitized else (sanitized, "")
        sanitized = name[: 255 - len(ext) - 1] + ("." + ext if ext else "")

    return sanitized


def validate_file_size(file_size: int, max_size_mb: int = 10) -> None:
    """验证文件大小"""
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400, detail=f"文件大小超过限制。最大允许: {max_size_mb}MB"
        )


def validate_image_dimensions(
    width: int, height: int, max_dimension: int = 10000
) -> None:
    """验证图片尺寸"""
    if width <= 0 or height <= 0:
        raise HTTPException(status_code=400, detail="图片尺寸必须大于0")

    if width > max_dimension or height > max_dimension:
        raise HTTPException(
            status_code=400,
            detail=f"图片尺寸超过限制。最大允许: {max_dimension}x{max_dimension}",
        )


def sanitize_user_input(text: str, max_length: int = 1000) -> str:
    """清理用户输入文本"""
    if not text:
        return ""

    # 移除控制字符
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 限制长度
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()


def validate_numeric_input(
    value: float, min_val: float, max_val: float, field_name: str
) -> None:
    """验证数值输入"""
    if not isinstance(value, (int, float)):
        raise HTTPException(status_code=400, detail=f"{field_name} 必须是数字")

    if value < min_val or value > max_val:
        raise HTTPException(
            status_code=400, detail=f"{field_name} 必须在 {min_val} 到 {max_val} 之间"
        )


def check_rate_limit(
    user_id: int, action: str, max_requests: int = 100, window_minutes: int = 60
) -> None:
    """简单的速率限制检查（内存实现）"""
    # 这里应该使用Redis或数据库实现，这里只是示例
    # 实际生产环境应该使用专业的速率限制库
    pass


def validate_session_security(session_data: dict[str, Any]) -> bool:
    """验证会话安全性"""
    # 检查会话是否包含必要的安全信息
    required_fields = ["user_id"]
    for field in required_fields:
        if field not in session_data:
            return False

    # 检查用户ID是否为有效整数
    try:
        user_id = int(session_data["user_id"])
        if user_id <= 0:
            return False
    except (ValueError, TypeError):
        return False

    return True
