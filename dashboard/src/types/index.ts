export interface DashboardData {
  name: string
  today: {
    health_score: number
    meals_count: number
    water_intake: number
    junk_count: number
  }
  streak: number
  onboarding_complete: boolean
}

export interface HealthHistoryPoint {
  date: string
  health_score: number
  streak_days: number
}

export interface MealEntry {
  id: string
  timestamp: string
  rating: "green" | "yellow" | "red" | null
  description: string | null
  feedback_text: string | null
  categories: {
    protein?: boolean
    carbs?: boolean
    fat?: boolean
    vegetables?: boolean
  } | null
}
