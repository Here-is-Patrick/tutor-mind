// ── Chat Types ────────────────────────────────────────────

export interface ChatMessage {
  id: string
  role: 'student' | 'assistant'
  content: string
  timestamp: string
  agentName?: string
  isGuided?: boolean
}

export interface ChatRequest {
  student_id: string
  session_id: string
  message: string
}

export interface ChatResponse {
  student_id: string
  session_id: string
  reply: string
  agent_name: string
  stage: string
  is_guided: boolean
  metadata?: Record<string, unknown>
}

// ── Student Types ──────────────────────────────────────────

export interface StudentProfile {
  student_id: string
  name?: string
  age?: number
  education?: string
  is_weak_foundation: boolean
  learning_goals?: string
}

export interface StudentProfileUpdate {
  name?: string
  age?: number
  education?: string
  is_weak_foundation?: boolean
  learning_goals?: string
}

// ── Learning Report ────────────────────────────────────────

export interface LearningReport {
  student_id: string
  total_questions: number
  guided_sessions: number
  search_sessions: number
  common_topics: string[]
  weak_foundation: boolean
  created_at: string
}

export interface LearningSummary {
  student_id: string
  total_messages: number
  recent_messages: number
  total_sessions: number
}