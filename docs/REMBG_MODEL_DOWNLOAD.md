# rembg 模型下载问题解决方案

## 问题描述

rembg 首次使用时需要从 GitHub 下载模型文件（u2net.onnx），如果服务器无法访问 GitHub 或网络超时，会导致分析失败。

## 解决方案

### 方案 1：构建时预下载（推荐）

在 Dockerfile 中已经添加了预下载步骤，重建镜像时会自动下载模型：

```bash
cd deploy
docker compose build --no-cache backend
docker compose up -d
```

### 方案 2：在运行中的容器内预下载

如果模型下载失败，可以在容器运行时手动下载：

```bash
# 方式 1：使用预下载脚本
docker exec quotation-backend python /app/scripts/preload_rembg_model.py

# 方式 2：直接执行（如果脚本不可用）
docker exec quotation-backend python -c "from rembg import new_session; new_session('u2net')"
```

### 方案 3：手动下载模型文件

如果服务器无法访问 GitHub，可以手动下载：

1. **下载模型文件**：
   ```bash
   # 在可以访问 GitHub 的机器上下载
   curl -L https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx \
     -o u2net.onnx
   ```

2. **复制到容器**：
   ```bash
   # 创建目录
   docker exec quotation-backend mkdir -p /root/.u2net
   
   # 复制文件
   docker cp u2net.onnx quotation-backend:/root/.u2net/u2net.onnx
   ```

3. **验证**：
   ```bash
   docker exec quotation-backend ls -lh /root/.u2net/
   ```

### 方案 4：使用 opencv 方法（最简单）

如果 rembg 模型下载困难，可以直接使用 opencv 方法：

- **优点**：无需下载模型，速度快，不依赖网络
- **缺点**：精度稍低于 rembg

在前端设置中选择 "opencv" 方法即可。

### 方案 5：配置代理（如果有）

如果服务器有代理，可以通过环境变量配置：

```bash
# 在 docker-compose.yml 中添加环境变量
environment:
  - HTTP_PROXY=http://proxy.example.com:8080
  - HTTPS_PROXY=http://proxy.example.com:8080
```

## 验证模型是否已下载

```bash
docker exec quotation-backend ls -lh /root/.u2net/
```

如果看到 `u2net.onnx` 文件（约 176MB），说明模型已下载成功。

## 临时解决方案

如果急需使用，可以先切换到 opencv 方法：

1. 在前端页面，打开设置
2. 将"识别算法"切换为 "opencv"
3. 保存设置

这样就不需要 rembg 模型了。

