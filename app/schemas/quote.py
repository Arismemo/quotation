from pydantic import BaseModel, Field
from typing import Optional


class QuoteRequest(BaseModel):
    length: float = Field(..., gt=0, description="产品长度 (cm)")
    width: float = Field(..., gt=0, description="产品宽度 (cm)")
    thickness: float = Field(..., gt=0, description="产品厚度 (cm)")
    color_count: int = Field(..., ge=0, description="颜色数量")
    area_ratio: float = Field(..., gt=0, le=1, description="占用面积比例")
    difficulty_factor: float = Field(..., gt=0, description="难度系数")
    order_quantity: int = Field(..., gt=0, description="订单数量")
    worker_type: str = Field(default="standard", description="工人类型")
    debug: bool = Field(default=False, description="调试模式")


class QuoteResponse(BaseModel):
    """报价响应（直接返回计算器的结果字典）"""
    pass  # 动态字典，不做严格校验


