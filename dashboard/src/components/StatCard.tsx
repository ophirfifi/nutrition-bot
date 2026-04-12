interface Props {
  icon: string
  label: string
  value: string | number
  sub?: string
  highlight?: boolean
}

export default function StatCard({ icon, label, value, sub, highlight }: Props) {
  return (
    <div
      className={`rounded-2xl p-4 flex flex-col gap-1 border animate-fade-in ${
        highlight
          ? "bg-primary/10 border-primary/30"
          : "bg-surface border-border"
      }`}
    >
      <span className="text-2xl">{icon}</span>
      <span className="text-2xl font-black text-white mt-1">{value}</span>
      <span className="text-xs font-medium text-muted">{label}</span>
      {sub && <span className="text-xs text-muted/70">{sub}</span>}
    </div>
  )
}
