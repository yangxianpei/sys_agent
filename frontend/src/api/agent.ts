import { post, get, del } from '../utils/request'






export const get_agent_all = () => {
    return get('/api/v1/get_agent_all')
}



export const create_agent = (data) => {
    return post('/api/v1/create_agent', {
        ...data
    })
}


export const get_agent_by_id = (id) => {
    return get('/api/v1/get_agent_by_id', {
        params: {
            id: id
        }
    })
}



export const agent_all_list = () => {
    return get('/api/v1/agent_all_list')
}

export const modfy_agent = (data) => {
    return post('/api/v1/modfy_agent', {
        ...data
    })
}



export const del_agent = (agent_id: string) => {
    return del('/api/v1/del_agent', {
        agent_id
    })
}


export const search_agent = ({ name }) => {
    return post('/api/v1/search_agent', {
        name
    })
}
