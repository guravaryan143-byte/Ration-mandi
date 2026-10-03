"""Demo data for hackathons.  Usage:  python -m app.utils.seed [--reset]

Creates demo users (all use SEED_PASSWORD, default 'Demo@12345'), then 12 approved locations around
Mumbai (3 ration shops, 2 museums, 3 EV stations, 4 pharmacies), some queue/status values and a few
audit-trail entries produced through the real service layer.
"""
from __future__ import annotations

import argparse
import os

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models import (
    EVStationDetails, Location, LocationUpdate, MuseumDetails, PharmacyMedicine, RationStock, User,
)
from app.models.enums import ApprovalStatus, Category, ChargingType, LocationStatus, QueueLevel, StockLevel, UserRole
from app.schemas.details import (
    EVAvailabilityUpdate, EVStationInput, MedicineItem, MuseumInput, PharmacyInventoryUpdate, RationStockUpdate,
)
from app.schemas.location import LocationCreate
from app.services import ev_service, location_service, pharmacy_service, ration_service

PASSWORD = os.getenv("SEED_PASSWORD", "Demo@12345")
S = StockLevel


def _user(db: Session, email: str, name: str, role: UserRole) -> User:
    user = User(email=email, full_name=name, hashed_password=hash_password(PASSWORD), role=role)
    db.add(user)
    db.flush()
    return user


def _create(db: Session, owner: User, **kwargs) -> Location:  # noqa: ANN003
    loc = location_service.create_location(db, owner, LocationCreate(**kwargs))
    loc.approval_status = ApprovalStatus.APPROVED
    db.commit()
    return loc


def seed(db: Session) -> None:
    admin = _user(db, "admin@example.com", "Demo Admin", UserRole.ADMIN)
    _user(db, "citizen@example.com", "Demo Citizen", UserRole.CITIZEN)
    o1 = _user(db, "owner1@example.com", "Ration & Museum Owner", UserRole.OWNER)
    o2 = _user(db, "owner2@example.com", "EV Network Owner", UserRole.OWNER)
    o3 = _user(db, "owner3@example.com", "Pharmacy Owner", UserRole.OWNER)
    db.commit()

    # ---- Scenario 1: ration shops
    r1 = _create(db, o1, name="Sunrise Fair Price Shop", category=Category.RATION_SHOP,
                 address="12 Station Road, Dadar, Mumbai", latitude=19.0178, longitude=72.8478,
                 phone="+91 22 5550 0101", description="Government ration shop, weekdays 9am-6pm",
                 queue_level=QueueLevel.LOW,
                 ration_stock=RationStockUpdate(rice=S.AVAILABLE, wheat=S.AVAILABLE, dal=S.AVAILABLE,
                                                other_items={"sugar": S.AVAILABLE, "kerosene": S.LOW_STOCK}))
    r2 = _create(db, o1, name="Gandhi Nagar Ration Store", category=Category.RATION_SHOP,
                 address="45 Market Lane, Bandra East, Mumbai", latitude=19.0596, longitude=72.8656,
                 phone="+91 22 5550 0102", queue_level=QueueLevel.HIGH, status=LocationStatus.BUSY,
                 ration_stock=RationStockUpdate(rice=S.AVAILABLE, wheat=S.LOW_STOCK, dal=S.OUT_OF_STOCK,
                                                other_items={"sugar": S.OUT_OF_STOCK}))
    _create(db, o1, name="Lakshmi Ration Depot", category=Category.RATION_SHOP,
            address="8 Temple Street, Kurla, Mumbai", latitude=19.0726, longitude=72.8845,
            phone="+91 22 5550 0103", status=LocationStatus.OUT_OF_STOCK, queue_level=QueueLevel.MEDIUM,
            ration_stock=RationStockUpdate(rice=S.OUT_OF_STOCK, wheat=S.OUT_OF_STOCK, dal=S.OUT_OF_STOCK))

    # ---- Scenario 2: museums / monuments
    m1 = _create(db, o1, name="Old Customs House Museum", category=Category.MUSEUM_MONUMENT,
                 address="1 Harbour Road, Fort, Mumbai", latitude=18.9322, longitude=72.8352,
                 phone="+91 22 5550 0201", queue_level=QueueLevel.MEDIUM,
                 description="Small maritime-trade museum (sample data).",
                 museum=MuseumInput(opening_hours="Tue-Sun 10:00-17:30; closed Mondays",
                                    historical_description="Sample text: a colonial-era customs building turned museum, "
                                    "with galleries on port trade and local craftsmen.",
                                    guide_available=True, guide_url="https://guides.example.org/customs-house",
                                    guide_content_id="GUIDE-CUSTOMS-001"))
    _create(db, o1, name="Hilltop Fort Monument", category=Category.MUSEUM_MONUMENT,
            address="Fort Hill, Sion, Mumbai", latitude=19.0434, longitude=72.8647,
            status=LocationStatus.CLOSED, queue_level=QueueLevel.NOT_APPLICABLE,
            description="Small hilltop monument (sample data).",
            museum=MuseumInput(opening_hours="Daily 07:00-18:00", guide_available=False,
                               historical_description="Sample text: a hilltop watch-fort with sweeping city views."))

    # ---- Scenario 3: EV charging
    e1 = _create(db, o2, name="GreenCharge Bandra Hub", category=Category.EV_CHARGING,
                 address="Linking Road, Bandra West, Mumbai", latitude=19.0607, longitude=72.8362,
                 phone="+91 22 5550 0301", queue_level=QueueLevel.LOW,
                 ev_station=EVStationInput(total_plugs=6, occupied_plugs=2, charging_type=ChargingType.DC_FAST,
                                           estimated_wait_minutes=0))
    e2 = _create(db, o2, name="VoltPoint Andheri", category=Category.EV_CHARGING,
                 address="Veera Desai Road, Andheri West, Mumbai", latitude=19.1330, longitude=72.8300,
                 queue_level=QueueLevel.HIGH,
                 ev_station=EVStationInput(total_plugs=4, occupied_plugs=4, charging_type=ChargingType.MIXED,
                                           estimated_wait_minutes=25))
    _create(db, o2, name="EcoCharge Powai", category=Category.EV_CHARGING,
            address="Hiranandani Gardens, Powai, Mumbai", latitude=19.1197, longitude=72.9050,
            status=LocationStatus.MAINTENANCE, queue_level=QueueLevel.NOT_APPLICABLE,
            ev_station=EVStationInput(total_plugs=3, occupied_plugs=0, charging_type=ChargingType.AC_SLOW))

    # ---- Scenario 4: pharmacies
    p1 = _create(db, o3, name="Shree Medical Store", category=Category.PHARMACY,
                 address="Hill Road, Bandra West, Mumbai", latitude=19.0544, longitude=72.8320,
                 phone="+91 22 5550 0401", queue_level=QueueLevel.LOW,
                 medicines=[MedicineItem(medicine_name="Paracetamol 500mg", quantity=240),
                            MedicineItem(medicine_name="Insulin Glargine", quantity=6, prescription_required=True),
                            MedicineItem(medicine_name="Riluzole 50mg", quantity=12, prescription_required=True)])
    p2 = _create(db, o3, name="City Care Pharmacy", category=Category.PHARMACY,
                 address="Lokhandwala, Andheri West, Mumbai", latitude=19.1363, longitude=72.8296,
                 phone="+91 22 5550 0402", queue_level=QueueLevel.MEDIUM,
                 medicines=[MedicineItem(medicine_name="Paracetamol 500mg", quantity=80),
                            MedicineItem(medicine_name="Riluzole 50mg", is_available=False),
                            MedicineItem(medicine_name="Metformin 500mg", quantity=150, prescription_required=True)])
    _create(db, o3, name="LifeLine Chemists", category=Category.PHARMACY,
            address="Station Road, Kurla, Mumbai", latitude=19.0653, longitude=72.8790,
            phone="+91 22 5550 0403", queue_level=QueueLevel.HIGH, status=LocationStatus.BUSY,
            medicines=[MedicineItem(medicine_name="Salbutamol Inhaler", quantity=20),
                       MedicineItem(medicine_name="Penicillamine 250mg", quantity=4, prescription_required=True)])
    _create(db, o3, name="Apollo Corner Pharmacy", category=Category.PHARMACY,
            address="Dadar TT Circle, Mumbai", latitude=19.0195, longitude=72.8433,
            phone="+91 22 5550 0404", queue_level=QueueLevel.LOW,
            medicines=[MedicineItem(medicine_name="Amoxicillin 250mg", quantity=60),
                       MedicineItem(medicine_name="Levothyroxine 50mcg", quantity=90, prescription_required=True),
                       MedicineItem(medicine_name="Penicillamine 250mg", is_available=False)])

    # ---- A little history so the audit trail isn't empty (goes through the real services)
    ration_service.update_stock(db, db.get(Location, r2.id), o1, RationStockUpdate(
        dal=S.LOW_STOCK, queue_level=QueueLevel.MEDIUM, note="Fresh dal delivery arrived"))
    ration_service.update_stock(db, db.get(Location, r2.id), o1, RationStockUpdate(
        dal=S.OUT_OF_STOCK, queue_level=QueueLevel.HIGH, note="Dal finished again"))
    ev_service.update_availability(db, db.get(Location, e1.id), o2, EVAvailabilityUpdate(occupied_plugs=3))
    ev_service.update_availability(db, db.get(Location, e1.id), o2, EVAvailabilityUpdate(occupied_plugs=2))
    ev_service.update_availability(db, db.get(Location, e2.id), o2, EVAvailabilityUpdate(estimated_wait_minutes=25))
    pharmacy_service.update_inventory(db, db.get(Location, p1.id), o3, PharmacyInventoryUpdate(
        items=[MedicineItem(medicine_name="Paracetamol 500mg", quantity=235)], note="Sold 5 strips"))
    location_service.update_status(db, db.get(Location, m1.id), o1, None, QueueLevel.MEDIUM, "School group visiting")
    assert admin.id  # admin exists; used for moderation demo via the API


def reset(db: Session) -> None:
    for model in (LocationUpdate, PharmacyMedicine, EVStationDetails, MuseumDetails, RationStock, Location, User):
        db.execute(delete(model))
    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data")
    parser.add_argument("--reset", action="store_true", help="delete ALL existing data first")
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.reset:
            reset(db)
        elif db.scalar(select(User.id).where(User.email == "admin@example.com")):
            print("Seed data already present (use --reset to wipe and re-seed).")
            return
        seed(db)
    print(f"Seeded. Demo logins (password: {PASSWORD}): admin@example.com, owner1@example.com, "
          "owner2@example.com, owner3@example.com, citizen@example.com")


if __name__ == "__main__":
    main()
