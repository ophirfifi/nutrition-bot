"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import clsx from "clsx"

const NAV = [
  { href: "/admin", label: "Overview", icon: "📊" },
  { href: "/admin/users", label: "Users", icon: "👥" },
  { href: "/admin/interactions", label: "Interactions", icon: "💬" },
  { href: "/admin/distress", label: "Distress Alerts", icon: "🚨" },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-56 shrink-0 bg-surface border-r border-border min-h-screen p-4 flex flex-col gap-1">
      <h1 className="text-lg font-bold text-white mb-6 px-3">Nutri Admin</h1>
      {NAV.map((item) => {
        const active =
          item.href === "/admin"
            ? pathname === "/admin"
            : pathname.startsWith(item.href)
        return (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors",
              active
                ? "bg-primary/15 text-primary font-semibold"
                : "text-muted hover:text-white hover:bg-surface-2"
            )}
          >
            <span>{item.icon}</span>
            {item.label}
          </Link>
        )
      })}
      <div className="mt-auto pt-4 border-t border-border">
        <Link
          href="/"
          className="text-xs text-muted hover:text-white px-3 py-1.5 block"
        >
          &larr; User Dashboard
        </Link>
      </div>
    </aside>
  )
}
