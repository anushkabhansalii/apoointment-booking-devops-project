import Icon from "./Icon.jsx";
import { addDays, formatDay, studioDate, studioMinutes, studioTime } from "../time.js";

const OPEN = 7 * 60;
const CLOSE = 21 * 60;
const HOURS = Array.from({ length: (CLOSE - OPEN) / 60 + 1 }, (_, i) => OPEN / 60 + i);
const PX_PER_MIN = 1.1;

// One column per practitioner, one block per booking, positioned by time.
export default function DayTimeline({ day, onDayChange, appointments, providers, onOpen, onNew }) {
  const today = studioDate();
  const nowMinutes = studioMinutes(new Date());
  const visible = appointments.filter((a) => a.status !== "cancelled");

  return (
    <section className="card timeline-card">
      <header className="card-head timeline-head">
        <div className="day-switch">
          <button className="icon-btn" onClick={() => onDayChange(addDays(day, -1))} aria-label="Previous day">
            <Icon name="chevronLeft" />
          </button>
          <div>
            <h2>{formatDay(day)}</h2>
            <span className="muted">{visible.length} active bookings</span>
          </div>
          <button className="icon-btn" onClick={() => onDayChange(addDays(day, 1))} aria-label="Next day">
            <Icon name="chevronRight" />
          </button>
        </div>
        <div className="row-gap">
          {day !== today && (
            <button className="btn btn-ghost" onClick={() => onDayChange(today)}>
              Today
            </button>
          )}
          <input
            type="date"
            className="input"
            value={day}
            onChange={(e) => e.target.value && onDayChange(e.target.value)}
            aria-label="Pick a day"
          />
        </div>
      </header>

      <div className="timeline-scroll">
        <div className="timeline" style={{ "--cols": providers.length }}>
          <div className="tl-corner" />
          {providers.map((p) => (
            <div key={p.id} className="tl-provider">
              <span className="avatar sm" style={{ background: p.color }}>
                {p.name[0]}
              </span>
              <div>
                <strong>{p.name}</strong>
                <span>{p.specialty}</span>
              </div>
            </div>
          ))}

          <div className="tl-hours" style={{ height: (CLOSE - OPEN) * PX_PER_MIN }}>
            {HOURS.map((h) => (
              <span key={h} style={{ top: (h * 60 - OPEN) * PX_PER_MIN }}>
                {String(h).padStart(2, "0")}:00
              </span>
            ))}
          </div>

          {providers.map((p) => (
            <div
              key={p.id}
              className="tl-col"
              style={{ height: (CLOSE - OPEN) * PX_PER_MIN }}
              onDoubleClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const minutes = OPEN + Math.floor((e.clientY - rect.top) / PX_PER_MIN / 30) * 30;
                const hh = String(Math.floor(minutes / 60)).padStart(2, "0");
                const mm = String(minutes % 60).padStart(2, "0");
                onNew({ provider_id: p.id, date: day, time: `${hh}:${mm}` });
              }}
              title="Double-click an empty slot to book"
            >
              {HOURS.map((h) => (
                <div key={h} className="tl-line" style={{ top: (h * 60 - OPEN) * PX_PER_MIN }} />
              ))}
              {day === today && nowMinutes > OPEN && nowMinutes < CLOSE && (
                <div className="tl-now" style={{ top: (nowMinutes - OPEN) * PX_PER_MIN }} />
              )}
              {visible
                .filter((a) => a.provider_id === p.id)
                .map((a) => {
                  const top = (studioMinutes(a.start_time) - OPEN) * PX_PER_MIN;
                  const height = Math.max(a.duration_minutes * PX_PER_MIN - 3, 26);
                  return (
                    <button
                      key={a.id}
                      className={`tl-event status-${a.status}`}
                      style={{ top, height, "--accent": p.color }}
                      onClick={() => onOpen(a)}
                    >
                      <strong>{a.customer_name}</strong>
                      <span>
                        {studioTime(a.start_time)}–{studioTime(a.end_time)} · {a.service}
                      </span>
                    </button>
                  );
                })}
            </div>
          ))}
        </div>
      </div>
      <p className="hint">Tip: double-click an empty slot to book it.</p>
    </section>
  );
}
