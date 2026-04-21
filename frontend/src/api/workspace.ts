import { request, post, get, del } from '../utils/request'
import { fetchEventSource } from '@microsoft/fetch-event-source'

function resolveApiUrl(path: string): string {
    const raw = import.meta.env.VITE_API_BASE_URL ?? ''
    const suffix = path.startsWith('/') ? path : `/${path}`
    const base = raw.replace(/\/$/, '')
    if (!base) {
        return suffix
    }
    return `${base}${suffix}`
}

export const session_list = () => {
    return get('/api/v1/session_list')
}

// 工作区日常对话接口
export interface WorkSpaceSimpleTask {
    query: string
    model_id: string
    plugins: string[]
    mcp_servers: string[]
    session_id?: string  // 会话ID，使用uuid4().hex格式
}

export const workspaceSimpleChatAPI = async (data: WorkSpaceSimpleTask) => {
    return request({
        url: '/api/v1/workspace/simple/chat',
        method: 'post',
        data,
        responseType: 'stream'
    })
}

// 工作区日常对话（SSE 流式）
export const workspaceSimpleChatStreamAPI = async (
    data: WorkSpaceSimpleTask,
    onMessage: (chunk: string) => void,
    onError?: (err: any) => void,
    onClose?: () => void
) => {
    const token = localStorage.getItem('token')
    const ctrl = new AbortController()
    let streamErrored = false


    try {
        // 与 workspaceSimpleChatAPI 保持一致；此前 /api/v1/simple/chat 易 404
        await fetchEventSource(resolveApiUrl('/api/v1/simple/chat'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token ? `Bearer ${token}` : ''
            },
            body: JSON.stringify(data),
            signal: ctrl.signal,
            openWhenHidden: true,
            onmessage(event) {
                console.log('📨 收到 SSE 原始消息:', event.data)
                if (!event.data) return
                try {
                    const parsed = JSON.parse(event.data)
                    console.log('📦 解析后的数据:', parsed)
                    // 兼容后端返回 {event:'task_result', data:{message}} 或 {data:{chunk}}
                    if (parsed?.data?.message !== undefined) {
                        // 只有当 message 不为空字符串时才调用回调
                        if (parsed.data.message !== '') {
                            console.log('📝 提取 message:', parsed.data.message)
                            onMessage(parsed.data.message)
                        } else {
                            console.log('⏭️ 跳过空 message')
                        }
                    } else if (parsed?.data?.chunk !== undefined) {
                        if (parsed.data.chunk !== '') {
                            console.log('📝 提取 chunk:', parsed.data.chunk)
                            onMessage(parsed.data.chunk)
                        } else {
                            console.log('⏭️ 跳过空 chunk')
                        }
                    } else {
                        console.warn('⚠️ 未识别的数据格式，跳过')
                    }
                } catch (_) {
                    console.warn('⚠️ JSON 解析失败，跳过:', event.data)
                }
            },
            onerror(err) {
                streamErrored = true
                console.error('❌ SSE 错误:', err)
                ctrl.abort()
                // fetch-event-source：onerror 不 throw 时会按间隔无限重连，必须抛错才能停止（onError 由外层 catch 统一调用）
                throw err
            },
            onclose() {
                console.log('✅ SSE 连接关闭')
                if (!streamErrored) {
                    onClose?.()
                }
            }
        })
    } catch (error: any) {
        streamErrored = true
        console.error('❌ fetchEventSource 异常:', error)
        if (error?.name !== 'AbortError') {
            onError?.(error)
        }
    }
}



export const get_session_by_id = (session_id: string) => {
    return post('/api/v1/get_session_by_id', {
        session_id
    })
}

export const del_session_by_id = (session_id: string) => {
    return del('/api/v1/del_session_by_id', {
        session_id
    })
}



// 生成灵寻的指导提示（流式）
export const generateLingSeekGuidePromptAPI = async (
    data: {
        query: string
        tools?: string[]
        web_search?: boolean
        mcp_servers?: string[]
    },
    onMessage: (data: any) => void,
    onError?: (error: any) => void,
    onClose?: () => void
) => {
    const token = localStorage.getItem('token')

    console.log('=== generateLingSeekGuidePromptAPI 调用 ===')
    console.log('参数:', data)
    console.log('Token:', token ? `${token.substring(0, 20)}...` : '无')


    const ctrl = new AbortController()

    try {
        await fetchEventSource(resolveApiUrl('/api/v1/lingseek/guide_prompt'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data),
            signal: ctrl.signal,
            openWhenHidden: true,
            onmessage(event) {
                console.log('📨 收到原始消息:', event.data)
                if (event.data) {
                    try {
                        // 后端返回的是 JSON 格式: { "event": "...", "data": { "chunk": "..." } }
                        const parsedData = JSON.parse(event.data)
                        console.log('📦 解析后的数据:', parsedData)

                        if (parsedData.data) {
                            const message = parsedData.data.message
                            console.log('📝 提取的 chunk:', message)
                            onMessage(message)
                        }
                    } catch (error) {
                        console.error('❌ JSON 解析失败:', error, '原始数据:', event.data)
                        // 如果解析失败，尝试直接使用原始数据
                        onMessage(event.data)
                    }
                }
            },
            onerror(err) {
                console.error('Stream 错误:', err)
                onError?.(err)
                // 不要 throw，而是中断连接
                ctrl.abort()
                throw err
            },
            onclose() {
                console.log('Stream 关闭')
                ctrl.abort()
                onClose?.()
            }
        })
    } catch (error) {
        console.error('fetchEventSource 异常:', error)
        if (error.name !== 'AbortError') {
            onError?.(error)
        }
    }
}


// 开始执行灵寻任务（流式）
export const startLingSeekTaskAPI = async (
    data: {
        query: string
        guide_prompt: string
        web_search?: boolean
        plugins?: string[]
        mcp_servers?: string[]
    },
    onMessage: (data: any) => void,
    onTaskGraph?: (graph: any) => void,  // 处理任务图数据
    onStepResult?: (stepData: { title: string; message: string }) => void,  // 处理步骤结果
    onTaskResult?: (message: string) => void,  // 新增：处理任务最终结果
    onError?: (error: any) => void,
    onClose?: () => void
) => {
    const token = localStorage.getItem('token')

    console.log('开始调用 task_start 接口，参数:', data)

    const ctrl = new AbortController()

    try {
        await fetchEventSource(resolveApiUrl('/api/v1/task_start'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data),
            signal: ctrl.signal,
            openWhenHidden: true,
            onmessage(event) {
                console.log('📨 收到原始消息:', event.data)
                debugger
                if (event.data) {
                    try {
                        // 后端返回的是 JSON 格式: { "event": "...", "data": {...} }
                        const parsedData = JSON.parse(event.data)
                        console.log('📦 解析后的数据:', parsedData)

                        // 处理不同类型的事件
                        if (parsedData.event === 'generate_tasks' && parsedData.data?.graph) {
                            // 处理任务图数据
                            console.log('📊 收到任务图数据:', parsedData.data.graph)
                            onTaskGraph?.(parsedData.data.graph)
                        } else if (parsedData.event === 'step_result' && parsedData.data?.title && parsedData.data?.message) {
                            // 处理步骤执行结果
                            console.log('✅ 收到步骤结果:', parsedData.data)
                            onStepResult?.({ title: parsedData.data.title, message: parsedData.data.message })
                        } else if (parsedData.event === 'task_result' && parsedData.data?.message) {
                            // 处理任务最终结果（流式）
                            console.log('📄 收到任务结果数据块:', parsedData.data.message)
                            onTaskResult?.(parsedData.data.message)
                        } else if (parsedData.data?.chunk) {
                            // 处理文本块数据
                            const chunk = parsedData.data.chunk
                            console.log('📝 提取的 chunk:', chunk)
                            onMessage(chunk)
                        } else {
                            // 其他类型的数据，直接传递
                            onMessage(parsedData)
                        }
                    } catch (error) {
                        console.error('❌ JSON 解析失败:', error, '原始数据:', event.data)
                        // 如果解析失败，尝试直接使用原始数据
                        onMessage(event.data)
                    }
                }
            },
            onerror(err) {
                console.error('Stream 错误:', err)
                onError?.(err)
                ctrl.abort()
            },
            onclose() {
                console.log('Stream 关闭')
                onClose?.()
            }
        })
    } catch (error) {
        console.error('fetchEventSource 异常:', error)
        if (error.name !== 'AbortError') {
            onError?.(error)
        }
    }
}



export function sendMessage(data, onmessage: any, onclose: any) {
    const ctrl = new AbortController();

    fetchEventSource(resolveApiUrl('/api/v1/completion'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: JSON.stringify({
            ...(data.fileUrl
                ? {
                    dialog_id: data.dialogId,
                    user_input: data.userInput,
                    file_url: data.fileUrl,
                }
                : {
                    dialog_id: data.dialogId,
                    user_input: data.userInput,
                }),
        }),
        signal: ctrl.signal,
        openWhenHidden: true,
        async onopen(response: any) {
            if (response.status !== 200) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        },
        onmessage(msg: any) {
            try {
                onmessage(msg);
            } catch (error) {
                console.log('处理消息时出错:', error);
            }
        },
        onclose() {
            onclose();
        },
        onerror(err: any) {
            console.log('聊天连接错误:', err);
            ctrl.abort();
            throw err;
        }
    });

    return ctrl;
}
