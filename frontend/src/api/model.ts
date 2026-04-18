import { post, get, del } from '../utils/request'

interface Idata {
    llm_id?: string
    model: string
    base_url: string
    api_key: string
}

// 注册接口
export const reagisterAPI = (data: Idata) => {
    return post('/api/v1/regist_llm', {
        model: data.model,
        base_url: data.base_url,
        api_key: data.api_key
    })
}


export const get_llm_list = () => {
    return get('/api/v1/llm_list')
}


export const del_llm = (llm_id: string) => {
    return del('/api/v1/del_llm', {
        llm_id
    })
}


export const modify_tool = (data: Idata) => {
    return post('/api/v1/modify_llm', {
        ...data
    })
}
