"""
Pytest configuration and fixtures for testing
"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load test environment variables
load_dotenv()

# Import app and database
from app import app
from models.database import Base
from db import get_db, SessionLocal

# Use test database if specified, otherwise derive from main database
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL or TEST_DATABASE_URL must be set in environment variables")
    
    # For PostgreSQL, modify database name to use test database
    if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
        # Replace database name with test_db
        if "/" in DATABASE_URL.rsplit("@", 1)[-1]:
            parts = DATABASE_URL.rsplit("/", 1)
            TEST_DATABASE_URL = parts[0] + "/test_db"
        else:
            TEST_DATABASE_URL = DATABASE_URL + "_test"
    else:
        # For other databases, append _test
        TEST_DATABASE_URL = DATABASE_URL.rsplit("/", 1)[0] + "/test_db"

# Create test engine (PostgreSQL doesn't need check_same_thread)
test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def test_db():
    """Create a test database session"""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up tables
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone_number": "1234567890"
    }

@pytest.fixture
def sample_user_data_2():
    """Second sample user data for testing"""
    return {
        "first_name": "Test2",
        "last_name": "User2",
        "email": "test2@example.com",
        "phone_number": "0987654321"
    }

