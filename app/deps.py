from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import crud
from app.db.models import User
from app.db.session import get_db


def get_current_user_optional(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前登录用户（可选，未登录返回 None）"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    user = crud.get_user_by_id(db, user_id)
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """获取当前登录用户（必须登录）"""
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="未登录或会话已过期")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
