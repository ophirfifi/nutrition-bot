"use client"

interface Props {
  score: number  // 0–100
}

function scoreColor(score: number): string {
  if (score >= 75) return "#22C55E"
  if (score >= 45) return "#F97316"
  return "#EF4444"
}

function scoreLabel(score: number): string {
  if (score >= 75) return "מצוין! 🔥"
  if (score >= 45) return "בסדר גמור 👍"
  return "יש על מה לעבוד 💪"
}

export default function HealthScoreGauge({ score }: Props) {
  const radius = 72
  const stroke = 10
  const normalizedRadius = radius - stroke / 2
  const circumference = normalizedRadius * 2 * Math.PI
  const progress = Math.max(0, Math.min(100, score))
  const strokeDashoffset = circumference - (progress / 100) * circumference
  const color = scoreColor(score)

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative">
        <svg height={radius * 2} width={radius * 2} className="rotate-[-90deg]">
          {/* Background ring */}
          <circle
            stroke="#1C2333"
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          {/* Progress ring */}
          <circle
            stroke={color}
            fill="transparent"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
            style={{ transition: "stroke-dashoffset 0.8s ease-in-out" }}
          />
        </svg>
        {/* Score text — centered inside ring */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-black" style={{ color }}>{score}</span>
          <span className="text-xs text-muted font-medium">/ 100</span>
        </div>
      </div>
      <span className="text-sm font-semibold" style={{ color }}>{scoreLabel(score)}</span>
    </div>
  )
}
