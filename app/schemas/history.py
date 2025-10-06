from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HistoryItemResponse(BaseModel):
    id: int
    worker_type: str
    unit_price: float
    total_price: float
    computed_at: datetime
    request_payload: dict
    result_payload: dict
    is_favorited: Optional[bool] = False  # 前端用于显示是否已收藏

    class Config:
        from_attributes = True


class FavoriteCreateRequest(BaseModel):
    history_id: int = Field(..., gt=0)
    name: Optional[str] = Field(None, max_length=200)


class FavoriteItemResponse(BaseModel):
    id: int
    history_id: int
    name: Optional[str]
    image_path: Optional[str] = None  # 图片路径
    created_at: datetime
    # 关联的历史记录信息
    history: HistoryItemResponse

    class Config:
        from_attributes = True
