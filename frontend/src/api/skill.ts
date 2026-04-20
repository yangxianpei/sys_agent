import { post, get, del } from '../utils/request'

export const reagisterAPI = (data) => {
    return post('/api/v1/regist_agent_skill', {
        name: data.name,
        description: data.description,
    })
}

export const list_agent_skill = () => {
    return get('/api/v1/list_agent_skill')
}

export const del_agent_skill = (id) => {
    return del('/api/v1/del_agent_skill', {
        id
    })
}

export const file_add = (data) => {
    return post('/api/v1/file/add', {
        ...data
    })
}
export const file_update = (data) => {
    return post('/api/v1/file/update', {
        ...data
    })
}