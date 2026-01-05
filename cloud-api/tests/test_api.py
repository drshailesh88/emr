"""API integration tests"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil
import os

# Set test environment before importing app
os.environ["DATABASE_PATH"] = ":memory:"
os.environ["BACKUP_STORAGE_PATH"] = tempfile.mkdtemp()
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-chars-long"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"

from main import app
from src.database import init_db
from src.backup.storage import init_storage


@pytest.fixture(scope="function")
async def test_db():
    """Create test database"""
    db = init_db(":memory:")
    await db.initialize()
    yield db


@pytest.fixture(scope="function")
def test_storage():
    """Create test storage"""
    temp_dir = tempfile.mkdtemp()
    storage = init_storage(temp_dir)
    yield storage
    shutil.rmtree(temp_dir)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestAuthentication:
    """Test authentication endpoints"""

    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "securepassword123",
                "name": "Dr. Test User",
                "phone": "+919876543210",
                "license_number": "MH-12345"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["name"] == "Dr. Test User"

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        # Register first user
        client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123",
                "name": "First User"
            }
        )

        # Try to register with same email
        response = client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password456",
                "name": "Second User"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post(
            "/auth/register",
            json={
                "email": "test2@example.com",
                "password": "weak",  # Less than 8 characters
                "name": "Dr. Test"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_login_success(self, client):
        """Test successful login"""
        # Register user first
        client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "password": "password123",
                "name": "Dr. Login Test"
            }
        )

        # Login
        response = client.post(
            "/auth/login",
            json={
                "email": "login@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "login@example.com"

    def test_login_invalid_password(self, client):
        """Test login with invalid password"""
        # Register user
        client.post(
            "/auth/register",
            json={
                "email": "test3@example.com",
                "password": "correctpassword",
                "name": "Dr. Test"
            }
        )

        # Try to login with wrong password
        response = client.post(
            "/auth/login",
            json={
                "email": "test3@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401


class TestBackup:
    """Test backup endpoints"""

    def get_auth_token(self, client) -> str:
        """Helper to get authentication token"""
        response = client.post(
            "/auth/register",
            json={
                "email": f"backup{id(self)}@example.com",
                "password": "password123",
                "name": "Dr. Backup Test"
            }
        )
        return response.json()["access_token"]

    def test_upload_backup(self, client):
        """Test backup upload"""
        token = self.get_auth_token(client)

        # Create test backup data
        backup_data = b"encrypted-backup-data-test-content"

        response = client.post(
            "/backup/upload",
            files={"file": ("backup.enc", backup_data, "application/octet-stream")},
            data={
                "device_id": "test-device-123",
                "device_name": "Test Desktop"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "backup_id" in data
        assert data["size_bytes"] == len(backup_data)

    def test_upload_empty_file(self, client):
        """Test upload with empty file"""
        token = self.get_auth_token(client)

        response = client.post(
            "/backup/upload",
            files={"file": ("backup.enc", b"", "application/octet-stream")},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400

    def test_get_latest_backup(self, client):
        """Test getting latest backup metadata"""
        token = self.get_auth_token(client)

        # Upload a backup first
        backup_data = b"test-backup-content"
        client.post(
            "/backup/upload",
            files={"file": ("backup.enc", backup_data, "application/octet-stream")},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Get latest backup
        response = client.get(
            "/backup/latest",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "backup_id" in data
        assert data["size_bytes"] == len(backup_data)

    def test_get_latest_backup_no_backups(self, client):
        """Test getting latest backup when none exist"""
        token = self.get_auth_token(client)

        response = client.get(
            "/backup/latest",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    def test_download_backup(self, client):
        """Test backup download"""
        token = self.get_auth_token(client)

        # Upload backup
        backup_data = b"encrypted-test-content-for-download"
        upload_response = client.post(
            "/backup/upload",
            files={"file": ("backup.enc", backup_data, "application/octet-stream")},
            headers={"Authorization": f"Bearer {token}"}
        )
        backup_id = upload_response.json()["backup_id"]

        # Download backup
        response = client.get(
            f"/backup/download/{backup_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.content == backup_data

    def test_download_nonexistent_backup(self, client):
        """Test downloading non-existent backup"""
        token = self.get_auth_token(client)

        response = client.get(
            "/backup/download/nonexistent-backup-id",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    def test_sync_status(self, client):
        """Test sync status endpoint"""
        token = self.get_auth_token(client)

        # Upload backups from different devices
        client.post(
            "/backup/upload",
            files={"file": ("backup1.enc", b"data1", "application/octet-stream")},
            data={"device_name": "Desktop"},
            headers={"Authorization": f"Bearer {token}"}
        )
        client.post(
            "/backup/upload",
            files={"file": ("backup2.enc", b"data2", "application/octet-stream")},
            data={"device_name": "Laptop"},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Get sync status
        response = client.get(
            "/backup/sync/status",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["backup_count"] == 2
        assert len(data["devices"]) == 2
        assert "Desktop" in data["devices"]
        assert "Laptop" in data["devices"]

    def test_unauthorized_access(self, client):
        """Test accessing protected endpoints without auth"""
        response = client.get("/backup/latest")
        assert response.status_code == 403  # No auth header


class TestHealth:
    """Test health and root endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
