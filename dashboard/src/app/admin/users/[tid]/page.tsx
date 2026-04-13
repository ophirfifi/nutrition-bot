"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { adminApi } from "@/lib/admin-api"
import type { AdminUserDetail } from "@/types/admin"

function Badge({ color, children }: { color: string; children: React.ReactNode }) {
  const colors: Record<string, string> = {
    green: "bg-primary/20 text-primary",
    yellow: "bg-warn/20 text-warn",
    red: "bg-danger/20 text-danger",
    blue: "bg-accent/20 text-accent",
    gray: "bg-surface-2 text-muted",
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[color] || colors.gray}`}>
      {children}
    </span>
  )
}

export default function UserDetailPage() {
  const params = useParams()
  const tid = Number(params.tid)
  const [data, setData] = useState<AdminUserDetail | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    if (tid) adminApi.userDetail(tid).then(setData).catch((e) => setError(e.message))
  }, [tid])

  if (error) return <p className="text-danger">{error}</p>
  if (!data) {
    return (
      <div className="flex justify-center py-12">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const { user, meals, scores, interactions } = data

  return (
    <div className="max-w-4xl">
      <Link href="/admin/users" className="text-muted text-sm hover:text-white mb-4 block">
        &larr; Back to Users
      </Link>

      <h1 className="text-2xl font-bold mb-6">
        {user.name || "Unknown"}{" "}
        <span className="text-muted text-base font-normal">#{user.telegram_id}</span>
      </h1>

      {/* Profile card */}
      <div className="glass rounded-2xl p-5 mb-6">
        <h2 className="font-semibold mb-3">Profile</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-muted text-xs">Age</p>
            <p>{user.age ?? "—"}</p>
          </div>
          <div>
            <p className="text-muted text-xs">Height</p>
            <p>{user.height ? `${user.height} cm` : "—"}</p>
          </div>
          <div>
            <p className="text-muted text-xs">Sport</p>
            <p>{user.sport_type ?? "—"}</p>
          </div>
          <div>
            <p className="text-muted text-xs">Training/week</p>
            <p>{user.sport_frequency ?? "—"}</p>
          </div>
          <div>
            <p className="text-muted text-xs">Onboarded</p>
            <p>{user.onboarding_complete ? "Yes" : "No"}</p>
          </div>
          <div>
            <p className="text-muted text-xs">Joined</p>
            <p>{user.created_at ? new Date(user.created_at).toLocaleDateString("en-GB") : "—"}</p>
          </div>
          {user.preferences && (
            <>
              <div>
                <p className="text-muted text-xs">Likes</p>
                <p>{(user.preferences as any).likes?.join(", ") || "—"}</p>
              </div>
              <div>
                <p className="text-muted text-xs">Dislikes</p>
                <p>{(user.preferences as any).dislikes?.join(", ") || "—"}</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Health scores */}
      {scores.length > 0 && (
        <div className="glass rounded-2xl p-5 mb-6">
          <h2 className="font-semibold mb-3">Health Scores (last 30 days)</h2>
          <div className="flex gap-1.5 items-end h-24">
            {scores.map((s) => (
              <div
                key={s.date}
                className="flex-1 bg-primary/60 rounded-t"
                style={{ height: `${Math.max(s.health_score, 4)}%` }}
                title={`${s.date}: ${s.health_score}`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Recent meals */}
      <div className="glass rounded-2xl p-5 mb-6">
        <h2 className="font-semibold mb-3">Recent Meals ({meals.length})</h2>
        {meals.length === 0 ? (
          <p className="text-muted text-sm">No meals logged yet.</p>
        ) : (
          <div className="space-y-2">
            {meals.map((m) => (
              <div
                key={m.id}
                className="flex items-center gap-3 text-sm border-b border-border/30 pb-2"
              >
                <Badge color={m.rating || "gray"}>{m.rating || "?"}</Badge>
                <span className="flex-1 truncate">{m.description || "Photo meal"}</span>
                <span className="text-muted text-xs">
                  {m.timestamp
                    ? new Date(m.timestamp).toLocaleString("en-GB", {
                        day: "2-digit",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : ""}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent interactions */}
      <div className="glass rounded-2xl p-5">
        <h2 className="font-semibold mb-3">Conversation Log ({interactions.length})</h2>
        {interactions.length === 0 ? (
          <p className="text-muted text-sm">No interactions yet.</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {interactions.map((i, idx) => (
              <div
                key={idx}
                className={`text-sm p-2.5 rounded-lg ${
                  i.direction === "inbound"
                    ? "bg-surface-2 mr-12"
                    : "bg-accent/10 ml-12"
                } ${i.distress_flag ? "border border-danger/40" : ""}`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Badge color={i.direction === "inbound" ? "blue" : "green"}>
                    {i.direction === "inbound" ? "User" : i.agent_type || "Bot"}
                  </Badge>
                  {i.distress_flag && <Badge color="red">DISTRESS</Badge>}
                  <span className="text-muted text-xs ml-auto">
                    {i.timestamp
                      ? new Date(i.timestamp).toLocaleTimeString("en-GB", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : ""}
                  </span>
                </div>
                <p className="text-muted text-xs whitespace-pre-wrap">
                  {i.message_text || "(no text)"}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
