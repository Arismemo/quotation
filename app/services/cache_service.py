"""Cache service for performance optimization."""

import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from sqlalchemy.orm import Session

from app.db import crud

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# 简单的内存缓存
_cache: dict[str, Any] = {}
_cache_ttl: dict[str, float] = {}


def cache_result(ttl_seconds: int = 300) -> Callable[[F], F]:
    """缓存装饰器，用于缓存函数结果"""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 生成缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # 检查缓存是否有效
            if cache_key in _cache:
                if cache_key in _cache_ttl:
                    import time

                    if time.time() - _cache_ttl[cache_key] < ttl_seconds:
                        logger.debug(f"Cache hit for {cache_key}")
                        return _cache[cache_key]

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            _cache[cache_key] = result
            import time

            _cache_ttl[cache_key] = time.time()

            logger.debug(f"Cache miss for {cache_key}")
            return result

        return wrapper  # type: ignore

    return decorator


def clear_cache() -> None:
    """清除所有缓存"""
    global _cache, _cache_ttl
    _cache.clear()
    _cache_ttl.clear()
    logger.info("Cache cleared")


def get_cached_settings(db: Session) -> Optional[dict]:
    """获取缓存的应用设置"""
    cache_key = "app_settings"

    if cache_key in _cache:
        import time

        if (
            cache_key in _cache_ttl and time.time() - _cache_ttl[cache_key] < 300
        ):  # 5分钟TTL
            return _cache[cache_key]

    settings = crud.get_app_settings(db)
    if settings:
        # 转换为字典以避免会话问题
        settings_dict = {
            "profit_margin": settings.profit_margin,
            "waste_rate": settings.waste_rate,
            "material_density": settings.material_density,
            "material_price_per_gram": settings.material_price_per_gram,
            "mold_edge_length": settings.mold_edge_length,
            "mold_spacing": settings.mold_spacing,
            "base_molds_per_shift": settings.base_molds_per_shift,
            "working_days_per_month": settings.working_days_per_month,
            "shifts_per_day": settings.shifts_per_day,
            "needles_per_machine": settings.needles_per_machine,
            "setup_fee_per_color": settings.setup_fee_per_color,
            "base_setup_fee": settings.base_setup_fee,
            "coloring_fee_per_color_per_shift": settings.coloring_fee_per_color_per_shift,
            "other_salary_per_cell_shift": settings.other_salary_per_cell_shift,
            "rent_per_cell_shift": settings.rent_per_cell_shift,
            "electricity_fee_per_cell_shift": settings.electricity_fee_per_cell_shift,
            "color_output_map": settings.color_output_map,
        }
        _cache[cache_key] = settings_dict
        import time

        _cache_ttl[cache_key] = time.time()
        return settings_dict

    return None


def get_cached_worker_profiles(db: Session) -> list[dict]:
    """获取缓存的工人配置"""
    cache_key = "worker_profiles"

    if cache_key in _cache:
        import time

        if (
            cache_key in _cache_ttl and time.time() - _cache_ttl[cache_key] < 300
        ):  # 5分钟TTL
            return _cache[cache_key]

    profiles = crud.get_worker_profiles(db)
    # 转换为字典列表以避免会话问题
    profiles_list = [
        {
            "name": profile.name,
            "monthly_salary": profile.monthly_salary,
            "machines_operated": profile.machines_operated,
        }
        for profile in profiles
    ]
    _cache[cache_key] = profiles_list
    import time

    _cache_ttl[cache_key] = time.time()

    return profiles_list


def invalidate_settings_cache() -> None:
    """使设置缓存失效"""
    cache_keys = ["app_settings", "worker_profiles"]
    for key in cache_keys:
        _cache.pop(key, None)
        _cache_ttl.pop(key, None)
    logger.info("Settings cache invalidated")
