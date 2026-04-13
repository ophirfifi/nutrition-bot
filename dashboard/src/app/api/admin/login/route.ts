import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  const { token } = await request.json()
  const expected = process.env.ADMIN_SECRET_TOKEN

  if (!expected || token !== expected) {
    return NextResponse.json({ error: "Invalid token" }, { status: 401 })
  }

  const response = NextResponse.json({ ok: true })
  response.cookies.set("admin_token", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7, // 7 days
  })
  return response
}
