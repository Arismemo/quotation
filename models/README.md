# rembg 模型文件下载说明

## ⚠️ 重要提示

**模型文件较大（约 167MB），不能直接提交到 GitHub（超过 100MB 限制）。**

## 下载模型到仓库

运行以下命令将 rembg 模型下载到项目的 `models/` 目录：

```bash
python scripts/download_model_to_repo.py
```

模型文件将保存到 `models/u2net.onnx`（约 167MB）。

## 使用本地模型

下载完成后，代码会自动检测并使用仓库中的模型文件：

1. **本地开发**：代码会自动检测 `models/u2net.onnx` 并使用
2. **Docker 部署**：模型文件会被复制到容器中，代码会自动使用

## 模型文件管理方案

### 方案 1：不提交到 Git（推荐）

模型文件已添加到 `.gitignore`，不会提交到仓库。

**部署时**：
- 开发环境：运行 `python scripts/download_model_to_repo.py` 手动下载
- Docker 部署：在构建时自动下载（如果网络可用），或手动复制到容器

### 方案 2：使用 Git LFS（适合团队协作）

如果想提交模型文件，可以使用 Git LFS：

```bash
# 安装 Git LFS
git lfs install

# 跟踪模型文件
git lfs track "models/*.onnx"

# 添加并提交
git add .gitattributes models/u2net.onnx
git commit -m "Add rembg model via Git LFS"
git push
```

### 方案 3：手动下载到容器

如果服务器无法访问 GitHub：

```bash
# 1. 在本地下载模型
python scripts/download_model_to_repo.py

# 2. 复制到容器
docker cp models/u2net.onnx quotation-backend:/app/models/u2net.onnx
```

## 验证

下载完成后，验证文件：
```bash
ls -lh models/u2net.onnx
```

应该看到文件大小约 167MB。

