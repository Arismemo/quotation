### PVC 卡通制品报价系统 Web 化设计方案（后端 + 前端设置页面 + SQLite 持久化）

本方案将现有 `quotation.py` 中的 `QuotationCalculator` 封装为 Web 服务，并提供：
- 前端首页：填写产品参数获取报价
- 前端设置页面：维护计算所需的全局参数（持久化到 SQLite）
- 后端 API：对外提供设置读取/更新与报价计算接口

遵循限制：不修改 `quotation.py`，仅在实例化后按需覆盖其实例属性。


### 一、目标与约束
- 不修改 `quotation.py` 文件，仅调用其中的 `QuotationCalculator`。
- 将“必要的计算报价信息”持久化到 SQLite，计算报价时从数据库加载。
- 提供一个首页用于输入报价参数并查看结果；提供一个设置页面用于调整全局参数。
- 项目简单可部署、易于本地运行。


### 二、技术选型
- 后端框架：FastAPI（高性能、内置交互式文档、Pydantic 校验）
- Web 服务器：Uvicorn（开发环境 `--reload`）
- 数据库：SQLite（内置文件型 DB）
- ORM：SQLAlchemy 2.x（声明式映射）
- 模型/校验：Pydantic（请求/响应模型）
- 模板引擎：Jinja2（服务端渲染首页与设置页面）
- 静态资源：纯前端（少量 JS + CSS，必要时可直接使用 CDN，例如 Bulma/Tailwind）


### 三、目录结构（新增文件与目录，不改动 `quotation.py`）
```
/Users/liukun/j/code/quotation/
  ├─ quotation.py                  # 保持不变
  ├─ DESIGN.md                     # 本设计文档
  ├─ requirements.txt              # 依赖（后续实现时添加）
  ├─ README.md                     # 运行说明（后续实现时添加）
  └─ app/
     ├─ main.py                    # FastAPI 入口
     ├─ deps.py                    # 依赖注入（DB 会话等）
     ├─ api/
     │  ├─ __init__.py
     │  └─ routers/
     │     ├─ health.py            # 健康检查
     │     ├─ settings.py          # 设置相关 API（读/改）
     │     └─ quote.py             # 报价计算 API
     ├─ services/
     │  └─ calculator_service.py   # 将 DB 设置映射到 QuotationCalculator 并计算
     ├─ db/
     │  ├─ __init__.py
     │  ├─ session.py              # SQLite 连接/引擎/会话
     │  ├─ models.py               # SQLAlchemy 模型定义
     │  ├─ crud.py                 # 数据访问（读/写设置、工人配置）
     │  └─ seed.py                 # 首次启动时的默认数据注入
     ├─ schemas/
     │  ├─ settings.py             # Pydantic 设置模型
     │  └─ quote.py                # Pydantic 报价输入/输出模型
     ├─ templates/
     │  ├─ base.html               # 基础布局
     │  ├─ index.html              # 首页（报价表单）
     │  └─ settings.html           # 设置管理页面
     └─ static/
        ├─ css/
        └─ js/
```


### 四、数据模型设计（SQLite + SQLAlchemy）

1) 全局设置（单行记录） AppSettings
- id: int, primary key（固定只有 1 行记录）
- profit_margin: float（利润率）
- waste_rate: float（废品率）
- material_density: float（材料密度 g/cm³）
- material_price_per_gram: float（材料价格 元/g）
- mold_edge_length: float（模具可用边长 cm）
- mold_spacing: float（产品间距 cm）
- base_molds_per_shift: float（单班基准产模数，难度系数为 3 时）
- working_days_per_month: int（每月工作天数）
- shifts_per_day: int（每日班次数）
- needles_per_machine: int（每台机台针头数）
- setup_fee_per_color: float（单个颜色调机费）
- base_setup_fee: float（基础调机费）
- coloring_fee_per_color_per_shift: float（单个颜色单班调色费）
- other_salary_per_cell_shift: float（每生产单元/班 其他工资）
- rent_per_cell_shift: float（每生产单元/班 房租）
- electricity_fee_per_cell_shift: float（每生产单元/班 电费）
- updated_at: datetime

说明：以上字段与 `QuotationCalculator.__init__` 中的同名/等义字段一一对应，便于实例化后统一覆盖。

2) 工人配置 WorkerProfile（多行记录）
- id: int, primary key
- name: str（"skilled" | "standard"，可扩展）唯一
- monthly_salary: float（月薪）
- machines_operated: int（可同时操作的机器数量）

初始化策略：首次启动若无数据，按 `quotation.py` 的默认值写入一条 AppSettings；同时写入两条 WorkerProfile：
- skilled: { monthly_salary: 8400, machines_operated: 3 }
- standard: { monthly_salary: 7000, machines_operated: 2 }


### 五、后端 API 设计

- GET /api/health
  - 返回 `{ status: "ok" }`

- GET /api/settings
  - 返回聚合后的设置：全局 AppSettings + WorkerProfile 列表
  - 响应示例：
    ```json
    {
      "settings": {
        "profit_margin": 0.3,
        "waste_rate": 0.1,
        "material_density": 1.166,
        "material_price_per_gram": 0.01,
        "mold_edge_length": 26,
        "mold_spacing": 1,
        "base_molds_per_shift": 120,
        "working_days_per_month": 26,
        "shifts_per_day": 2,
        "needles_per_machine": 18,
        "setup_fee_per_color": 20,
        "base_setup_fee": 15,
        "coloring_fee_per_color_per_shift": 5,
        "other_salary_per_cell_shift": 50,
        "rent_per_cell_shift": 40,
        "electricity_fee_per_cell_shift": 60
      },
      "worker_profiles": [
        { "name": "skilled", "monthly_salary": 8400, "machines_operated": 3 },
        { "name": "standard", "monthly_salary": 7000, "machines_operated": 2 }
      ]
    }
    ```

- PUT /api/settings
  - 接收与 GET 返回相同结构的子集（允许部分字段更新，未传字段保持不变）
  - 校验：数值 > 0（或在合理区间），`needles_per_machine` ≥ max(color_count+1)
  - 对 `worker_profiles` 的更新策略：根据 name upsert（存在则更新，不存在则新增）
  - 返回最新设置

- POST /api/quote
  - 请求体（对应 `QuotationCalculator.calculate_quote` 所需字段）：
    ```json
    {
      "length": 3,
      "width": 3,
      "thickness": 0.3,
      "color_count": 5,
      "area_ratio": 0.7,
      "difficulty_factor": 3,
      "order_quantity": 100000,
      "worker_type": "skilled",
      "debug": false
    }
    ```
  - 处理流程：
    1. 读取数据库中的 AppSettings 与 WorkerProfiles
    2. 实例化 `QuotationCalculator()`
    3. 将 DB 值逐一覆盖到实例属性（包括 `WORKER_PROFILES`）
    4. 传入用户输入参数调用 `calculate_quote(...)`
    5. 将返回字典直接作为响应（若含 `error` 字段，返回 400 并携带错误信息）


### 六、服务层设计（Calculator 映射与调用）

`app/services/calculator_service.py`
- `build_calculator_from_db(session) -> QuotationCalculator`
  - 从 DB 读取 AppSettings + WorkerProfiles
  - `calc = QuotationCalculator()`
  - 覆盖：
    - `PROFIT_MARGIN`, `WASTE_RATE`
    - `MATERIAL_DENSITY`, `MATERIAL_PRICE_PER_GRAM`
    - `MOLD_EDGE_LENGTH`, `MOLD_SPACING`
    - `BASE_MOLDS_PER_SHIFT`, `WORKING_DAYS_PER_MONTH`, `SHIFTS_PER_DAY`
    - `NEEDLES_PER_MACHINE`
    - `SETUP_FEE_PER_COLOR`, `BASE_SETUP_FEE`, `COLORING_FEE_PER_COLOR_PER_SHIFT`
    - `OTHER_SALARY_PER_CELL_SHIFT`, `RENT_PER_CELL_SHIFT`, `ELECTRICITY_FEE_PER_CELL_SHIFT`
    - `WORKER_PROFILES`（由表 `worker_profiles` 聚合为字典）
- `compute_quote(session, QuoteRequest) -> dict`
  - 调用 `build_calculator_from_db`
  - 透传 `worker_type` 与用户输入参数，调用 `calculate_quote`
  - 若返回中存在 `error` 键：抛出 HTTP 400


### 七、前端页面设计（Jinja2 模板）

1) 首页 `/`（`templates/index.html`）
- 表单字段：
  - length, width, thickness, color_count, area_ratio, difficulty_factor, order_quantity
  - worker_type（下拉：从 `/api/settings` 的 worker_profiles 加载）
  - debug（可选开关）
- 交互：
  - 提交后以 `fetch('/api/quote')` POST JSON
  - 展示: "产品单价"、"订单货款总额" 及关键汇总；可展开显示详细字段

2) 设置页面 `/settings`（`templates/settings.html`）
- 加载 `/api/settings` 初始化表单
- 可编辑：文中“全局设置”各字段 + `worker_profiles` 中每条的 `monthly_salary` 与 `machines_operated`
- 提交：PUT `/api/settings`，成功后提示“已保存”

3) 布局与样式
- `base.html`：统一头部导航（首页 | 设置），引用 CSS 框架（CDN）
- 尽量少 JS，表单校验以 HTML5 + 轻量 JS 实现


### 八、输入校验与错误处理
- Pydantic 严格校验：正数/非负数、区间（如 0 < area_ratio ≤ 1）
- 业务校验：`color_count + 1 <= needles_per_machine`（由后端在计算前二次检查）
- FastAPI 全局异常处理：
  - Pydantic 校验错误：422 → 统一结构返回
  - 计算错误（返回含 `error`）：400 → `{ "error": "..." }`


### 九、安全与配置
- 设置接口默认无鉴权，便于本地演示；生产可选：
  - 环境变量 `ADMIN_TOKEN` 存在时，要求请求头 `X-Admin-Token` 一致方可读写设置
- CORS：本项目前后端同源，默认关闭；如需分离部署可开启 `CORSMiddleware`


### 十、初始化与运行
- 首次启动：
  1. 创建 SQLite 文件（默认 `app.db`）并建表
  2. 若无设置即从 `QuotationCalculator()` 读取默认值进行种子写入
  3. 写入两条默认 `WorkerProfile`（skilled/standard）
- 启动命令：
  - 开发：`uvicorn app.main:app --reload`
  - 访问：`/` 首页，`/settings` 设置页；交互式文档：`/docs`


### 十一、依赖清单（实现阶段在 requirements.txt 落地）
- fastapi
- uvicorn[standard]
- SQLAlchemy>=2.0
- pydantic
- Jinja2


### 十二、开发任务拆解（对应实施计划）
1) 实现 FastAPI 入口、路由与模板挂载
2) 建表与种子：AppSettings + WorkerProfile
3) DB CRUD：读取/更新设置，upsert 工人配置
4) 服务层：将 DB 设置映射到 `QuotationCalculator`，并计算报价
5) API：GET/PUT settings、POST quote、GET health
6) 前端：`index.html` 报价表单、`settings.html` 设置表单
7) 输入校验与错误处理（Pydantic + 业务检查）
8) README 与运行说明、requirements.txt


### 十三、字段对照表（DB → 计算器属性）
- AppSettings.profit_margin → QuotationCalculator.PROFIT_MARGIN
- AppSettings.waste_rate → QuotationCalculator.WASTE_RATE
- AppSettings.material_density → QuotationCalculator.MATERIAL_DENSITY
- AppSettings.material_price_per_gram → QuotationCalculator.MATERIAL_PRICE_PER_GRAM
- AppSettings.mold_edge_length → QuotationCalculator.MOLD_EDGE_LENGTH
- AppSettings.mold_spacing → QuotationCalculator.MOLD_SPACING
- AppSettings.base_molds_per_shift → QuotationCalculator.BASE_MOLDS_PER_SHIFT
- AppSettings.working_days_per_month → QuotationCalculator.WORKING_DAYS_PER_MONTH
- AppSettings.shifts_per_day → QuotationCalculator.SHIFTS_PER_DAY
- AppSettings.needles_per_machine → QuotationCalculator.NEEDLES_PER_MACHINE
- AppSettings.setup_fee_per_color → QuotationCalculator.SETUP_FEE_PER_COLOR
- AppSettings.base_setup_fee → QuotationCalculator.BASE_SETUP_FEE
- AppSettings.coloring_fee_per_color_per_shift → QuotationCalculator.COLORING_FEE_PER_COLOR_PER_SHIFT
- AppSettings.other_salary_per_cell_shift → QuotationCalculator.OTHER_SALARY_PER_CELL_SHIFT
- AppSettings.rent_per_cell_shift → QuotationCalculator.RENT_PER_CELL_SHIFT
- AppSettings.electricity_fee_per_cell_shift → QuotationCalculator.ELECTRICITY_FEE_PER_CELL_SHIFT
- WorkerProfiles(name→{monthly_salary,machines_operated}) → QuotationCalculator.WORKER_PROFILES


### 十四、验证要点与边界条件
- 极端尺寸导致 `units_per_mold == 0`：后端直接返回错误提示
- 难度系数为 0：后端返回错误提示
- 颜色数量超过针头数：后端返回错误提示
- 所有金额与结果保留与后端一致的小数精度（响应中按原方法返回）


### 十五、后续可拓展
- 用户管理与鉴权（仅管理员可修改设置）
- 导出报价单（PDF/Excel）
- 多套设置方案（按客户/项目保存配置模板）
- 国际化（i18n）与多语言 UI
- 日志与审计 Trail（记录每次设置变更与报价请求）


### 十六、小结
本方案以最小侵入方式复用既有 `QuotationCalculator`，通过 FastAPI + SQLite 构建可配置、可维护的报价系统。前端提供首页与设置页，后端提供清晰的 API，设置持久化后在计算时动态注入，满足“不可修改 `quotation.py`”与“配置持久化”的约束。


### 十七、用户与鉴权设计（新增）
- 用户模型 `User`：
  - id: int, primary key
  - username: str, unique, not null
  - password_hash: str, not null（使用 bcrypt 存储）
  - is_admin: bool, default False
  - created_at: datetime
- 登录状态：使用 Starlette `SessionMiddleware` 基于签名 Cookie 存储 `user_id`
  - 会话 Cookie：`HttpOnly`，开发环境用固定 `SECRET_KEY`，生产从环境变量注入
  - 依赖 `get_current_user()`：从会话解析用户，未登录时返回 401
- 默认管理员：首启 Seed 时创建 `admin/admin`（以 bcrypt 存储，绝不明文）
- 权限控制：
  - 设置相关 API/页面仅管理员可访问
  - 历史/收藏 API 仅登录用户可访问（按 `user_id` 作用域隔离）


### 十八、报价历史与收藏（新增）
1) 数据模型
- `QuotationHistory`
  - id: int, primary key
  - user_id: int, FK → User.id, index
  - request_payload: JSON（请求参数快照）
  - result_payload: JSON（计算结果快照）
  - worker_type: str
  - unit_price: float（冗余，便于列表展示）
  - total_price: float（冗余，便于列表展示）
  - computed_at: datetime, index
- `QuotationFavorite`
  - id: int, primary key
  - user_id: int, FK → User.id, index
  - history_id: int, FK → QuotationHistory.id, index
  - name: str（自定义标题/别名）
  - created_at: datetime
  - 约束：unique(user_id, history_id)

2) 写入策略
- 当登录用户调用 `POST /api/quote` 成功时，自动写入一条 `QuotationHistory`
- 收藏行为基于历史：`POST /api/favorites` 传入 `history_id` 和可选 `name`

3) API（需登录）
- GET `/api/history?offset=0&limit=20&from=...&to=...&kw=...`
  - 分页与筛选（按时间区间、关键字匹配 name/备注/结果字段）
- GET `/api/history/{id}`：查看详情（仅限资源所有者）
- DELETE `/api/history/{id}`：删除（软删除可选）
- POST `/api/history/{id}/recompute`：从快照复算（可用于复用参数）
- GET `/api/favorites`：列表
- POST `/api/favorites`：创建收藏（body: { history_id, name? })
- DELETE `/api/favorites/{id}`：取消收藏

4) 前端交互
- 历史列表项支持：查看详情、复制参数到表单、加入/取消收藏
- 收藏列表项支持：查看详情、填充表单、取消收藏


### 十九、首页布局调整（新增）
- 页面结构（`templates/index.html`）：
  - 上半部分：报价输入区域（原表单，增加“保存到历史/收藏”的显式提示；登录状态下自动写入历史）
  - 下半部分：两列布局
    - 左侧：报价历史（当前用户，分页加载）
    - 右侧：报价收藏（当前用户，分页加载）
- 未登录时：
  - 顶部导航显示“登录”，下半部分历史/收藏区域显示登录提示与入口
- 已登录时：
  - 顶部显示用户名与“退出登录”，显示可用的历史/收藏列表


### 二十、认证与页面（新增）
- 新增模板：`templates/login.html`（用户名/密码表单）
- 新增路由：
  - GET `/login`：渲染登录页（未登录访问）
  - POST `/api/auth/login`：JSON 或表单登录，成功后写入会话并返回用户信息
  - POST `/api/auth/logout`：清除会话
  - GET `/api/auth/me`：返回当前用户信息
- 导航策略：
  - 非管理员隐藏“设置”入口（直接访问返回 403）
  - 登录状态在 `base.html` 统一处理（显示用户名/退出）


### 二十一、依赖补充（新增）
- passlib[bcrypt]：密码哈希与校验
- itsdangerous 或直接使用 Starlette `SessionMiddleware`（推荐后者）
- （如登录用表单提交）python-multipart


### 二十二、初始化与迁移更新（新增）
- `db/models.py` 新增：`User`、`QuotationHistory`、`QuotationFavorite`
- `db/seed.py` 新增逻辑：若无用户则创建 `admin/admin`（bcrypt 哈希）
- 为 `QuotationHistory.computed_at`、`QuotationFavorite.user_id` 等添加索引
- 后续可引入 Alembic 做结构迁移与版本管理


### 二十三、开发任务增补
9) 实现登录/退出与会话（后端 + 模板）
10) 新增用户、历史、收藏的模型与 CRUD
11) 历史/收藏 API 与权限控制
12) 首页模板改版：上方表单 + 下方两列（历史/收藏）
13) 种子：默认 admin 用户


### 二十四、实现细节补充

#### 1. 数据库会话管理
- `app/db/session.py`：
  - 使用 SQLAlchemy 2.x 声明式 Base
  - 创建同步引擎：`create_engine("sqlite:///app.db", echo=False)`
  - SessionLocal 工厂：`sessionmaker(autocommit=False, autoflush=False, bind=engine)`
  - `init_db()` 函数：建表 + 调用 seed

#### 2. 密码哈希策略
- 使用 `passlib.context.CryptContext` 配置 bcrypt
- `app/services/auth_service.py`：
  - `hash_password(plain: str) -> str`
  - `verify_password(plain: str, hashed: str) -> bool`
  - `authenticate_user(db, username, password) -> User | None`

#### 3. 会话中间件配置
- Starlette `SessionMiddleware`：
  - `secret_key`：开发环境固定，生产从环境变量 `SESSION_SECRET` 读取
  - `max_age`：7天（604800秒）
  - `same_site`："lax"
- 登录后写入 `request.session["user_id"] = user.id`
- 依赖 `get_current_user(request, db)` 从 session 读取并查询用户

#### 4. 权限装饰器/依赖
- `get_current_user_optional`：未登录返回 None
- `get_current_user`：未登录抛 401
- `require_admin`：非管理员抛 403

#### 5. 历史自动写入策略
- `POST /api/quote` 在计算成功后，若当前用户已登录：
  - 提取 `request_payload`（输入参数）
  - 提取 `result_payload`（完整返回字典）
  - 冗余字段：`unit_price`、`total_price`、`worker_type`
  - 写入 `QuotationHistory` 并 commit
- 未登录用户仍可计算，但不写历史

#### 6. 前端交互流程
- 登录：
  - 访问 `/login` 渲染表单
  - 提交 POST `/api/auth/login`（JSON 或 form-data）
  - 成功后重定向到 `/`
- 首页：
  - 页面加载时：`GET /api/auth/me` 获取当前用户，判断是否显示历史/收藏
  - 提交报价：`POST /api/quote`，成功后刷新历史列表
  - 历史/收藏列表：分页加载 `GET /api/history?offset=...`、`GET /api/favorites`
  - 列表项操作：复用参数（填充表单）、查看详情（弹窗）、收藏/取消收藏
- 设置页：
  - 仅管理员可见导航入口
  - 加载 `GET /api/settings`
  - 更新 `PUT /api/settings`

#### 7. UI/UX 细节
- CSS 框架：Tailwind CSS（通过 CDN）
- 响应式布局：首页下半部分在移动端上下堆叠，桌面端左右分栏
- 加载状态：提交表单时显示 spinner
- 错误提示：Toast 或内联红色提示
- 分页：简单 offset/limit，前端"加载更多"按钮

#### 8. 环境变量与配置
- `app/config.py`：
  - `DATABASE_URL`：默认 `sqlite:///app.db`
  - `SESSION_SECRET`：默认固定值，生产从环境变量读取
  - `ADMIN_USERNAME`、`ADMIN_PASSWORD`：默认 `admin`/`admin`（仅 seed 时使用）

#### 9. 错误处理
- 全局异常处理器：
  - `HTTPException` → JSON 错误响应
  - `Exception` → 500 + 日志记录
- 业务错误：
  - 计算返回 `{"error": "..."}` → 400
  - 权限不足 → 403
  - 资源不存在 → 404

#### 10. 日志
- 使用 Python `logging`：
  - INFO：启动、数据库初始化
  - WARNING：业务校验失败
  - ERROR：异常捕获