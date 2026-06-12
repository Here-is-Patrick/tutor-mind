import React, { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import { createSession, getStudentSessions } from './services/api'

const LAST_STUDENT_KEY = 'tutormind_last_student'

export default function App() {
  const [studentId, setStudentId] = useState(() => {
    return localStorage.getItem(LAST_STUDENT_KEY) || 'student_001'
  })
  const [sessionId, setSessionId] = useState('')
  const [sessionKey, setSessionKey] = useState(0)
  const [isLoading, setIsLoading] = useState(false)

  // Create initial session only when student changes and no sessions exist
  useEffect(() => {
    if (!studentId) return

    const initSession = async () => {
      setIsLoading(true)
      try {
        const sessionsRes = await getStudentSessions(studentId)
        if (sessionsRes.sessions.length > 0) {
          // Use the most recent session
          const latest = sessionsRes.sessions[0]
          setSessionId(latest.session_id)
          setSessionKey((k) => k + 1)
        } else {
          // No existing sessions, create a new one
          const res = await createSession(studentId)
          setSessionId(res.session_id)
          setSessionKey((k) => k + 1)
        }
      } catch (err) {
        console.error('Failed to initialize session:', err)
      } finally {
        setIsLoading(false)
      }
    }

    initSession()
  }, [studentId])

  const handleNewSession = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await createSession(studentId)
      setSessionId(res.session_id)
      setSessionKey((k) => k + 1)
    } catch (err) {
      console.error('Failed to create session:', err)
    } finally {
      setIsLoading(false)
    }
  }, [studentId])

  const handleSwitchSession = useCallback((newSessionId: string) => {
    if (newSessionId === sessionId) return
    setSessionId(newSessionId)
    setSessionKey((k) => k + 1)
  }, [sessionId])

  const handleStudentChange = useCallback((newStudentId: string) => {
    if (newStudentId === studentId) return
    setStudentId(newStudentId)
    localStorage.setItem(LAST_STUDENT_KEY, newStudentId)
    // session will be created by useEffect above
  }, [studentId])

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar
        studentId={studentId}
        sessionId={sessionId}
        onStudentIdChange={handleStudentChange}
        onSessionChange={handleSwitchSession}
        onNewSession={handleNewSession}
      />
      <main className="flex-1 p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mr-3" />
            加载中...
          </div>
        ) : sessionId ? (
          <ChatPanel
            key={`${studentId}-${sessionId}-${sessionKey}`}
            studentId={studentId}
            sessionId={sessionId}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            请选择一个学生开始
          </div>
        )}
      </main>
    </div>
  )
}