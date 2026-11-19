
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.database import DATABASE_URL, Base, get_db
from app.main import app
from app.models import URL


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

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_test_database():
    with test_engine.begin() as connection:
        connection.execute(delete(URL))

    yield

    with test_engine.begin() as connection:
        connection.execute(delete(URL))


@pytest.fixture
def test_client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
