"""Exception handling utilities."""

import logging
from typing import Any, Callable, TypeVar

from fastapi import HTTPException

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def handle_common_exceptions(
    file_not_found_msg: str = "文件未找到",
    value_error_msg: str = "参数错误",
    general_error_msg: str = "内部服务器错误",
) -> Callable[[F], F]:
    """装饰器：处理常见的异常类型并转换为HTTP异常"""

    def decorator(func: F) -> F:
        import functools

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except FileNotFoundError as e:
                raise HTTPException(
                    status_code=404, detail=f"{file_not_found_msg}: {str(e)}"
                ) from e
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"{value_error_msg}: {str(e)}"
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise HTTPException(status_code=500, detail=general_error_msg) from e

        return wrapper  # type: ignore

    return decorator


def handle_db_exceptions(
    not_found_msg: str = "记录未找到",
    conflict_msg: str = "数据冲突",
    general_error_msg: str = "数据库操作失败",
) -> Callable[[F], F]:
    """装饰器：处理数据库相关异常"""

    def decorator(func: F) -> F:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                if "not found" in error_msg or "does not exist" in error_msg:
                    raise HTTPException(status_code=404, detail=not_found_msg) from e
                elif "conflict" in error_msg or "duplicate" in error_msg:
                    raise HTTPException(status_code=409, detail=conflict_msg) from e
                else:
                    logger.error(f"Database error in {func.__name__}: {e}")
                    raise HTTPException(
                        status_code=500, detail=general_error_msg
                    ) from e

        return wrapper  # type: ignore

    return decorator
