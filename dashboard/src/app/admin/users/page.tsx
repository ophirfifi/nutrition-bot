"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { adminApi } from "@/lib/admin-api"
import type { AdminUserRow } from "@/types/admin"

export default function UsersPage() {
  const [users, setUsers] = useState<AdminUserRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    adminApi
      .users()
      .then(setUsers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (error) return <p className="text-danger">{error}</p>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Users</h1>
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : users.length === 0 ? (
        <p className="text-muted">No users yet.</p>
      ) : (
        <div className="glass rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-muted text-left">
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Telegram ID</th>
                <th className="px-4 py-3 font-medium">Age</th>
                <th className="px-4 py-3 font-medium">Sport</th>
                <th className="px-4 py-3 font-medium">Onboarded</th>
                <th className="px-4 py-3 font-medium">Health Score</th>
                <th className="px-4 py-3 font-medium">Last Active</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr
                  key={u.telegram_id}
                  className="border-b border-border/50 hover:bg-surface-2/50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/admin/users/${u.telegram_id}`}
                      className="text-primary hover:underline font-medium"
                    >
                      {u.name || "—"}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-muted font-mono text-xs">
                    {u.telegram_id}
                  </td>
                  <td className="px-4 py-3">{u.age ?? "—"}</td>
                  <td className="px-4 py-3">{u.sport_type ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block w-2 h-2 rounded-full ${
                        u.onboarding_complete ? "bg-primary" : "bg-warn"
                      }`}
                    />
                  </td>
                  <td className="px-4 py-3 font-semibold">{u.health_score}</td>
                  <td className="px-4 py-3 text-muted text-xs">
                    {u.updated_at
                      ? new Date(u.updated_at).toLocaleString("en-GB", {
                          day: "2-digit",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
