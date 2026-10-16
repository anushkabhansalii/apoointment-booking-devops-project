// Pure-CSS bar charts: service mix and practitioner load.
function Bars({ data, colors }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  if (!entries.length) return <p className="empty-small">No bookings yet.</p>;
  return (
    <ul className="bars">
      {entries.map(([label, value]) => (
        <li key={label}>
          <div className="bar-label">
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(value / max) * 100}%`, background: colors?.[label] }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function Insights({ stats, providers }) {
  const providerColors = Object.fromEntries(providers.map((p) => [p.name, p.color]));
  return (
    <div className="insights">
      <section className="card">
        <header className="card-head">
          <h2>Service mix</h2>
        </header>
        <Bars data={stats?.by_service ?? {}} />
      </section>
      <section className="card">
        <header className="card-head">
          <h2>Practitioner load</h2>
        </header>
        <Bars data={stats?.by_provider ?? {}} colors={providerColors} />
      </section>
    </div>
  );
}
