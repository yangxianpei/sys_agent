import { post, get, del } from '../utils/request'


export const KnowledgeFileStatus = {
  FAIL: 2,
  PROCESS: 0,
  SUCCESS: 1
} as const

export type KnowledgeFileStatus = typeof KnowledgeFileStatus[keyof typeof KnowledgeFileStatus]


export const Upload = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return post('/api/v1/upload_doc', formData)
}


export const get_agent_all = () => {
  return get('/api/v1/get_agent_all')
}

export const knowledge_doc_list = (knowledge_id: string | number) => {
  return post('/api/v1/knowledge_doc_list', {
    knowledge_id
  })
}




export const knowledge_del = (knowledge_id: string | number) => {
  return del('/api/v1/knowledge_del', {
    knowledge_id
  })
}
export const create_knowledge = (data: Record<string, unknown>) => {
  return post('/api/v1/create_knowledge', {
    ...data
  })
}
export const modify_knowledge = (data: Record<string, unknown>) => {
  return post('/api/v1/modify_knowledge', {
    ...data
  })
}

export const knowledge_list = () => {
  return get('/api/v1/knowledge_list')
}

export const del_kb = (doc_id: string) => {
  return del('/api/v1/knowledge_doc_del', {
    doc_id
  })
}


export function getFileType(file_path: string): string {
  const ext = file_path?.split('.').pop()?.toLowerCase()

  const fileTypes = {
    pdf: 'PDF文档',
    doc: 'Word文档',
    docx: 'Word文档',
    txt: '文本文件',
    md: 'Markdown文档',
    xls: 'Excel表格',
    xlsx: 'Excel表格',
    ppt: 'PowerPoint演示',
    pptx: 'PowerPoint演示',
    jpg: '图片文件',
    jpeg: '图片文件',
    png: '图片文件',
    gif: '图片文件',
    bmp: '图片文件'
  } as const

  if (!ext) {
    return '未知文件'
  }

  if (ext in fileTypes) {
    return fileTypes[ext as keyof typeof fileTypes]
  }


} 