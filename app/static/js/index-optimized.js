/**
 * index.html 优化后的关键函数
 * 使用新工具库优化原有功能
 */

(function() {
    'use strict';
    
    // 等待工具库加载
    function getAppUtils() {
        if (!window.AppUtils) {
            console.warn('AppUtils not loaded yet, functions may not work');
            return {
                Loading: { show: () => {}, hide: () => {} },
                Toast: { error: () => {}, success: () => {}, info: () => {}, warning: () => {} },
                Utils: { 
                    validateImageFile: () => ({ valid: true }), 
                    compressImage: (file) => Promise.resolve(file),
                    formatFileSize: (size) => `${size} bytes`,
                    debounce: (fn) => fn
                },
                Http: { 
                    request: (...args) => fetch(...args).then(r => r.json()),
                    post: (url, body) => fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(r => r.json()),
                    get: (url) => fetch(url).then(r => r.json()),
                    delete: (url) => fetch(url, { method: 'DELETE' }).then(r => r.json()),
                    clearCache: () => {}
                },
                FormValidator: { 
                    attachRealTimeValidation: () => {},
                    validateNumber: () => ({ valid: true })
                }
            };
        }
        return window.AppUtils;
    }
    
    const AppUtils = getAppUtils();
    const { Loading, Toast, Utils, Http, FormValidator } = AppUtils;

// ==================== 优化后的图片上传函数 ====================

/**
 * 优化的图片上传（带压缩和验证）
 */
async function uploadImageWithCompression(file, uploadEndpoint = '/api/upload/image') {
    // 1. 验证文件
    const validation = Utils.validateImageFile(file);
    if (!validation.valid) {
        Toast.error(validation.error);
        return null;
    }

    Loading.show('处理图片中...', '正在压缩');

    try {
        // 2. 压缩图片
        const compressedFile = await Utils.compressImage(file);
        const originalSize = Utils.formatFileSize(file.size);
        const compressedSize = Utils.formatFileSize(compressedFile.size);
        
        if (compressedFile.size < file.size) {
            Toast.info(`图片已压缩: ${originalSize} → ${compressedSize}`, 2000);
        }

        // 3. 上传
        Loading.show('上传中...', '请稍候');
        const formData = new FormData();
        formData.append('file', compressedFile);

        const data = await Http.request(uploadEndpoint, {
            method: 'POST',
            body: formData,
            timeout: 60000
        });

        Loading.hide();
        Toast.success('上传成功！');
        return data;

    } catch (error) {
        Loading.hide();
        Toast.error(error.message || '上传失败');
        throw error;
    }
}

// ==================== 优化的API请求函数 ====================

/**
 * 计算报价（使用Http客户端）
 */
async function calculateQuoteOptimized(payload) {
    Loading.show('计算中...', '请稍候');
    try {
        const result = await Http.post('/api/quote/calculate', payload);
        Loading.hide();
        return result;
    } catch (error) {
        Loading.hide();
        Toast.error(error.message || '计算失败');
        throw error;
    }
}

/**
 * 加载历史记录（使用Http客户端和缓存）
 */
async function loadHistoryOptimized(params = {}) {
    try {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `/api/history?${queryString}` : '/api/history';
        
        // 启用缓存，减少重复请求
        const data = await Http.get(url, true);
        return data;
    } catch (error) {
        Toast.error(error.message || '加载历史记录失败');
        throw error;
    }
}

/**
 * 加载收藏（使用Http客户端和缓存）
 */
async function loadFavoritesOptimized() {
    try {
        // 启用缓存
        const data = await Http.get('/api/favorites', true);
        return data;
    } catch (error) {
        Toast.error(error.message || '加载收藏失败');
        throw error;
    }
}

/**
 * 收藏/取消收藏（使用Http客户端）
 */
async function toggleFavoriteOptimized(historyId, isFavorited) {
    Loading.show('处理中...');
    try {
        if (isFavorited) {
            // 取消收藏
            const favorites = await Http.get('/api/favorites', true);
            const favorite = favorites.find(f => f.history_id === historyId);
            if (favorite) {
                await Http.delete(`/api/favorites/${favorite.id}`);
                Toast.success('已取消收藏');
            }
        } else {
            // 创建收藏
            await Http.post('/api/favorites', {
                history_id: historyId,
                name: '未命名收藏'
            });
            Toast.success('收藏成功');
        }
        
        // 清除缓存，强制刷新
        Http.clearCache();
        
        Loading.hide();
        // 重新加载收藏列表
        if (typeof loadFavorites === 'function') {
            await loadFavorites();
        }
    } catch (error) {
        Loading.hide();
        Toast.error(error.message || '操作失败');
    }
}

/**
 * 删除收藏（使用Http客户端）
 */
async function removeFavoriteOptimized(favoriteId) {
    if (!confirm('确认删除该收藏？')) return;
    
    Loading.show('删除中...');
    try {
        await Http.delete(`/api/favorites/${favoriteId}`);
        Http.clearCache(); // 清除缓存
        Toast.success('删除成功');
        Loading.hide();
        
        // 重新加载
        if (typeof loadFavorites === 'function') {
            await loadFavorites();
        }
    } catch (error) {
        Loading.hide();
        Toast.error(error.message || '删除失败');
    }
}

/**
 * 保存收藏备注（使用Http客户端）
 */
async function saveFavoriteNoteOptimized(favoriteId, name, imagePath) {
    Loading.show('保存中...');
    try {
        await Http.request(`/api/favorites/${favoriteId}`, {
            method: 'PUT',
            body: JSON.stringify({
                name: name || null,
                image_path: imagePath || null
            })
        });
        
        Http.clearCache(); // 清除缓存
        Toast.success('保存成功');
        Loading.hide();
        
        // 重新加载
        if (typeof loadFavorites === 'function') {
            await loadFavorites();
        }
    } catch (error) {
        Loading.hide();
        Toast.error(error.message || '保存失败');
    }
}

/**
 * 批量删除历史记录（使用Http客户端）
 */
async function batchDeleteHistoryOptimized(historyIds) {
    if (!historyIds || historyIds.length === 0) {
        Toast.warning('请选择要删除的记录');
        return;
    }
    
    if (!confirm(`确认删除 ${historyIds.length} 条记录？`)) return;
    
    Loading.show('删除中...', `正在删除 ${historyIds.length} 条记录`);
    try {
        const result = await Http.post('/api/history/batch-delete', {
            history_ids: historyIds
        });
        
        Http.clearCache(); // 清除缓存
        Loading.hide();
        Toast.success(result.message || `成功删除 ${result.deleted_count} 条记录`);
        
        // 重新加载
        if (typeof loadHistory === 'function') {
            await loadHistory();
        }
    } catch (error) {
        Loading.hide();
        Toast.error(error.message || '批量删除失败');
    }
}

// ==================== 表单验证优化 ====================

/**
 * 初始化表单实时验证
 */
function initFormValidation() {
    if (!FormValidator || !FormValidator.attachRealTimeValidation) {
        console.warn('FormValidator not available');
        return;
    }
    
    // 验证数字输入
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        const min = parseFloat(input.min);
        const max = parseFloat(input.max);
        const fieldName = input.labels?.[0]?.textContent?.replace(/\(.*\)/, '').trim() || '此字段';
        
        FormValidator.attachRealTimeValidation(input, (value) => {
            if (!value) return { valid: true }; // 允许空值
            return FormValidator.validateNumber(value, min, max, fieldName);
        });
    });
}

// ==================== 搜索防抖优化 ====================

/**
 * 创建防抖搜索函数
 */
function createDebouncedSearch(searchFunction, delay = 300) {
    return Utils.debounce(searchFunction, delay);
}

/**
 * 防抖的收藏搜索
 */
function debouncedFavoriteSearch(keyword) {
    if (!Utils || !Utils.debounce) {
        // 降级到直接执行
        const favorites = document.querySelectorAll('#favoriteList > div');
        const lowerKeyword = keyword.toLowerCase();
        favorites.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(lowerKeyword) ? '' : 'none';
        });
        return;
    }
    
    // 使用防抖版本（首次调用时创建）
    if (!debouncedFavoriteSearch._debouncedFn) {
        debouncedFavoriteSearch._debouncedFn = Utils.debounce((keyword) => {
            const favorites = document.querySelectorAll('#favoriteList > div');
            const lowerKeyword = keyword.toLowerCase();
            favorites.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(lowerKeyword) ? '' : 'none';
            });
        }, 300);
    }
    
    debouncedFavoriteSearch._debouncedFn(keyword);
}

// ==================== 图像分析优化 ====================

/**
 * 优化的图像分析
 */
async function analyzeImageOptimized(imagePath, enableAreaRatio = true, enableColorCount = false, method = 'opencv') {
    Loading.show('分析中...', '请耐心等待');
    
    try {
        const promises = [];
        
        if (enableAreaRatio) {
            promises.push(
                Http.post('/api/analyze/area-ratio', {
                    image_path: imagePath,
                    method: method
                }, {
                    timeout: method === 'rembg' ? 300000 : 120000
                }).then(result => ({ type: 'area', result }))
            );
        }
        
        if (enableColorCount) {
            promises.push(
                Http.post('/api/analyze/colors', {
                    image_path: imagePath,
                    method: method
                }, {
                    timeout: method === 'rembg' ? 300000 : 120000
                }).then(result => ({ type: 'colors', result }))
            );
        }
        
        const results = await Promise.all(promises);
        Loading.hide();
        
        return results.reduce((acc, { type, result }) => {
            acc[type] = result;
            return acc;
        }, {});
        
    } catch (error) {
        Loading.hide();
        Toast.error(error.message || '图像分析失败');
        throw error;
    }
}

// ==================== 导出优化函数 ====================

    // 导出到全局，供index.html使用
    window.OptimizedFunctions = {
        uploadImageWithCompression,
        calculateQuoteOptimized,
        loadHistoryOptimized,
        loadFavoritesOptimized,
        toggleFavoriteOptimized,
        removeFavoriteOptimized,
        saveFavoriteNoteOptimized,
        batchDeleteHistoryOptimized,
        initFormValidation,
        createDebouncedSearch,
        debouncedFavoriteSearch,
        analyzeImageOptimized
    };

    console.log('✓ 优化函数已加载');
    
    // 如果已经DOMContentLoaded，立即初始化表单验证
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(() => {
            if (typeof initFormValidation === 'function') {
                initFormValidation();
            }
        }, 100);
    }
    
})(); // 立即执行函数结束

