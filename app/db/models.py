from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    histories = relationship("QuotationHistory", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("QuotationFavorite", back_populates="user", cascade="all, delete-orphan")


class AppSettings(Base):
    __tablename__ = "app_settings"
    
    id = Column(Integer, primary_key=True)  # 固定只有一行 id=1
    
    # 利润与损耗
    profit_margin = Column(Float, nullable=False, default=0.30)
    waste_rate = Column(Float, nullable=False, default=0.10)
    
    # 材料参数
    material_density = Column(Float, nullable=False, default=1.166)
    material_price_per_gram = Column(Float, nullable=False, default=0.01)
    
    # 产能参数
    mold_edge_length = Column(Float, nullable=False, default=26.0)
    mold_spacing = Column(Float, nullable=False, default=1.0)
    base_molds_per_shift = Column(Float, nullable=False, default=120.0)
    working_days_per_month = Column(Integer, nullable=False, default=26)
    shifts_per_day = Column(Integer, nullable=False, default=2)
    
    # 机台参数
    needles_per_machine = Column(Integer, nullable=False, default=18)
    
    # 调机与调色费用
    setup_fee_per_color = Column(Float, nullable=False, default=20.0)
    base_setup_fee = Column(Float, nullable=False, default=15.0)
    coloring_fee_per_color_per_shift = Column(Float, nullable=False, default=5.0)
    
    # 生产单元成本
    other_salary_per_cell_shift = Column(Float, nullable=False, default=50.0)
    rent_per_cell_shift = Column(Float, nullable=False, default=40.0)
    electricity_fee_per_cell_shift = Column(Float, nullable=False, default=60.0)
    
    # 颜色数量 -> 单班产模数 映射（用于替代难度系数）
    # 存储为数组对象，例如：[{"min_colors":1, "max_colors":2, "molds_per_shift":150}, ...]
    color_output_map = Column(JSON, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class WorkerProfile(Base):
    __tablename__ = "worker_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    monthly_salary = Column(Float, nullable=False)
    machines_operated = Column(Integer, nullable=False)


class QuotationHistory(Base):
    __tablename__ = "quotation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 请求与响应快照
    request_payload = Column(JSON, nullable=False)
    result_payload = Column(JSON, nullable=False)
    
    # 冗余字段（便于列表展示与筛选）
    worker_type = Column(String(50), nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    user = relationship("User", back_populates="histories")
    favorites = relationship("QuotationFavorite", back_populates="history", cascade="all, delete-orphan")


class QuotationFavorite(Base):
    __tablename__ = "quotation_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    history_id = Column(Integer, ForeignKey("quotation_history.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=True)  # 自定义标题
    image_path = Column(String(500), nullable=True)  # 图片路径
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="favorites")
    history = relationship("QuotationHistory", back_populates="favorites")
    
    # 约束：同一用户不能重复收藏同一历史记录
    __table_args__ = (
        UniqueConstraint('user_id', 'history_id', name='uq_user_history'),
    )


