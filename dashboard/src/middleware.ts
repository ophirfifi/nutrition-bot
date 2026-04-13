import { NextRequest, NextResponse } from "next/server"

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Only protect /admin routes (but not the login page or login API)
  if (!pathname.startsWith("/admin")) return NextResponse.next()
  if (pathname === "/admin/login") return NextResponse.next()
  if (pathname.startsWith("/api/admin/login")) return NextResponse.next()

  const token = request.cookies.get("admin_token")?.value
  const expected = process.env.ADMIN_SECRET_TOKEN

  if (!expected || !token || token !== expected) {
    const loginUrl = request.nextUrl.clone()
    loginUrl.pathname = "/admin/login"
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/admin/:path*"],
}
