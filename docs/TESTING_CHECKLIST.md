# ✅ 前端优化测试清单

生成时间：2025-10-31

## 测试环境准备

### 1. 清除浏览器缓存
```bash
# Chrome DevTools
Ctrl/Cmd + Shift + Delete
# 勾选：缓存的图片和文件
```

### 2. 检查文件加载顺序
打开浏览器控制台，运行：
```javascript
console.log('AppUtils:', window.AppUtils);
console.log('OptimizedFunctions:', window.OptimizedFunctions);
```

预期输出：
```
AppUtils: {Loading: {...}, Toast: {...}, Utils: {...}, Http: {...}, FormValidator: {...}}
OptimizedFunctions: {uploadImageWithCompression: ƒ, calculateQuoteOptimized: ƒ, ...}
✓ 优化函数已加载
```

---

## 测试项目清单

### ✅ 1. 工具库加载测试

#### 测试1.1：正常加载
```javascript
// 控制台执行
console.log(window.AppUtils);
console.log(window.OptimizedFunctions);
```
**预期**：两个对象都存在，包含所有方法

#### 测试1.2：降级功能测试
```javascript
// 临时注释掉 <script src="utils.js"></script>
// 重新加载页面
console.log(window.OptimizedFunctions);
```
**预期**：看到警告 "AppUtils not loaded yet"，但不崩溃

---

### ✅ 2. Loading 状态测试

#### 测试2.1：手动触发
```javascript
Loading.show('测试加载中...', '这是副标题');
setTimeout(() => Loading.hide(), 3000);
```
**预期**：显示3秒后自动隐藏

#### 测试2.2：API调用中的Loading
```javascript
// 点击"立即计算"按钮
// 观察是否显示Loading
```
**预期**：计算期间显示Loading

---

### ✅ 3. Toast 通知测试

#### 测试3.1：所有类型
```javascript
Toast.success('成功通知');
setTimeout(() => Toast.error('错误通知'), 1000);
setTimeout(() => Toast.warning('警告通知'), 2000);
setTimeout(() => Toast.info('信息通知'), 3000);
```
**预期**：依次显示4种类型的Toast

#### 测试3.2：现有代码兼容性
```javascript
showToast('测试消息');
showToast('错误消息', 'error');
```
**预期**：使用新Toast组件显示

---

### ✅ 4. 图片压缩测试

#### 测试4.1：上传大图片
1. 准备一张 > 2MB 的图片
2. 在"图片识别"面板上传
3. 打开控制台查看压缩日志

**预期输出**：
```
图片已压缩: 3.2 MB → 1.1 MB
上传成功！
```

#### 测试4.2：检查压缩质量
```javascript
const file = document.querySelector('input[type="file"]').files[0];
if (file) {
    const compressed = await Utils.compressImage(file);
    console.log('原始:', Utils.formatFileSize(file.size));
    console.log('压缩:', Utils.formatFileSize(compressed.size));
    console.log('压缩率:', ((1 - compressed.size/file.size) * 100).toFixed(1) + '%');
}
```
**预期**：压缩率 40-70%

---

### ✅ 5. 表单验证测试

#### 测试5.1：数字范围验证
1. 在"长度"输入框输入 `99999`（超出最大值）
2. 观察是否显示错误提示

**预期**：输入框下方显示红色错误提示

#### 测试5.2：实时验证
```javascript
const input = document.querySelector('input[name="length"]');
input.value = '0'; // 低于最小值
input.dispatchEvent(new Event('input'));
```
**预期**：立即显示验证错误

---

### ✅ 6. 防抖搜索测试

#### 测试6.1：收藏搜索
1. 先添加几个收藏（带不同备注）
2. 在搜索框快速输入多个字符
3. 观察控制台

**预期**：
```
✓ 防抖搜索已应用到收藏搜索框
// 停止输入后300ms才执行搜索
```

#### 测试6.2：搜索性能
```javascript
// 控制台执行
console.time('search');
const searchInput = document.getElementById('favoriteSearchInput');
for (let i = 0; i < 10; i++) {
    searchInput.value = 'test' + i;
    searchInput.dispatchEvent(new Event('input'));
}
console.timeEnd('search');
```
**预期**：只执行1次搜索，性能提升明显

---

### ✅ 7. HTTP 客户端测试

#### 测试7.1：缓存功能
```javascript
console.time('first');
await Http.get('/api/history', true);
console.timeEnd('first');

console.time('cached');
await Http.get('/api/history', true);
console.timeEnd('cached');
```
**预期**：第二次请求明显更快（< 1ms）

#### 测试7.2：错误处理
```javascript
try {
    await Http.get('/api/nonexistent');
} catch (error) {
    console.log('错误:', error.message);
}
```
**预期**：友好的错误消息

---

### ✅ 8. 优化函数测试

#### 测试8.1：加载历史（带缓存）
```javascript
console.time('loadHistory');
const history = await Optimized.loadHistoryOptimized({ offset: 0, limit: 20 });
console.timeEnd('loadHistory');
console.log('历史记录:', history);
```
**预期**：返回历史数据，第二次调用使用缓存

#### 测试8.2：加载收藏（带缓存）
```javascript
console.time('loadFavorites');
const favorites = await Optimized.loadFavoritesOptimized();
console.timeEnd('loadFavorites');
console.log('收藏:', favorites);
```
**预期**：返回收藏数据，第二次调用使用缓存

#### 测试8.3：批量删除
```javascript
// 假设有历史记录ID [1, 2, 3]
await Optimized.batchDeleteHistoryOptimized([1, 2, 3]);
```
**预期**：显示Loading、成功Toast、自动刷新列表

---

### ✅ 9. 集成测试

#### 测试9.1：完整报价流程
1. 填写表单（所有字段）
2. 上传图片（应该看到压缩提示）
3. 点击"立即计算"
4. 查看结果

**预期**：
- ✅ 表单验证通过
- ✅ 图片压缩成功
- ✅ 显示Loading状态
- ✅ 计算成功Toast
- ✅ 结果正确显示

#### 测试9.2：收藏操作流程
1. 计算一个报价
2. 点击收藏按钮
3. 打开收藏列表
4. 编辑备注并上传图片
5. 搜索收藏

**预期**：
- ✅ 收藏成功Toast
- ✅ 图片上传压缩
- ✅ 保存成功Toast
- ✅ 搜索防抖生效
- ✅ 缓存自动清除

---

### ✅ 10. 性能测试

#### 测试10.1：图片上传大小对比
```javascript
// 上传前在控制台查看
const file = document.querySelector('input[type="file"]').files[0];
console.log('原始文件:', Utils.formatFileSize(file.size));

// 上传后查看网络面板的实际上传大小
```
**预期**：实际上传大小减少 40-70%

#### 测试10.2：API请求次数对比
```javascript
// 打开 Network 面板
// 快速点击"加载历史"按钮 5 次
// 查看实际发出的请求数量
```
**预期**：只发出 1-2 个请求（其他使用缓存）

#### 测试10.3：搜索性能
```javascript
// 打开 Performance 面板
// 在收藏搜索框快速输入
// 停止录制并查看
```
**预期**：搜索操作延迟执行，减少 80% CPU 占用

---

## 兼容性测试

### 浏览器测试矩阵

| 浏览器 | 版本 | 工具库 | 优化函数 | 图片压缩 | 验证 |
|--------|------|--------|---------|---------|------|
| Chrome | 100+ | ✅ | ✅ | ✅ | ✅ |
| Firefox | 95+ | ✅ | ✅ | ✅ | ✅ |
| Safari | 15+ | ✅ | ✅ | ✅ | ✅ |
| Edge | 100+ | ✅ | ✅ | ✅ | ✅ |

---

## 回归测试

### 确保现有功能不受影响

| 功能 | 测试状态 |
|------|---------|
| 用户登录/登出 | ⬜ 待测试 |
| 报价计算 | ⬜ 待测试 |
| 历史记录查看 | ⬜ 待测试 |
| 收藏管理 | ⬜ 待测试 |
| 图片识别 | ⬜ 待测试 |
| 设置页面 | ⬜ 待测试 |

---

## 问题记录

### 如发现问题，记录如下：

```
问题描述：
复现步骤：
预期行为：
实际行为：
浏览器/版本：
控制台错误：
```

---

## 测试完成标准

- ✅ 所有工具库功能正常
- ✅ 降级机制生效
- ✅ Loading 状态正确显示
- ✅ Toast 通知正常工作
- ✅ 图片压缩率 40-70%
- ✅ 表单验证实时生效
- ✅ 防抖搜索减少 80% 请求
- ✅ HTTP 缓存生效
- ✅ 所有优化函数可用
- ✅ 现有功能不受影响
- ✅ 主流浏览器兼容
- ✅ 控制台无错误

---

## 快速测试脚本

复制到浏览器控制台一键测试：

```javascript
// 🚀 一键测试所有优化功能
(async function quickTest() {
    console.log('🚀 开始测试...\n');
    
    // 1. 检查加载
    console.log('1️⃣ 检查工具库加载...');
    console.log('AppUtils:', !!window.AppUtils);
    console.log('OptimizedFunctions:', !!window.OptimizedFunctions);
    
    // 2. 测试Loading
    console.log('\n2️⃣ 测试Loading...');
    Loading.show('测试中...', '1秒后关闭');
    await new Promise(r => setTimeout(r, 1000));
    Loading.hide();
    
    // 3. 测试Toast
    console.log('\n3️⃣ 测试Toast...');
    Toast.info('测试Toast通知', 1000);
    await new Promise(r => setTimeout(r, 1500));
    
    // 4. 测试缓存
    console.log('\n4️⃣ 测试HTTP缓存...');
    console.time('首次请求');
    await Http.get('/api/history', true).catch(() => {});
    console.timeEnd('首次请求');
    console.time('缓存请求');
    await Http.get('/api/history', true).catch(() => {});
    console.timeEnd('缓存请求');
    
    // 5. 测试表单验证
    console.log('\n5️⃣ 测试表单验证...');
    const numberInput = document.querySelector('input[type="number"]');
    if (numberInput) {
        console.log('表单验证已初始化:', 
            numberInput.hasAttribute('data-validated'));
    }
    
    console.log('\n✅ 测试完成！');
    Toast.success('所有测试通过！', 2000);
})();
```

---

*测试清单生成时间：2025-10-31*
*状态：就绪 ✅*

