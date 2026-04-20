import { post, get, del } from '../utils/request'


export const get_model = () => {
    return get('/api/v1/get_model')
}


export const get_agent = () => {
    return get('/api/v1/get_agent')
}
export const usage_count = (data) => {
    return post('/api/v1/usage_count', {
        ...data
    })
}

export const usage = (data) => {
    return post('/api/v1/usage', {
        ...data
    })
}