"use client"

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import type { HealthHistoryPoint } from "@/types"
import { format, parseISO } from "date-fns"

interface Props {
  data: HealthHistoryPoint[]
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm shadow-xl">
      <p className="text-muted mb-1">{label}</p>
      <p className="font-bold text-primary">{payload[0].value} נקודות</p>
    </div>
  )
}

export default function HealthTrendChart({ data }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    label: format(parseISO(d.date), "dd/MM"),
  }))

  return (
    <ResponsiveContainer width="100%" height={180}>
      <AreaChart data={formatted} margin={{ top: 5, right: 8, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22C55E" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#22C55E" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1C2333" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fill: "#9CA3AF", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: "#9CA3AF", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="health_score"
          stroke="#22C55E"
          strokeWidth={2.5}
          fill="url(#scoreGrad)"
          dot={false}
          activeDot={{ r: 5, fill: "#22C55E", strokeWidth: 0 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
