from typing import Optional, Union

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.deps import get_current_user_optional
from app.schemas.auth import LoginRequest, UserResponse
from app.services.auth_service import authenticate_user, create_user
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["认证"])


@router.post("/register")
async def register(
    request: Request, user_data: LoginRequest, db: Session = Depends(get_db)
) -> dict[str, Union[str, dict[str, object]]]:
    """用户注册"""
    try:
        user = create_user(db, user_data.username, user_data.password)
        return success_response(data={"user_id": user.id}, message="注册成功")
    except ValueError as e:
        raise error_response(str(e), status_code=400) from e


@router.post("/login")
async def login(
    request: Request, login_data: LoginRequest, db: Session = Depends(get_db)
) -> dict[str, Union[str, dict[str, object]]]:
    """用户登录"""
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise error_response("用户名或密码错误", status_code=401)

    # 写入会话
    request.session["user_id"] = user.id

    return success_response(
        data={"user": UserResponse.model_validate(user).model_dump(mode='json')}, message="登录成功"
    )


@router.post("/logout")
async def logout(request: Request):
    """用户登出"""
    request.session.clear()
    return {"message": "已退出登录"}


@router.get("/me", response_model=Optional[UserResponse])
async def get_current_user_info(
    user: Optional[User] = Depends(get_current_user_optional),
):
    """获取当前登录用户信息"""
    if not user:
        return None
    return UserResponse.model_validate(user).model_dump(mode='json')
