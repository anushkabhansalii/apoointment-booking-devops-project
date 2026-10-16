import Icon from "./Icon.jsx";

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: "grid" },
  { id: "schedule", label: "Schedule", icon: "calendar" },
  { id: "appointments", label: "Appointments", icon: "list" },
];

export default function Sidebar({ view, onNavigate, providers, health, open, onClose }) {
  return (
    <>
      <div className={`scrim ${open ? "show" : ""}`} onClick={onClose} />
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="brand">
          <img src="/favicon.svg" alt="" width="32" height="32" />
          <div>
            <strong>SlotSync</strong>
            <span>Bloom Wellness Studio</span>
          </div>
        </div>

        <nav aria-label="Main">
          <p className="nav-heading">Workspace</p>
          {NAV.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${view === item.id ? "active" : ""}`}
              onClick={() => {
                onNavigate(item.id);
                onClose();
              }}
            >
              <Icon name={item.icon} />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="team">
          <p className="nav-heading">Practitioners</p>
          {providers.map((p) => (
            <div key={p.id} className="team-member">
              <span className="avatar" style={{ background: p.color }}>
                {p.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
              </span>
              <div>
                <strong>{p.name}</strong>
                <span>{p.specialty}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="pipeline-card">
          <div className="pipeline-row">
            <span className={`dot ${health}`} />
            <span>{health === "up" ? "API healthy" : health === "down" ? "API unreachable" : "Checking API…"}</span>
          </div>
          <div className="pipeline-row muted">
            <Icon name="gitCommit" size={14} />
            <span>
              build <code>{__APP_VERSION__.slice(0, 7)}</code>
            </span>
          </div>
          <div className="pipeline-steps" aria-label="Delivery pipeline">
            {["test", "build", "scan", "push", "deploy"].map((step) => (
              <span key={step}>{step}</span>
            ))}
          </div>
        </div>
      </aside>
    </>
  );
}
