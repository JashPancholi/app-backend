import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from typing import Dict, Any
from jwt import ExpiredSignatureError, InvalidTokenError
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable is not set")

ALGORITHM = os.getenv("JWT_ALG", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TTL_MIN", 30))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_REFRESH_TTL_MIN", 43200))

class CredentialsException(HTTPException):
    """Custom exception for invalid credentials."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class TokenExpiredException(HTTPException):
    """Custom exception for expired tokens."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

class InvalidTokenException(HTTPException):
    """Custom exception for invalid token types (e.g., refresh as access)."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_id,
        "role": role,
        "exp": int(expire.timestamp()),
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_id,
        "exp": int(expire.timestamp()),
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise TokenExpiredException()
    except InvalidTokenError:
        raise CredentialsException()

def verify_access_token(token: str) -> Dict[str, Any]:
    payload = _decode_token(token)
    
    if payload.get("type") != "access":
        raise InvalidTokenException()
        
    user_id = payload.get("sub")
    role = payload.get("role")
    
    if user_id is None or role is None:
        raise CredentialsException()
        
    return {"user_id": user_id, "role": role}

def verify_refresh_token(token: str) -> str:
    payload = _decode_token(token)
    
    if payload.get("type") != "refresh":
        raise InvalidTokenException()
        
    user_id = payload.get("sub")
    
    if user_id is None:
        raise CredentialsException()
        
    return user_id