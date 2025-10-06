from typing import Union

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.db.models import User
from app.deps import get_current_user
from app.services.image_analysis_service import analyze_area_ratio, analyze_colors
from app.utils.exceptions import handle_common_exceptions

router = APIRouter(tags=["图像分析"])


class AnalyzeRequest(BaseModel):
    image_path: str = Field(
        ..., description="已上传图片的静态路径，如 /static/uploads/xxx.png"
    )


@router.post("/area-ratio")
@handle_common_exceptions(
    file_not_found_msg="图片文件未找到",
    value_error_msg="图片分析参数错误",
    general_error_msg="图像分析失败",
)
async def analyze_area_ratio_api(
    payload: AnalyzeRequest, current_user: User = Depends(get_current_user)
) -> dict[str, Union[str, float]]:
    ratio, preview_path = analyze_area_ratio(
        static_path=payload.image_path, method="rembg"
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
    payload: AnalyzeRequest, current_user: User = Depends(get_current_user)
) -> dict[str, object]:
    result = analyze_colors(static_path=payload.image_path)
    return result

    return result
