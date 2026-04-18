import { post, get, del } from '../utils/request'

export const Upload = (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return post('/api/v1/upload', formData)
}

export interface Atool {
    name: string,
    logo: string,
    auth_config?: object,
    description: string,
    openai_schema: {
        openapi: string,
        info: object,
        servers: Array<{ url: string }>
        paths: object
    }
}

export const regist_tool = (data: Atool) => {
    return post('/api/v1/regist_tool', {
        ...data
    })
}

export const get_tool_list = () => {
    return get('/api/v1/tool_list')
}


export const del_tool = (tool_id: string) => {
    return del('/api/v1/del_tool', {
        tool_id
    })
}

export const modify_tool = (data: Atool) => {
    return post('/api/v1/modify_tool', {
        ...data
    })
}
