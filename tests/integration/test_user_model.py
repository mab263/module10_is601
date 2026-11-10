from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.exc import DataError, IntegrityError

from app.models import User
from app.schemas import UserCreate, UserRead
from app.security import hash_password, verify_password


def register(session, username="alice", email="alice@example.com", password="secret123"):
    """Validate the input with the schema, hash the password, and save a new user."""
    data = UserCreate(username=username, email=email, password=password)
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def count_users(session):
    return session.scalar(select(func.count()).select_from(User))


def test_saved_user_gets_an_id_and_a_timestamp(db_session):
    user = register(db_session)
    assert user.id is not None
    assert datetime.now(timezone.utc) - user.created_at < timedelta(minutes=1)


def test_password_is_stored_as_a_hash(db_session):
    register(db_session, password="secret123")
    stored = db_session.execute(
        text("SELECT password_hash FROM users WHERE username = :name"),
        {"name": "alice"},
    ).scalar_one()
    assert stored != "secret123"
    assert stored.startswith("$2")
    assert verify_password("secret123", stored)


def test_stored_hash_rejects_the_wrong_password(db_session):
    register(db_session)
    db_session.expire_all()
    saved = db_session.scalar(select(User).where(User.username == "alice"))
    assert verify_password("secret123", saved.password_hash)
    assert not verify_password("wrong-password", saved.password_hash)


def test_duplicate_username_is_rejected(db_session):
    register(db_session)
    with pytest.raises(IntegrityError) as error:
        register(db_session, email="other@example.com")
    assert "Key (username)=(alice)" in str(error.value.orig)
    db_session.rollback()
    assert count_users(db_session) == 1


def test_duplicate_email_is_rejected(db_session):
    register(db_session)
    with pytest.raises(IntegrityError) as error:
        register(db_session, username="bob")
    assert "Key (email)=(alice@example.com)" in str(error.value.orig)
    db_session.rollback()
    assert count_users(db_session) == 1


def test_email_uniqueness_ignores_case(db_session):
    register(db_session, email="alice@example.com")
    with pytest.raises(IntegrityError) as error:
        register(db_session, username="bob", email="ALICE@Example.COM")
    assert "Key (email)=(alice@example.com)" in str(error.value.orig)


def test_password_hash_is_required(db_session):
    db_session.add(User(username="alice", email="alice@example.com"))
    with pytest.raises(IntegrityError) as error:
        db_session.commit()
    assert "password_hash" in str(error.value.orig)


def test_username_longer_than_the_column_is_rejected_by_the_database(db_session):
    db_session.add(User(username="a" * 51, email="a@example.com", password_hash="x"))
    with pytest.raises(DataError):
        db_session.commit()


@pytest.mark.parametrize(
    "email",
    ["not-an-email", "alice@", "@example.com", "alice@@example.com"],
)
def test_invalid_email_is_rejected_before_anything_is_saved(db_session, email):
    with pytest.raises(ValidationError):
        register(db_session, email=email)
    assert count_users(db_session) == 0


def test_different_users_can_coexist(db_session):
    register(db_session, username="alice", email="alice@example.com")
    register(db_session, username="bob", email="bob@example.com")
    assert count_users(db_session) == 2


def test_user_read_from_a_real_user_has_no_password_hash(db_session):
    user = register(db_session)
    public = UserRead.model_validate(user)
    assert public.username == "alice"
    assert set(public.model_dump()) == {"id", "username", "email", "created_at"}
    assert user.password_hash not in public.model_dump_json()