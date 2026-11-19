
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import URL
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from app.main import app

def test_concurrent_clicks(test_client, test_db):
    # Create a short URL
    create_response = test_client.post(
        "/api/shorten",
        json={"url": "https://example.com"}
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    # Each worker sends one independent request
    def make_request():
        with TestClient(app) as client:
            return client.get(
                f"/{short_code}",
                follow_redirects=False
            )

    # Send 10 requests using 5 workers
    with ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(
            executor.map(
                lambda _: make_request(),
                range(10)
            )
        )

    # Every request should redirect successfully
    assert all(
        response.status_code == 302
        for response in responses
    )

    # Verify the final click count
    url_record = test_db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    assert url_record.click_count == 10

def test_redirect_nonexistent_url(test_client):
    response = test_client.get(
        "/doesnotexist123",
        follow_redirects=False
    )

    assert response.status_code == 404
def test_delete_nonexistent_url(test_client):
    response = test_client.delete(
        "/api/urls/doesnotexist123"
    )

    assert response.status_code == 404
def test_redirect_expired_url(test_client):
    expired_time = (
        datetime.now(timezone.utc) + timedelta(minutes=5)
    ).isoformat()

    create_response = test_client.post(
        "/api/shorten",
        json={
            "url": "https://example.com",
            "expires_at": expired_time
        }
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    # Change the expiry directly in the test database
    from app.models import URL
    from app.database import SessionLocal

    # Do not use SessionLocal here; it connects to development DB.

def test_expired_url(test_client):
    expired_time = (
        datetime.now(timezone.utc) - timedelta(minutes=5)
    ).isoformat()

    create_response = test_client.post(
        "/api/shorten",
        json={
            "url": "https://example.com",
            "expires_at": expired_time
        }
    )

    assert create_response.status_code == 422

def test_home(test_client):
    response = test_client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "URL Shortener API is running"
    }


def test_shorten_url(test_client):
    response = test_client.post(
        "/api/shorten",
        json={"url": "https://example.com"}
    )

    assert response.status_code == 201

    data = response.json()

    assert "short_code" in data
    assert "short_url" in data


def test_invalid_url(test_client):
    response = test_client.post(
        "/api/shorten",
        json={"url": "not-a-valid-url"}
    )

    assert response.status_code == 422


def test_redirect_url(test_client):
    create_response = test_client.post(
        "/api/shorten",
        json={"url": "https://example.com"}
    )

    short_code = create_response.json()["short_code"]

    response = test_client.get(
        f"/{short_code}",
        follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/"


def test_analytics(test_client):
    create_response = test_client.post(
        "/api/shorten",
        json={"url": "https://example.com"}
    )

    short_code = create_response.json()["short_code"]

    test_client.get(
        f"/{short_code}",
        follow_redirects=False
    )

    response = test_client.get(
        f"/api/analytics/{short_code}"
    )

    assert response.status_code == 200
    assert response.json()["total_clicks"] == 1


def test_delete_url(test_client):
    create_response = test_client.post(
        "/api/shorten",
        json={"url": "https://example.com"}
    )

    short_code = create_response.json()["short_code"]

    response = test_client.delete(
        f"/api/urls/{short_code}"
    )

    assert response.status_code == 200

    redirect_response = test_client.get(
        f"/{short_code}",
        follow_redirects=False
    )

    assert redirect_response.status_code == 404
