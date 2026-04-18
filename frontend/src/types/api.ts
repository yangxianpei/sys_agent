/** 后端统一响应结构 */
export interface ApiResponse<T = any> {
  message: string
  data: T
  code: number
}

/** 业务码非成功时，拦截器会 reject 此错误 */
export class ApiError extends Error {
  readonly code: number
  readonly data?: unknown

  constructor(code: number, message: string, data?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.data = data
  }
}



export interface User {
  password: string
  username: string
  is_active: boolean,
  id: string,
  token?: string
}