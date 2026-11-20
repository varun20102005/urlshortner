def test_create_short_url(test_client):

    response = test_client.post(
        "/api/shorten",
        json={"url": "https://www.google.com"}
    )

    assert response.status_code in (200, 201)

    data = response.json()

    assert "short_code" in data
    assert "short_url" in data


def test_invalid_url(test_client):

    response = test_client.post(
        "/api/shorten",
        json={"url": "not-a-valid-url"}
    )

    assert response.status_code == 422


def test_unknown_short_code(test_client):

    response = test_client.get(
        "/nonexistentcode",
        follow_redirects=False
    )

    assert response.status_code == 404