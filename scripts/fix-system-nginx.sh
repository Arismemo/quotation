#!/bin/bash
# 修复系统 Nginx 配置文件中的 client_max_body_size 设置
# 用法: sudo bash fix-system-nginx.sh

CONFIG_FILE="/etc/nginx/sites-available/quotation"
BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误: 配置文件不存在: $CONFIG_FILE"
    echo "请先创建配置文件或检查路径是否正确"
    exit 1
fi

# 备份原文件
echo "备份配置文件到: $BACKUP_FILE"
cp "$CONFIG_FILE" "$BACKUP_FILE"

# 检查是否已有 client_max_body_size 配置
if grep -q "client_max_body_size" "$CONFIG_FILE"; then
    echo "发现现有的 client_max_body_size 配置，将更新为 10m"
    # 使用 sed 替换现有的配置
    sed -i 's/client_max_body_size.*/client_max_body_size 10m;/' "$CONFIG_FILE"
else
    echo "添加 client_max_body_size 10m 配置"
    # 在 server 块中添加配置（在第一个 location 之前）
    if grep -q "location /" "$CONFIG_FILE"; then
        # 在第一个 location / 之前插入
        sed -i '/location \//i\    # 设置客户端请求体最大大小为 10MB（支持图片上传）\n    client_max_body_size 10m;\n' "$CONFIG_FILE"
    else
        # 如果没有 location，在 server { 之后添加
        sed -i '/server {/a\    # 设置客户端请求体最大大小为 10MB（支持图片上传）\n    client_max_body_size 10m;' "$CONFIG_FILE"
    fi
fi

# 检查并添加超时配置
if ! grep -q "proxy_connect_timeout" "$CONFIG_FILE"; then
    echo "添加代理超时配置"
    if grep -q "proxy_pass" "$CONFIG_FILE"; then
        # 在 proxy_pass 行之后添加超时配置
        sed -i '/proxy_pass/a\        \n        # 增加超时时间以支持大文件上传\n        proxy_connect_timeout 300s;\n        proxy_send_timeout 300s;\n        proxy_read_timeout 300s;\n        proxy_buffering off;\n        proxy_request_buffering off;' "$CONFIG_FILE"
    fi
fi

echo ""
echo "配置已更新！"
echo "请执行以下命令："
echo "1. 测试配置: sudo nginx -t"
echo "2. 如果测试通过，重新加载: sudo systemctl reload nginx"
echo ""

