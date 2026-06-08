"""Unit tests for AuthService — no HTTP, pure service logic."""
import pytest
from fastapi import HTTPException

from api.services.auth_service import AuthService
from api.utils.security import hash_password, verify_password, create_access_token, decode_token


# ── Password hashing ──────────────────────────────────────────────────────────

def test_hash_password_is_not_plaintext():
    hashed = hash_password("MySecret1")
    assert hashed != "MySecret1"
    assert len(hashed) > 30


def test_verify_correct_password():
    hashed = hash_password("Correct1")
    assert verify_password("Correct1", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("Correct1")
    assert verify_password("Wrong999", hashed) is False


def test_hashes_are_unique():
    h1 = hash_password("Same1")
    h2 = hash_password("Same1")
    assert h1 != h2  # bcrypt uses random salt


# ── JWT tokens ────────────────────────────────────────────────────────────────

def test_create_and_decode_access_token():
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_access_token_extra_claims():
    token = create_access_token("user-abc", extra={"role": "admin"})
    payload = decode_token(token)
    assert payload["role"] == "admin"


def test_invalid_token_raises():
    from jose import JWTError
    with pytest.raises(JWTError):
        decode_token("not.a.valid.token")


# ── AuthService ───────────────────────────────────────────────────────────────

def test_create_user(db):
    svc = AuthService(db)
    user = svc.create_user("newuser@test.com", "NewPass1", "New User")
    assert user.id is not None
    assert user.email == "newuser@test.com"
    assert user.hashed_password != "NewPass1"


def test_create_duplicate_user_raises(db):
    svc = AuthService(db)
    svc.create_user("dup@test.com", "Pass1234", "Dup User")
    with pytest.raises(HTTPException) as exc:
        svc.create_user("dup@test.com", "Pass1234", "Dup Again")
    assert exc.value.status_code == 400


def test_login_success(db, regular_user):
    svc = AuthService(db)
    tokens = svc.login("user@test.com", "User1234")
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_login_wrong_password_raises(db, regular_user):
    svc = AuthService(db)
    with pytest.raises(HTTPException) as exc:
        svc.login("user@test.com", "WrongPass1")
    assert exc.value.status_code == 401


def test_login_unknown_email_raises(db):
    svc = AuthService(db)
    with pytest.raises(HTTPException) as exc:
        svc.login("nobody@test.com", "Any1pass")
    assert exc.value.status_code == 401


def test_login_inactive_user_raises(db):
    from api.models.user import User
    user = User(
        email="inactive@test.com",
        hashed_password=hash_password("Pass1234"),
        full_name="Inactive",
        is_active=False,
    )
    db.add(user)
    db.commit()
    svc = AuthService(db)
    with pytest.raises(HTTPException) as exc:
        svc.login("inactive@test.com", "Pass1234")
    assert exc.value.status_code == 403


def test_logout_revokes_session(db, regular_user):
    svc = AuthService(db)
    tokens = svc.login("user@test.com", "User1234")
    refresh = tokens["refresh_token"]
    svc.logout(refresh)
    # Refresh after logout should fail
    with pytest.raises(HTTPException) as exc:
        svc.refresh_access_token(refresh)
    assert exc.value.status_code == 401


def test_refresh_token(db, regular_user):
    svc = AuthService(db)
    tokens = svc.login("user@test.com", "User1234")
    result = svc.refresh_access_token(tokens["refresh_token"])
    assert "access_token" in result
    payload = decode_token(result["access_token"])
    assert payload["sub"] == str(regular_user.id)
