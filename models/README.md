# rembg 模型文件下载说明

## 下载模型到仓库

运行以下命令将 rembg 模型下载到项目的 `models/` 目录：

```bash
python scripts/download_model_to_repo.py
```

模型文件将保存到 `models/u2net.onnx`（约 176MB）。

## 使用本地模型

下载完成后，代码会自动检测并使用仓库中的模型文件：

1. **本地开发**：代码会自动检测 `models/u2net.onnx` 并使用
2. **Docker 部署**：模型文件会被复制到容器中，代码会自动使用

## 提交到 Git（可选）

模型文件较大（约176MB），可以选择：

- **提交到仓库**：方便团队共享，但会增加仓库大小
- **不提交**：每个开发者自己下载，或使用 Git LFS

如果不想提交，在 `.gitignore` 中取消注释：
```
models/*.onnx
```

## 验证

下载完成后，验证文件：
```bash
ls -lh models/u2net.onnx
```

应该看到文件大小约 176MB。

