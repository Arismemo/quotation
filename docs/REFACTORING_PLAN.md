# 重构优化计划 (Refactoring & Optimization Plan)

本项目旨在对现有代码库进行全面的重构和优化，以提升其代码质量、性能、可维护性和安全性。

---

### **阶段 0: 分析、基准与安全网 (Analysis, Benchmarking & Safety Net)**

*目标：在不修改核心逻辑的情况下，建立代码质量标准，并搭建测试“安全网”，为后续重构做准备。*

1.  **依赖分析 (Dependency Analysis):**
    *   检查 `requirements.txt`，识别并升级过时的库，移除未使用的库。
    *   使用 `pip-audit` 或类似工具扫描依赖项，检查是否存在已知的安全漏洞。

2.  **代码规范与格式化 (Code Style & Formatting):**
    *   引入 `black` 作为代码格式化工具，确保整个项目风格统一。
    *   引入 `ruff` 作为代码 Linter，用于检查代码质量、潜在错误和不规范的导入。
    *   配置这些工具，并对整个项目进行一次初步的格式化和 linting 修复。

3.  **建立测试框架 (Establish Testing Framework):**
    *   创建 `tests/` 目录。
    *   引入 `pytest` 作为测试框架。
    *   为最核心的业务逻辑（例如 `quotation.py` 和 `app/services/` 中的关键服务）编写初步的单元测试和集成测试，确保核心功能在重构过程中不被破坏。

4.  **配置与环境管理 (Configuration & Environment):**
    *   标准化配置管理。将 `app/config.py` 中的硬编码配置（如密钥、数据库URL）迁移到环境变量中。
    *   引入 `python-dotenv`，并创建一个 `.env.example` 文件来记录所有需要的环境变量，方便项目部署和协作。

### **阶段 1: 代码质量与结构优化 (Code Quality & Structure)**

*目标：提升代码的可读性、可维护性和健壮性。*

1.  **全面类型提示 (Comprehensive Type Hinting):**
    *   为项目中的所有函数、类和变量添加明确的 Python 类型提示。
    *   引入 `mypy` 进行静态类型检查，并解决所有类型错误。

2.  **代码去重与简化 (DRY & Simplification):**
    *   审查 `app/api/routers/`, `app/services/` 和根目录下的 `.py` 文件，找出重复的代码块，将其抽象成可复用的函数或类。
    *   重构过于复杂（过长或嵌套过深）的函数，将其拆分为更小、更专注的单元。

3.  **API 层重构 (API Layer Refactoring):**
    *   审查所有 FastAPI 路由，确保：
        *   使用标准的 HTTP 状态码。
        *   请求体和响应体都使用清晰的 Pydantic `schemas`。
        *   使用 `Depends` 机制来处理依赖注入。

4.  **数据库交互优化 (Database Interaction):**
    *   审查 `app/db/crud.py` 中的所有数据库操作。
    *   确保没有裸露的 SQL 语句，所有交互都通过 ORM (SQLAlchemy) 进行。
    *   检查是否存在 N+1 查询问题，并使用 `selectinload` 或 `joinedload` 进行预加载优化。

### **阶段 2: 性能与安全强化 (Performance & Security Hardening)**

*目标：提升应用的运行速度和安全性。*

1.  **性能优化 (Performance Optimization):**
    *   **异步操作:** 检查所有 I/O 密集型操作，确保它们都使用了 `async/await`。
    *   **图片处理:** 分析图片处理脚本，评估是否可以优化算法或使用后台任务。
    *   **数据库索引:** 根据常见的查询模式，在 `app/db/models.py` 中添加数据库索引。

2.  **安全加固 (Security Hardening):**
    *   **认证与授权:** 审查认证和授权逻辑，确保密码哈希安全，Token 机制健壮。
    *   **输入验证:** 确保所有用户输入都经过了严格的验证。
    *   **依赖安全:** 再次运行依赖漏洞扫描。

### **阶段 3: 文档与最终化 (Documentation & Finalization)**

*目标：让项目易于理解、部署和交接。*

1.  **完善 `README.md`:**
    *   更新项目说明、安装/运行指南、API 概览。
2.  **API 文档:**
    *   审查并完善 FastAPI 自动生成的文档元数据。
3.  **清理与收尾:**
    *   删除所有无用的代码、注释和文件。
    *   确保项目通过所有代码质量和测试检查。
