from app.models.enums import UserRole
from app.utils.rate_limit import limiter


def test_owner_creates_location_pending_until_admin_approves(client, owner, admin, create_location):
    loc = create_location(owner, approve=False, name="Pending Shop")
    assert loc["approval_status"] == "PENDING"
    assert loc["ration_stock"]["rice"] == "AVAILABLE"
    # hidden from the public until approved
    assert client.get(f"/api/locations/{loc['id']}").status_code == 404
    assert client.get("/api/locations").json()["data"] == []
    # ...but the owner can see it
    assert client.get(f"/api/locations/{loc['id']}", headers=owner).status_code == 200
    assert client.put(f"/api/admin/locations/{loc['id']}/approve", headers=admin).status_code == 200
    res = client.get(f"/api/locations/{loc['id']}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert {"status", "queue_level", "last_updated"} <= data.keys()


def test_not_found_error_format(client):
    res = client.get("/api/locations/9999")
    assert res.status_code == 404
    assert res.json() == {"success": False, "error": {"code": "LOCATION_NOT_FOUND", "message": "Location not found"}}


def test_create_validation(client, owner):
    base = {"name": "X", "category": "EV_CHARGING", "address": "a", "latitude": 10, "longitude": 10}
    assert client.post("/api/owner/locations", json=base, headers=owner).status_code == 422  # needs ev_station
    bad = {**base, "ev_station": {"total_plugs": 2, "occupied_plugs": 3}}
    assert client.post("/api/owner/locations", json=bad, headers=owner).status_code == 422
    mismatch = {**base, "category": "PHARMACY", "ev_station": {"total_plugs": 2}}
    assert client.post("/api/owner/locations", json=mismatch, headers=owner).status_code == 422
    assert client.post("/api/owner/locations", json={**base, "latitude": 123}, headers=owner).status_code == 422


def test_filters(client, owner, create_location):
    create_location(owner, name="Alpha Ration", category="RATION_SHOP", queue_level="LOW")
    create_location(owner, name="Beta Pharmacy", category="PHARMACY", queue_level="HIGH", status="BUSY")
    names = lambda r: sorted(x["name"] for x in r.json()["data"])  # noqa: E731
    assert names(client.get("/api/locations?category=PHARMACY")) == ["Beta Pharmacy"]
    assert names(client.get("/api/locations?queue_level=LOW")) == ["Alpha Ration"]
    assert names(client.get("/api/locations?status=BUSY")) == ["Beta Pharmacy"]
    assert names(client.get("/api/locations/search?keyword=alpha")) == ["Alpha Ration"]
    assert client.get("/api/locations?category=NOPE").status_code == 422
    meta = client.get("/api/locations?limit=1").json()["meta"]
    assert meta == {"total": 2, "limit": 1, "offset": 0}


def test_nearby_search_sorted_with_distance(client, owner, create_location):
    create_location(owner, name="Near", latitude=19.0800, longitude=72.8800)       # ~0.5 km
    create_location(owner, name="Middle", latitude=19.1200, longitude=72.9000)     # ~6 km
    create_location(owner, name="Far", latitude=28.6139, longitude=77.2090)        # Delhi
    res = client.get("/api/locations/nearby?latitude=19.0760&longitude=72.8777&radius=10")
    data = res.json()["data"]
    assert [x["name"] for x in data] == ["Near", "Middle"]
    assert data[0]["distance_km"] < data[1]["distance_km"] < 10
    small = client.get("/api/locations/nearby?latitude=19.0760&longitude=72.8777&radius=1").json()["data"]
    assert [x["name"] for x in small] == ["Near"]
    assert client.get("/api/locations/nearby?latitude=19.07").status_code == 422
    assert client.get("/api/locations?latitude=19.07").json()["error"]["code"] == "INVALID_GEO_PARAMS"


def test_owner_profile_update_and_soft_delete(client, owner, create_location):
    loc = create_location(owner)
    res = client.put(f"/api/owner/locations/{loc['id']}", json={"name": "Renamed", "phone": "+91 99999 11111"}, headers=owner)
    assert res.status_code == 200 and res.json()["data"]["name"] == "Renamed"
    assert client.delete(f"/api/owner/locations/{loc['id']}", headers=owner).status_code == 200
    assert client.get(f"/api/locations/{loc['id']}").status_code == 404
    assert client.get("/api/owner/locations", headers=owner).json()["data"] == []


def test_rate_limit_on_public_search(client, monkeypatch):
    import dataclasses

    import app.utils.rate_limit as rl

    limiter.reset()
    limited = dataclasses.replace(rl.get_settings(), rate_limit_per_minute=3)
    monkeypatch.setattr(rl, "get_settings", lambda: limited)
    codes = [client.get("/api/locations").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    limiter.reset()
