import { Suspense } from "react"
import { api } from "@/lib/api"
import HealthScoreGauge from "@/components/HealthScoreGauge"
import HealthTrendChart from "@/components/HealthTrendChart"
import StatCard from "@/components/StatCard"
import MealsLog from "@/components/MealsLog"
import AchievementsSection from "@/components/AchievementsSection"
import { format } from "date-fns"

// Telegram ID comes from URL: /dashboard?id=123456789
interface Props {
  searchParams: { id?: string }
}

async function DashboardContent({ telegramId }: { telegramId: number }) {
  const [dashboard, history, meals] = await Promise.all([
    api.dashboard(telegramId),
    api.healthHistory(telegramId, 14),
    api.meals(telegramId, 8),
  ])

  const today = format(new Date(), "EEEE, d MMMM")
  const score = dashboard.today.health_score

  return (
    <div className="min-h-screen bg-bg text-white pb-16">
      {/* ── Header ─────────────────────────────────────────── */}
      <div className="px-5 pt-8 pb-4">
        <p className="text-muted text-sm">{today}</p>
        <h1 className="text-3xl font-black mt-0.5">
          שלום {dashboard.name || "חבר"} 👋
        </h1>
      </div>

      {/* ── Health Score card ──────────────────────────────── */}
      <section className="mx-4 mb-4">
        <div className="glass rounded-3xl p-5 animate-fade-in">
          <p className="text-muted text-xs font-semibold uppercase tracking-widest mb-4">
            ניקוד בריאות יומי
          </p>
          <div className="flex items-center gap-6">
            <HealthScoreGauge score={score} />
            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted mb-2">7 הימים האחרונים</p>
              <HealthTrendChart data={history} />
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats grid ─────────────────────────────────────── */}
      <section className="px-4 mb-4 grid grid-cols-2 gap-3">
        <StatCard
          icon="🔥"
          label="ימים ברצף"
          value={dashboard.streak}
          sub={dashboard.streak >= 3 ? "כל הכבוד!" : "בוא נשבור שיא 💪"}
          highlight={dashboard.streak >= 3}
        />
        <StatCard
          icon="🍽"
          label="ארוחות היום"
          value={dashboard.today.meals_count}
        />
        <StatCard
          icon="💧"
          label="כוסות מים"
          value={dashboard.today.water_intake}
          sub="יעד: 8 כוסות"
        />
        <StatCard
          icon="⚡"
          label="ג׳אנק היום"
          value={dashboard.today.junk_count}
          sub={dashboard.today.junk_count === 0 ? "נקי לגמרי! 🌟" : "לגמרי בסדר מדי פעם"}
        />
      </section>

      {/* ── Meals log ──────────────────────────────────────── */}
      <section className="mx-4 mb-4">
        <div className="glass rounded-3xl p-5">
          <h2 className="font-bold text-base mb-4">הארוחות שלי 🥗</h2>
          <Suspense fallback={<p className="text-muted text-sm">טוען...</p>}>
            <MealsLog meals={meals} />
          </Suspense>
        </div>
      </section>

      {/* ── Achievements ───────────────────────────────────── */}
      <section className="mx-4 mb-4">
        <div className="glass rounded-3xl p-5">
          <h2 className="font-bold text-base mb-4">הישגים 🏅</h2>
          <AchievementsSection
            streak={dashboard.streak}
            mealsToday={dashboard.today.meals_count}
            waterToday={dashboard.today.water_intake}
          />
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────── */}
      <div className="text-center mt-4 px-4">
        <p className="text-xs text-muted/50">
          נוטרי • אפליקציית תזונה חכמה לנוער
        </p>
      </div>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="min-h-screen bg-bg flex flex-col items-center justify-center gap-4 px-6 text-center">
      <span className="text-5xl">😕</span>
      <h1 className="text-xl font-bold text-white">משהו השתבש</h1>
      <p className="text-muted text-sm">{message}</p>
    </div>
  )
}

function NoId() {
  return (
    <div className="min-h-screen bg-bg flex flex-col items-center justify-center gap-4 px-6 text-center">
      <span className="text-5xl">🤖</span>
      <h1 className="text-2xl font-black text-white">נוטרי</h1>
      <p className="text-muted">כדי לראות את הדשבורד שלך,</p>
      <p className="text-muted">פנה ל-<strong className="text-white">@NutriBot</strong> בטלגרם</p>
      <p className="text-xs text-muted/60 mt-4">הבוט ישלח לך לינק אישי לדשבורד</p>
    </div>
  )
}

export default async function DashboardPage({ searchParams }: Props) {
  const rawId = searchParams.id
  if (!rawId) return <NoId />

  const telegramId = parseInt(rawId, 10)
  if (isNaN(telegramId)) return <ErrorState message="מזהה משתמש לא תקין" />

  try {
    return (
      <Suspense
        fallback={
          <div className="min-h-screen bg-bg flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-muted text-sm">טוען את הדשבורד שלך...</p>
            </div>
          </div>
        }
      >
        <DashboardContent telegramId={telegramId} />
      </Suspense>
    )
  } catch {
    return <ErrorState message="לא נמצא משתמש. האם כבר נרשמת לבוט?" />
  }
}
