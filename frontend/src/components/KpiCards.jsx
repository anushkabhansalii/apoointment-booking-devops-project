import Icon from "./Icon.jsx";
import { rupees } from "../time.js";

export default function KpiCards({ stats }) {
  const cards = [
    {
      label: "Today's bookings",
      value: stats?.today ?? "–",
      hint: `${stats?.by_status?.confirmed ?? 0} confirmed overall`,
      icon: "calendar",
      tone: "indigo",
    },
    {
      label: "Upcoming",
      value: stats?.upcoming ?? "–",
      hint: "scheduled or confirmed",
      icon: "clock",
      tone: "teal",
    },
    {
      label: "Completion rate",
      value: stats ? `${Math.round(stats.completion_rate * 100)}%` : "–",
      hint: `${stats?.by_status?.no_show ?? 0} no-shows`,
      icon: "trend",
      tone: "amber",
    },
    {
      label: "Booked revenue",
      value: stats ? rupees(stats.booked_revenue) : "–",
      hint: `${Math.round((stats?.cancellation_rate ?? 0) * 100)}% cancelled`,
      icon: "wallet",
      tone: "pink",
    },
  ];
  return (
    <section className="kpis" aria-label="Key metrics">
      {cards.map((card) => (
        <article key={card.label} className={`kpi tone-${card.tone}`}>
          <div className="kpi-icon">
            <Icon name={card.icon} />
          </div>
          <div>
            <p>{card.label}</p>
            <strong>{card.value}</strong>
            <span>{card.hint}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
