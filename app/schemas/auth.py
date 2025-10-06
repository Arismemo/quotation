from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    is_admin: bool = Field(..., description="是否为管理员")
    created_at: datetime = Field(..., description="创建时间")


class LoginResponse(BaseModel):
    """登录响应"""

    success: bool = Field(True, description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: dict[str, UserResponse] = Field(..., description="用户数据")
