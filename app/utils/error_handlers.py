"""Enhanced error handling utilities."""

import logging
from typing import Any, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class BusinessLogicError(Exception):
    """Custom exception for business logic errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class DatabaseError(Exception):
    """Custom exception for database-related errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(message)


def create_error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_code: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> JSONResponse:
    """Create a standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Optional error code for client handling
        details: Optional additional error details

    Returns:
        JSONResponse with error information
    """
    error_data = {
        "error": True,
        "message": message,
        "status_code": status_code,
    }

    if error_code:
        error_data["error_code"] = error_code

    if details:
        error_data["details"] = details

    return JSONResponse(status_code=status_code, content=error_data)


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error on {request.url}: {exc}")

    error_details = []
    for error in exc.errors():
        error_details.append(
            {
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return create_error_response(
        message="请求数据验证失败",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        details={"validation_errors": error_details},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception on {request.url}: {exc.detail}")

    return create_error_response(
        message=exc.detail, status_code=exc.status_code, error_code="HTTP_ERROR"
    )


async def business_logic_exception_handler(
    request: Request, exc: BusinessLogicError
) -> JSONResponse:
    """Handle business logic errors."""
    logger.warning(f"Business logic error on {request.url}: {exc.message}")

    return create_error_response(
        message=exc.message,
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code=exc.error_code or "BUSINESS_LOGIC_ERROR",
    )


async def database_exception_handler(
    request: Request, exc: DatabaseError
) -> JSONResponse:
    """Handle database errors."""
    logger.error(f"Database error on {request.url}: {exc.message}")
    if exc.original_error:
        logger.error(f"Original error: {exc.original_error}")

    return create_error_response(
        message="数据库操作失败，请稍后重试",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="DATABASE_ERROR",
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy errors."""
    logger.error(f"SQLAlchemy error on {request.url}: {exc}")

    return create_error_response(
        message="数据库操作失败",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="DATABASE_ERROR",
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.error(f"Unexpected error on {request.url}: {exc}", exc_info=True)

    return create_error_response(
        message="服务器内部错误，请稍后重试",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
    )


def safe_execute(func, *args, error_message: str = "操作失败", **kwargs):
    """Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Function arguments
        error_message: Error message if function fails
        **kwargs: Function keyword arguments

    Returns:
        Function result or raises appropriate exception

    Raises:
        BusinessLogicError: If function execution fails
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {e}")
        raise BusinessLogicError(f"{error_message}: {str(e)}") from e


def validate_required_fields(data: dict[str, Any], required_fields: list[str]) -> None:
    """Validate that all required fields are present and not None.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Raises:
        BusinessLogicError: If any required fields are missing
    """
    missing_fields = [
        field for field in required_fields if field not in data or data[field] is None
    ]

    if missing_fields:
        raise BusinessLogicError(
            f"缺少必需字段: {', '.join(missing_fields)}",
            error_code="MISSING_REQUIRED_FIELDS",
        )


def validate_numeric_range(
    value: float, min_val: float, max_val: float, field_name: str
) -> None:
    """Validate that a numeric value is within the specified range.

    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Name of the field for error messages

    Raises:
        BusinessLogicError: If value is outside the valid range
    """
    if not (min_val <= value <= max_val):
        raise BusinessLogicError(
            f"{field_name} 必须在 {min_val} 到 {max_val} 之间，当前值: {value}",
            error_code="VALUE_OUT_OF_RANGE",
        )
