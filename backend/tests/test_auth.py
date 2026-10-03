import jwt

from app.config import get_settings
from tests.conftest import PASSWORD


def register(client, **overrides):
    body = {"email": "Shop@Example.com", "full_name": "Shop Owner", "password": PASSWORD, "role": "OWNER"}
    body.update(overrides)
    return client.post("/api/auth/register", json=body)


def test_register_and_login(client):
    res = register(client)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["email"] == "shop@example.com" and data["role"] == "OWNER"
    assert "password" not in data and "hashed_password" not in data

    login = client.post("/api/auth/login", json={"email": "shop@example.com", "password": PASSWORD})
    assert login.status_code == 200
    body = login.json()["data"]
    assert body["token_type"] == "bearer" and body["access_token"]
    assert "hashed_password" not in login.text


def test_duplicate_email_rejected(client):
    assert register(client).status_code == 201
    res = register(client)
    assert res.status_code == 409
    assert res.json() == {"success": False, "error": {"code": "EMAIL_ALREADY_REGISTERED",
                                                      "message": "An account with this email already exists"}}


def test_cannot_self_register_as_admin_or_weak_password(client):
    assert register(client, role="ADMIN").status_code == 422
    assert register(client, password="short1").status_code == 422
    assert register(client, password="onlyletters").status_code == 422


def test_wrong_password_and_unknown_user(client):
    register(client)
    for creds in ({"email": "shop@example.com", "password": "Wrong-pass1"},
                  {"email": "nobody@example.com", "password": PASSWORD}):
        res = client.post("/api/auth/login", json=creds)
        assert res.status_code == 401 and res.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_jwt_protects_me_endpoint(client, owner):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    res = client.get("/api/auth/me", headers=owner)
    assert res.status_code == 200 and res.json()["data"]["role"] == "OWNER"


def test_expired_and_forged_tokens_rejected(client, owner):
    settings = get_settings()
    me = client.get("/api/auth/me", headers=owner).json()["data"]
    expired = jwt.encode({"sub": str(me["id"]), "exp": 1}, settings.secret_key, algorithm="HS256")
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert res.status_code == 401 and res.json()["error"]["code"] == "TOKEN_EXPIRED"
    forged = jwt.encode({"sub": str(me["id"]), "exp": 9999999999}, "x" * 40, algorithm="HS256")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_validation_errors_use_envelope(client):
    res = client.post("/api/auth/login", json={"email": "not-an-email"})
    assert res.status_code == 422
    assert res.json()["success"] is False and res.json()["error"]["code"] == "VALIDATION_ERROR"
