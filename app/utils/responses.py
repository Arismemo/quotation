"""Response utilities for consistent API responses."""

from typing import Any, Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse


def success_response(
    data: Any = None, message: str = "操作成功", status_code: int = 200
) -> JSONResponse:
    """创建成功响应"""
    response_data: dict[str, Any] = {"success": True, "message": message}
    if data is not None:
        response_data["data"] = data

    return JSONResponse(content=response_data, status_code=status_code)


def error_response(
    message: str = "操作失败",
    status_code: int = 400,
    details: Optional[dict[str, Any]] = None,
) -> HTTPException:
    """创建错误响应"""
    return HTTPException(
        status_code=status_code,
        detail={"success": False, "message": message, "details": details},
    )


def paginated_response(
    items: list[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "查询成功",
) -> JSONResponse:
    """创建分页响应"""
    response_data = {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            },
        },
    }

    return JSONResponse(content=response_data, status_code=200)
