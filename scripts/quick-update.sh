#!/bin/bash

# 快速更新脚本（无交互）
# 适用于自动化部署或 CI/CD

set -e

echo "🚀 快速更新报价系统..."

# 检查是否在项目根目录
if [ ! -f "deploy/docker-compose.yml" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 拉取最新代码
echo "📥 拉取最新代码..."
git fetch origin
git pull origin main

# 停止并重建服务
echo "🔄 重启服务..."
docker compose -f deploy/docker-compose.yml down
docker compose -f deploy/docker-compose.yml up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
echo "🏥 健康检查..."
if curl -fsS http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "✅ 更新成功！服务已就绪"
    exit 0
else
    echo "❌ 更新失败！服务未就绪"
    exit 1
fi
