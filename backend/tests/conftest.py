import os

# Must be set before the app is imported.
os.environ.setdefault("SECRET_KEY", "test-secret-key-test-secret-key-test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ["RATE_LIMIT_PER_MINUTE"] = "0"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.auth.security import hash_password  # noqa: E402
from app.database import Base, enable_sqlite_foreign_keys, get_db, get_session_factory  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.models.enums import UserRole  # noqa: E402

PASSWORD = "Str0ng-Pass!"


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    enable_sqlite_foreign_keys(engine)
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture()
def client(session_factory):
    def _get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    with TestClient(app) as test_client:  # context manager keeps one event loop (needed for WebSockets)
        yield test_client
    app.dependency_overrides.clear()


def _login(client: TestClient, email: str) -> dict:
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['data']['access_token']}"}


@pytest.fixture()
def make_user(client, session_factory):
    """make_user(role, email) -> auth headers. Admins are inserted directly (no public sign-up)."""

    def factory(role: UserRole = UserRole.OWNER, email: str | None = None) -> dict:
        email = email or f"{role.value.lower()}-{os.urandom(3).hex()}@example.com"
        if role == UserRole.ADMIN:
            with session_factory() as s:
                s.add(User(email=email, full_name="Admin", hashed_password=hash_password(PASSWORD), role=role))
                s.commit()
        else:
            res = client.post("/api/auth/register", json={
                "email": email, "full_name": "Test User", "password": PASSWORD, "role": role.value})
            assert res.status_code == 201, res.text
        return _login(client, email)

    return factory


@pytest.fixture()
def owner(make_user):
    return make_user(UserRole.OWNER)


@pytest.fixture()
def admin(make_user):
    return make_user(UserRole.ADMIN)


@pytest.fixture()
def create_location(client, admin):
    """create_location(headers, approve=True, **overrides) -> location dict (approved by default)."""

    def factory(headers: dict, approve: bool = True, **overrides) -> dict:
        body = {"name": "Test Shop", "category": "RATION_SHOP", "address": "1 Test Street",
                "latitude": 19.0760, "longitude": 72.8777, "phone": "+91 22 5550 0000"}
        body.update(overrides)
        res = client.post("/api/owner/locations", json=body, headers=headers)
        assert res.status_code == 201, res.text
        loc = res.json()["data"]
        if approve:
            res = client.put(f"/api/admin/locations/{loc['id']}/approve", headers=admin)
            assert res.status_code == 200, res.text
            loc = res.json()["data"]
        return loc

    return factory
