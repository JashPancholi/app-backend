"""
Tests for Credits System - atomic transactions, race conditions, etc.
"""
import pytest
import threading
import time
from fastapi import status
from models.database import UserDB
from models.user_model import User
from models.role_model import Role

def test_allocate_points(client, test_db, sample_user_data):
    """Test basic allocation of points"""
    # Create admin user
    admin_data = {
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@test.com",
        "phone_number": "1111111111"
    }
    admin_response = client.post("/user/add", json=admin_data)
    admin_id = admin_response.json()["user"]["unique_id"]
    
    # Update admin role
    admin_db = test_db.query(UserDB).filter(UserDB.unique_id == admin_id).first()
    admin_db.role = Role.ADMIN.value
    test_db.commit()
    
    # Create target user
    user_response = client.post("/user/add", json=sample_user_data)
    user_id = user_response.json()["user"]["unique_id"]
    
    # Allocate points
    allocate_data = {
        "current_user_id": admin_id,
        "target_user_id": user_id,
        "points": 100
    }
    response = client.post("/points/allocate", json=allocate_data)
    
    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.json()
    
    # Verify points were allocated
    user = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    assert user.credits == 100

def test_redeem_points(client, test_db, sample_user_data):
    """Test basic redemption of points"""
    # Create user with credits
    user_response = client.post("/user/add", json=sample_user_data)
    user_id = user_response.json()["user"]["unique_id"]
    
    # Add credits directly
    user_db = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    user_db.credits = 100
    test_db.commit()
    
    # Redeem points
    redeem_data = {
        "current_user_id": user_id,
        "points": 50
    }
    response = client.post("/points/redeem", json=redeem_data)
    
    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.json()
    
    # Verify points were redeemed
    user = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    assert user.credits == 50

def test_insufficient_credits(client, test_db, sample_user_data):
    """Test redemption with insufficient credits"""
    # Create user with limited credits
    user_response = client.post("/user/add", json=sample_user_data)
    user_id = user_response.json()["user"]["unique_id"]
    
    # Add only 10 credits
    user_db = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    user_db.credits = 10
    test_db.commit()
    
    # Try to redeem more than available
    redeem_data = {
        "current_user_id": user_id,
        "points": 50
    }
    response = client.post("/points/redeem", json=redeem_data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insufficient credits" in response.json()["detail"]
    
    # Verify credits unchanged
    user = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    assert user.credits == 10

def test_concurrent_allocate(client, test_db, sample_user_data):
    """Test race condition with concurrent allocation"""
    # Create admin
    admin_data = {
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@test.com",
        "phone_number": "1111111111"
    }
    admin_response = client.post("/user/add", json=admin_data)
    admin_id = admin_response.json()["user"]["unique_id"]
    
    admin_db = test_db.query(UserDB).filter(UserDB.unique_id == admin_id).first()
    admin_db.role = Role.ADMIN.value
    test_db.commit()
    
    # Create target user
    user_response = client.post("/user/add", json=sample_user_data)
    user_id = user_response.json()["user"]["unique_id"]
    
    # Concurrent allocation results
    results = []
    errors = []
    
    def allocate_points_thread():
        try:
            allocate_data = {
                "current_user_id": admin_id,
                "target_user_id": user_id,
                "points": 10
            }
            response = client.post("/points/allocate", json=allocate_data)
            results.append(response.status_code)
        except Exception as e:
            errors.append(str(e))
    
    # Create 5 concurrent threads
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=allocate_points_thread)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    # All should succeed
    assert len(results) == 5
    assert all(status_code == status.HTTP_200_OK for status_code in results)
    
    # Verify total points (5 * 10 = 50)
    user = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    assert user.credits == 50

def test_double_spend_prevention(client, test_db, sample_user_data):
    """Test concurrent redemption prevention (double-spend)"""
    # Create user with credits
    user_response = client.post("/user/add", json=sample_user_data)
    user_id = user_response.json()["user"]["unique_id"]
    
    # Add 50 credits
    user_db = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    user_db.credits = 50
    test_db.commit()
    
    # Concurrent redemption results
    results = []
    
    def redeem_points_thread():
        redeem_data = {
            "current_user_id": user_id,
            "points": 30  # Each thread tries to redeem 30, but only 50 total
        }
        response = client.post("/points/redeem", json=redeem_data)
        results.append(response.status_code)
    
    # Create 3 concurrent threads (each trying to redeem 30, but only 50 available)
    threads = []
    for _ in range(3):
        thread = threading.Thread(target=redeem_points_thread)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    # At least one should fail due to insufficient credits
    success_count = sum(1 for r in results if r == status.HTTP_200_OK)
    failure_count = sum(1 for r in results if r == status.HTTP_400_BAD_REQUEST)
    
    # At least one should succeed, at least one should fail
    assert success_count >= 1
    assert failure_count >= 1
    
    # Verify final credits are consistent (should be 20 or 50, depending on which succeeded)
    user = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    assert user.credits in [20, 50]  # Either one succeeded (20) or none succeeded (50)

def test_atomic_transaction_rollback(client, test_db, sample_user_data):
    """Test rollback on errors"""
    # Create admin
    admin_data = {
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@test.com",
        "phone_number": "1111111111"
    }
    admin_response = client.post("/user/add", json=admin_data)
    admin_id = admin_response.json()["user"]["unique_id"]
    
    admin_db = test_db.query(UserDB).filter(UserDB.unique_id == admin_id).first()
    admin_db.role = Role.ADMIN.value
    test_db.commit()
    
    # Create target user
    user_response = client.post("/user/add", json=sample_user_data)
    user_id = user_response.json()["user"]["unique_id"]
    
    initial_credits = 0
    
    # Try to allocate to non-existent user (should rollback)
    allocate_data = {
        "current_user_id": admin_id,
        "target_user_id": "non-existent-id",
        "points": 100
    }
    response = client.post("/points/allocate", json=allocate_data)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # Verify target user credits unchanged
    user = test_db.query(UserDB).filter(UserDB.unique_id == user_id).first()
    assert user.credits == initial_credits

def test_leaderboard_cache_ttl(client, test_db, sample_user_data):
    """Test leaderboard cache expiration"""
    # Create users with different credit amounts
    user1_data = {**sample_user_data, "email": "user1@test.com", "phone_number": "1111111111"}
    user2_data = {**sample_user_data, "email": "user2@test.com", "phone_number": "2222222222"}
    
    user1_response = client.post("/user/add", json=user1_data)
    user2_response = client.post("/user/add", json=user2_data)
    
    user1_id = user1_response.json()["user"]["unique_id"]
    user2_id = user2_response.json()["user"]["unique_id"]
    
    # Set credits
    user1_db = test_db.query(UserDB).filter(UserDB.unique_id == user1_id).first()
    user1_db.credits = 100
    user2_db = test_db.query(UserDB).filter(UserDB.unique_id == user2_id).first()
    user2_db.credits = 200
    test_db.commit()
    
    # First request - should fetch fresh data
    response1 = client.get("/leaderboard?limit=10")
    assert response1.status_code == status.HTTP_200_OK
    assert response1.json()["cached"] == False
    
    # Second request immediately - should use cache
    response2 = client.get("/leaderboard?limit=10")
    assert response2.status_code == status.HTTP_200_OK
    assert response2.json()["cached"] == True
    assert "cache_age" in response2.json()

def test_history_pagination(client, test_db, sample_user_data):
    """Test transaction history pagination"""
    # Create user
    user_response = client.post("/user/add", json=sample_user_data)
    user_id = user_response.json()["user"]["unique_id"]
    
    # Create admin and allocate points multiple times
    admin_data = {
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@test.com",
        "phone_number": "1111111111"
    }
    admin_response = client.post("/user/add", json=admin_data)
    admin_id = admin_response.json()["user"]["unique_id"]
    
    admin_db = test_db.query(UserDB).filter(UserDB.unique_id == admin_id).first()
    admin_db.role = Role.ADMIN.value
    test_db.commit()
    
    # Allocate points 5 times
    for _ in range(5):
        allocate_data = {
            "current_user_id": admin_id,
            "target_user_id": user_id,
            "points": 10
        }
        client.post("/points/allocate", json=allocate_data)
    
    # Test pagination
    response = client.get(f"/history/{user_id}?page=1&limit=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "transaction_history" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "has_more" in data
    assert len(data["transaction_history"]) == 2
    assert data["total"] >= 5

def test_history_csv_export(client, test_db, sample_user_data):
    """Test CSV export of transaction history"""
    # Create user and admin
    user_response = client.post("/user/add", json=sample_user_data)
    user_id = user_response.json()["user"]["unique_id"]
    
    admin_data = {
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@test.com",
        "phone_number": "1111111111"
    }
    admin_response = client.post("/user/add", json=admin_data)
    admin_id = admin_response.json()["user"]["unique_id"]
    
    admin_db = test_db.query(UserDB).filter(UserDB.unique_id == admin_id).first()
    admin_db.role = Role.ADMIN.value
    test_db.commit()
    
    # Allocate some points
    allocate_data = {
        "current_user_id": admin_id,
        "target_user_id": user_id,
        "points": 50
    }
    client.post("/points/allocate", json=allocate_data)
    
    # Request CSV export
    response = client.get(f"/history/{user_id}?format=csv")
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    
    # Verify CSV content
    csv_content = response.text
    assert "transaction_id" in csv_content
    assert "type" in csv_content
    assert "points" in csv_content

