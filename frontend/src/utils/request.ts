// axios的封装处理
import axios, { type AxiosRequestConfig } from 'axios'
import { ApiError, type ApiResponse } from '../types/api'
// 1.根域名配置
// 2.超时时间
// 3.请求拦截器,响应拦截器

const request = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 10000  // 全局超时10秒，对于耗时操作单独设置
})

/** 与后端约定：这些 code 表示 HTTP 成功且业务成功 */
function isBusinessSuccess(code: number): boolean {
    return code === 200 || code === 0
}

function isApiEnvelope(payload: unknown): payload is ApiResponse {
    return (
        payload !== null &&
        typeof payload === 'object' &&
        'code' in payload &&
        'message' in payload &&
        'data' in payload
    )
}

// 添加请求拦截器
request.interceptors.request.use(function (config) {
    // 添加token到请求头
    const token = localStorage.getItem('token');
    if (token) {
        // 确保headers对象存在
        config.headers = config.headers || {};
        config.headers['Authorization'] = `Bearer ${token}`;
    }

    return config;
}, function (error) {
    // 对请求错误做些什么
    console.error('请求拦截器错误:', error)
    return Promise.reject(error);
});

// 添加响应拦截器：统一解析 { message, data, code }
request.interceptors.response.use(function (response) {
    const payload = response.data
    if (isApiEnvelope(payload) && !isBusinessSuccess(payload.code)) {
        return Promise.reject(
            new ApiError(payload.code, payload.message, payload.data)
        )
    }
    return response;
}, function (error) {
    const body = error.response?.data
    if (body && isApiEnvelope(body)) {
        if (body.code == 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('userInfo');
            window.location.href = '/login';
        }
        return Promise.reject(
            new ApiError(body.code, body.message, body.data)
        )
    }

    return Promise.reject(body.detail[0].msg);
});

/**
 * POST，返回与后端一致的 ApiResponse<T>（不再包一层 AxiosResponse）
 */
function post<T = any>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
): Promise<ApiResponse<T>> {
    return request.post<ApiResponse<T>>(url, data, config).then((res) => res.data)
}

/**
 * GET，返回与后端一致的 ApiResponse<T>（query 放在 config.params）
 */
function get<T = any>(
    url: string,
    config?: AxiosRequestConfig
): Promise<ApiResponse<T>> {
    return request.get<ApiResponse<T>>(url, config).then((res) => res.data)
}

function del<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
): Promise<ApiResponse<T>> {
    return request.delete<ApiResponse<T>>(url, {
        ...config,
        data
    }).then((res) => res.data)
}
export { request, post, get, del }
