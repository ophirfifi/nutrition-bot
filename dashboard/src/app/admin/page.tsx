"use client"

import { useEffect, useState } from "react"
import { adminApi } from "@/lib/admin-api"
import type { AdminOverview } from "@/types/admin"

function StatCard({
  icon,
  label,
  value,
  alert,
}: {
  icon: string
  label: string
  value: number
  alert?: boolean
}) {
  return (
    <div className={`glass rounded-2xl p-5 ${alert && value > 0 ? "border-danger/40" : ""}`}>
      <div className="flex items-center gap-3 mb-2">
        <span className="text-2xl">{icon}</span>
        <span className="text-muted text-sm">{label}</span>
      </div>
      <p className={`text-3xl font-black ${alert && value > 0 ? "text-danger" : "text-white"}`}>
        {value}
      </p>
    </div>
  )
}

export default function AdminOverviewPage() {
  const [data, setData] = useState<AdminOverview | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    adminApi.overview().then(setData).catch((e) => setError(e.message))
  }, [])

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-danger">{error}</p>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Overview</h1>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon="👥" label="Total Users" value={data.total_users} />
        <StatCard icon="🟢" label="Active Today" value={data.active_today} />
        <StatCard icon="🍽" label="Meals Today" value={data.meals_today} />
        <StatCard icon="🚨" label="Distress Flags" value={data.distress_today} alert />
      </div>
    </div>
  )
}
