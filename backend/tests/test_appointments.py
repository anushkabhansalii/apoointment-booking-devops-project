"""Appointment CRUD and booking rules."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

IST = ZoneInfo("Asia/Kolkata")


# ---------- create ----------


def test_create_appointment_returns_201_and_defaults(client, booking):
    response = client.post("/api/appointments", json=booking())
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["status"] == "scheduled"
    assert body["duration_minutes"] == 60  # taken from the service menu
    assert body["provider"]["name"] == "Aarav Mehta"
    # 10:00 studio time (IST, UTC+5:30) is stored and returned as 04:30 UTC.
    assert datetime.fromisoformat(body["start_time"]) == datetime(2030, 1, 15, 4, 30, tzinfo=UTC)
    assert datetime.fromisoformat(body["end_time"]) == datetime(2030, 1, 15, 5, 30, tzinfo=UTC)


def test_create_accepts_explicit_timezone_and_duration(client, booking):
    payload = booking(start_time="2030-01-15T06:00:00+00:00", duration_minutes=90)
    body = client.post("/api/appointments", json=payload).json()
    assert body["duration_minutes"] == 90
    assert datetime.fromisoformat(body["start_time"]).astimezone(IST).hour == 11


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("customer_email", "not-an-email"),
        ("service", "Skydiving"),
        ("customer_name", " "),
        ("provider_id", 0),
        ("duration_minutes", 5),
    ],
)
def test_create_rejects_invalid_payload(client, booking, field, value):
    response = client.post("/api/appointments", json=booking(**{field: value}))
    assert response.status_code == 422


def test_create_rejects_unknown_or_inactive_provider(client, booking):
    assert client.post("/api/appointments", json=booking(provider_id=99)).status_code == 422
    assert client.post("/api/appointments", json=booking(provider_id=3)).status_code == 422


@pytest.mark.parametrize("start", ["2030-01-15T06:30:00", "2030-01-15T20:30:00"])
def test_create_rejects_outside_opening_hours(client, booking, start):
    response = client.post("/api/appointments", json=booking(start_time=start))
    assert response.status_code == 422
    assert "07:00 and 21:00" in response.json()["detail"]


def test_double_booking_same_provider_is_rejected(client, booking):
    assert client.post("/api/appointments", json=booking()).status_code == 201
    overlap = client.post("/api/appointments", json=booking(start_time="2030-01-15T10:30:00"))
    assert overlap.status_code == 409
    assert "already booked from 10:00 to 11:00" in overlap.json()["detail"]


def test_back_to_back_and_other_provider_are_allowed(client, booking):
    assert client.post("/api/appointments", json=booking()).status_code == 201
    assert client.post("/api/appointments", json=booking(start_time="2030-01-15T11:00:00")).status_code == 201
    assert client.post("/api/appointments", json=booking(provider_id=2)).status_code == 201


def test_cancelled_booking_frees_the_slot(client, booking):
    first = client.post("/api/appointments", json=booking()).json()
    client.patch(f"/api/appointments/{first['id']}/status", json={"status": "cancelled"})
    assert client.post("/api/appointments", json=booking()).status_code == 201


# ---------- read ----------


def test_get_appointment_by_id(client, booking):
    created = client.post("/api/appointments", json=booking()).json()
    response = client.get(f"/api/appointments/{created['id']}")
    assert response.status_code == 200
    assert response.json()["customer_email"] == "riya@example.com"


def test_get_missing_appointment_returns_404(client):
    response = client.get("/api/appointments/12345")
    assert response.status_code == 404
    assert response.json()["detail"] == "Appointment 12345 not found"


def test_list_is_sorted_and_filterable(client, booking):
    client.post("/api/appointments", json=booking(start_time="2030-01-16T09:00:00", customer_name="Zoya"))
    second = client.post("/api/appointments", json=booking(customer_name="Arjun", service="Pilates")).json()
    client.patch(f"/api/appointments/{second['id']}/status", json={"status": "confirmed"})

    names = [a["customer_name"] for a in client.get("/api/appointments").json()]
    assert names == ["Arjun", "Zoya"]  # earliest first

    confirmed = client.get("/api/appointments", params={"status": "confirmed"}).json()
    assert [a["customer_name"] for a in confirmed] == ["Arjun"]

    searched = client.get("/api/appointments", params={"search": "pilat"}).json()
    assert [a["customer_name"] for a in searched] == ["Arjun"]

    by_day = client.get("/api/appointments", params={"day": "2030-01-16"}).json()
    assert [a["customer_name"] for a in by_day] == ["Zoya"]


def test_list_rejects_bad_day_format(client):
    assert client.get("/api/appointments", params={"day": "16/01/2030"}).status_code == 422


# ---------- update ----------


def test_put_updates_fields(client, booking):
    created = client.post("/api/appointments", json=booking()).json()
    response = client.put(
        f"/api/appointments/{created['id']}",
        json={"service": "Physiotherapy", "provider_id": 2, "notes": "Knee pain"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "Physiotherapy"
    assert body["duration_minutes"] == 45
    assert body["provider"]["name"] == "Diya Sharma"
    assert body["notes"] == "Knee pain"
    assert body["customer_name"] == "Riya Kapoor"  # untouched


def test_put_reschedule_into_conflict_is_rejected(client, booking):
    client.post("/api/appointments", json=booking())
    other = client.post("/api/appointments", json=booking(start_time="2030-01-15T14:00:00")).json()
    response = client.put(f"/api/appointments/{other['id']}", json={"start_time": "2030-01-15T10:15:00"})
    assert response.status_code == 409


def test_put_missing_appointment_returns_404(client):
    assert client.put("/api/appointments/999", json={"notes": "x"}).status_code == 404


def test_patch_status_transitions(client, booking):
    created = client.post("/api/appointments", json=booking()).json()
    response = client.patch(f"/api/appointments/{created['id']}/status", json={"status": "completed"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    bad = client.patch(f"/api/appointments/{created['id']}/status", json={"status": "teleported"})
    assert bad.status_code == 422


# ---------- delete ----------


def test_delete_appointment(client, booking):
    created = client.post("/api/appointments", json=booking()).json()
    assert client.delete(f"/api/appointments/{created['id']}").status_code == 204
    assert client.get(f"/api/appointments/{created['id']}").status_code == 404
    assert client.delete(f"/api/appointments/{created['id']}").status_code == 404


# ---------- stats ----------


def test_stats_summarise_bookings(client, booking):
    today_10am = datetime.now(IST).replace(hour=10, minute=0, second=0, microsecond=0)
    future = (datetime.now(IST) + timedelta(days=3)).replace(hour=12, minute=0, second=0, microsecond=0)

    today_booking = client.post("/api/appointments", json=booking(start_time=today_10am.isoformat())).json()
    done = client.post("/api/appointments", json=booking(start_time=today_10am.isoformat(), provider_id=2)).json()
    client.patch(f"/api/appointments/{done['id']}/status", json={"status": "completed"})
    upcoming = client.post(
        "/api/appointments", json=booking(start_time=future.isoformat(), service="Physiotherapy")
    ).json()
    cancelled = client.post("/api/appointments", json=booking(start_time=future.replace(hour=16).isoformat())).json()
    client.patch(f"/api/appointments/{cancelled['id']}/status", json={"status": "cancelled"})

    stats = client.get("/api/appointments/stats").json()
    assert stats["total"] == 4
    assert stats["today"] == 2
    assert stats["by_status"] == {
        "scheduled": 2,
        "confirmed": 0,
        "completed": 1,
        "cancelled": 1,
        "no_show": 0,
    }
    assert stats["by_service"] == {"Yoga Session": 2, "Physiotherapy": 1}
    assert stats["completion_rate"] == 1.0
    assert stats["cancellation_rate"] == 0.25
    assert stats["booked_revenue"] == 900 + 900 + 1500
    # Before 10:00 IST today's booking is still ahead of us; after it, the next one is in 3 days.
    expected_next = today_booking if datetime.now(IST) < today_10am else upcoming
    assert stats["next_appointment"]["id"] == expected_next["id"]


def test_stats_on_empty_database(client):
    stats = client.get("/api/appointments/stats").json()
    assert stats["total"] == 0
    assert stats["completion_rate"] == 0.0
    assert stats["next_appointment"] is None
