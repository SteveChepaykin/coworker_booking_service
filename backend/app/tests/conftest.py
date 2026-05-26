import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    Provides a standard, unauthenticated TestClient.
    """
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def authenticated_client() -> TestClient:
    """
    Provides a TestClient that is pre-authenticated as the default test user.
    This is useful for testing protected endpoints.
    """
    with TestClient(app) as c:
        response = c.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "password"}
        )
        # Add an assertion to provide a clear error if login fails during test setup.
        assert response.status_code == 200, f"Login failed with status {response.status_code}: {response.text}"
        token = response.json()["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"
        yield c