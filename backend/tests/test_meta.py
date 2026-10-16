"""Probe, metadata and metrics endpoints."""


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_checks_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_root_describes_service(client):
    body = client.get("/").json()
    assert body["service"] == "SlotSync API"
    assert body["docs"] == "/docs"


def test_metrics_exposes_prometheus_format(client, booking):
    client.post("/api/appointments", json=booking())
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "http_requests_total" in response.text
    assert 'slotsync_appointments_created_total{service="Yoga Session"}' in response.text


def test_openapi_lists_crud_routes(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"get", "post"} <= paths["/api/appointments"].keys()
    assert {"get", "put", "delete"} <= paths["/api/appointments/{appointment_id}"].keys()


def test_wait_for_db_succeeds_and_times_out():
    from app.wait_for_db import wait

    assert wait("sqlite+pysqlite:///:memory:", timeout=1) is True
    # Nothing listens on port 1, so this must give up after the timeout.
    assert wait("postgresql+psycopg://u:p@127.0.0.1:1/none", timeout=0.1, interval=0.05) is False
