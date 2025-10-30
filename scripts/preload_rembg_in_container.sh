#!/bin/bash
# 在运行中的容器内预下载 rembg 模型
# 使用方法: docker exec quotation-backend python /app/scripts/preload_rembg_model.py

echo "正在预下载 rembg 模型..."
python /app/scripts/preload_rembg_model.py

if [ $? -eq 0 ]; then
    echo "✓ 模型下载成功"
else
    echo "✗ 模型下载失败"
    echo "提示：如果网络不可用，可以："
    echo "1. 手动下载模型文件到 ~/.u2net/u2net.onnx"
    echo "2. 或使用 opencv 方法（不需要模型）"
fi

