#!/bin/bash

# 一键更新脚本 - 拉取最新代码并重启服务
set -e

echo "🚀 开始更新服务..."

# 1. 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 2. 停止现有服务
echo "⏹️  停止现有服务..."
docker compose -f deploy/docker-compose.yml down

# 3. 重建并启动服务
echo "🔨 重建并启动服务..."
docker compose -f deploy/docker-compose.yml up -d --build

# 4. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 5. 检查服务状态
echo "✅ 检查服务状态..."
docker compose -f deploy/docker-compose.yml ps

# 6. 健康检查
echo "🏥 健康检查..."
if curl -fsS http://localhost:8000/api/health > /dev/null; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务异常"
    exit 1
fi

if curl -fsS http://localhost:8080/ > /dev/null; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务异常"
    exit 1
fi

echo "🎉 更新完成！服务已重启并正常运行"
echo "🌐 前端地址: http://localhost:8080"
echo "🔧 后端地址: http://localhost:8000"
