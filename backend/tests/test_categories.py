import pytest
from sqlalchemy.exc import IntegrityError

from app.models import EVStationDetails, PharmacyMedicine, RationStock


# ---------------- scenario 1: ration shop ----------------
def test_ration_stock_and_queue_in_one_request(client, owner, create_location):
    shop = create_location(owner)
    res = client.put(
        f"/api/ration-shops/{shop['id']}/stock",
        json={"rice": "AVAILABLE", "wheat": "LOW_STOCK", "dal": "OUT_OF_STOCK",
              "other_items": {"Sugar": "AVAILABLE"}, "queue_level": "HIGH"},
        headers=owner,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["ration_stock"] == {"rice": "AVAILABLE", "wheat": "LOW_STOCK", "dal": "OUT_OF_STOCK",
                                    "other_items": {"sugar": "AVAILABLE"}}
    assert data["queue_level"] == "HIGH"

    public = client.get(f"/api/ration-shops/{shop['id']}").json()["data"]
    assert public["queue_level"] == "HIGH" and public["last_updated"] > shop["last_updated"]
    assert client.get(f"/api/museums/{shop['id']}").status_code == 404  # wrong category


def test_ration_overall_status_derived(client, owner, create_location):
    shop = create_location(owner)
    out = client.put(f"/api/ration-shops/{shop['id']}/stock",
                     json={"rice": "OUT_OF_STOCK", "wheat": "OUT_OF_STOCK", "dal": "OUT_OF_STOCK"}, headers=owner)
    assert out.json()["data"]["status"] == "OUT_OF_STOCK"
    back = client.put(f"/api/ration-shops/{shop['id']}/stock", json={"rice": "AVAILABLE"}, headers=owner)
    assert back.json()["data"]["status"] == "AVAILABLE"
    assert client.put(f"/api/ration-shops/{shop['id']}/stock", json={}, headers=owner).status_code == 422
    assert client.put(f"/api/ration-shops/{shop['id']}/stock", json={"rice": "MAYBE"}, headers=owner).status_code == 422


def test_queue_update(client, owner, create_location):
    shop = create_location(owner)
    res = client.put(f"/api/ration-shops/{shop['id']}/status", json={"queue_level": "MEDIUM", "status": "BUSY"}, headers=owner)
    assert res.json()["data"]["queue_level"] == "MEDIUM" and res.json()["data"]["status"] == "BUSY"
    assert client.put(f"/api/ration-shops/{shop['id']}/status", json={"queue_level": "HUGE"}, headers=owner).status_code == 422


# ---------------- scenario 2: museum ----------------
def test_museum_status_guide_and_crowd(client, owner, create_location):
    m = create_location(owner, name="Fort", category="MUSEUM_MONUMENT",
                        museum={"opening_hours": "10-5", "historical_description": "Built long ago."})
    assert m["museum"]["guide_available"] is False
    res = client.put(f"/api/museums/{m['id']}/status", headers=owner, json={
        "status": "AVAILABLE", "queue_level": "LOW", "guide_available": True,
        "guide_url": "https://guides.example.org/fort", "guide_content_id": "G-1"})
    assert res.status_code == 200
    assert res.json()["data"]["museum"]["crowd_level"] == "LOW"
    guide = client.get(f"/api/museums/{m['id']}/guide").json()["data"]
    assert guide["guide_available"] is True and guide["guide_url"] == "https://guides.example.org/fort"
    assert guide["historical_description"] == "Built long ago."
    bad = client.put(f"/api/museums/{m['id']}/status", json={"guide_url": "javascript:alert(1)"}, headers=owner)
    assert bad.status_code == 422
    closed = client.put(f"/api/museums/{m['id']}/status", json={"status": "CLOSED"}, headers=owner)
    assert closed.json()["data"]["status"] == "CLOSED"
    assert [x["name"] for x in client.get("/api/museums?status=CLOSED").json()["data"]] == ["Fort"]


# ---------------- scenario 3: EV ----------------
def test_ev_availability_calculated_and_validated(client, owner, create_location):
    ev = create_location(owner, name="EV", category="EV_CHARGING", queue_level="LOW",
                         ev_station={"total_plugs": 4, "occupied_plugs": 1, "charging_type": "DC_FAST"})
    assert ev["ev_station"]["available_plugs"] == 3

    res = client.put(f"/api/ev-stations/{ev['id']}/availability", headers=owner,
                     json={"occupied_plugs": 4, "estimated_wait_minutes": 20, "queue_level": "HIGH"})
    data = res.json()["data"]
    assert data["ev_station"]["available_plugs"] == 0 and data["status"] == "BUSY"
    assert data["ev_station"]["estimated_wait_minutes"] == 20

    free = client.put(f"/api/ev-stations/{ev['id']}/availability", json={"occupied_plugs": 2}, headers=owner)
    assert free.json()["data"]["ev_station"]["available_plugs"] == 2 and free.json()["data"]["status"] == "AVAILABLE"

    over = client.put(f"/api/ev-stations/{ev['id']}/availability", json={"occupied_plugs": 5}, headers=owner)
    assert over.status_code == 422 and over.json()["error"]["code"] == "INVALID_PLUG_COUNT"
    shrink = client.put(f"/api/ev-stations/{ev['id']}/availability", json={"total_plugs": 1}, headers=owner)
    assert shrink.status_code == 422  # 2 occupied > 1 total
    both = client.put(f"/api/ev-stations/{ev['id']}/availability", json={"total_plugs": 2, "occupied_plugs": 3}, headers=owner)
    assert both.status_code == 422
    assert client.put(f"/api/ev-stations/{ev['id']}/availability", json={"occupied_plugs": -1}, headers=owner).status_code == 422
    unchanged = client.get(f"/api/ev-stations/{ev['id']}").json()["data"]["ev_station"]
    assert unchanged["occupied_plugs"] == 2 and unchanged["total_plugs"] == 4


def test_database_enforces_ev_and_category_rules(db, client, owner, create_location):
    ev = create_location(owner, category="EV_CHARGING", ev_station={"total_plugs": 2})
    shop = create_location(owner)
    # occupied > total is rejected by the database itself
    row = db.get(EVStationDetails, 1)
    row.occupied_plugs = 3
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    # a medicine on a non-pharmacy location, and ration stock on an EV location, are rejected too
    db.add(PharmacyMedicine(location_id=shop["id"], medicine_name="X", name_key="x"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.add(RationStock(location_id=ev["id"]))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


# ---------------- scenario 4: pharmacy ----------------
def test_pharmacy_medicine_search_with_distance(client, owner, create_location):
    near = create_location(owner, name="Near Pharmacy", category="PHARMACY", latitude=19.0800, longitude=72.8800,
                           medicines=[{"medicine_name": "Riluzole 50mg", "quantity": 12, "prescription_required": True}])
    far = create_location(owner, name="Far Pharmacy", category="PHARMACY", latitude=19.1200, longitude=72.9000,
                          medicines=[{"medicine_name": "Riluzole 50mg"}, {"medicine_name": "Aspirin", "quantity": 0}])
    create_location(owner, name="Wrong City", category="PHARMACY", latitude=28.61, longitude=77.20,
                    medicines=[{"medicine_name": "Riluzole 50mg", "quantity": 3}])

    res = client.get("/api/pharmacies/search-medicine?medicine=riluzole&latitude=19.0760&longitude=72.8777&radius=10")
    assert res.status_code == 200
    rows = res.json()["data"]
    assert [r["pharmacy_name"] for r in rows] == ["Near Pharmacy", "Far Pharmacy"]
    first = rows[0]
    assert first["quantity"] == 12 and first["prescription_required"] is True and first["distance_km"] < 2
    assert {"address", "last_updated", "last_stock_update", "is_available", "phone"} <= first.keys()
    assert rows[1]["quantity"] is None  # quantity only when provided

    # unavailable medicines are excluded unless asked for
    assert client.get("/api/pharmacies/search-medicine?medicine=aspirin").json()["data"] == []
    listed = client.get("/api/pharmacies/search-medicine?medicine=aspirin&available_only=false").json()["data"]
    assert len(listed) == 1 and listed[0]["is_available"] is False

    # without coordinates there is no distance
    assert client.get("/api/pharmacies/search-medicine?medicine=riluzole").json()["data"][0]["distance_km"] is None
    assert client.get("/api/pharmacies/search-medicine").status_code == 422
    assert near["id"] != far["id"]


def test_pharmacy_inventory_update_and_search_reflects_it(client, owner, create_location):
    ph = create_location(owner, category="PHARMACY", medicines=[{"medicine_name": "Insulin", "quantity": 5}])
    res = client.put(f"/api/pharmacies/{ph['id']}/inventory", headers=owner, json={
        "items": [{"medicine_name": "insulin", "is_available": False}, {"medicine_name": "Paracetamol", "quantity": 100}],
        "queue_level": "LOW"})
    assert res.status_code == 200
    meds = {m["medicine_name"]: m for m in res.json()["data"]["medicines"]}
    assert meds["Insulin"]["is_available"] is False and meds["Insulin"]["quantity"] == 5  # omitted quantity kept
    assert meds["Paracetamol"]["quantity"] == 100
    assert client.get("/api/pharmacies/search-medicine?medicine=insulin").json()["data"] == []
    removed = client.put(f"/api/pharmacies/{ph['id']}/inventory", json={"remove": ["Paracetamol"]}, headers=owner)
    assert [m["medicine_name"] for m in removed.json()["data"]["medicines"]] == ["Insulin"]
    assert client.put(f"/api/pharmacies/{ph['id']}/inventory", json={}, headers=owner).status_code == 422
    # keyword search on generic endpoint also finds medicines
    assert len(client.get("/api/locations/search?keyword=insulin").json()["data"]) == 1
