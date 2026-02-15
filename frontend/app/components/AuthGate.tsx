/**
 * AuthGate component - simple password gate for internal tool access.
 * Checks sessionStorage for auth flag, shows password prompt if missing.
 * Password sourced from NEXT_PUBLIC_ACCESS_PASSWORD env var.
 */
'use client'

import { useState, useEffect, FormEvent } from 'react'

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true) // prevents flash of password form
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  // Check sessionStorage on mount
  useEffect(() => {
    if (sessionStorage.getItem('auth') === 'true') {
      setAuthenticated(true)
    }
    setLoading(false)
  }, [])

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const expected = process.env.NEXT_PUBLIC_ACCESS_PASSWORD
    if (password === expected) {
      sessionStorage.setItem('auth', 'true') // persists until tab close
      setAuthenticated(true)
      setError('')
    } else {
      setError('Wrong password')
    }
  }

  // Don't render anything while checking sessionStorage
  if (loading) return null

  if (authenticated) return <>{children}</>

  // Password prompt - dark theme matching existing UI
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <form onSubmit={handleSubmit} className="bg-gray-800 p-8 rounded-lg border border-gray-700 w-80">
        <h1 className="text-gray-100 text-lg font-semibold mb-4">Access Required</h1>
        <input
          type="password"
          value={password}
          onChange={(e) => { setPassword(e.target.value); setError('') }}
          placeholder="Enter password"
          autoFocus
          className="w-full p-2 rounded bg-gray-700 border border-gray-600 text-gray-100 placeholder-gray-400 mb-3 focus:outline-none focus:border-blue-500"
        />
        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded font-medium"
        >
          Enter
        </button>
      </form>
    </div>
  )
}
