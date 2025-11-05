import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from app import app 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base, UserDB

# Setup the database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Using SQLite for testing

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables in the test database
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="module")
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    client = TestClient(app)
    yield client


@pytest.fixture(scope="module")
def create_user(db):
    # Create a test user
    user = UserDB(
        unique_id="user_1",
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="1234567890",
        role="USER",
        credits=100,  # Initial credits
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def create_admin_user(db):
    # Create an admin user for testing allocate points
    admin_user = UserDB(
        unique_id="admin_1",
        first_name="Admin",
        last_name="User",
        email="admin.user@example.com",
        phone_number="0987654321",
        role="ADMIN",
        credits=500,  # Admin has more credits
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user


def test_allocate_credits(client, db, create_user, create_admin_user):
    # Admin allocates credits to a regular user
    response = client.post(
        "/points/allocate",
        json={
            "current_user_id": create_admin_user.unique_id,
            "target_user_id": create_user.unique_id,
            "points": 50,
        },
    )

    # Assert successful allocation
    assert response.status_code == 200
    assert response.json() == {"message": f"Points successfully allocated to user {create_user.unique_id}"}

    # Verify the updated credits
    updated_user = db.query(UserDB).filter(UserDB.unique_id == create_user.unique_id).first()
    assert updated_user.credits == 150


def test_redeem_credits(client, db, create_user):
    # User redeems some of their credits
    response = client.post(
        "/points/redeem",
        json={
            "current_user_id": create_user.unique_id,
            "points": 30,
        },
    )

    # Assert successful redemption
    assert response.status_code == 200
    assert response.json() == {"message": "Points redeemed successfully"}

    # Verify the updated credits
    updated_user = db.query(UserDB).filter(UserDB.unique_id == create_user.unique_id).first()
    assert updated_user.credits == 120  # Initial 150 - Redeemed 30


def test_transaction_history(client, db, create_user):
    # Fetch transaction history for the user
    response = client.post(
        "/transactions/history",
        json={"user_id": create_user.unique_id},
    )

    # Assert response is correct
    assert response.status_code == 200
    assert isinstance(response.json().get("transaction_history"), list)
    assert len(response.json().get("transaction_history")) > 0  # Should contain at least one transaction


def test_leaderboard(client, db, create_user, create_admin_user):
    # Add a few users for the leaderboard
    response = client.get("/leaderboard?limit=10")
    
    # Assert that the leaderboard returns a list
    assert response.status_code == 200
    assert isinstance(response.json().get("data"), list)
    assert len(response.json().get("data")) > 0  # Should contain at least one user
