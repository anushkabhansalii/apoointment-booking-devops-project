import Icon from "./Icon.jsx";
import StatusBadge from "./StatusBadge.jsx";
import { STATUSES } from "../statuses.js";
import { formatDateTime } from "../time.js";

const NEXT_ACTIONS = {
  scheduled: [
    { status: "confirmed", label: "Confirm", icon: "check" },
    { status: "cancelled", label: "Cancel", icon: "x" },
  ],
  confirmed: [
    { status: "completed", label: "Complete", icon: "check" },
    { status: "no_show", label: "No-show", icon: "x" },
  ],
  completed: [],
  cancelled: [{ status: "scheduled", label: "Restore", icon: "refresh" }],
  no_show: [{ status: "scheduled", label: "Rebook", icon: "refresh" }],
};

export default function AppointmentsTable({
  appointments,
  providers,
  filters,
  onFiltersChange,
  counts,
  onEdit,
  onStatus,
  onDelete,
  loading,
}) {
  const set = (patch) => onFiltersChange({ ...filters, ...patch });
  return (
    <section className="card">
      <header className="card-head wrap">
        <h2>Appointments</h2>
        <div className="filters">
          <label className="search">
            <Icon name="search" size={16} />
            <input
              placeholder="Search name, email or service"
              value={filters.search}
              onChange={(e) => set({ search: e.target.value })}
            />
          </label>
          <select className="input" value={filters.provider_id} onChange={(e) => set({ provider_id: e.target.value })}>
            <option value="">All practitioners</option>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </header>

      <div className="chips" role="tablist" aria-label="Filter by status">
        <button className={`chip ${filters.status === "" ? "active" : ""}`} onClick={() => set({ status: "" })}>
          All <span>{counts.total}</span>
        </button>
        {STATUSES.map((s) => (
          <button
            key={s.value}
            className={`chip ${filters.status === s.value ? "active" : ""}`}
            onClick={() => set({ status: s.value })}
          >
            {s.label} <span>{counts.by_status?.[s.value] ?? 0}</span>
          </button>
        ))}
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Customer</th>
              <th>Service</th>
              <th>Practitioner</th>
              <th>When</th>
              <th>Status</th>
              <th aria-label="Actions" />
            </tr>
          </thead>
          <tbody>
            {loading && appointments.length === 0 &&
              Array.from({ length: 4 }, (_, i) => (
                <tr key={i} className="skeleton-row">
                  <td colSpan={6}>
                    <span className="skeleton" />
                  </td>
                </tr>
              ))}
            {!loading && appointments.length === 0 && (
              <tr>
                <td colSpan={6} className="empty-cell">
                  No appointments match these filters.
                </td>
              </tr>
            )}
            {appointments.map((a) => (
              <tr key={a.id}>
                <td data-label="Customer">
                  <strong>{a.customer_name}</strong>
                  <span className="sub">{a.customer_email}</span>
                </td>
                <td data-label="Service">
                  {a.service}
                  <span className="sub">{a.duration_minutes} min</span>
                </td>
                <td data-label="Practitioner">
                  <span className="who">
                    <span className="dot-color" style={{ background: a.provider.color }} />
                    {a.provider.name}
                  </span>
                </td>
                <td data-label="When">{formatDateTime(a.start_time)}</td>
                <td data-label="Status">
                  <StatusBadge status={a.status} />
                </td>
                <td className="actions">
                  {NEXT_ACTIONS[a.status].map((action) => (
                    <button
                      key={action.status}
                      className={`btn btn-xs act-${action.status}`}
                      onClick={() => onStatus(a, action.status)}
                    >
                      <Icon name={action.icon} size={14} />
                      {action.label}
                    </button>
                  ))}
                  <button className="icon-btn" onClick={() => onEdit(a)} aria-label={`Edit ${a.customer_name}`}>
                    <Icon name="edit" size={16} />
                  </button>
                  <button
                    className="icon-btn danger"
                    onClick={() => onDelete(a)}
                    aria-label={`Delete ${a.customer_name}`}
                  >
                    <Icon name="trash" size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
