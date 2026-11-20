import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.database import DATABASE_URL, Base, get_db
from app.main import app
from app.models import URL
from app.cache import redis_client


# --------------------------------------------------
# TEST DATABASE
# --------------------------------------------------

TEST_DATABASE_URL = make_url(DATABASE_URL).set(
    database="url_shortener_test"
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


# Create tables in the test database
Base.metadata.create_all(bind=test_engine)


# --------------------------------------------------
# DATABASE DEPENDENCY OVERRIDE
# --------------------------------------------------

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


# Preserve any existing dependency override
previous_override = app.dependency_overrides.get(get_db)

app.dependency_overrides[get_db] = override_get_db


# --------------------------------------------------
# REDIS CLEANUP
# --------------------------------------------------

def clean_test_redis():
    """
    Remove Linkly-related Redis cache and rate-limit keys
    without flushing the entire Redis database.
    """

    patterns = [
        "url:*",
        "rate_limit:shorten:*",
    ]

    for pattern in patterns:
        keys = list(redis_client.scan_iter(match=pattern))

        if keys:
            redis_client.delete(*keys)


# --------------------------------------------------
# CLEAN DATABASE BEFORE AND AFTER EACH TEST
# --------------------------------------------------

@pytest.fixture(autouse=True)
def clean_test_database():

    with test_engine.begin() as connection:
        connection.execute(delete(URL))

    clean_test_redis()

    yield

    with test_engine.begin() as connection:
        connection.execute(delete(URL))

    clean_test_redis()


# --------------------------------------------------
# FASTAPI TEST CLIENT
# --------------------------------------------------

@pytest.fixture
def test_client():

    with TestClient(app) as client:
        yield client


# --------------------------------------------------
# TEST DATABASE SESSION
# --------------------------------------------------

@pytest.fixture
def test_db():

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# RESTORE APP CONFIGURATION AFTER TEST SESSION
# --------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def restore_dependency_overrides():

    yield

    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override

    test_engine.dispose()