from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
from app.db.session import init_db
from app.api.routers import health, auth, quote, history, favorites, settings as settings_router
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="PVC卡通制品报价系统 API",
    version="1.0.0",
    debug=settings.DEBUG
)

# 添加会话中间件
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    max_age=settings.SESSION_MAX_AGE,
    same_site="lax",
    https_only=False  # 开发环境设为 False，生产环境建议 True
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="app/templates")

# 注册 API 路由
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(quote.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(favorites.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")


# ========== 前端页面路由 ==========

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
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


# ========== 应用启动事件 ==========

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    logger.info("应用启动中...")
    
    # 检查数据库文件是否存在
    db_file = settings.DATABASE_URL.replace("sqlite:///", "").replace("./", "")
    db_exists = os.path.exists(db_file)
    
    if not db_exists:
        logger.info(f"数据库文件不存在，将创建并初始化: {db_file}")
    
    init_db()
    logger.info("应用启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("应用关闭")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


