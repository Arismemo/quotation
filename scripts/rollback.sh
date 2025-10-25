#!/bin/bash

# 回滚脚本
# 回滚到上一个版本

set -e

echo "🔄 回滚报价系统..."

# 检查是否在项目根目录
if [ ! -f "deploy/docker-compose.yml" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 回滚到上一个提交
echo "📥 回滚到上一个版本..."
git reset --hard HEAD~1

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
    echo "✅ 回滚成功！服务已就绪"
else
    echo "❌ 回滚失败！服务未就绪"
    exit 1
fi
