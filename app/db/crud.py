import logging
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    AppSettings,
    QuotationFavorite,
    QuotationHistory,
    User,
    WorkerProfile,
)

logger = logging.getLogger(__name__)


# ==================== User CRUD ====================
def create_user(
    db: Session, username: str, password_hash: str, is_admin: bool = False
) -> User:
    """创建新用户"""
    user = User(username=username, password_hash=password_hash, is_admin=is_admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


# ==================== AppSettings CRUD ====================
def get_app_settings(db: Session) -> Optional[AppSettings]:
    return db.query(AppSettings).filter(AppSettings.id == 1).first()


def create_default_settings(db: Session) -> AppSettings:
    settings = AppSettings(id=1)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def update_app_settings(db: Session, **kwargs: object) -> AppSettings:
    settings = get_app_settings(db)
    if not settings:
        settings = create_default_settings(db)

    for key, value in kwargs.items():
        if hasattr(settings, key) and value is not None:
            setattr(settings, key, value)

    db.commit()
    db.refresh(settings)
    return settings


# ==================== WorkerProfile CRUD ====================
def get_worker_profiles(db: Session) -> list[WorkerProfile]:
    return db.query(WorkerProfile).all()


def get_worker_profile_by_name(db: Session, name: str) -> Optional[WorkerProfile]:
    return db.query(WorkerProfile).filter(WorkerProfile.name == name).first()


def upsert_worker_profile(
    db: Session, name: str, monthly_salary: float, machines_operated: int
) -> WorkerProfile:
    profile = get_worker_profile_by_name(db, name)
    if profile:
        profile.monthly_salary = monthly_salary
        profile.machines_operated = machines_operated
    else:
        profile = WorkerProfile(
            name=name,
            monthly_salary=monthly_salary,
            machines_operated=machines_operated,
        )
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile


# ==================== QuotationHistory CRUD ====================
def create_history(
    db: Session,
    user_id: int,
    request_payload: dict,
    result_payload: dict,
    worker_type: str,
    unit_price: float,
    total_price: float,
) -> QuotationHistory:
    history = QuotationHistory(
        user_id=user_id,
        request_payload=request_payload,
        result_payload=result_payload,
        worker_type=worker_type,
        unit_price=unit_price,
        total_price=total_price,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_user_histories(
    db: Session, user_id: int, offset: int = 0, limit: int = 20
) -> list[QuotationHistory]:
    return (
        db.query(QuotationHistory)
        .filter(QuotationHistory.user_id == user_id)
        .order_by(QuotationHistory.computed_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_history_by_id(
    db: Session, history_id: int, user_id: int
) -> Optional[QuotationHistory]:
    return (
        db.query(QuotationHistory)
        .filter(QuotationHistory.id == history_id, QuotationHistory.user_id == user_id)
        .first()
    )


def delete_history(db: Session, history_id: int, user_id: int) -> bool:
    history = get_history_by_id(db, history_id, user_id)
    if history:
        db.delete(history)
        db.commit()
        return True
    return False


# ==================== QuotationFavorite CRUD ====================
def create_favorite(
    db: Session, user_id: int, history_id: int, name: Optional[str] = None
) -> QuotationFavorite:
    favorite = QuotationFavorite(user_id=user_id, history_id=history_id, name=name)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def get_user_favorites(db: Session, user_id: int) -> list[QuotationFavorite]:
    return (
        db.query(QuotationFavorite)
        .options(joinedload(QuotationFavorite.history))
        .filter(QuotationFavorite.user_id == user_id)
        .order_by(QuotationFavorite.created_at.desc())
        .all()
    )


def get_favorite_by_id(
    db: Session, favorite_id: int, user_id: int
) -> Optional[QuotationFavorite]:
    return (
        db.query(QuotationFavorite)
        .filter(
            QuotationFavorite.id == favorite_id, QuotationFavorite.user_id == user_id
        )
        .first()
    )


def delete_favorite(db: Session, favorite_id: int, user_id: int) -> bool:
    favorite = get_favorite_by_id(db, favorite_id, user_id)
    if favorite:
        db.delete(favorite)
        db.commit()
        return True
    return False


def check_favorite_exists(db: Session, user_id: int, history_id: int) -> bool:
    return (
        db.query(QuotationFavorite)
        .filter(
            QuotationFavorite.user_id == user_id,
            QuotationFavorite.history_id == history_id,
        )
        .first()
        is not None
    )
