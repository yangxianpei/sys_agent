

import { post, get, del } from '../utils/request'

interface Regist_mcp {
    mcp_name: string,
    mcpServers: object,
    logo?: string
}
interface Modify_mcp {
    mcp_id: string,
    mcp_name: string,
    mcpServers: object,
    logo?: string
}


export const regist_mcp_api = (data: Regist_mcp) => {
    return post('/api/v1/regist_mcp', {
        mcp_name: data.mcp_name,
        mcpServers: data.mcpServers,
        logo: data.logo
    })
}

//修改
export const modify_mcp_api = (data: Modify_mcp) => {
    return post('/api/v1/regist_mcp_modify', {
        mcp_id: data.mcp_id,
        mcp_name: data.mcp_name,
        mcpServers: data.mcpServers,
        logo: data.logo
    })
}


export const get_mcp_list = () => {
    return get('/api/v1/regist_mcp')
}


export const del_mcp_list = (mcp_id: string) => {
    return del('/api/v1/regist_mcp', {
        "mcp_id": mcp_id
    })
}
