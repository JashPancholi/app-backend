"""
Unit tests for User CRUD operations
"""
import pytest
from fastapi import status
from models.database import UserDB
from models.user_model import User

def test_create_user(client, test_db, sample_user_data):
    """Test 1: Create a new user"""
    response = client.post("/user/add", json=sample_user_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "user" in data
    assert data["user"]["first_name"] == sample_user_data["first_name"]
    assert data["user"]["email"] == sample_user_data["email"]
    
    # Verify user exists in database
    user = test_db.query(UserDB).filter(UserDB.email == sample_user_data["email"]).first()
    assert user is not None
    assert user.first_name == sample_user_data["first_name"]

def test_get_user_by_id(client, test_db, sample_user_data):
    """Test 2: Get user by unique_id"""
    # First create a user
    create_response = client.post("/user/add", json=sample_user_data)
    assert create_response.status_code == status.HTTP_200_OK
    user_id = create_response.json()["user"]["unique_id"]
    
    # Then retrieve it
    response = client.get(f"/user/profile/{user_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "user" in data
    assert data["user"]["unique_id"] == user_id
    assert data["user"]["first_name"] == sample_user_data["first_name"]
    assert data["user"]["email"] == sample_user_data["email"]

def test_update_user(client, test_db, sample_user_data):
    """Test 3: Update user profile"""
    # First create a user
    create_response = client.post("/user/add", json=sample_user_data)
    assert create_response.status_code == status.HTTP_200_OK
    user_id = create_response.json()["user"]["unique_id"]
    
    # Update the user
    update_data = {
        "unique_id": user_id,
        "first_name": "Updated",
        "last_name": "Name",
        "email": "updated@example.com"
    }
    response = client.put("/user/update", json=update_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user"]["first_name"] == "Updated"
    assert data["user"]["last_name"] == "Name"
    assert data["user"]["email"] == "updated@example.com"
    
    # Verify in database
    user = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    assert user.first_name == "Updated"

def test_delete_user(client, test_db, sample_user_data):
    """Test 4: Delete user"""
    # First create a user
    create_response = client.post("/user/add", json=sample_user_data)
    assert create_response.status_code == status.HTTP_200_OK
    user_id = create_response.json()["user"]["unique_id"]
    
    # Verify user exists
    user = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    assert user is not None
    
    # Delete the user
    delete_data = {"unique_id": user_id}
    response = client.delete("/user/delete", json=delete_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    
    # Verify user is deleted
    user = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    assert user is None

def test_list_users_pagination(client, test_db, sample_user_data, sample_user_data_2):
    """Test 5: List users with pagination"""
    # Create multiple users
    client.post("/user/add", json=sample_user_data)
    client.post("/user/add", json=sample_user_data_2)
    
    # Test pagination
    response = client.get("/user/list?page=1&limit=1")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "has_more" in data
    assert len(data["users"]) == 1
    assert data["page"] == 1
    assert data["limit"] == 1
    assert data["total"] >= 2

def test_user_validation(client, test_db):
    """Test 6: User validation (email uniqueness, required fields)"""
    # Test missing both email and phone
    invalid_data = {
        "first_name": "Test",
        "last_name": "User"
    }
    response = client.post("/user/add", json=invalid_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Test duplicate email
    sample_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "duplicate@example.com",
        "phone_number": "1111111111"
    }
    client.post("/user/add", json=sample_data)
    
    # Try to create another user with same email
    duplicate_response = client.post("/user/add", json=sample_data)
    # Should fail due to unique constraint (handled by database)
    assert duplicate_response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

