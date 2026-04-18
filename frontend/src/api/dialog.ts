import { post, get, del } from '../utils/request'






export const diolog_list = () => {
    return get('/api/v1/diolog_list')
}
export const create_dialog = (data) => {
    return post('/api/v1/create_dialog', {
        ...data
    })
}


export const del_dialog = (dialog_id) => {
    return del('/api/v1/diolog_del', {
        dialog_id
    })
}
