// All times are shown in the studio's timezone, whatever the browser's is.
export const STUDIO_TZ = "Asia/Kolkata";

const partsFormatter = new Intl.DateTimeFormat("en-CA", {
  timeZone: STUDIO_TZ,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

function parts(date) {
  return Object.fromEntries(partsFormatter.formatToParts(new Date(date)).map((p) => [p.type, p.value]));
}

/** "YYYY-MM-DD" of a moment, in studio time. */
export function studioDate(date = new Date()) {
  const p = parts(date);
  return `${p.year}-${p.month}-${p.day}`;
}

/** "HH:mm" of a moment, in studio time. */
export function studioTime(date) {
  const p = parts(date);
  return `${p.hour}:${p.minute}`;
}

/** Minutes since studio-local midnight. */
export function studioMinutes(date) {
  const p = parts(date);
  return Number(p.hour) * 60 + Number(p.minute);
}

export function addDays(isoDay, days) {
  const d = new Date(`${isoDay}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export function formatDay(isoDay, opts = { weekday: "long", day: "numeric", month: "long" }) {
  return new Date(`${isoDay}T12:00:00Z`).toLocaleDateString("en-IN", { ...opts, timeZone: "UTC" });
}

export function formatDateTime(date) {
  return new Date(date).toLocaleString("en-IN", {
    timeZone: STUDIO_TZ,
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function relative(date) {
  const diff = (new Date(date) - Date.now()) / 60000;
  const abs = Math.abs(diff);
  const fmt = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  if (abs < 60) return fmt.format(Math.round(diff), "minute");
  if (abs < 60 * 24) return fmt.format(Math.round(diff / 60), "hour");
  return fmt.format(Math.round(diff / 1440), "day");
}

export const rupees = (n) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
