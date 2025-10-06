from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class QuoteRequest(BaseModel):
    """报价请求"""

    length: float = Field(..., gt=0, le=1000, description="产品长度 (cm)")
    width: float = Field(..., gt=0, le=1000, description="产品宽度 (cm)")
    thickness: float = Field(..., gt=0, le=100, description="产品厚度 (cm)")
    color_count: int = Field(..., ge=0, le=50, description="颜色数量")
    area_ratio: float = Field(..., gt=0, le=1, description="占用面积比例")
    order_quantity: int = Field(..., gt=0, le=1000000, description="订单数量")
    worker_type: str = Field(default="standard", description="工人类型")
    debug: bool = Field(default=False, description="调试模式")


class QuoteResponse(BaseModel):
    """报价响应"""

    model_config = ConfigDict(extra="allow")  # 允许额外字段

    # 基础计算结果
    total_price: float = Field(..., description="总价格")
    unit_price: float = Field(..., description="单价")
    material_cost: float = Field(..., description="材料成本")
    labor_cost: float = Field(..., description="人工成本")
    overhead_cost: float = Field(..., description="间接成本")

    # 可选字段
    history_id: Optional[int] = Field(None, description="历史记录ID")
    settings_snapshot: Optional[dict[str, Any]] = Field(None, description="设置快照")

    # 其他动态字段
    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
