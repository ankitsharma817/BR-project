"""Unit tests for input validators."""
import pytest
from fastapi import HTTPException

from api.utils.validators import (
    validate_email,
    validate_password_strength,
    validate_score,
    validate_pagination,
)


# ── Email ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("email", [
    "user@example.com",
    "User.Name+tag@sub.domain.co.uk",
    "a@b.io",
])
def test_valid_emails(email):
    assert validate_email(email) == email.lower()


@pytest.mark.parametrize("email", [
    "notanemail", "@nodomain.com", "user@", "user@.com", "",
])
def test_invalid_emails(email):
    with pytest.raises(HTTPException) as exc:
        validate_email(email)
    assert exc.value.status_code == 422


# ── Password strength ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("pw", ["Abcdef12", "MyStr0ng!", "UPPER1lower"])
def test_strong_passwords_pass(pw):
    validate_password_strength(pw)  # should not raise


@pytest.mark.parametrize("pw,reason", [
    ("short1A", "too short"),
    ("alllower1", "no uppercase"),
    ("ALLUPPER", "no digit"),
    ("NoDigit!!", "no digit"),
])
def test_weak_passwords_raise(pw, reason):
    with pytest.raises(HTTPException) as exc:
        validate_password_strength(pw)
    assert exc.value.status_code == 422, reason


# ── Score ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("s", [0.0, 0.5, 1.0, 0.999])
def test_valid_scores(s):
    assert validate_score(s) == s


@pytest.mark.parametrize("s", [-0.01, 1.001, 2.0, -1.0])
def test_invalid_scores(s):
    with pytest.raises(HTTPException) as exc:
        validate_score(s)
    assert exc.value.status_code == 422


# ── Pagination ────────────────────────────────────────────────────────────────

def test_valid_pagination():
    assert validate_pagination(1, 20) == (1, 20)
    assert validate_pagination(5, 100) == (5, 100)


def test_invalid_page():
    with pytest.raises(HTTPException):
        validate_pagination(0, 10)


def test_invalid_page_size_too_large():
    with pytest.raises(HTTPException):
        validate_pagination(1, 101)


def test_invalid_page_size_zero():
    with pytest.raises(HTTPException):
        validate_pagination(1, 0)
