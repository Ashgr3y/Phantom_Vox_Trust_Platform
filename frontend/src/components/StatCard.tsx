import type { LucideIcon } from "lucide-react";

export function StatCard({
  label,
  value,
  detail,
  icon: Icon,
  tone = "blue",
}: {
  label: string;
  value: string | number;
  detail: string;
  icon: LucideIcon;
  tone?: "blue" | "cyan" | "green" | "amber" | "red";
}) {
  return (
    <article className="stat-card">
      <div className={`stat-icon tone-${tone}`}><Icon size={19} aria-hidden="true" /></div>
      <div>
        <p className="stat-label">{label}</p>
        <strong className="stat-value">{value}</strong>
        <p className="stat-detail">{detail}</p>
      </div>
    </article>
  );
}
