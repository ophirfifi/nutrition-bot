interface Achievement {
  id: string
  icon: string
  label: string
  description: string
  earned: boolean
}

function getAchievements(streak: number, mealsToday: number, waterToday: number): Achievement[] {
  return [
    {
      id: "first_meal",
      icon: "🍽",
      label: "ארוחה ראשונה",
      description: "שלחת את הארוחה הראשונה שלך",
      earned: mealsToday >= 1,
    },
    {
      id: "hydrated",
      icon: "💧",
      label: "שתיין",
      description: "שתית 6+ כוסות מים היום",
      earned: waterToday >= 6,
    },
    {
      id: "streak3",
      icon: "🔥",
      label: "3 ימים ברצף",
      description: "שמרת על איזון 3 ימים רצופים",
      earned: streak >= 3,
    },
    {
      id: "streak7",
      icon: "⚡",
      label: "שבוע מלא",
      description: "7 ימים רצופים של הרגלים טובים",
      earned: streak >= 7,
    },
    {
      id: "balanced",
      icon: "🥗",
      label: "ארוחה מאוזנת",
      description: "קיבלת דירוג ירוק על ארוחה",
      earned: mealsToday >= 1,  // simplified — ideally check ratings
    },
    {
      id: "streak30",
      icon: "🏆",
      label: "חודש!",
      description: "30 ימים רצופים — אלוף!",
      earned: streak >= 30,
    },
  ]
}

interface Props {
  streak: number
  mealsToday: number
  waterToday: number
}

export default function AchievementsSection({ streak, mealsToday, waterToday }: Props) {
  const achievements = getAchievements(streak, mealsToday, waterToday)
  const earned = achievements.filter((a) => a.earned)
  const locked = achievements.filter((a) => !a.earned)

  return (
    <div>
      {earned.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-muted mb-2 font-medium">🏅 הישגים שהשגת</p>
          <div className="grid grid-cols-3 gap-2">
            {earned.map((a) => (
              <BadgeCard key={a.id} achievement={a} />
            ))}
          </div>
        </div>
      )}
      {locked.length > 0 && (
        <div>
          <p className="text-xs text-muted mb-2 font-medium">🔒 הישגים הבאים</p>
          <div className="grid grid-cols-3 gap-2">
            {locked.slice(0, 3).map((a) => (
              <BadgeCard key={a.id} achievement={a} locked />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function BadgeCard({ achievement, locked = false }: { achievement: Achievement; locked?: boolean }) {
  return (
    <div
      className={`rounded-xl p-3 flex flex-col items-center gap-1 text-center border ${
        locked
          ? "bg-surface border-border opacity-40"
          : "bg-surface-2 border-primary/20 animate-scale-in"
      }`}
    >
      <span className={`text-2xl ${locked ? "grayscale" : ""}`}>{achievement.icon}</span>
      <span className="text-[11px] font-semibold text-white leading-tight">{achievement.label}</span>
      <span className="text-[9px] text-muted leading-tight">{achievement.description}</span>
    </div>
  )
}
