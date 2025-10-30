# 前端工具库使用指南

## 📚 概述

前端工具库 (`/static/js/utils.js`) 提供了一套完整的前端开发工具，包括：

- **Loading管理器** - 统一的加载状态管理
- **Toast通知** - 美观的消息提示系统
- **HTTP客户端** - 带缓存和错误处理的请求封装
- **表单验证** - 实时表单验证工具
- **工具函数** - 防抖、节流、图片压缩等
- **错误码映射** - 用户友好的错误消息

## 🚀 快速开始

### 1. 引入工具库

在HTML模板中引入：

```html
<!-- 在</head>前添加 -->
<script src="{{ url_for('static', path='js/utils.js') }}"></script>

<!-- 或在</body>前添加 -->
<script src="/static/js/utils.js"></script>
```

### 2. 访问全局对象

所有工具通过 `window.AppUtils` 访问：

```javascript
const { Loading, Toast, Utils, Http, FormValidator } = window.AppUtils;
```

---

## 💫 Loading管理器

### 基本用法

```javascript
// 显示loading
Loading.show('处理中...', '请稍候');

// 隐藏loading
Loading.hide();

// 重置loading计数
Loading.reset();
```

### 实际示例

```javascript
async function uploadFile(file) {
    Loading.show('上传中...', '请勿关闭页面');
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        Loading.hide();
        Toast.success('上传成功！');
        return data;
    } catch (error) {
        Loading.hide();
        Toast.error(error.message);
    }
}
```

### 特性

- ✅ 支持嵌套调用（计数器机制）
- ✅ 自动居中显示
- ✅ 支持主消息和副消息
- ✅ 优雅的动画效果

---

## 🎉 Toast通知

### 基本用法

```javascript
// 成功消息
Toast.success('操作成功！');

// 错误消息
Toast.error('操作失败，请重试');

// 警告消息
Toast.warning('请注意...');

// 信息消息
Toast.info('提示信息');
```

### 高级用法

```javascript
// 自定义显示时长（毫秒）
Toast.success('自定义3秒显示', 3000);

// 永久显示（需手动关闭）
Toast.error('需手动关闭的消息', 0);

// 获取toast元素进行操作
const toast = Toast.success('操作成功');
setTimeout(() => toast.remove(), 5000);
```

### 样式说明

- `success` - 绿色，表示成功操作
- `error` - 红色，表示错误
- `warning` - 黄色，表示警告
- `info` - 蓝色，表示一般信息

---

## 🌐 HTTP客户端

### 基本用法

```javascript
// GET请求
const data = await Http.get('/api/histories');

// GET请求（带缓存，1分钟内复用）
const cachedData = await Http.get('/api/settings', true);

// POST请求
const result = await Http.post('/api/quote/calculate', {
    length: 10,
    width: 5
});

// DELETE请求
await Http.delete('/api/history/123');
```

### 错误处理

```javascript
try {
    const data = await Http.get('/api/data');
    console.log(data);
} catch (error) {
    // error.message 会自动映射为用户友好的消息
    Toast.error(error.message);
}
```

### 自定义请求

```javascript
// 使用原始request方法
const response = await Http.request('/api/custom', {
    method: 'PUT',
    headers: { 'X-Custom-Header': 'value' },
    body: JSON.stringify({ data: 'test' }),
    timeout: 30000 // 30秒超时
});
```

### 缓存管理

```javascript
// 清除所有缓存
Http.clearCache();
```

---

## ✅ 表单验证

### 数字验证

```javascript
// 验证数字范围
const result = FormValidator.validateNumber(value, 0, 100, '长度');
if (!result.valid) {
    console.error(result.error); // "长度不能小于0"
}
```

### 实时验证

```javascript
// 为输入框添加实时验证
const lengthInput = document.getElementById('length');
FormValidator.attachRealTimeValidation(lengthInput, (value) => {
    return FormValidator.validateNumber(value, 0.1, 1000, '长度');
});
```

### 错误标记

```javascript
// 手动标记错误
const input = document.getElementById('myInput');
FormValidator.markError(input, '输入无效');

// 清除错误标记
FormValidator.clearError(input);
```

### 完整示例

```javascript
document.getElementById('quoteForm').addEventListener('submit', (e) => {
    e.preventDefault();
    
    const lengthInput = document.querySelector('[name="length"]');
    const result = FormValidator.validateNumber(
        lengthInput.value, 
        0.1, 
        1000, 
        '产品长度'
    );
    
    if (!result.valid) {
        FormValidator.markError(lengthInput, result.error);
        Toast.error(result.error);
        return;
    }
    
    FormValidator.clearError(lengthInput);
    // 继续处理表单...
});
```

---

## 🛠️ 工具函数

### 防抖 (Debounce)

```javascript
// 搜索输入防抖
const searchInput = document.getElementById('search');
const debouncedSearch = Utils.debounce((value) => {
    console.log('搜索:', value);
    // 执行搜索
}, 300); // 300ms延迟

searchInput.addEventListener('input', (e) => {
    debouncedSearch(e.target.value);
});
```

### 节流 (Throttle)

```javascript
// 滚动事件节流
const handleScroll = Utils.throttle(() => {
    console.log('滚动位置:', window.scrollY);
}, 1000); // 1秒内最多执行1次

window.addEventListener('scroll', handleScroll);
```

### 图片压缩

```javascript
// 压缩图片（自动）
const fileInput = document.getElementById('imageInput');
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    
    Loading.show('压缩图片中...');
    try {
        const compressedFile = await Utils.compressImage(file);
        console.log('原始大小:', Utils.formatFileSize(file.size));
        console.log('压缩后:', Utils.formatFileSize(compressedFile.size));
        Loading.hide();
        Toast.success('图片压缩完成');
    } catch (error) {
        Loading.hide();
        Toast.error('图片压缩失败');
    }
});

// 自定义压缩参数
const compressed = await Utils.compressImage(
    file,
    1920,  // 最大宽度
    1920,  // 最大高度
    0.8    // 质量 (0-1)
);
```

### 文件验证

```javascript
const validation = Utils.validateImageFile(file);
if (!validation.valid) {
    Toast.error(validation.error);
    return;
}
// 继续处理...
```

### 格式化

```javascript
// 格式化文件大小
Utils.formatFileSize(1024); // "1 KB"
Utils.formatFileSize(1048576); // "1 MB"

// 格式化日期
Utils.formatDate(new Date()); // "2025-10-31 12:30:45"
Utils.formatDate(new Date(), 'YYYY-MM-DD'); // "2025-10-31"
```

---

## 🎨 配置选项

所有配置在 `AppUtils.CONFIG` 中：

```javascript
const config = window.AppUtils.CONFIG;

console.log(config.MAX_UPLOAD_SIZE); // 10485760 (10MB)
console.log(config.ALLOWED_IMAGE_TYPES); // ['image/jpeg', 'image/jpg', ...]
console.log(config.IMAGE_COMPRESS_QUALITY); // 0.8
```

### 可用配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MAX_UPLOAD_SIZE` | 10MB | 最大上传文件大小 |
| `ALLOWED_IMAGE_TYPES` | JPEG/PNG/GIF/WebP | 允许的图片类型 |
| `IMAGE_COMPRESS_MAX_WIDTH` | 1920 | 压缩后最大宽度 |
| `IMAGE_COMPRESS_MAX_HEIGHT` | 1920 | 压缩后最大高度 |
| `IMAGE_COMPRESS_QUALITY` | 0.8 | 压缩质量 (0-1) |
| `DEBOUNCE_DELAY` | 300ms | 默认防抖延迟 |
| `REQUEST_TIMEOUT` | 60s | 请求超时时间 |
| `ANALYSIS_TIMEOUT` | 5min | 图像分析超时 |

---

## 📝 错误消息映射

访问 `AppUtils.ERROR_MESSAGES` 获取所有错误消息：

```javascript
const errors = window.AppUtils.ERROR_MESSAGES;

console.log(errors.FILE_TOO_LARGE); // "文件大小超过限制（最大10MB）"
console.log(errors['413']); // "文件大小超过服务器限制（10MB）"
```

### 支持的错误码

- `FILE_TOO_LARGE` - 文件过大
- `INVALID_FORMAT` - 格式无效
- `NETWORK_ERROR` - 网络错误
- `TIMEOUT` - 请求超时
- `400/401/403/404/500/503/504` - HTTP状态码

---

## 🎯 完整示例：图片上传

```javascript
async function handleImageUpload(file) {
    // 1. 验证文件
    const validation = Utils.validateImageFile(file);
    if (!validation.valid) {
        Toast.error(validation.error);
        return;
    }

    Loading.show('处理图片中...', '正在压缩');

    try {
        // 2. 压缩图片
        const compressedFile = await Utils.compressImage(file);
        Toast.info(`图片已压缩: ${Utils.formatFileSize(file.size)} → ${Utils.formatFileSize(compressedFile.size)}`);

        // 3. 上传
        const formData = new FormData();
        formData.append('file', compressedFile);

        Loading.show('上传中...', '请稍候');
        const response = await fetch('/api/upload/image', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(ERROR_MESSAGES[response.status] || '上传失败');
        }

        const data = await response.json();
        Loading.hide();
        Toast.success('上传成功！');
        return data;

    } catch (error) {
        Loading.hide();
        Toast.error(error.message);
        throw error;
    }
}
```

---

## 🎓 最佳实践

### 1. 始终使用try-catch

```javascript
try {
    const data = await Http.get('/api/data');
    // 处理数据
} catch (error) {
    Toast.error(error.message);
}
```

### 2. 合理使用Loading

```javascript
// ✅ 好的做法
Loading.show('加载中...');
try {
    await someAsyncOperation();
} finally {
    Loading.hide(); // 确保一定会隐藏
}

// ❌ 不好的做法
Loading.show();
await someAsyncOperation();
Loading.hide(); // 如果出错，loading不会隐藏
```

### 3. 防抖搜索

```javascript
const search = Utils.debounce(async (keyword) => {
    const results = await Http.get(`/api/search?q=${keyword}`, true);
    displayResults(results);
}, 300);
```

### 4. 表单验证

```javascript
// 页面加载时添加验证
document.querySelectorAll('input[type="number"]').forEach(input => {
    const min = parseFloat(input.min);
    const max = parseFloat(input.max);
    const name = input.labels[0]?.textContent || '此字段';
    
    FormValidator.attachRealTimeValidation(input, (value) => {
        return FormValidator.validateNumber(value, min, max, name);
    });
});
```

---

## 🔧 自定义扩展

### 扩展HTTP客户端

```javascript
// 添加自定义方法
Http.uploadWithProgress = async function(url, formData, onProgress) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable && onProgress) {
                onProgress(e.loaded / e.total * 100);
            }
        });
        xhr.addEventListener('load', () => resolve(JSON.parse(xhr.responseText)));
        xhr.addEventListener('error', () => reject(new Error('上传失败')));
        xhr.open('POST', url);
        xhr.send(formData);
    });
};
```

### 扩展Toast

```javascript
// 添加确认对话框
Toast.confirm = function(message, onConfirm) {
    const toast = this.warning(message, 0);
    const buttons = document.createElement('div');
    buttons.className = 'mt-2 flex space-x-2';
    buttons.innerHTML = `
        <button class="px-3 py-1 bg-blue-600 text-white rounded text-sm">确认</button>
        <button class="px-3 py-1 bg-gray-300 text-gray-700 rounded text-sm">取消</button>
    `;
    toast.querySelector('.flex-1').appendChild(buttons);
    // 添加事件处理...
};
```

---

## 📱 响应式支持

工具库已优化移动端：

- Toast自动适配屏幕宽度
- Loading居中显示
- 触摸友好的交互

---

## 🐛 故障排查

### Loading不消失

```javascript
// 使用reset强制清除
Loading.reset();
```

### Toast不显示

```javascript
// 检查容器是否存在
console.log(document.getElementById('toastContainer'));

// 手动初始化
Toast.init();
```

### 图片压缩失败

```javascript
// 检查文件类型
const validation = Utils.validateImageFile(file);
console.log(validation);

// 降低压缩质量
const compressed = await Utils.compressImage(file, 1920, 1920, 0.9);
```

---

## 📚 参考资料

- [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)
- [File API](https://developer.mozilla.org/en-US/docs/Web/API/File)

---

*最后更新：2025-10-31*

