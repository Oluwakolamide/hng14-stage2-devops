import sys
from unittest.mock import MagicMock

# Mock the redis module before importing main so no real connection is attempted
mock_redis_module = MagicMock()
mock_redis_instance = MagicMock()
mock_redis_module.Redis.return_value = mock_redis_instance
sys.modules["redis"] = mock_redis_module

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)


def setup_function():
    """Reset mock state before each test."""
    mock_redis_instance.reset_mock()


def test_health_endpoint():
    """Health endpoint must return 200 with ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_job_returns_job_id():
    """POST /jobs must return a job_id UUID and push to Redis."""
    mock_redis_instance.lpush.return_value = 1
    mock_redis_instance.hset.return_value = 1

    response = client.post("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    # UUID4 is 36 characters including hyphens
    assert len(data["job_id"]) == 36

    # Verify Redis interactions
    mock_redis_instance.lpush.assert_called_once()
    mock_redis_instance.hset.assert_called_once()


def test_get_job_found():
    """GET /jobs/{id} returns job status when job exists."""
    mock_redis_instance.hget.return_value = "queued"

    response = client.get("/jobs/test-job-id-1234")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-job-id-1234"
    assert data["status"] == "queued"


def test_get_job_not_found_returns_404():
    """GET /jobs/{id} returns 404 when job does not exist."""
    mock_redis_instance.hget.return_value = None

    response = client.get("/jobs/nonexistent-id")
    assert response.status_code == 404
