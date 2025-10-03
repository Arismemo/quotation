from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Literal

from app.deps import get_current_user
from app.db.models import User
from app.services.image_analysis_service import analyze_area_ratio, analyze_colors


router = APIRouter(prefix="/analyze", tags=["图像分析"])


class AnalyzeRequest(BaseModel):
    image_path: str = Field(..., description="已上传图片的静态路径，如 /static/uploads/xxx.png")


@router.post("/area-ratio")
async def analyze_area_ratio_api(payload: AnalyzeRequest, current_user: User = Depends(get_current_user)):
    try:
        ratio, preview_path = analyze_area_ratio(static_path=payload.image_path, method="rembg")
        return {
            "area_ratio": round(float(ratio), 4),
            "method": "rembg",
            "preview_path": preview_path,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="图像分析失败")


@router.post("/colors")
async def analyze_colors_api(payload: AnalyzeRequest, current_user: User = Depends(get_current_user)):
    try:
        result = analyze_colors(static_path=payload.image_path)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 将异常信息透传一部分，便于前端定位
        raise HTTPException(status_code=500, detail=f"颜色统计失败: {type(e).__name__}")


