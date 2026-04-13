"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { adminApi } from "@/lib/admin-api"
import type { AdminInteraction } from "@/types/admin"

export default function DistressPage() {
  const [items, setItems] = useState<AdminInteraction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    adminApi
      .distress(50)
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (error) return <p className="text-danger">{error}</p>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Distress Alerts</h1>
      <p className="text-muted text-sm mb-6">
        Messages that triggered the distress detection system.
      </p>
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <div className="glass rounded-2xl p-8 text-center">
          <span className="text-4xl block mb-3">✅</span>
          <p className="text-white font-medium">No distress alerts</p>
          <p className="text-muted text-sm mt-1">All clear.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((i, idx) => (
            <div
              key={idx}
              className="glass rounded-xl p-4 text-sm border border-danger/30"
            >
              <div className="flex items-center gap-2 mb-1.5">
                <Link
                  href={`/admin/users/${i.telegram_id}`}
                  className="text-primary hover:underline font-medium"
                >
                  {i.user_name || `#${i.telegram_id}`}
                </Link>
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-danger/20 text-danger">
                  DISTRESS
                </span>
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
              <p className="text-white whitespace-pre-wrap">
                {i.message_text || "(no text)"}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
