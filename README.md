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

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动应用

```bash
# 方式一：使用 uvicorn 直接运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式二：使用 Python 运行
python -m app.main
```

### 4. 访问应用

- **首页（报价计算）**: http://localhost:8000
- **登录页面**: http://localhost:8000/login
- **系统设置**: http://localhost:8000/settings （仅管理员）
- **API 文档**: http://localhost:8000/docs

### 5. 默认账户

首次启动会自动创建管理员账户：

- **用户名**: `admin`
- **密码**: `admin`

⚠️ **生产环境请务必修改默认密码！**

## 📁 项目结构

```
quotation/
├── quotation.py                 # 原始报价计算器（不修改）
├── requirements.txt             # Python 依赖
├── pyproject.toml              # 项目配置 (Black, Ruff, MyPy)
├── pytest.ini                 # 测试配置
├── .env.example                # 环境变量示例
├── README.md                    # 本文档
├── DESIGN.md                    # 设计文档
├── REFACTORING_PLAN.md          # 重构计划
├── app.db                       # SQLite 数据库（首次启动自动创建）
├── tests/                       # 测试文件
│   ├── conftest.py             # 测试配置
│   ├── test_auth.py            # 认证测试
│   ├── test_models.py          # 模型测试
│   ├── test_services.py        # 服务测试
│   └── test_quote.py           # 报价测试
└── app/
    ├── main.py                  # FastAPI 应用入口
    ├── config.py                # 配置文件
    ├── deps.py                  # 依赖注入
    ├── api/
    │   └── routers/             # API 路由
    │       ├── auth.py          # 认证相关
    │       ├── quote.py         # 报价计算
    │       ├── history.py      # 历史记录
    │       ├── favorites.py    # 收藏管理
    │       ├── settings.py     # 系统设置
    │       ├── upload.py       # 文件上传
    │       ├── analyze.py      # 图像分析
    │       └── health.py       # 健康检查
    ├── db/
    │   ├── models.py            # 数据库模型 (带索引优化)
    │   ├── session.py           # 数据库会话
    │   ├── crud.py              # 数据访问层 (N+1优化)
    │   └── seed.py              # 种子数据
    ├── schemas/                 # Pydantic 模型
    │   ├── auth.py             # 认证模型
    │   ├── quote.py            # 报价模型
    │   ├── settings.py         # 设置模型
    │   └── history.py          # 历史模型
    ├── services/                # 业务逻辑层
    │   ├── auth_service.py     # 认证服务
    │   ├── calculator_service.py # 计算服务
    │   ├── image_analysis_service.py # 图像分析
    │   └── cache_service.py    # 缓存服务
    ├── utils/                   # 工具模块
    │   ├── exceptions.py       # 异常处理
    │   ├── responses.py        # 响应工具
    │   ├── validation.py       # 验证工具
    │   └── security.py         # 安全工具
    ├── templates/               # Jinja2 模板
    │   ├── base.html
    │   ├── index.html
    │   ├── login.html
    │   └── settings.html
    └── static/                  # 静态资源
        ├── css/
        └── js/
```

## API 端点

### 认证
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/me` - 获取当前用户信息

### 报价
- `POST /api/quote` - 计算报价（自动记录历史）

### 历史记录
- `GET /api/history` - 获取历史列表（分页）
- `GET /api/history/{id}` - 获取单条历史详情
- `DELETE /api/history/{id}` - 删除历史记录

### 收藏
- `GET /api/favorites` - 获取收藏列表
- `POST /api/favorites` - 添加收藏
- `DELETE /api/favorites/{id}` - 取消收藏

### 系统设置（仅管理员）
- `GET /api/settings` - 获取系统设置
- `PUT /api/settings` - 更新系统设置

### 健康检查
- `GET /api/health` - 健康检查

## 环境变量配置

可通过环境变量自定义配置（可选）：

```bash
# 数据库 URL
export DATABASE_URL="sqlite:///./app.db"

# 会话密钥（生产环境必须修改）
export SESSION_SECRET="your-secret-key-here"

# 默认管理员账户（仅首次启动时使用）
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="admin"

# 调试模式
export DEBUG="False"
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

## 数据模型

### User（用户）
- 用户名、密码（bcrypt 加密）
- 管理员标识

### AppSettings（应用设置）
- 利润率、废品率
- 材料密度、材料单价
- 模具参数、产能参数
- 调机费用、生产单元成本

### WorkerProfile（工人配置）
- 工人类型（skilled/standard）
- 月薪、可操作机器数

### QuotationHistory（报价历史）
- 用户 ID
- 请求参数快照
- 计算结果快照
- 单价、总价（冗余字段）

### QuotationFavorite（报价收藏）
- 用户 ID
- 关联历史记录 ID
- 自定义名称

## 注意事项

1. **不修改 `quotation.py`**：系统通过实例化后覆盖属性的方式使用原计算器
2. **生产环境安全**：
   - 修改默认管理员密码
   - 设置强随机 `SESSION_SECRET`
   - 启用 HTTPS
   - 配置防火墙与访问控制
3. **数据库备份**：定期备份 `app.db` 文件
4. **性能优化**：SQLite 适合中小规模，高并发请迁移到 PostgreSQL/MySQL

## 🧪 开发与调试

### 代码质量工具

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

### 开发模式

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload

# 查看交互式 API 文档
# 访问 http://localhost:8000/docs

# 查看日志
# 日志会输出到控制台
```

### 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系项目维护者。


