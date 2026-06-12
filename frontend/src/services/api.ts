import type {
  ChatRequest,
  ChatResponse,
  StudentProfile,
  StudentProfileUpdate,
  LearningReport,
  LearningSummary,
} from '../types'

const API_BASE = '/api'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ── Chat (Non-streaming) ──────────────────────────────────

export async function sendMessage(data: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/chat/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// ── Chat (Streaming SSE) ──────────────────────────────────

export interface StreamCallbacks {
  onMeta?: (meta: { agent_name: string; stage: string; is_guided: boolean; mode?: string }) => void
  onContent?: (chunk: string) => void
  onDone?: () => void
  onError?: (error: string) => void
}

export function sendMessageStream(
  data: ChatRequest,
  callbacks: StreamCallbacks
): () => void {
  const abortController = new AbortController()

  fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    signal: abortController.signal,
  }).then(async (res) => {
    if (!res.ok || !res.body) {
      const err = await res.json().catch(() => ({ detail: 'Request failed' }))
      callbacks.onError?.(err.detail || `HTTP ${res.status}`)
      return
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value, { stream: true })
      const lines = text.split('\n')

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const jsonStr = line.slice(6)
        if (!jsonStr) continue

        try {
          const event = JSON.parse(jsonStr)
          switch (event.type) {
            case 'meta':
              callbacks.onMeta?.(event)
              break
            case 'content':
              callbacks.onContent?.(event.content)
              break
            case 'done':
              callbacks.onDone?.()
              break
            case 'error':
              callbacks.onError?.(event.content)
              break
          }
        } catch {
          // ignore parse errors
        }
      }
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') {
      callbacks.onError?.(err.message)
    }
  })

  return () => abortController.abort()
}

// ── Session & History ─────────────────────────────────────

export async function createSession(studentId: string): Promise<{
  student_id: string
  session_id: string
}> {
  return request(`/chat/create_session/${studentId}`, { method: 'POST' })
}

export async function getChatHistory(studentId: string, sessionId: string): Promise<{
  student_id: string
  session_id: string
  messages: Array<{
    role: string
    content: string
    agent_name: string | null
    created_at: string
  }>
}> {
  return request(`/chat/history/${studentId}/${sessionId}`)
}

export async function getStudentSessions(studentId: string): Promise<{
  student_id: string
  sessions: Array<{
    session_id: string
    created_at: string
    is_active: number
    title: string | null
  }>
}> {
  return request(`/chat/sessions/${studentId}`)
}

export async function deleteSession(studentId: string, sessionId: string): Promise<{
  student_id: string
  session_id: string
  deleted: boolean
}> {
  return request(`/chat/session/${studentId}/${sessionId}`, { method: 'DELETE' })
}

export async function deleteMessage(studentId: string, sessionId: string, messageId: string): Promise<{
  student_id: string
  session_id: string
  message_id: string
  deleted: boolean
}> {
  return request(`/chat/message/${studentId}/${sessionId}/${encodeURIComponent(messageId)}`, { method: 'DELETE' })
}

// ── Students ──────────────────────────────────────────────

export async function getStudent(
  studentId: string
): Promise<StudentProfile> {
  return request<StudentProfile>(`/students/${studentId}`)
}

export async function updateStudent(
  studentId: string,
  data: StudentProfileUpdate
): Promise<StudentProfile> {
  return request<StudentProfile>(`/students/${studentId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function createStudent(
  data: StudentProfile
): Promise<StudentProfile> {
  return request<StudentProfile>('/students/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// ── Analytics ─────────────────────────────────────────────

export async function getLearningReport(
  studentId: string
): Promise<LearningReport> {
  return request<LearningReport>(`/analytics/${studentId}`)
}

export async function getLearningSummary(
  studentId: string
): Promise<LearningSummary> {
  return request<LearningSummary>(`/analytics/${studentId}/summary`)
}