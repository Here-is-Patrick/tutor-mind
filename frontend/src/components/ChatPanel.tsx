import React, { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import { Send, Brain, User, Loader2, Trash2 } from 'lucide-react'
import type { ChatMessage } from '../types'
import { sendMessageStream, getChatHistory, deleteMessage } from '../services/api'

interface ChatPanelProps {
  studentId: string
  sessionId: string
}

export default function ChatPanel({ studentId, sessionId }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const messagesEnd = useRef<HTMLDivElement>(null)
  const abortRef = useRef<(() => void) | null>(null)

  // Load history when session changes
  useEffect(() => {
    if (!studentId || !sessionId) return

    setMessages([])
    setLoading(true)

    getChatHistory(studentId, sessionId)
      .then((res) => {
        const historyMessages: ChatMessage[] = res.messages.map((m, idx) => ({
          id: `hist-${idx}`,
          role: m.role === 'student' ? 'student' : 'assistant',
          content: m.content,
          timestamp: m.created_at,
          agentName: m.agent_name || undefined,
        }))
        setMessages(historyMessages)
      })
      .catch((err) => {
        console.error('Failed to load history:', err)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [studentId, sessionId])

  // Auto-scroll
  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(() => {
    const text = input.trim()
    if (!text || !sessionId || streaming) return

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'student',
      content: text,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setStreaming(true)

    // Create placeholder for assistant response
    const assistantId = (Date.now() + 1).toString()
    setMessages((prev) => [
      ...prev,
      {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        agentName: undefined,
        isGuided: false,
      },
    ])

    let currentContent = ''

    abortRef.current = sendMessageStream(
      {
        student_id: studentId,
        session_id: sessionId,
        message: text,
      },
      {
        onMeta: (meta) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    agentName: meta.agent_name,
                    isGuided: meta.is_guided,
                  }
                : m
            )
          )
        },
        onContent: (chunk) => {
          currentContent += chunk
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: currentContent } : m
            )
          )
        },
        onDone: () => {
          setStreaming(false)
        },
        onError: (error) => {
          setStreaming(false)
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: `抱歉，发生了错误：${error}`,
                  }
                : m
            )
          )
        },
      }
    )
  }, [input, sessionId, streaming, studentId])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const agentLabel = (agentName?: string) => {
    const labels: Record<string, string> = {
      info_collector: '信息收集',
      socratic_tutor: '苏格拉底导师',
      search_agent: '知识搜索',
    }
    return labels[agentName || ''] || agentName || 'TutorMind'
  }

  const handleDeleteMessage = async (msg: ChatMessage) => {
    if (!msg.timestamp) return
    if (!confirm('确定要删除这条消息吗？')) return
    try {
      await deleteMessage(studentId, sessionId, msg.timestamp)
      setMessages((prev) => prev.filter((m) => m.id !== msg.id))
    } catch (err) {
      console.error('Failed to delete message:', err)
    }
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-primary-50 to-blue-50">
        <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center">
          <Brain className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="font-semibold text-gray-800">TutorMind</h2>
          <p className="text-xs text-gray-500">一对一智能学习辅导</p>
        </div>
        {sessionId && (
          <span className="ml-auto text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
            Session: {sessionId.slice(0, 8)}...
          </span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {loading && messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            加载历史记录...
          </div>
        )}

        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Brain className="w-16 h-16 mb-4 text-gray-200" />
            <p className="text-lg font-medium text-gray-500">欢迎使用 TutorMind</p>
            <p className="text-sm mt-1">输入你的学习问题，开始一对一辅导</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`group flex gap-3 ${msg.role === 'student' ? 'flex-row-reverse' : ''}`}
          >
            {/* Avatar */}
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                msg.role === 'student'
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-purple-100 text-purple-700'
              }`}
            >
              {msg.role === 'student' ? (
                <User className="w-4 h-4" />
              ) : (
                <Brain className="w-4 h-4" />
              )}
            </div>

            {/* Bubble */}
            <div
              className={`relative max-w-[75%] rounded-2xl px-4 py-3 ${
                msg.role === 'student'
                  ? 'bg-primary-600 text-white rounded-tr-sm'
                  : 'bg-gray-100 text-gray-800 rounded-tl-sm'
              }`}
            >
              {msg.agentName && msg.role === 'assistant' && (
                <div className="text-xs text-gray-500 mb-1">
                  {agentLabel(msg.agentName)}
                  {msg.isGuided && (
                    <span className="ml-2 text-purple-500 font-medium">苏格拉底引导</span>
                  )}
                </div>
              )}
              <div
                className={`text-sm leading-relaxed markdown-body ${
                  msg.role === 'student' ? 'text-white' : 'text-gray-800'
                }`}
              >
                {msg.content ? (
                  <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                    {msg.content}
                  </ReactMarkdown>
                ) : streaming ? (
                  <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                ) : null}
              </div>
              {/* Delete button */}
              <button
                onClick={() => handleDeleteMessage(msg)}
                className={`absolute -top-2 ${msg.role === 'student' ? '-left-2' : '-right-2'} opacity-0 group-hover:opacity-100 p-1 rounded-full bg-white shadow-sm border border-gray-200 text-gray-400 hover:text-red-500 hover:border-red-200 transition-all`}
                title="删除消息"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}

        <div ref={messagesEnd} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-100 px-4 py-3">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的问题... (Shift+Enter 换行)"
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent"
            disabled={streaming}
          />
          <button
            onClick={handleSend}
            disabled={streaming || !input.trim()}
            className="px-4 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {streaming ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
