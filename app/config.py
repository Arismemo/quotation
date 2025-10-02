import os

class Settings:
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    # 会话配置
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "dev-secret-key-change-in-production")
    SESSION_MAX_AGE: int = 604800  # 7天
    
    # 默认管理员账户（仅用于种子数据）
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin")
    
    # 应用配置
    APP_NAME: str = "PVC卡通制品报价系统"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

settings = Settings()


