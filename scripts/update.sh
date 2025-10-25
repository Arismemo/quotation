#!/bin/bash

# 报价系统一键更新脚本
# 功能：拉取最新代码、重建容器、重启服务

set -e  # 遇到错误立即退出

echo "🚀 开始更新报价系统..."

# 检查是否在项目根目录
if [ ! -f "deploy/docker-compose.yml" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ 错误：Docker 未运行，请先启动 Docker"
    exit 1
fi

echo "📥 拉取最新代码..."
git fetch origin
git pull origin main

echo "🛑 停止现有服务..."
docker compose -f deploy/docker-compose.yml down

echo "🗑️  清理旧镜像（可选）..."
read -p "是否清理未使用的 Docker 镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker image prune -f
    echo "✅ 已清理未使用的镜像"
fi

echo "🔨 重建并启动服务..."
docker compose -f deploy/docker-compose.yml up -d --build

echo "⏳ 等待服务启动..."
sleep 5

echo "🔍 检查服务状态..."
docker compose -f deploy/docker-compose.yml ps

echo "🏥 健康检查..."
if curl -fsS http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "✅ 后端服务健康"
else
    echo "⚠️  后端服务可能未就绪，请稍后检查"
fi

if curl -fsS http://localhost:8080/ >/dev/null 2>&1; then
    echo "✅ 前端服务可达"
else
    echo "⚠️  前端服务可能未就绪，请稍后检查"
fi

echo ""
echo "🎉 更新完成！"
echo "📱 前端地址: http://localhost:8080"
echo "🔧 后端地址: http://localhost:8000"
echo ""
echo "📋 常用命令："
echo "  查看日志: docker compose -f deploy/docker-compose.yml logs -f"
echo "  查看状态: docker compose -f deploy/docker-compose.yml ps"
echo "  停止服务: docker compose -f deploy/docker-compose.yml down"
echo "  重启服务: docker compose -f deploy/docker-compose.yml restart"
