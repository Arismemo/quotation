from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import crud
from app.deps import get_current_user
from app.db.models import User
from app.schemas.history import HistoryItemResponse
from typing import List

router = APIRouter(prefix="/history", tags=["报价历史"])


@router.get("", response_model=List[HistoryItemResponse])
async def get_histories(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的报价历史列表"""
    histories = crud.get_user_histories(db, current_user.id, offset, limit)
    
    # 检查每条历史是否已收藏
    result = []
    for history in histories:
        is_favorited = crud.check_favorite_exists(db, current_user.id, history.id)
        history_dict = HistoryItemResponse.model_validate(history).model_dump()
        history_dict["is_favorited"] = is_favorited
        result.append(history_dict)
    
    return result


@router.get("/{history_id}", response_model=HistoryItemResponse)
async def get_history_detail(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单条历史记录详情"""
    history = crud.get_history_by_id(db, history_id, current_user.id)
    if not history:
        raise HTTPException(status_code=404, detail="历史记录不存在或无权访问")
    
    is_favorited = crud.check_favorite_exists(db, current_user.id, history.id)
    history_dict = HistoryItemResponse.model_validate(history).model_dump()
    history_dict["is_favorited"] = is_favorited
    
    return history_dict


@router.delete("/{history_id}")
async def delete_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除历史记录"""
    success = crud.delete_history(db, history_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="历史记录不存在或无权删除")
    
    return {"message": "历史记录已删除"}


