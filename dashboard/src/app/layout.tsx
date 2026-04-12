import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "נוטרי — ההתקדמות שלי",
  description: "דשבורד תזונה אישי",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl">
      <body>{children}</body>
    </html>
  )
}
