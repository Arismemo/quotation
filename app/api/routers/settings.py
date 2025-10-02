from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import crud
from app.deps import require_admin
from app.db.models import User
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest, AppSettingsSchema, WorkerProfileSchema

router = APIRouter(prefix="/settings", tags=["系统设置"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """获取系统设置（仅管理员）"""
    
    app_settings = crud.get_app_settings(db)
    worker_profiles = crud.get_worker_profiles(db)
    
    return SettingsResponse(
        settings=AppSettingsSchema.model_validate(app_settings),
        worker_profiles=[WorkerProfileSchema.model_validate(wp) for wp in worker_profiles]
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(
    settings_update: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """更新系统设置（仅管理员）"""
    
    # 更新应用设置
    if settings_update.settings:
        update_data = settings_update.settings.model_dump(exclude_unset=True)
        crud.update_app_settings(db, **update_data)
    
    # 更新工人配置
    if settings_update.worker_profiles:
        for profile_data in settings_update.worker_profiles:
            crud.upsert_worker_profile(
                db,
                name=profile_data.name,
                monthly_salary=profile_data.monthly_salary,
                machines_operated=profile_data.machines_operated
            )
    
    # 返回更新后的设置
    app_settings = crud.get_app_settings(db)
    worker_profiles = crud.get_worker_profiles(db)
    
    return SettingsResponse(
        settings=AppSettingsSchema.model_validate(app_settings),
        worker_profiles=[WorkerProfileSchema.model_validate(wp) for wp in worker_profiles]
    )


