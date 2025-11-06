import pytest
import time
import jwt
import os  # <-- Import os here
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from app.core.jwt import (
    create_access_token, 
    create_refresh_token, 
    verify_token
    # --- DO NOT import SECRET_KEY or ALGORITHM here ---
)

# Use a test user ID for the "subject"
TEST_USER_ID = "test-user-uuid-123"

def test_create_and_verify_access_token():
    token = create_access_token(subject=TEST_USER_ID)
    
    assert isinstance(token, str)
    
    payload = verify_token(token)
    assert payload.sub == TEST_USER_ID

def test_create_and_verify_refresh_token():
    token = create_refresh_token(subject=TEST_USER_ID)
    
    assert isinstance(token, str)
    
    payload = verify_token(token)
    assert payload.sub == TEST_USER_ID

def test_expired_token_raises_exception():
    # --- Get env vars manually for this test ---
    # conftest.py will have loaded them by this point
    SECRET_KEY = os.getenv("JWT_SECRET")
    ALGORITHM = os.getenv("JWT_ALG")
    # ---
    
    # Create a token that expired 1 second ago
    expire = datetime.now(timezone.utc) - timedelta(seconds=1)
    to_encode = {"sub": TEST_USER_ID, "exp": expire}
    
    expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Use pytest.raises to check that the expected error occurs
    with pytest.raises(HTTPException) as exc_info:
        verify_token(expired_token)
        
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has expired"

def test_invalid_token_signature_raises_exception():
    token = create_access_token(subject=TEST_USER_ID)
    
    # Create a bad token by adding extra characters
    invalid_token = token + "invalid-signature"
    
    with pytest.raises(HTTPException) as exc_info:
        verify_token(invalid_token)
        
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_missing_subject_raises_exception():
    # --- Get env vars manually for this test ---
    SECRET_KEY = os.getenv("JWT_SECRET")
    ALGORITHM = os.getenv("JWT_ALG")
    # ---

    # Create a token with no "sub" field
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"foo": "bar", "exp": expire} # "sub" is missing
    
    bad_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    with pytest.raises(HTTPException) as exc_info:
        verify_token(bad_token)
        
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"