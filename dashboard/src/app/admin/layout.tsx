import Sidebar from "@/components/admin/Sidebar"

export const metadata = {
  title: "Nutri Admin",
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div dir="ltr" lang="en" className="flex min-h-screen bg-bg text-white">
      <Sidebar />
      <main className="flex-1 p-6 overflow-auto">{children}</main>
    </div>
  )
}
