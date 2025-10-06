from typing import Optional

import bcrypt
from sqlalchemy.orm import Session

from app.db import crud
from app.db.models import User


def hash_password(plain_password: str) -> str:
    """哈希密码"""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_user(db: Session, username: str, password: str) -> User:
    """创建新用户"""
    # 检查用户名是否已存在
    existing_user = crud.get_user_by_username(db, username)
    if existing_user:
        raise ValueError("用户名已存在")

    # 创建新用户
    hashed_password = hash_password(password)
    user = crud.create_user(db, username, hashed_password)
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户登录"""
    user = crud.get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
