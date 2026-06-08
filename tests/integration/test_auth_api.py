"""Integration tests for /api/v1/auth/* endpoints."""
import pytest
from tests.conftest import auth_header


def test_register_new_user(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "newreg@test.com",
        "password": "NewPass1",
        "full_name": "New Reg",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["data"]["email"] == "newreg@test.com"


def test_register_duplicate_email(client, regular_user):
    res = client.post("/api/v1/auth/register", json={
        "email": "user@test.com",
        "password": "User1234",
        "full_name": "Dup",
    })
    assert res.status_code == 400


def test_register_weak_password(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "weak@test.com",
        "password": "weak",
        "full_name": "Weak User",
    })
    assert res.status_code == 422


def test_login_success(client, regular_user):
    res = client.post("/api/v1/auth/login", json={
        "email": "user@test.com",
        "password": "User1234",
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, regular_user):
    res = client.post("/api/v1/auth/login", json={
        "email": "user@test.com",
        "password": "WrongPass1",
    })
    assert res.status_code == 401


def test_login_unknown_email(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "ghost@test.com",
        "password": "Ghost1234",
    })
    assert res.status_code == 401


def test_get_profile(client, user_token):
    res = client.get("/api/v1/auth/profile", headers=auth_header(user_token))
    assert res.status_code == 200
    assert res.json()["data"]["email"] == "user@test.com"


def test_get_profile_no_token(client):
    res = client.get("/api/v1/auth/profile")
    assert res.status_code == 403  # Missing bearer → 403 from HTTPBearer


def test_get_profile_bad_token(client):
    res = client.get("/api/v1/auth/profile", headers={"Authorization": "Bearer badtoken"})
    assert res.status_code == 401


def test_logout(client, user_token):
    # Get a fresh login to have a real refresh token
    login_res = client.post("/api/v1/auth/login", json={
        "email": "user@test.com",
        "password": "User1234",
    })
    refresh = login_res.json()["data"]["refresh_token"]
    res = client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    assert res.status_code == 200


def test_refresh_token(client, regular_user):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "user@test.com",
        "password": "User1234",
    })
    refresh = login_res.json()["data"]["refresh_token"]
    res = client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh})
    assert res.status_code == 200
    assert "access_token" in res.json()["data"]
