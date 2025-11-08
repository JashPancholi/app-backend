import pytest
import jwt
import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

# Assumes the new jwt.py file is at 'app.core.jwt'
# Make sure this import path matches your project structure.
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    CredentialsException,  # Import the custom exception classes
    TokenExpiredException,
    InvalidTokenException
)

# --- Test Constants ---
TEST_USER_ID = "test-user-uuid-123"
TEST_USER_ROLE = "USER"

# --- Helper Variables ---
# Use getenv with a default to match the logic in jwt.py
SECRET_KEY = os.getenv("JWT_SECRET", "8587a92cc1278e23c46f6bc714b0eec6583e70d16f0da4aec7cafef662e40f9d")
ALGORITHM = os.getenv("JWT_ALG", "HS256")

if not SECRET_KEY:
    print("Warning: JWT_SECRET is not set. Using a default for testing.")
    # --- THIS IS THE FIX ---
    # This key MUST match the default key in your jwt.py file
    SECRET_KEY = "a-very-insecure-default-secret-key-for-dev"


# --- Test Cases ---

def test_create_and_verify_access_token():
    """Tests successful creation and verification of an access token."""
    token = create_access_token(user_id=TEST_USER_ID, role=TEST_USER_ROLE)
    
    assert isinstance(token, str)
    
    # verify_access_token should return a dict
    payload = verify_access_token(token)
    assert payload["user_id"] == TEST_USER_ID
    assert payload["role"] == TEST_USER_ROLE

def test_create_and_verify_refresh_token():
    """Tests successful creation and verification of a refresh token."""
    token = create_refresh_token(user_id=TEST_USER_ID)
    
    assert isinstance(token, str)
    
    # verify_refresh_token should return just the user_id string
    user_id = verify_refresh_token(token)
    assert user_id == TEST_USER_ID

def test_expired_token_raises_exception():
    """Tests that an expired token raises TokenExpiredException for both types."""
    
    # Create a token that expired 1 second ago
    expire = datetime.now(timezone.utc) - timedelta(seconds=1)
    
    # Manually created token must have all expected claims
    to_encode_access = {
        "sub": TEST_USER_ID, 
        "role": TEST_USER_ROLE, 
        "type": "access", 
        "exp": expire
    }
    
    expired_token = jwt.encode(to_encode_access, SECRET_KEY, algorithm=ALGORITHM)
    
    # Test against verify_access_token
    with pytest.raises(TokenExpiredException) as exc_info_access:
        verify_access_token(expired_token)
    assert exc_info_access.value.status_code == 401
    assert exc_info_access.value.detail == "Token has expired"
    
    # Test against verify_refresh_token (with a refresh token payload)
    to_encode_refresh = {
        "sub": TEST_USER_ID, 
        "type": "refresh", 
        "exp": expire
    }
    expired_refresh_token = jwt.encode(to_encode_refresh, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(TokenExpiredException) as exc_info_refresh:
        verify_refresh_token(expired_refresh_token)
    assert exc_info_refresh.value.status_code == 401
    assert exc_info_refresh.value.detail == "Token has expired"

def test_invalid_token_signature_raises_exception():
    """Tests that a token with a bad signature raises CredentialsException."""
    token = create_access_token(user_id=TEST_USER_ID, role=TEST_USER_ROLE)
    
    # Create a bad token by adding extra characters
    invalid_token = token + "invalid-signature"
    
    with pytest.raises(CredentialsException) as exc_info:
        verify_access_token(invalid_token)
        
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_access_token_missing_sub_raises_exception():
    """Tests that an access token missing the 'sub' claim fails validation."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {
        "role": TEST_USER_ROLE,
        "type": "access",
        "exp": expire
    } # 'sub' is missing
    
    bad_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    with pytest.raises(CredentialsException) as exc_info:
        verify_access_token(bad_token)
        
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_access_token_missing_role_raises_exception():
    """Tests that an access token missing the 'role' claim fails validation."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {
        "sub": TEST_USER_ID,
        "type": "access",
        "exp": expire
    } # 'role' is missing
    
    bad_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    with pytest.raises(CredentialsException) as exc_info:
        verify_access_token(bad_token)
        
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_refresh_token_missing_sub_raises_exception():
    """Tests that a refresh token missing the 'sub' claim fails validation."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {
        "type": "refresh",
        "exp": expire
    } # 'sub' is missing
    
    bad_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    with pytest.raises(CredentialsException) as exc_info:
        verify_refresh_token(bad_token)
        
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_invalid_token_type_raises_exception():
    """
    Tests that using the wrong token type for verification fails.
    (e.g., using a refresh token as an access token)
    """
    # Create a refresh token
    refresh_token = create_refresh_token(user_id=TEST_USER_ID)
    
    # ...and try to use it with verify_access_token
    with pytest.raises(InvalidTokenException) as exc_info:
        verify_access_token(refresh_token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token type"

    # Create an access token
    access_token = create_access_token(user_id=TEST_USER_ID, role=TEST_USER_ROLE)
    
    # ...and try to use it with verify_refresh_token
    with pytest.raises(InvalidTokenException) as exc_info_refresh:
        verify_refresh_token(access_token)
    assert exc_info_refresh.value.status_code == 401
    assert exc_info_refresh.value.detail == "Invalid token type"