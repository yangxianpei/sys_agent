import { post } from '../utils/request'

export interface LoginForm {
    username: string
    password: string
}
export interface RegisterForm {
    email: string
}
// 登录接口
export const loginAPI = (data: LoginForm) => {
    return post('/api/v1/login', {
        username: data.username,
        password: data.password
    })
}


// 注册接口
export const reagisterAPI = (data: LoginForm & RegisterForm) => {
    return post('/api/v1/register', {
        username: data.username,
        password: data.password,
        email: data.email
    })
}