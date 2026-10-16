"""Business metrics exposed on /metrics next to the HTTP metrics.

HTTP request count/latency come from prometheus-fastapi-instrumentator; these
counters answer the questions the studio actually cares about.
"""

from prometheus_client import Counter

from app.catalog import SERVICES
from app.models import AppointmentStatus

APPOINTMENTS_CREATED = Counter(
    "slotsync_appointments_created_total",
    "Appointments booked, by service",
    ["service"],
)
STATUS_CHANGES = Counter(
    "slotsync_appointment_status_changes_total",
    "Appointment status transitions, by new status",
    ["status"],
)
BOOKING_CONFLICTS = Counter(
    "slotsync_booking_conflicts_total",
    "Bookings rejected because the provider was already booked",
)

# Pre-create every label combination so Grafana shows 0 instead of "No data"
# before the first booking arrives.
for _service in SERVICES:
    APPOINTMENTS_CREATED.labels(service=_service)
for _status in AppointmentStatus:
    STATUS_CHANGES.labels(status=_status.value)
