# PVC 卡通制品报价系统

基于 FastAPI + SQLite 的现代化 Web 报价系统，提供产品报价计算、用户认证、历史记录管理和系统配置功能。

## 🚀 功能特性

- ✅ **智能报价计算**：根据产品参数自动计算报价（复用原有 `quotation.py` 计算器）
- ✅ **安全用户认证**：基于会话的身份验证，支持密码强度验证
- ✅ **报价历史管理**：自动记录每次报价结果，支持查看、搜索和导出
- ✅ **报价收藏系统**：收藏重要的报价记录，便于快速访问
- ✅ **系统设置管理**：管理员可修改全局参数（利润率、材料成本、工人配置等）
- ✅ **响应式界面**：基于 Tailwind CSS 的现代化 UI
- ✅ **图像分析功能**：支持图片上传和面积比例分析
- ✅ **性能优化**：数据库索引优化、缓存机制、N+1查询优化
- ✅ **代码质量**：完整的类型提示、代码格式化、测试覆盖

## 🛠️ 技术栈

- **后端框架**: FastAPI (异步支持)
- **数据库**: SQLite + SQLAlchemy 2.x (ORM)
- **模板引擎**: Jinja2
- **前端样式**: Tailwind CSS (CDN)
- **密码加密**: Passlib + Bcrypt (安全哈希)
- **会话管理**: Starlette SessionMiddleware
- **代码质量**: Black (格式化) + Ruff (Linting) + MyPy (类型检查)
- **测试框架**: Pytest + Coverage
- **图像处理**: OpenCV + Pillow + RemBG
- **缓存机制**: 内存缓存 (可扩展至Redis)

## 快速开始

### 1. 环境要求

- Python 3.8+
- pip
- Docker / Docker Compose（可选，推荐）

### 2. 安装依赖（本地运行）

```bash
pip install -r requirements.txt
```

### 3. 启动应用（本地运行）

```bash
# 方式一：使用 uvicorn 直接运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式二：使用 Python 运行
python -m app.main
```

### 4. 启动应用（Docker Compose 推荐）

```bash
# 复制环境变量示例并按需修改
cp deploy/env/.env.example .env  # 可选：在 deploy/docker-compose.yml 同目录外也会生效（通过变量传入）

# 一键构建并启动（使用 deploy 下的 compose 文件）
docker compose -f deploy/docker-compose.yml up -d --build

# 关闭
# docker compose -f deploy/docker-compose.yml down
```

### 5. 访问应用

- **前端入口（经 Nginx 反代）**: http://localhost:8080
- **后端直连**: http://localhost:8000
- **登录页面**: http://localhost:8000/login
- **系统设置**: http://localhost:8000/settings （仅管理员）
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

### 6. 默认账户

首次启动会自动创建管理员账户：

- **用户名**: `admin`
- **密码**: `admin`

⚠️ 生产环境请务必修改默认密码！

## 📁 项目结构（已整理）

```
quotation/
├── app/                       # FastAPI 应用
│   ├── api/routers/           # API 路由
│   ├── db/                    # 数据库模型/会话/种子
│   ├── schemas/               # Pydantic 模型
│   ├── services/              # 业务逻辑与封装
│   ├── utils/                 # 工具模块
│   ├── templates/             # Jinja2 模板
│   └── static/                # 静态资源（uploads 在 data/）
├── deploy/                    # 部署资产（唯一 Compose 位置）
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── nginx/
│   │   └── nginx.conf
│   └── env/
│       └── .env.example
├── data/                      # 本地数据卷（不纳入版本控制）
│   ├── sqlite/                # SQLite 文件挂载到容器 /data
│   └── uploads/               # 上传目录挂载到容器 /app/app/static/uploads
├── docs/                      # 文档归档（设计/计划/说明）
├── scripts/                   # 辅助/示例脚本
├── quotation.py               # 原始计算器（被服务层引用）
├── requirements.txt
├── pyproject.toml
├── pytest.ini
└── README.md
```

## 环境变量配置

可通过环境变量自定义配置（可选）：

```bash
# 数据库 URL
DATABASE_URL="sqlite:////data/app.db"

# 会话密钥（生产环境必须修改）
SESSION_SECRET="your-secret-key-here"

# 默认管理员账户（仅首次启动）
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin"

# 调试模式
DEBUG="False"
```

## 使用流程

### 1. 普通用户
1. 访问首页，填写产品参数
2. 点击"计算报价"查看结果
3. （可选）登录后自动保存历史记录
4. 查看历史记录，收藏重要报价
5. 点击历史/收藏项快速填充表单

### 2. 管理员
1. 登录后访问"系统设置"
2. 修改全局参数（利润率、材料成本、工人配置等）
3. 保存设置后立即生效于后续报价计算

## 数据模型（节选）

- User（用户）：用户名、密码（bcrypt）、是否管理员
- AppSettings（应用设置）：利润/废品、材料、产能、费用等
- WorkerProfile（工人配置）：月薪、可操作机器数
- QuotationHistory（报价历史）：请求/结果快照、冗余字段
- QuotationFavorite（报价收藏）：history 关联与备注/图片

## 注意事项

1. **不修改 `quotation.py`**：系统通过实例化后覆盖属性的方式使用原计算器
2. **生产环境安全**：
   - 修改默认管理员密码
   - 设置强随机 `SESSION_SECRET`
   - 启用 HTTPS
   - 配置防火墙与访问控制
3. **数据库与上传位置**：
   - SQLite 位于宿主 `data/sqlite`（容器内 `/data/app.db`）
   - 上传目录位于宿主 `data/uploads`（容器内 `/app/app/static/uploads`）

## 🧪 开发与调试

```bash
# 代码格式化
black .

# 代码检查
ruff check . --fix

# 类型检查
mypy app/ --ignore-missing-imports

# 运行测试
pytest tests/ -v

# 测试覆盖率
pytest tests/ --cov=app --cov-report=html
```


