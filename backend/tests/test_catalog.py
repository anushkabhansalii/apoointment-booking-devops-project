"""Providers and services lookups."""


def test_list_providers_hides_inactive(client):
    response = client.get("/api/providers")
    assert response.status_code == 200
    names = [p["name"] for p in response.json()]
    assert names == ["Aarav Mehta", "Diya Sharma"]


def test_list_services_has_durations_and_prices(client):
    services = {s["name"]: s for s in client.get("/api/services").json()}
    assert services["Physiotherapy"] == {"name": "Physiotherapy", "duration": 45, "price": 1500}
    assert len(services) == 5


def test_version_reports_build_and_environment(client):
    body = client.get("/api/version").json()
    assert set(body) == {"version", "environment"}
    assert body["version"]  # "dev" locally, the Git SHA in images built by CI
