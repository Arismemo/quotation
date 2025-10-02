from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.models import Base
import logging

logger = logging.getLogger(__name__)

# 创建引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库：建表 + 种子数据"""
    logger.info("正在初始化数据库...")
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")
    
    # 导入并执行种子
    from app.db.seed import seed_database
    db = SessionLocal()
    try:
        seed_database(db)
        logger.info("种子数据注入完成")
    finally:
        db.close()


def get_db():
    """依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


