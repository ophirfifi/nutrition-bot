"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { adminApi } from "@/lib/admin-api"
import type { AdminInteraction } from "@/types/admin"

export default function InteractionsPage() {
  const [items, setItems] = useState<AdminInteraction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    adminApi
      .interactions(100)
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (error) return <p className="text-danger">{error}</p>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Recent Interactions</h1>
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <p className="text-muted">No interactions yet.</p>
      ) : (
        <div className="space-y-2">
          {items.map((i, idx) => (
            <div
              key={idx}
              className={`glass rounded-xl p-4 text-sm ${
                i.distress_flag ? "border border-danger/40" : ""
              }`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <Link
                  href={`/admin/users/${i.telegram_id}`}
                  className="text-primary hover:underline font-medium"
                >
                  {i.user_name || `#${i.telegram_id}`}
                </Link>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    i.direction === "inbound"
                      ? "bg-accent/20 text-accent"
                      : "bg-primary/20 text-primary"
                  }`}
                >
                  {i.direction === "inbound" ? "User" : i.agent_type || "Bot"}
                </span>
                {i.distress_flag && (
                  <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-danger/20 text-danger">
                    DISTRESS
                  </span>
                )}
                <span className="text-muted text-xs ml-auto">
                  {i.timestamp
                    ? new Date(i.timestamp).toLocaleString("en-GB", {
                        day: "2-digit",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : ""}
                </span>
              </div>
              <p className="text-muted whitespace-pre-wrap line-clamp-3">
                {i.message_text || "(no text)"}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
