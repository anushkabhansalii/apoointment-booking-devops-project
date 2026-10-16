import { statusLabel } from "../statuses.js";

export default function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{statusLabel(status)}</span>;
}
