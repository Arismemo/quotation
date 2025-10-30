/**
 * 前端核心工具库
 * 包含：Loading管理、错误处理、工具函数等
 */

// ==================== 全局配置 ====================
const CONFIG = {
    MAX_UPLOAD_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'],
    ALLOWED_IMAGE_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    IMAGE_COMPRESS_MAX_WIDTH: 1920,
    IMAGE_COMPRESS_MAX_HEIGHT: 1920,
    IMAGE_COMPRESS_QUALITY: 0.8,
    DEBOUNCE_DELAY: 300,
    REQUEST_TIMEOUT: 60000, // 60秒
    ANALYSIS_TIMEOUT: 300000, // 5分钟
};

// ==================== 错误码映射 ====================
const ERROR_MESSAGES = {
    'FILE_TOO_LARGE': `文件大小超过限制（最大${CONFIG.MAX_UPLOAD_SIZE / (1024 * 1024)}MB）`,
    'INVALID_FORMAT': '不支持的文件格式',
    'INVALID_IMAGE': '无效的图片文件',
    'NETWORK_ERROR': '网络连接失败，请检查网络',
    'TIMEOUT': '请求超时，请重试',
    'SERVER_ERROR': '服务器错误，请稍后重试',
    '413': '文件大小超过服务器限制（10MB）',
    '400': '请求参数错误',
    '401': '未登录或登录已过期',
    '403': '无权限访问',
    '404': '请求的资源不存在',
    '500': '服务器内部错误',
    '503': '服务暂时不可用',
    '504': '请求超时',
};

// ==================== Loading管理器 ====================
class LoadingManager {
    constructor() {
        this.loadingCount = 0;
        this.init();
    }

    init() {
        // 创建全局loading元素
        if (!document.getElementById('globalLoading')) {
            const loadingHTML = `
                <div id="globalLoading" class="fixed inset-0 bg-black bg-opacity-50 z-[9999] hidden flex items-center justify-center">
                    <div class="bg-white rounded-lg p-6 shadow-xl max-w-sm mx-4">
                        <div class="flex items-center space-x-4">
                            <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
                            <div>
                                <div id="loadingMessage" class="text-lg font-medium text-gray-900">处理中...</div>
                                <div id="loadingSubMessage" class="text-sm text-gray-500 mt-1"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', loadingHTML);
        }
    }

    show(message = '处理中...', subMessage = '') {
        this.loadingCount++;
        const loadingEl = document.getElementById('globalLoading');
        const messageEl = document.getElementById('loadingMessage');
        const subMessageEl = document.getElementById('loadingSubMessage');
        
        if (messageEl) messageEl.textContent = message;
        if (subMessageEl) subMessageEl.textContent = subMessage;
        if (loadingEl) loadingEl.classList.remove('hidden');
    }

    hide() {
        this.loadingCount = Math.max(0, this.loadingCount - 1);
        if (this.loadingCount === 0) {
            const loadingEl = document.getElementById('globalLoading');
            if (loadingEl) loadingEl.classList.add('hidden');
        }
    }

    reset() {
        this.loadingCount = 0;
        this.hide();
    }
}

// 全局Loading实例
const Loading = new LoadingManager();

// ==================== Toast通知组件 ====================
class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        if (!document.getElementById('toastContainer')) {
            const container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'fixed top-4 right-4 z-[10000] space-y-2';
            document.body.appendChild(container);
            this.container = container;
        } else {
            this.container = document.getElementById('toastContainer');
        }
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        const icons = {
            success: `<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>`,
            error: `<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>`,
            warning: `<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>`,
            info: `<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>`
        };

        const colors = {
            success: 'bg-green-50 text-green-800 border-green-200',
            error: 'bg-red-50 text-red-800 border-red-200',
            warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
            info: 'bg-blue-50 text-blue-800 border-blue-200'
        };

        toast.className = `${colors[type]} border rounded-lg shadow-lg p-4 min-w-[300px] max-w-md animate-slide-in-right`;
        toast.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    ${icons[type]}
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-sm font-medium">${message}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 flex-shrink-0 text-gray-400 hover:text-gray-600">
                    <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
        `;

        this.container.appendChild(toast);

        if (duration > 0) {
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }

        return toast;
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// 全局Toast实例
const Toast = new ToastManager();

// ==================== 工具函数 ====================
const Utils = {
    /**
     * 防抖函数
     */
    debounce(func, delay = CONFIG.DEBOUNCE_DELAY) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    },

    /**
     * 节流函数
     */
    throttle(func, limit = 1000) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },

    /**
     * 验证文件类型
     */
    validateImageFile(file) {
        // 检查文件大小
        if (file.size > CONFIG.MAX_UPLOAD_SIZE) {
            return { valid: false, error: ERROR_MESSAGES.FILE_TOO_LARGE };
        }

        // 检查MIME类型
        if (!CONFIG.ALLOWED_IMAGE_TYPES.includes(file.type)) {
            return { valid: false, error: ERROR_MESSAGES.INVALID_FORMAT };
        }

        // 检查文件扩展名
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!CONFIG.ALLOWED_IMAGE_EXTENSIONS.includes(ext)) {
            return { valid: false, error: ERROR_MESSAGES.INVALID_FORMAT };
        }

        return { valid: true };
    },

    /**
     * 压缩图片
     */
    async compressImage(file, maxWidth = CONFIG.IMAGE_COMPRESS_MAX_WIDTH, maxHeight = CONFIG.IMAGE_COMPRESS_MAX_HEIGHT, quality = CONFIG.IMAGE_COMPRESS_QUALITY) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    let width = img.width;
                    let height = img.height;

                    // 计算新尺寸
                    if (width > height) {
                        if (width > maxWidth) {
                            height = height * (maxWidth / width);
                            width = maxWidth;
                        }
                    } else {
                        if (height > maxHeight) {
                            width = width * (maxHeight / height);
                            height = maxHeight;
                        }
                    }

                    canvas.width = width;
                    canvas.height = height;

                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    canvas.toBlob((blob) => {
                        if (blob) {
                            // 如果压缩后更大，使用原文件
                            if (blob.size < file.size) {
                                resolve(new File([blob], file.name, {
                                    type: file.type,
                                    lastModified: Date.now()
                                }));
                            } else {
                                resolve(file);
                            }
                        } else {
                            reject(new Error('图片压缩失败'));
                        }
                    }, file.type, quality);
                };
                img.onerror = () => reject(new Error(ERROR_MESSAGES.INVALID_IMAGE));
                img.src = e.target.result;
            };
            reader.onerror = () => reject(new Error(ERROR_MESSAGES.INVALID_IMAGE));
            reader.readAsDataURL(file);
        });
    },

    /**
     * 格式化日期
     */
    formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
        const d = new Date(date);
        const map = {
            'YYYY': d.getFullYear(),
            'MM': String(d.getMonth() + 1).padStart(2, '0'),
            'DD': String(d.getDate()).padStart(2, '0'),
            'HH': String(d.getHours()).padStart(2, '0'),
            'mm': String(d.getMinutes()).padStart(2, '0'),
            'ss': String(d.getSeconds()).padStart(2, '0')
        };
        return format.replace(/YYYY|MM|DD|HH|mm|ss/g, matched => map[matched]);
    }
};

// ==================== HTTP请求封装 ====================
class HttpClient {
    constructor() {
        this.cache = new Map();
    }

    /**
     * 通用请求方法
     */
    async request(url, options = {}) {
        const controller = new AbortController();
        const timeout = options.timeout || CONFIG.REQUEST_TIMEOUT;
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
            signal: controller.signal
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            clearTimeout(timeoutId);

            if (!response.ok) {
                const error = await this.handleErrorResponse(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            throw this.handleError(error);
        }
    }

    /**
     * GET请求（支持缓存）
     */
    async get(url, useCache = false) {
        if (useCache && this.cache.has(url)) {
            const cached = this.cache.get(url);
            if (Date.now() - cached.timestamp < 60000) { // 1分钟缓存
                return cached.data;
            }
        }

        const data = await this.request(url, { method: 'GET' });
        
        if (useCache) {
            this.cache.set(url, { data, timestamp: Date.now() });
        }

        return data;
    }

    /**
     * POST请求
     */
    async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE请求
     */
    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }

    /**
     * 处理错误响应
     */
    async handleErrorResponse(response) {
        let errorMessage = ERROR_MESSAGES[response.status] || ERROR_MESSAGES.SERVER_ERROR;
        
        try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
            // 无法解析错误响应，使用默认消息
        }

        return new Error(errorMessage);
    }

    /**
     * 处理网络错误
     */
    handleError(error) {
        if (error.name === 'AbortError') {
            return new Error(ERROR_MESSAGES.TIMEOUT);
        }
        if (error.message.includes('fetch') || error.message.includes('network')) {
            return new Error(ERROR_MESSAGES.NETWORK_ERROR);
        }
        return error;
    }

    /**
     * 清除缓存
     */
    clearCache() {
        this.cache.clear();
    }
}

// 全局HTTP客户端实例
const Http = new HttpClient();

// ==================== 表单验证 ====================
class FormValidator {
    /**
     * 验证数字输入
     */
    static validateNumber(value, min, max, fieldName = '字段') {
        const num = parseFloat(value);
        
        if (isNaN(num)) {
            return { valid: false, error: `${fieldName}必须是数字` };
        }
        
        if (min !== undefined && num < min) {
            return { valid: false, error: `${fieldName}不能小于${min}` };
        }
        
        if (max !== undefined && num > max) {
            return { valid: false, error: `${fieldName}不能大于${max}` };
        }
        
        return { valid: true };
    }

    /**
     * 高亮错误输入框
     */
    static markError(inputElement, errorMessage) {
        inputElement.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        inputElement.classList.remove('border-gray-300');
        
        // 添加错误提示
        const errorId = `${inputElement.id || inputElement.name}-error`;
        let errorEl = document.getElementById(errorId);
        
        if (!errorEl) {
            errorEl = document.createElement('p');
            errorEl.id = errorId;
            errorEl.className = 'mt-1 text-sm text-red-600';
            inputElement.parentElement.appendChild(errorEl);
        }
        
        errorEl.textContent = errorMessage;
    }

    /**
     * 清除错误标记
     */
    static clearError(inputElement) {
        inputElement.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        inputElement.classList.add('border-gray-300');
        
        const errorId = `${inputElement.id || inputElement.name}-error`;
        const errorEl = document.getElementById(errorId);
        if (errorEl) {
            errorEl.remove();
        }
    }

    /**
     * 实时验证输入
     */
    static attachRealTimeValidation(inputElement, validationFunc) {
        inputElement.addEventListener('input', () => {
            const result = validationFunc(inputElement.value);
            if (result.valid) {
                this.clearError(inputElement);
            } else {
                this.markError(inputElement, result.error);
            }
        });

        inputElement.addEventListener('blur', () => {
            const result = validationFunc(inputElement.value);
            if (!result.valid) {
                this.markError(inputElement, result.error);
            }
        });
    }
}

// ==================== 导出全局对象 ====================
window.AppUtils = {
    Loading,
    Toast,
    Utils,
    Http,
    FormValidator,
    CONFIG,
    ERROR_MESSAGES
};

// ==================== CSS动画 ====================
if (!document.getElementById('utilsStyles')) {
    const style = document.createElement('style');
    style.id = 'utilsStyles';
    style.textContent = `
        @keyframes slide-in-right {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        .animate-slide-in-right {
            animation: slide-in-right 0.3s ease-out;
        }
    `;
    document.head.appendChild(style);
}

console.log('✓ 前端工具库加载完成');

