import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware

from app.api.routers import (
    analyze,
    auth,
    favorites,
    health,
    history,
    quote,
    settings,
    upload,
)
from app.config import settings as config_settings
from app.db.session import init_db
from app.utils.error_handlers import (
    BusinessLogicError,
    DatabaseError,
    business_logic_exception_handler,
    database_exception_handler,
    general_exception_handler,
    http_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO if config_settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ========== 应用生命周期事件 ==========


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("应用启动中...")

    # 检查数据库文件是否存在
    db_file = config_settings.DATABASE_URL.replace("sqlite:///", "").replace("./", "")
    db_exists = os.path.exists(db_file)

    if not db_exists:
        logger.info(f"数据库文件不存在，将创建并初始化: {db_file}")

    init_db()
    
    # 可选：预加载 rembg 模型（如果可用）
    # 这可以避免首次使用时因下载模型导致的延迟
    try:
        import os
        if os.getenv("PRELOAD_REMBG_MODEL", "false").lower() == "true":
            logger.info("正在预加载 rembg 模型...")
            try:
                from rembg import new_session
                session = new_session("u2net")
                logger.info("✓ rembg 模型预加载成功")
            except Exception as e:
                logger.warning(f"rembg 模型预加载失败（不影响使用）: {e}")
    except ImportError:
        pass  # rembg 未安装，跳过
    
    logger.info("应用启动完成")

    yield

    # 关闭时清理
    logger.info("应用关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=config_settings.APP_NAME,
    description="PVC卡通制品报价系统 API",
    version="1.0.0",
    debug=config_settings.DEBUG,
    lifespan=lifespan,
)

# 添加会话中间件
app.add_middleware(
    SessionMiddleware,
    secret_key=config_settings.SESSION_SECRET,
    max_age=config_settings.SESSION_MAX_AGE,
    same_site="lax",
    https_only=False,  # 开发环境设为 False，生产环境建议 True
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 注册异常处理器
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(BusinessLogicError, business_logic_exception_handler)
app.add_exception_handler(DatabaseError, database_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册API路由
app.include_router(auth.router, prefix="/api/auth")
app.include_router(quote.router, prefix="/api/quote")
app.include_router(history.router, prefix="/api/history")
app.include_router(favorites.router, prefix="/api/favorites")
app.include_router(settings.router, prefix="/api/settings")
app.include_router(upload.router, prefix="/api/upload")
app.include_router(analyze.router, prefix="/api/analyze")
app.include_router(health.router, prefix="/api/health")

# 模板引擎
templates = Jinja2Templates(directory="app/templates")


# ========== 前端页面路由 ==========


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页"""
    # 如果已登录，重定向到首页
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """设置页（需管理员权限，前端校验）"""
    return templates.TemplateResponse("settings.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
