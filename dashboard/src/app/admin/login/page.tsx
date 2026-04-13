"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

export default function AdminLogin() {
  const [token, setToken] = useState("")
  const [error, setError] = useState("")
  const router = useRouter()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    const res = await fetch("/api/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
    if (res.ok) {
      router.push("/admin")
      router.refresh()
    } else {
      setError("Invalid token")
    }
  }

  return (
    <div dir="ltr" className="min-h-screen bg-bg flex items-center justify-center">
      <form
        onSubmit={handleSubmit}
        className="glass rounded-2xl p-8 w-full max-w-sm flex flex-col gap-4"
      >
        <h1 className="text-xl font-bold text-white text-center">Nutri Admin</h1>
        <p className="text-muted text-sm text-center">Enter admin token to continue</p>
        <input
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Admin token"
          className="w-full px-4 py-2.5 rounded-lg bg-surface-2 border border-border text-white text-sm placeholder:text-muted/50 focus:outline-none focus:border-primary"
        />
        {error && <p className="text-danger text-sm text-center">{error}</p>}
        <button
          type="submit"
          className="w-full py-2.5 rounded-lg bg-primary text-white font-semibold text-sm hover:bg-primary/90 transition-colors"
        >
          Sign In
        </button>
      </form>
    </div>
  )
}
