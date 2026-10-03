from sqlalchemy import func, select

from app.models import Location
from app.models.enums import Category
from app.utils.seed import seed


def test_seed_populates_all_scenarios(client, db):
    seed(db)
    counts = dict(db.execute(select(Location.category, func.count()).group_by(Location.category)).all())
    assert counts == {Category.RATION_SHOP: 3, Category.MUSEUM_MONUMENT: 2, Category.EV_CHARGING: 3, Category.PHARMACY: 4}

    rare = client.get("/api/pharmacies/search-medicine?medicine=riluzole&latitude=19.0760&longitude=72.8777").json()["data"]
    assert [r["pharmacy_name"] for r in rare] == ["Shree Medical Store"]  # the other pharmacy marks it unavailable
    assert client.get("/api/ev-stations").json()["meta"]["total"] == 3
    museums = client.get("/api/museums").json()["data"]
    assert len(museums) == 2
    with_guide = next(m for m in museums if m["museum"]["guide_available"])
    guide = client.get(f"/api/museums/{with_guide['id']}/guide").json()["data"]
    assert guide["guide_url"] and guide["guide_content_id"]
