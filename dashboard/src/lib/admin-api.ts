import type {
  AdminOverview,
  AdminUserRow,
  AdminUserDetail,
  AdminInteraction,
} from "@/types/admin"

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

function getToken(): string {
  if (typeof document === "undefined") return ""
  const match = document.cookie.match(/(?:^|; )admin_token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : ""
}

async function adminFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
    cache: "no-store",
  })
  if (!res.ok) throw new Error(`Admin API error ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

export const adminApi = {
  overview: () => adminFetch<AdminOverview>("/api/admin/overview"),
  users: (limit = 50, offset = 0) =>
    adminFetch<AdminUserRow[]>(`/api/admin/users?limit=${limit}&offset=${offset}`),
  userDetail: (tid: number) =>
    adminFetch<AdminUserDetail>(`/api/admin/users/${tid}`),
  interactions: (limit = 50) =>
    adminFetch<AdminInteraction[]>(`/api/admin/interactions?limit=${limit}`),
  distress: (limit = 50) =>
    adminFetch<AdminInteraction[]>(`/api/admin/distress?limit=${limit}`),
}
