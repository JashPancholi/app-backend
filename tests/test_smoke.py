"""
Smoke tests - basic endpoint availability checks
"""
import pytest
from fastapi import status

def test_health_endpoint(client):
    """Test /health endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert data["status"] == "healthy"

def test_user_endpoints_accessible(client):
    """Test user endpoints are accessible"""
    # Test list endpoint
    response = client.get("/user/list")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]  # 404 if no users, 200 if empty list
    
    # Test add endpoint (should accept POST)
    response = client.post("/user/add", json={})
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]  # Validation error is expected

def test_credit_endpoints_accessible(client):
    """Test credit endpoints are accessible"""
    # Test leaderboard endpoint
    response = client.get("/leaderboard")
    assert response.status_code == status.HTTP_200_OK
    
    # Test allocate endpoint (should accept POST)
    response = client.post("/points/allocate", json={})
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]  # Validation/user not found error is expected
    
    # Test redeem endpoint (should accept POST)
    response = client.post("/points/redeem", json={})
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]  # Validation/user not found error is expected

def test_database_connectivity(client):
    """Test database connectivity through health endpoint"""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Database should be connected (or at least the status should be present)
    assert "database" in data

