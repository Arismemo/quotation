import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.image_analysis_service import analyze_area_ratio, analyze_colors
from app.utils.exceptions import handle_common_exceptions

logger = logging.getLogger(__name__)

# 创建线程池用于执行 CPU 密集型任务
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="image_analysis")

router = APIRouter(tags=["图像分析"])


class AnalyzeRequest(BaseModel):
    image_path: str = Field(
        ..., description="已上传图片的静态路径，如 /static/uploads/xxx.png"
    )
    method: str | None = Field(
        default=None, description="可选：rembg 或 opencv，默认 opencv"
    )


@router.post("/area-ratio")
@handle_common_exceptions(
    file_not_found_msg="图片文件未找到",
    value_error_msg="图片分析参数错误",
    general_error_msg="图像分析失败",
)
async def analyze_area_ratio_api(
    payload: AnalyzeRequest,
) -> dict[str, Union[str, float]]:
    method = (payload.method or "opencv").lower()
    if method not in {"opencv", "rembg"}:
        method = "opencv"
    
    # 根据方法设置不同的超时时间
    # rembg 首次加载模型可能需要较长时间
    timeout = 300 if method == "rembg" else 120  # rembg: 5分钟, opencv: 2分钟
    
    logger.info(f"开始面积比例分析: path={payload.image_path}, method={method}, timeout={timeout}s")
    
    try:
        # 在线程池中执行同步的 CPU 密集型任务，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        ratio, preview_path = await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                analyze_area_ratio,
                payload.image_path,
                method,
            ),
            timeout=timeout,
        )
        logger.info(f"面积比例分析完成: ratio={ratio:.4f}")
    return {
        "area_ratio": round(float(ratio), 4),
        "method": method,
        "preview_path": preview_path,
    }
    except asyncio.TimeoutError:
        logger.error(f"面积比例分析超时: path={payload.image_path}, method={method}, timeout={timeout}s")
        raise HTTPException(
            status_code=504,
            detail=f"分析超时（{timeout}秒）。如果使用 rembg 方法，首次运行可能需要下载模型。请稍后重试，或尝试使用 opencv 方法。",
        )
    except Exception as e:
        logger.exception(f"面积比例分析失败: {e}")
        
        # 检查是否是 rembg 模型下载失败
        error_str = str(e).lower()
        if "rembg" in error_str or "github.com" in error_str or "download" in error_str or "timeout" in error_str:
            raise HTTPException(
                status_code=503,
                detail="rembg 模型下载失败（网络问题）。请检查服务器网络连接，或使用 opencv 方法（更快且不需要网络）。",
            ) from e
        
        raise


@router.post("/colors")
@handle_common_exceptions(
    file_not_found_msg="图片文件未找到",
    value_error_msg="颜色分析参数错误",
    general_error_msg="颜色统计失败",
)
async def analyze_colors_api(
    payload: AnalyzeRequest,
) -> dict[str, object]:
    method = (payload.method or "opencv").lower()
    if method not in {"opencv", "rembg"}:
        method = "opencv"
    
    # 颜色分析也需要较长时间，特别是使用 rembg
    timeout = 300 if method == "rembg" else 120
    
    logger.info(f"开始颜色分析: path={payload.image_path}, method={method}, timeout={timeout}s")
    
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                analyze_colors,
                payload.image_path,
                method,
            ),
            timeout=timeout,
        )
        logger.info(f"颜色分析完成: colors={result.get('color_count', 0)}")
    return result
    except asyncio.TimeoutError:
        logger.error(f"颜色分析超时: path={payload.image_path}, method={method}, timeout={timeout}s")
        raise HTTPException(
            status_code=504,
            detail=f"颜色分析超时（{timeout}秒）。请稍后重试。",
        )
    except Exception as e:
        logger.exception(f"颜色分析失败: {e}")
        raise

