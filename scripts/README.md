# 部署脚本说明

## 脚本列表

### 1. `update.sh` - 完整更新脚本
**功能**：拉取最新代码、重建容器、重启服务
**特点**：
- 交互式确认清理镜像
- 详细的状态检查和日志输出
- 健康检查验证

**使用方法**：
```bash
./scripts/update.sh
```

### 2. `quick-update.sh` - 快速更新脚本
**功能**：无交互快速更新
**特点**：
- 适用于自动化部署
- 最小化输出
- 返回状态码供 CI/CD 使用

**使用方法**：
```bash
./scripts/quick-update.sh
```

### 3. `rollback.sh` - 回滚脚本
**功能**：回滚到上一个版本
**特点**：
- 快速回滚到上一个 Git 提交
- 自动重启服务
- 健康检查验证

**使用方法**：
```bash
./scripts/rollback.sh
```

## 手动更新步骤

如果脚本无法使用，可以手动执行以下步骤：

### 1. 拉取最新代码
```bash
git fetch origin
git pull origin main
```

### 2. 停止现有服务
```bash
docker compose -f deploy/docker-compose.yml down
```

### 3. 重建并启动服务
```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

### 4. 检查服务状态
```bash
docker compose -f deploy/docker-compose.yml ps
```

### 5. 健康检查
```bash
curl http://localhost:8000/api/health
curl http://localhost:8080/
```

## 常用 Docker Compose 命令

```bash
# 查看服务状态
docker compose -f deploy/docker-compose.yml ps

# 查看日志
docker compose -f deploy/docker-compose.yml logs -f

# 查看特定服务日志
docker compose -f deploy/docker-compose.yml logs -f backend
docker compose -f deploy/docker-compose.yml logs -f frontend

# 重启服务
docker compose -f deploy/docker-compose.yml restart

# 停止服务
docker compose -f deploy/docker-compose.yml down

# 停止并删除卷（谨慎使用）
docker compose -f deploy/docker-compose.yml down -v
```

## 故障排除

### 1. 端口冲突
如果遇到端口冲突，检查是否有其他服务占用 8000 或 8080 端口：
```bash
lsof -i :8000
lsof -i :8080
```

### 2. 容器启动失败
查看详细日志：
```bash
docker compose -f deploy/docker-compose.yml logs backend
docker compose -f deploy/docker-compose.yml logs frontend
```

### 3. 数据库问题
如果数据库出现问题，可以重新初始化：
```bash
docker compose -f deploy/docker-compose.yml down
docker volume rm quotation_sqlite_data
docker compose -f deploy/docker-compose.yml up -d --build
```

### 4. 清理 Docker 资源
```bash
# 清理未使用的镜像
docker image prune -f

# 清理未使用的容器
docker container prune -f

# 清理未使用的卷
docker volume prune -f

# 清理所有未使用的资源
docker system prune -f
```
