// API服务模块

const API_BASE_URL = 'http://localhost:8000'

// 会话ID管理
const SESSION_STORAGE_KEY = 'current_session_id'
const SESSION_COUNTER_KEY = 'session_counter'

// 生成新的会话ID
export const generateNewSessionId = (): string => {
  // 获取当前计数器值
  const counter = parseInt(localStorage.getItem(SESSION_COUNTER_KEY) || '0') + 1
  // 保存新的计数器值
  localStorage.setItem(SESSION_COUNTER_KEY, counter.toString())
  // 生成会话ID
  return `新对话${counter}`
}

export const getCurrentSessionId = (): string | null => {
  return sessionStorage.getItem(SESSION_STORAGE_KEY)
}

export const setCurrentSessionId = (sessionId: string): void => {
  sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId)
}

export const clearCurrentSessionId = (): void => {
  sessionStorage.removeItem(SESSION_STORAGE_KEY)
}

// API响应类型
export interface AgentResponse {
  response: string
  session_id: string
}

export interface RagResponse {
  response: string
}

export interface SessionHistory {
  session_id: string
  history: [string, string][]
}

export interface SessionDeleteResponse {
  message: string
}

export interface SessionsResponse {
  sessions: string[]
}

// API调用函数
export const agentQuery = async (query: string, sessionId?: string): Promise<AgentResponse> => {
  const currentSessionId = sessionId || getCurrentSessionId()

  const response = await fetch(`${API_BASE_URL}/api/agent/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      session_id: currentSessionId || '',
    }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  const data = (await response.json()) as AgentResponse

  // 保存会话ID
  if (data.session_id) {
    setCurrentSessionId(data.session_id)
  }

  return data
}

// 流式API调用函数
export const agentQueryStream = (
  query: string,
  sessionId?: string,
  onChunk?: (chunk: string, sessionId: string) => void,
  onComplete?: () => void,
  onError?: (error: Error) => void,
): (() => void) => {
  const currentSessionId = sessionId || getCurrentSessionId()
  let controller: AbortController | null = new AbortController()

  const fetchStream = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          session_id: currentSessionId || '',
        }),
        signal: controller?.signal,
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      let fullResponse = ''
      let receivedSessionId = ''
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          if (onComplete) {
            onComplete()
          }
          break
        }

        // 解码Uint8Array为字符串
        const chunk = new TextDecoder('utf-8').decode(value)
        buffer += chunk

        // 处理可能的多个事件
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue

          try {
            // 处理 SSE 格式，移除 'data: ' 前缀
            let content = line
            if (content.startsWith('data: ')) {
              content = content.substring(6)
            }

            // 跳过空数据
            if (!content.trim()) continue

            // 检查是否结束标志
            if (content === '[DONE]') {
              // 保存会话ID（如果有）
              if (receivedSessionId) {
                setCurrentSessionId(receivedSessionId)
              }
              if (onComplete) {
                onComplete()
              }
              return
            }

            // 直接将内容作为 chunk 处理
            fullResponse += content
            // 这里需要生成或获取 sessionId
            // 暂时使用当前会话ID或生成一个临时ID
            const sessionId = currentSessionId || 'temp-session-' + Date.now()
            receivedSessionId = sessionId

            if (onChunk) {
              onChunk(content, sessionId)
            }
          } catch (error) {
            console.error('Error processing stream data:', error)
          }
        }
      }
    } catch (error) {
      console.error('Stream error:', error)
      if (onError) {
        onError(error as Error)
      }
    }
  }

  fetchStream()

  // 返回关闭流的函数
  return () => {
    if (controller) {
      controller.abort()
      controller = null
    }
  }
}

export const ragQuery = async (query: string): Promise<RagResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/rag/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return (await response.json()) as RagResponse
}

export const getSessionHistory = async (sessionId: string): Promise<SessionHistory> => {
  const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}`)

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return (await response.json()) as SessionHistory
}

export const deleteSession = async (sessionId: string): Promise<SessionDeleteResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return (await response.json()) as SessionDeleteResponse
}

export const getSessions = async (): Promise<SessionsResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/sessions`)

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return (await response.json()) as SessionsResponse
}
