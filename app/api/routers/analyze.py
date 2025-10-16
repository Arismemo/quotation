from typing import Union

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.db.models import User  # 保留类型引用兼容
from app.services.image_analysis_service import analyze_area_ratio, analyze_colors
from app.utils.exceptions import handle_common_exceptions

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
    ratio, preview_path = analyze_area_ratio(
        static_path=payload.image_path, method=method
    )
    return {
        "area_ratio": round(float(ratio), 4),
        "method": "rembg",
        "preview_path": preview_path,
    }


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
    result = analyze_colors(static_path=payload.image_path, method=method)
    return result

    return result
