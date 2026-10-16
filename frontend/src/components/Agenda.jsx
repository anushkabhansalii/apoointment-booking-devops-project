import Icon from "./Icon.jsx";
import StatusBadge from "./StatusBadge.jsx";
import { relative, studioTime } from "../time.js";

// Compact list of one day's bookings, used on the dashboard.
export default function Agenda({ appointments, onOpen, onNew, nextAppointment }) {
  const active = appointments.filter((a) => a.status !== "cancelled");
  return (
    <section className="card agenda">
      <header className="card-head">
        <h2>Today's schedule</h2>
        <span className="pill">{active.length} bookings</span>
      </header>

      {nextAppointment && (
        <div className="next-up" style={{ "--accent": nextAppointment.provider.color }}>
          <span className="eyebrow">Next up · {relative(nextAppointment.start_time)}</span>
          <strong>{nextAppointment.customer_name}</strong>
          <span>
            {nextAppointment.service} with {nextAppointment.provider.name}
          </span>
        </div>
      )}

      {active.length === 0 ? (
        <div className="empty">
          <Icon name="calendar" size={28} />
          <p>No bookings today.</p>
          <button className="btn btn-ghost" onClick={onNew}>
            <Icon name="plus" size={16} /> Add one
          </button>
        </div>
      ) : (
        <ol className="agenda-list">
          {active.map((a) => (
            <li key={a.id}>
              <button className="agenda-item" onClick={() => onOpen(a)}>
                <span className="agenda-time">
                  {studioTime(a.start_time)}
                  <small>{studioTime(a.end_time)}</small>
                </span>
                <span className="agenda-bar" style={{ background: a.provider.color }} />
                <span className="agenda-body">
                  <strong>{a.customer_name}</strong>
                  <span>
                    {a.service} · {a.provider.name}
                  </span>
                </span>
                <StatusBadge status={a.status} />
              </button>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
