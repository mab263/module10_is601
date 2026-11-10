from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas import UserCreate, UserRead

VALID = {"username": "alice", "email": "alice@example.com", "password": "secret123"}


def test_valid_user_create():
    user = UserCreate(**VALID)
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.password == "secret123"


def test_email_is_lowercased():
    user = UserCreate(**{**VALID, "email": "Alice@Example.COM"})
    assert user.email == "alice@example.com"


@pytest.mark.parametrize(
    "email",
    ["not-an-email", "alice@", "@example.com", "alice@@example.com", "alice example@x.com", ""],
)
def test_invalid_emails_are_rejected(email):
    with pytest.raises(ValidationError):
        UserCreate(**{**VALID, "email": email})


@pytest.mark.parametrize(
    "username",
    ["", "ab", "a" * 51, "has space", " alice", "bad-name!"],
)
def test_invalid_usernames_are_rejected(username):
    with pytest.raises(ValidationError):
        UserCreate(**{**VALID, "username": username})


@pytest.mark.parametrize(
    "password",
    ["", "short", "1234567", "a" * 73, "密" * 25],
)
def test_invalid_passwords_are_rejected(password):
    with pytest.raises(ValidationError):
        UserCreate(**{**VALID, "password": password})


@pytest.mark.parametrize("password", ["12345678", "a" * 72])
def test_passwords_at_the_limits_are_accepted(password):
    assert UserCreate(**{**VALID, "password": password}).password == password


@pytest.mark.parametrize("missing", ["username", "email", "password"])
def test_missing_fields_are_rejected(missing):
    data = {key: value for key, value in VALID.items() if key != missing}
    with pytest.raises(ValidationError):
        UserCreate(**data)


def make_orm_user():
    """Stands in for a database User, including the password hash."""
    return SimpleNamespace(
        id=1,
        username="alice",
        email="alice@example.com",
        password_hash="$2b$12$abcdefghijklmnopqrstuv",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_user_read_copies_the_public_fields():
    user = UserRead.model_validate(make_orm_user())
    assert (user.id, user.username, user.email) == (1, "alice", "alice@example.com")
    assert user.created_at == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_user_read_never_includes_the_password_hash():
    user = UserRead.model_validate(make_orm_user())
    assert set(user.model_dump()) == {"id", "username", "email", "created_at"}
    assert "password" not in user.model_dump_json()
    assert "$2b$" not in user.model_dump_json()


def test_user_read_schema_has_no_password_fields():
    assert "password_hash" not in UserRead.model_fields
    assert "password" not in UserRead.model_fields