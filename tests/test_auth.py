import time

import jwt
import pytest

from app.core.config import settings


def payload(**overrides):
    data = {"name": "John Doe", "email": "john@example.com", "password": "Password123"}
    data.update(overrides)
    return data


def test_register_success(client):
    res = client.post("/api/auth/register", json=payload())
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "john@example.com"
    assert len(body["accountNumber"]) == 10
    assert "password" not in body and "passwordHash" not in body


def test_register_duplicate_email(client):
    client.post("/api/auth/register", json=payload())
    res = client.post("/api/auth/register", json=payload(email="JOHN@example.com"))
    assert res.status_code == 409


@pytest.mark.parametrize(
    "bad",
    [
        {"email": "not-an-email"},
        {"name": "   "},
        {"password": "short1A"},
        {"password": "alllowercase1"},
        {"password": "NOLOWERCASE1"},
        {"password": "NoDigitsHere"},
    ],
)
def test_register_validation(client, bad):
    res = client.post("/api/auth/register", json=payload(**bad))
    assert res.status_code == 422


def test_login_success(client):
    client.post("/api/auth/register", json=payload())
    res = client.post(
        "/api/auth/login", json={"email": "john@example.com", "password": "Password123"}
    )
    assert res.status_code == 200
    assert res.json()["tokenType"] == "bearer"
    assert res.json()["accessToken"]


def test_login_wrong_password(client):
    client.post("/api/auth/register", json=payload())
    res = client.post(
        "/api/auth/login", json={"email": "john@example.com", "password": "WrongPass1"}
    )
    assert res.status_code == 401


def test_login_unknown_email(client):
    res = client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "Password123"}
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


def test_missing_token_is_401(client):
    assert client.get("/api/accounts/me").status_code == 401


def test_invalid_token_is_401(client):
    res = client.get("/api/accounts/me", headers={"Authorization": "Bearer garbage"})
    assert res.status_code == 401


def test_expired_token_is_401(client, auth):
    expired = jwt.encode(
        {"sub": "1", "jti": "abc", "exp": int(time.time()) - 60},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    res = client.get("/api/accounts/me", headers={"Authorization": f"Bearer {expired}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_logout_revokes_token(client, auth):
    assert client.get("/api/accounts/me", headers=auth).status_code == 200
    assert client.post("/api/auth/logout", headers=auth).status_code == 200
    assert client.get("/api/accounts/me", headers=auth).status_code == 401


def test_logout_requires_auth(client):
    assert client.post("/api/auth/logout").status_code == 401
