import React, { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import { createSession } from './services/api'

export default function App() {
  const [studentId, setStudentId] = useState('student_001')
  const [sessionId, setSessionId] = useState('')
  const [sessionKey, setSessionKey] = useState(0)
  const [isLoading, setIsLoading] = useState(false)

  // Create initial session when student changes
  useEffect(() => {
    if (!studentId) return
    setIsLoading(true)
    createSession(studentId)
      .then((res) => {
        setSessionId(res.session_id)
        setSessionKey((k) => k + 1)
      })
      .catch(console.error)
      .finally(() => setIsLoading(false))
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
    // session will be created by useEffect above
  }, [studentId])

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar
        studentId={studentId}
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