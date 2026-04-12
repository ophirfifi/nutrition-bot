import type { MealEntry } from "@/types"
import { format, parseISO } from "date-fns"

const RATING_CONFIG = {
  green:  { emoji: "🟢", label: "מאוזן",          bg: "bg-green-900/30",  border: "border-green-700/40" },
  yellow: { emoji: "🟡", label: "בסדר",            bg: "bg-yellow-900/30", border: "border-yellow-700/40" },
  red:    { emoji: "🔴", label: "פחות אידיאלי",   bg: "bg-red-900/30",    border: "border-red-700/40" },
} as const

interface Props {
  meals: MealEntry[]
}

export default function MealsLog({ meals }: Props) {
  if (meals.length === 0) {
    return (
      <div className="text-center py-8 text-muted">
        <p className="text-3xl mb-2">🍽</p>
        <p className="text-sm">עדיין לא שלחת ארוחות היום</p>
        <p className="text-xs mt-1 text-muted/60">שלח תמונה בטלגרם לפידבק מיידי</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {meals.map((meal) => {
        const cfg = meal.rating ? RATING_CONFIG[meal.rating] : RATING_CONFIG.yellow
        const time = meal.timestamp
          ? format(parseISO(meal.timestamp), "HH:mm")
          : ""
        return (
          <div
            key={meal.id}
            className={`rounded-xl p-3 border flex gap-3 items-start animate-fade-in ${cfg.bg} ${cfg.border}`}
          >
            <span className="text-xl mt-0.5">{cfg.emoji}</span>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-center gap-2">
                <span className="text-sm font-semibold text-white truncate">
                  {meal.description || "ארוחה"}
                </span>
                <span className="text-xs text-muted shrink-0">{time}</span>
              </div>
              {meal.feedback_text && (
                <p className="text-xs text-muted mt-1 leading-relaxed">{meal.feedback_text}</p>
              )}
              {meal.categories && (
                <div className="flex gap-1 mt-2 flex-wrap">
                  {meal.categories.protein  && <Tag label="חלבון" />}
                  {meal.categories.carbs    && <Tag label="פחמימות" />}
                  {meal.categories.fat      && <Tag label="שומן" />}
                  {meal.categories.vegetables && <Tag label="ירקות" color="green" />}
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function Tag({ label, color = "gray" }: { label: string; color?: "gray" | "green" }) {
  return (
    <span
      className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
        color === "green"
          ? "bg-green-800/50 text-green-300"
          : "bg-white/10 text-muted"
      }`}
    >
      {label}
    </span>
  )
}
