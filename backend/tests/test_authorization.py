from app.models.enums import UserRole


def test_citizen_cannot_use_owner_or_admin_endpoints(client, make_user, owner, create_location):
    citizen = make_user(UserRole.CITIZEN)
    loc = create_location(owner)
    body = {"name": "x", "category": "RATION_SHOP", "address": "a", "latitude": 1, "longitude": 1}
    assert client.post("/api/owner/locations", json=body, headers=citizen).status_code == 403
    assert client.get("/api/owner/locations", headers=citizen).status_code == 403
    assert client.put(f"/api/ration-shops/{loc['id']}/stock", json={"rice": "OUT_OF_STOCK"}, headers=citizen).status_code == 403
    assert client.get("/api/admin/users", headers=citizen).status_code == 403


def test_owner_cannot_use_admin_endpoints(client, owner):
    assert client.get("/api/admin/users", headers=owner).status_code == 403
    assert client.get("/api/admin/stats", headers=owner).status_code == 403
    assert client.put("/api/admin/locations/1/approve", headers=owner).status_code == 403


def test_anonymous_cannot_update(client, owner, create_location):
    loc = create_location(owner)
    for method, url, body in (
        ("put", f"/api/ration-shops/{loc['id']}/stock", {"rice": "OUT_OF_STOCK"}),
        ("put", f"/api/ration-shops/{loc['id']}/status", {"queue_level": "HIGH"}),
        ("post", f"/api/owner/locations/{loc['id']}/update-status", {"queue_level": "HIGH"}),
        ("delete", f"/api/owner/locations/{loc['id']}", None),
    ):
        res = getattr(client, method)(url, json=body) if body else getattr(client, method)(url)
        assert res.status_code == 401, url


def test_owner_cannot_modify_someone_elses_location(client, make_user, owner, create_location):
    loc = create_location(owner)
    other = make_user(UserRole.OWNER)
    checks = [
        client.put(f"/api/ration-shops/{loc['id']}/stock", json={"rice": "OUT_OF_STOCK"}, headers=other),
        client.put(f"/api/ration-shops/{loc['id']}/status", json={"queue_level": "HIGH"}, headers=other),
        client.put(f"/api/owner/locations/{loc['id']}", json={"name": "Hijacked"}, headers=other),
        client.post(f"/api/owner/locations/{loc['id']}/update-status", json={"status": "CLOSED"}, headers=other),
        client.delete(f"/api/owner/locations/{loc['id']}", headers=other),
        client.get(f"/api/owner/locations/{loc['id']}/updates", headers=other),
    ]
    assert [r.status_code for r in checks] == [403] * 6
    assert checks[0].json()["error"]["code"] == "FORBIDDEN"
    current = client.get(f"/api/locations/{loc['id']}").json()["data"]
    assert current["name"] == "Test Shop" and current["ration_stock"]["rice"] == "AVAILABLE"


def test_admin_can_manage_any_location_and_users(client, admin, owner, create_location):
    loc = create_location(owner)
    res = client.put(f"/api/ration-shops/{loc['id']}/status", json={"status": "CLOSED"}, headers=admin)
    assert res.status_code == 200 and res.json()["data"]["status"] == "CLOSED"
    users = client.get("/api/admin/users", headers=admin).json()
    assert users["meta"]["total"] == 2 and all("hashed_password" not in u for u in users["data"])
    stats = client.get("/api/admin/stats", headers=admin).json()["data"]
    assert stats["locations_total"] == 1 and stats["users_by_role"]["OWNER"] == 1


def test_admin_reject_delete_and_disable_user(client, admin, owner, create_location):
    loc = create_location(owner)
    res = client.put(f"/api/admin/locations/{loc['id']}/reject", json={"reason": "Fraudulent listing"}, headers=admin)
    assert res.json()["data"]["approval_status"] == "REJECTED"
    assert client.get(f"/api/locations/{loc['id']}").status_code == 404
    assert client.delete(f"/api/admin/locations/{loc['id']}", headers=admin).status_code == 200
    assert client.get("/api/admin/locations", headers=admin).json()["data"] == []

    me = client.get("/api/auth/me", headers=owner).json()["data"]
    assert client.put(f"/api/admin/users/{me['id']}/active", json={"is_active": False}, headers=admin).status_code == 200
    assert client.get("/api/auth/me", headers=owner).status_code == 401  # existing token stops working
