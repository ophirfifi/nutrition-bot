export interface AdminOverview {
  total_users: number
  active_today: number
  meals_today: number
  distress_today: number
}

export interface AdminUserRow {
  telegram_id: number
  name: string | null
  age: number | null
  sport_type: string | null
  onboarding_complete: boolean
  health_score: number
  updated_at: string | null
  created_at: string | null
}

export interface AdminInteraction {
  telegram_id: number
  user_name: string | null
  timestamp: string
  agent_type: string | null
  direction: "inbound" | "outbound"
  message_text: string | null
  message_type: string
  distress_flag: boolean
}

export interface AdminUserDetail {
  user: {
    telegram_id: number
    name: string | null
    age: number | null
    height: number | null
    sport_type: string | null
    sport_frequency: number | null
    eating_habits: Record<string, unknown> | null
    preferences: Record<string, unknown> | null
    triggers: Record<string, unknown> | null
    onboarding_complete: boolean
    created_at: string | null
  }
  meals: Array<{
    id: string
    timestamp: string
    rating: string | null
    description: string | null
    feedback_text: string | null
    categories: Record<string, unknown> | null
  }>
  scores: Array<{
    date: string
    health_score: number
    meals_count: number
    water_intake: number
    junk_count: number
  }>
  interactions: AdminInteraction[]
}
