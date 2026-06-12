import React, { useState, useEffect } from 'react'
import {
  GraduationCap,
  BarChart3,
  UserCircle,
  Settings,
  LogIn,
  MessageSquare,
  Plus,
  History,
  UserPlus,
  Users,
} from 'lucide-react'
import { getStudent, getLearningSummary, getStudentSessions, createSession } from '../services/api'
import type { StudentProfile, LearningSummary } from '../types'

interface SidebarProps {
  studentId: string
  onStudentIdChange: (id: string) => void
  onSessionChange: (sessionId: string) => void
  onNewSession: () => void
}

export default function Sidebar({ studentId, onStudentIdChange, onSessionChange, onNewSession }: SidebarProps) {
  const [profile, setProfile] = useState<StudentProfile | null>(null)
  const [summary, setSummary] = useState<LearningSummary | null>(null)
  const [sessions, setSessions] = useState<Array<{ session_id: string; created_at: string; is_active: number }>>([])
  const [inputId, setInputId] = useState('')
  const [showLogin, setShowLogin] = useState(false)
  const [showNewUser, setShowNewUser] = useState(false)
  const [newUserId, setNewUserId] = useState('')

  useEffect(() => {
    if (studentId) {
      getStudent(studentId)
        .then(setProfile)
        .catch(() => setProfile(null))
      getLearningSummary(studentId)
        .then(setSummary)
        .catch(() => setSummary(null))
      getStudentSessions(studentId)
        .then((res) => setSessions(res.sessions))
        .catch(() => setSessions([]))
    }
  }, [studentId])

  const handleLogin = () => {
    if (inputId.trim()) {
      onStudentIdChange(inputId.trim())
      setInputId('')
      setShowLogin(false)
    }
  }

  const handleNewUser = () => {
    if (newUserId.trim()) {
      onStudentIdChange(newUserId.trim())
      setNewUserId('')
      setShowNewUser(false)
      setShowLogin(false)
    }
  }

  const handleNewSessionClick = async () => {
    try {
      onNewSession() // Let App.tsx handle the actual creation and state update
      // Refresh session list after a short delay
      setTimeout(async () => {
        const sessionsRes = await getStudentSessions(studentId)
        setSessions(sessionsRes.sessions)
      }, 300)
    } catch (err) {
      console.error('Failed to create session:', err)
    }
  }

  const handleSwitchSession = (sessionId: string) => {
    onSessionChange(sessionId)
  }

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr)
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  }

  return (
    <div className="w-72 bg-white border-r border-gray-100 h-full flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
            <GraduationCap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-800">TutorMind</h1>
            <p className="text-xs text-gray-400">v0.1.0</p>
          </div>
        </div>
      </div>

      {/* Student Info */}
      <div className="px-5 py-4 border-b border-gray-100">
        {profile ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <UserCircle className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-700 flex-1">
                {profile.name || studentId}
              </span>
              <span className="text-xs text-gray-400">({studentId})</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
              <div>
                <span className="text-gray-400">年龄</span>
                <p className="font-medium text-gray-600">{profile.age || '—'}</p>
              </div>
              <div>
                <span className="text-gray-400">学历</span>
                <p className="font-medium text-gray-600">{profile.education || '—'}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                  profile.is_weak_foundation
                    ? 'bg-orange-100 text-orange-700'
                    : 'bg-green-100 text-green-700'
                }`}
              >
                {profile.is_weak_foundation ? '基础薄弱' : '有一定基础'}
              </span>
            </div>
            {/* User Actions */}
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => { setShowLogin(true); setShowNewUser(false); }}
                className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 px-2 py-1 rounded hover:bg-primary-50 transition-colors"
              >
                <Users className="w-3 h-3" />
                切换用户
              </button>
              <button
                onClick={() => { setShowNewUser(true); setShowLogin(false); }}
                className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 px-2 py-1 rounded hover:bg-primary-50 transition-colors"
              >
                <UserPlus className="w-3 h-3" />
                新建用户
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-sm text-gray-500 mb-3">当前用户: {studentId}</p>
            <div className="flex gap-2 justify-center">
              <button
                onClick={() => { setShowLogin(true); setShowNewUser(false); }}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                <LogIn className="w-3.5 h-3.5" />
                切换用户
              </button>
              <button
                onClick={() => { setShowNewUser(true); setShowLogin(false); }}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <UserPlus className="w-3.5 h-3.5" />
                新建用户
              </button>
            </div>
          </div>
        )}

        {/* Switch User Form */}
        {showLogin && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500 mb-2">切换到已有用户</p>
            <div className="flex gap-2">
              <input
                type="text"
                value={inputId}
                onChange={(e) => setInputId(e.target.value)}
                placeholder="输入学生ID"
                className="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-400"
                onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
              />
              <button
                onClick={handleLogin}
                className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                切换
              </button>
            </div>
            <button
              onClick={() => setShowLogin(false)}
              className="mt-2 text-xs text-gray-400 hover:text-gray-600"
            >
              取消
            </button>
          </div>
        )}

        {/* New User Form */}
        {showNewUser && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500 mb-2">创建新用户（输入新ID即可）</p>
            <div className="flex gap-2">
              <input
                type="text"
                value={newUserId}
                onChange={(e) => setNewUserId(e.target.value)}
                placeholder="输入新学生ID，如 student_002"
                className="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-400"
                onKeyDown={(e) => e.key === 'Enter' && handleNewUser()}
              />
              <button
                onClick={handleNewUser}
                className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                创建
              </button>
            </div>
            <button
              onClick={() => setShowNewUser(false)}
              className="mt-2 text-xs text-gray-400 hover:text-gray-600"
            >
              取消
            </button>
          </div>
        )}
      </div>

      {/* Stats */}
      {summary && (
        <div className="px-5 py-4 border-b border-gray-100">
          <h3 className="text-xs font-semibold text-gray-400 uppercase mb-3">学习概览</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 rounded-lg p-3">
              <MessageSquare className="w-4 h-4 text-primary-500 mb-1" />
              <p className="text-lg font-bold text-gray-700">{summary.total_messages}</p>
              <p className="text-xs text-gray-400">总消息数</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <BarChart3 className="w-4 h-4 text-purple-500 mb-1" />
              <p className="text-lg font-bold text-gray-700">{summary.total_sessions}</p>
              <p className="text-xs text-gray-400">会话数</p>
            </div>
          </div>
        </div>
      )}

      {/* Sessions */}
      <div className="px-5 py-4 border-b border-gray-100 flex-1 overflow-y-auto">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold text-gray-400 uppercase">历史会话</h3>
          <button
            onClick={handleNewSessionClick}
            className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700"
          >
            <Plus className="w-3 h-3" />
            新会话
          </button>
        </div>
        <div className="space-y-1">
          {sessions.map((sess) => (
            <button
              key={sess.session_id}
              onClick={() => handleSwitchSession(sess.session_id)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors text-left"
            >
              <History className="w-3.5 h-3.5 text-gray-400" />
              <span className="flex-1 truncate">{formatDate(sess.created_at)}</span>
              {sess.is_active ? (
                <span className="w-2 h-2 rounded-full bg-green-400" />
              ) : null}
            </button>
          ))}
          {sessions.length === 0 && (
            <p className="text-xs text-gray-400 text-center py-2">暂无历史会话</p>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-gray-100 text-center">
        <p className="text-xs text-gray-400">TutorMind v0.1.0</p>
        <p className="text-xs text-gray-300">Powered by DashScope & LangGraph</p>
      </div>
    </div>
  )
}