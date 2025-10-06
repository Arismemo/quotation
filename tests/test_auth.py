"""Tests for authentication functionality."""

from fastapi.testclient import TestClient


class TestAuth:
    """Test authentication endpoints."""

    def test_register_user(self, client: TestClient, test_user_data):
        """Test user registration."""
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "user_id" in data["data"]
        assert data["data"]["user_id"] is not None

    def test_register_duplicate_user(self, client: TestClient, test_user_data):
        """Test registration with duplicate username."""
        # First registration
        client.post("/api/auth/register", json=test_user_data)

        # Second registration should fail
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 400

    def test_login_user(self, client: TestClient, test_user_data):
        """Test user login."""
        # Register user first
        client.post("/api/auth/register", json=test_user_data)

        # Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        login_data = {"username": "nonexistent", "password": "wrongpassword"}
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401

    def test_get_current_user(self, client: TestClient, test_user_data):
        """Test getting current user info."""
        # Register and login
        client.post("/api/auth/register", json=test_user_data)
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
