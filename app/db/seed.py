from sqlalchemy.orm import Session
from app.db import crud
from app.config import settings
import bcrypt
import logging

logger = logging.getLogger(__name__)


def seed_database(db: Session):
    """注入默认数据"""
    
    # 1. 创建默认 AppSettings（如果不存在）
    app_settings = crud.get_app_settings(db)
    if not app_settings:
        logger.info("创建默认应用设置...")
        crud.create_default_settings(db)
    else:
        logger.info("应用设置已存在，跳过")
    
    # 2. 创建默认工人配置（如果不存在）
    worker_profiles_data = [
        {"name": "skilled", "monthly_salary": 8400, "machines_operated": 3},
        {"name": "standard", "monthly_salary": 7000, "machines_operated": 2}
    ]
    
    for profile_data in worker_profiles_data:
        existing = crud.get_worker_profile_by_name(db, profile_data["name"])
        if not existing:
            logger.info(f"创建工人配置: {profile_data['name']}")
            crud.upsert_worker_profile(db, **profile_data)
        else:
            logger.info(f"工人配置 {profile_data['name']} 已存在，跳过")
    
    # 3. 创建默认管理员用户（如果不存在）
    admin_user = crud.get_user_by_username(db, settings.ADMIN_USERNAME)
    if not admin_user:
        logger.info(f"创建默认管理员用户: {settings.ADMIN_USERNAME}")
        # 使用 bcrypt 直接哈希密码
        password_hash = bcrypt.hashpw(settings.ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        crud.create_user(db, username=settings.ADMIN_USERNAME, password_hash=password_hash, is_admin=True)
    else:
        logger.info(f"管理员用户 {settings.ADMIN_USERNAME} 已存在，跳过")


