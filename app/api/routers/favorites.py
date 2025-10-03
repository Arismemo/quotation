from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
from app.db import crud
from app.deps import get_current_user
from app.db.models import User
from app.schemas.history import FavoriteCreateRequest, FavoriteItemResponse
from typing import List

router = APIRouter(prefix="/favorites", tags=["报价收藏"])


@router.get("", response_model=List[FavoriteItemResponse])
async def get_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的收藏列表"""
    favorites = crud.get_user_favorites(db, current_user.id)
    return [FavoriteItemResponse.model_validate(fav) for fav in favorites]


@router.post("", response_model=FavoriteItemResponse)
async def create_favorite(
    favorite_req: FavoriteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建收藏"""
    
    # 检查历史记录是否存在且属于当前用户
    history = crud.get_history_by_id(db, favorite_req.history_id, current_user.id)
    if not history:
        raise HTTPException(status_code=404, detail="历史记录不存在或无权访问")
    
    # 创建收藏
    try:
        favorite = crud.create_favorite(
            db, 
            user_id=current_user.id, 
            history_id=favorite_req.history_id,
            name=favorite_req.name
        )
        return FavoriteItemResponse.model_validate(favorite)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="该历史记录已收藏")


@router.delete("/{favorite_id}")
async def delete_favorite(
    favorite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消收藏"""
    success = crud.delete_favorite(db, favorite_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="收藏不存在或无权删除")
    
    return {"message": "收藏已取消"}


@router.put("/{favorite_id}", response_model=FavoriteItemResponse)
async def update_favorite(
    favorite_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新收藏备注和图片（使用 name 字段作为备注存储，image_path 存储图片路径）"""
    favorite = crud.get_favorite_by_id(db, favorite_id, current_user.id)
    if not favorite:
        raise HTTPException(status_code=404, detail="收藏不存在或无权访问")
    
    # 更新备注
    if "name" in payload:
        favorite.name = str(payload["name"])[:200] if payload["name"] else None
    
    # 更新图片路径
    if "image_path" in payload:
        favorite.image_path = str(payload["image_path"])[:500] if payload["image_path"] else None
    
    db.commit()
    db.refresh(favorite)
    return FavoriteItemResponse.model_validate(favorite)


