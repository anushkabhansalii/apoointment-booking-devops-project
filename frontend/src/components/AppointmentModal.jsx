import { useEffect, useRef, useState } from "react";
import Icon from "./Icon.jsx";
import { STATUSES } from "../statuses.js";
import { rupees, studioDate, studioTime } from "../time.js";

function initialForm(appointment, preset, providers) {
  if (appointment) {
    return {
      customer_name: appointment.customer_name,
      customer_email: appointment.customer_email,
      customer_phone: appointment.customer_phone ?? "",
      service: appointment.service,
      provider_id: String(appointment.provider_id),
      date: studioDate(appointment.start_time),
      time: studioTime(appointment.start_time),
      duration_minutes: String(appointment.duration_minutes),
      status: appointment.status,
      notes: appointment.notes ?? "",
    };
  }
  return {
    customer_name: "",
    customer_email: "",
    customer_phone: "",
    service: "",
    provider_id: String(preset?.provider_id ?? providers[0]?.id ?? ""),
    date: preset?.date ?? studioDate(),
    time: preset?.time ?? "10:00",
    duration_minutes: "",
    status: "scheduled",
    notes: "",
  };
}

export default function AppointmentModal({ appointment, preset, providers, services, onClose, onSave, onDelete }) {
  const editing = Boolean(appointment);
  const [form, setForm] = useState(() => initialForm(appointment, preset, providers));
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const firstField = useRef(null);

  useEffect(() => {
    firstField.current?.focus();
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const service = services.find((s) => s.name === form.service);
  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    const payload = {
      customer_name: form.customer_name,
      customer_email: form.customer_email,
      customer_phone: form.customer_phone || null,
      service: form.service,
      provider_id: Number(form.provider_id),
      // Sent without an offset: the API treats it as studio-local time.
      start_time: `${form.date}T${form.time}:00`,
      duration_minutes: form.duration_minutes ? Number(form.duration_minutes) : service?.duration,
      notes: form.notes || null,
    };
    if (editing) payload.status = form.status;
    try {
      await onSave(payload);
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <form className="modal" onSubmit={submit} role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <header className="modal-head">
          <div>
            <h2 id="modal-title">{editing ? "Edit appointment" : "New appointment"}</h2>
            <p className="muted">{editing ? `Booking #${appointment.id}` : "Book a session for a customer"}</p>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
            <Icon name="x" />
          </button>
        </header>

        <div className="form-grid">
          <label className="field span-2">
            <span>Customer name</span>
            <input ref={firstField} className="input" required minLength={2} value={form.customer_name} onChange={set("customer_name")} placeholder="e.g. Riya Kapoor" />
          </label>
          <label className="field">
            <span>Email</span>
            <input className="input" type="email" required value={form.customer_email} onChange={set("customer_email")} placeholder="riya@example.com" />
          </label>
          <label className="field">
            <span>Phone</span>
            <input className="input" type="tel" value={form.customer_phone} onChange={set("customer_phone")} placeholder="+91 98765 43210" />
          </label>
          <label className="field">
            <span>Service</span>
            <select className="input" required value={form.service} onChange={set("service")}>
              <option value="" disabled>
                Choose a service
              </option>
              {services.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name} · {s.duration} min · {rupees(s.price)}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Practitioner</span>
            <select className="input" required value={form.provider_id} onChange={set("provider_id")}>
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} — {p.specialty}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Date</span>
            <input className="input" type="date" required value={form.date} onChange={set("date")} />
          </label>
          <label className="field">
            <span>Start time</span>
            <input className="input" type="time" required step={900} min="07:00" max="20:45" value={form.time} onChange={set("time")} />
          </label>
          <label className="field">
            <span>Duration (min)</span>
            <input className="input" type="number" min={15} max={240} step={5} value={form.duration_minutes} onChange={set("duration_minutes")} placeholder={service ? `${service.duration} (default)` : "From service"} />
          </label>
          {editing ? (
            <label className="field">
              <span>Status</span>
              <select className="input" value={form.status} onChange={set("status")}>
                {STATUSES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <div className="field price-preview">
              <span>Price</span>
              <strong>{service ? rupees(service.price) : "—"}</strong>
            </div>
          )}
          <label className="field span-2">
            <span>Notes</span>
            <textarea className="input" rows={3} value={form.notes} onChange={set("notes")} placeholder="Injuries, preferences, first visit…" />
          </label>
        </div>

        {error && (
          <div className="form-error" role="alert">
            <Icon name="alert" size={16} /> {error}
          </div>
        )}

        <footer className="modal-foot">
          {editing && (
            <button type="button" className="btn btn-danger-ghost" onClick={() => onDelete(appointment)}>
              <Icon name="trash" size={16} /> Delete
            </button>
          )}
          <span className="spacer" />
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Saving…" : editing ? "Save changes" : "Book appointment"}
          </button>
        </footer>
      </form>
    </div>
  );
}
