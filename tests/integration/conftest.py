"""Fixtures that give integration tests a real Postgres database."""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  (importing registers the User table on Base)
from app.database import Base

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def db_engine():
    """Create a fresh set of tables in the test database for the whole run."""
    if not TEST_DATABASE_URL:
        if os.getenv("CI"):
            pytest.fail("TEST_DATABASE_URL must be set in CI")
        pytest.skip("TEST_DATABASE_URL is not set")

    if not (make_url(TEST_DATABASE_URL).database or "").endswith("_test"):
        pytest.fail("Refusing to run: the test database name must end in '_test'")

    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """A session for one test; every table is emptied afterward."""
    session = sessionmaker(bind=db_engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        with db_engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())