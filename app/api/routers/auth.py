from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import LoginRequest, UserResponse
from app.services.auth_service import authenticate_user
from app.deps import get_current_user_optional
from app.db.models import User
from typing import Optional

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login")
async def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 写入会话
    request.session["user_id"] = user.id
    
    return {
        "message": "登录成功",
        "user": UserResponse.model_validate(user)
    }


@router.post("/logout")
async def logout(request: Request):
    """用户登出"""
    request.session.clear()
    return {"message": "已退出登录"}


@router.get("/me", response_model=Optional[UserResponse])
async def get_current_user_info(user: Optional[User] = Depends(get_current_user_optional)):
    """获取当前登录用户信息"""
    if not user:
        return None
    return UserResponse.model_validate(user)


