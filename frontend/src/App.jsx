import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import { formatDay, studioDate } from "./time.js";
import Agenda from "./components/Agenda.jsx";
import AppointmentModal from "./components/AppointmentModal.jsx";
import AppointmentsTable from "./components/AppointmentsTable.jsx";
import DayTimeline from "./components/DayTimeline.jsx";
import Icon from "./components/Icon.jsx";
import Insights from "./components/Insights.jsx";
import KpiCards from "./components/KpiCards.jsx";
import Sidebar from "./components/Sidebar.jsx";
import { statusLabel } from "./statuses.js";
import Toasts from "./components/Toasts.jsx";

const TITLES = {
  dashboard: "Front desk",
  schedule: "Schedule",
  appointments: "Appointments",
};

export default function App() {
  const [view, setView] = useState("dashboard");
  const [menuOpen, setMenuOpen] = useState(false);
  const [providers, setProviders] = useState([]);
  const [services, setServices] = useState([]);
  const [apiVersion, setApiVersion] = useState(null);
  const [stats, setStats] = useState(null);
  const [dayAppointments, setDayAppointments] = useState([]);
  const [todayAppointments, setTodayAppointments] = useState([]);
  const [list, setList] = useState([]);
  const [day, setDay] = useState(studioDate());
  const [filters, setFilters] = useState({ status: "", provider_id: "", search: "" });
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [modal, setModal] = useState(null); // { appointment?, preset? }
  const [toasts, setToasts] = useState([]);

  const toast = useCallback((message, tone = "success") => {
    const id = crypto.randomUUID?.() ?? String(Math.random());
    setToasts((t) => [...t, { id, message, tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4500);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [s, today, onDay, all] = await Promise.all([
        api.stats(),
        api.listAppointments({ day: studioDate() }),
        api.listAppointments({ day }),
        api.listAppointments(filters),
      ]);
      setStats(s);
      setTodayAppointments(today);
      setDayAppointments(onDay);
      setList(all);
      setLoadError(null);
    } catch (err) {
      setLoadError(err.message);
    } finally {
      setLoading(false);
    }
  }, [day, filters]);

  useEffect(() => {
    Promise.all([api.providers(), api.services(), api.version()])
      .then(([p, s, v]) => {
        setProviders(p);
        setServices(s);
        setApiVersion(v.version);
      })
      .catch((err) => setLoadError(err.message));
  }, []);

  // Debounce so typing in the search box does not fire a request per key.
  useEffect(() => {
    const handle = setTimeout(refresh, 200);
    return () => clearTimeout(handle);
  }, [refresh]);

  const health = loadError ? "down" : stats ? "up" : "pending";

  async function save(payload) {
    if (modal?.appointment) {
      await api.update(modal.appointment.id, payload);
      toast(`Updated ${payload.customer_name}'s booking`);
    } else {
      const created = await api.create(payload);
      toast(`Booked ${created.customer_name} with ${created.provider.name}`);
    }
    setModal(null);
    refresh();
  }

  async function changeStatus(appointment, status) {
    try {
      await api.setStatus(appointment.id, status);
      toast(`${appointment.customer_name}: ${statusLabel(status)}`);
      refresh();
    } catch (err) {
      toast(err.message, "error");
    }
  }

  async function remove(appointment) {
    if (!window.confirm(`Delete ${appointment.customer_name}'s ${appointment.service} booking?`)) return;
    try {
      await api.remove(appointment.id);
      toast("Appointment deleted");
      setModal(null);
      refresh();
    } catch (err) {
      toast(err.message, "error");
    }
  }

  const counts = useMemo(() => ({ total: stats?.total ?? 0, by_status: stats?.by_status }), [stats]);
  const openNew = (preset) => setModal({ preset });
  const openEdit = (appointment) => setModal({ appointment });

  return (
    <div className="shell">
      <Sidebar
        view={view}
        onNavigate={setView}
        providers={providers}
        health={health}
        apiVersion={apiVersion}
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
      />

      <main className="main">
        <header className="topbar">
          <button className="icon-btn menu-btn" onClick={() => setMenuOpen(true)} aria-label="Open menu">
            <Icon name="menu" />
          </button>
          <div>
            <p className="eyebrow">{formatDay(studioDate())}</p>
            <h1>{TITLES[view]}</h1>
          </div>
          <div className="topbar-actions">
            <button className="icon-btn" onClick={refresh} aria-label="Refresh" title="Refresh">
              <Icon name="refresh" className={loading ? "spin" : ""} />
            </button>
            <button className="btn btn-primary" onClick={() => openNew()} disabled={!providers.length}>
              <Icon name="plus" size={16} /> New booking
            </button>
          </div>
        </header>

        {loadError && (
          <div className="banner" role="alert">
            <Icon name="alert" />
            <div>
              <strong>Backend unavailable.</strong> {loadError}
            </div>
            <button className="btn btn-ghost" onClick={refresh}>
              Retry
            </button>
          </div>
        )}

        {view === "dashboard" && (
          <>
            <KpiCards stats={stats} />
            <div className="dash-grid">
              <Agenda
                appointments={todayAppointments}
                nextAppointment={stats?.next_appointment}
                onOpen={openEdit}
                onNew={() => openNew()}
              />
              <Insights stats={stats} providers={providers} />
            </div>
          </>
        )}

        {view === "schedule" && (
          <DayTimeline
            day={day}
            onDayChange={setDay}
            appointments={dayAppointments}
            providers={providers}
            onOpen={openEdit}
            onNew={openNew}
          />
        )}

        {view === "appointments" && (
          <AppointmentsTable
            appointments={list}
            providers={providers}
            filters={filters}
            onFiltersChange={setFilters}
            counts={counts}
            loading={loading}
            onEdit={openEdit}
            onStatus={changeStatus}
            onDelete={remove}
          />
        )}
      </main>

      {modal && (
        <AppointmentModal
          appointment={modal.appointment}
          preset={modal.preset}
          providers={providers}
          services={services}
          onClose={() => setModal(null)}
          onSave={save}
          onDelete={remove}
        />
      )}
      <Toasts toasts={toasts} onDismiss={(id) => setToasts((t) => t.filter((x) => x.id !== id))} />
    </div>
  );
}
