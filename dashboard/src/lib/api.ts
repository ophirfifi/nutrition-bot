import type { DashboardData, HealthHistoryPoint, MealEntry } from "@/types"

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { next: { revalidate: 60 } })
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

export const api = {
  dashboard: (telegramId: number) =>
    apiFetch<DashboardData>(`/api/dashboard/${telegramId}`),

  healthHistory: (telegramId: number, days = 30) =>
    apiFetch<HealthHistoryPoint[]>(`/api/health-history/${telegramId}?days=${days}`),

  meals: (telegramId: number, limit = 8) =>
    apiFetch<MealEntry[]>(`/api/meals/${telegramId}?limit=${limit}`),
}
