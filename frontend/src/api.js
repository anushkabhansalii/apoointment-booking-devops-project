// Thin wrapper around fetch. The browser always calls relative /api URLs;
// Vite (dev), Nginx (Docker) or the Ingress (Kubernetes) route them to FastAPI.

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function describe(detail) {
  if (!detail) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = d.loc?.filter((p) => p !== "body").join(".");
        return field ? `${field}: ${d.msg}` : d.msg;
      })
      .join("; ");
  }
  return JSON.stringify(detail);
}

async function request(path, { method = "GET", body } = {}) {
  let response;
  try {
    response = await fetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the SlotSync API. Is the backend running?", 0);
  }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(describe(data?.detail) || `Request failed (${response.status})`, response.status);
  }
  return data;
}

export const api = {
  listAppointments: (params = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== "" && v != null));
    return request(`/api/appointments${query.size ? `?${query}` : ""}`);
  },
  stats: () => request("/api/appointments/stats"),
  providers: () => request("/api/providers"),
  services: () => request("/api/services"),
  version: () => request("/api/version"),
  create: (payload) => request("/api/appointments", { method: "POST", body: payload }),
  update: (id, payload) => request(`/api/appointments/${id}`, { method: "PUT", body: payload }),
  setStatus: (id, status) => request(`/api/appointments/${id}/status`, { method: "PATCH", body: { status } }),
  remove: (id) => request(`/api/appointments/${id}`, { method: "DELETE" }),
};
