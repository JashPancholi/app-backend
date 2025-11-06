import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from pydantic import BaseModel

# --- Config variables are now loaded inside functions ---
# This ensures they are read *after* .env is loaded (e.g., by conftest.py)

# exception for auth error
CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# This defines the data we store in the token ("sub" is the standard)
class TokenPayload(BaseModel):
    sub: str | None = None

def create_access_token(subject: str) -> str:
    # --- Load vars inside the function ---
    SECRET_KEY = os.getenv("JWT_SECRET")
    ALGORITHM = os.getenv("JWT_ALG", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TTL_MIN", 30))
    # ---
    
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set in environment")
        
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: str) -> str:
    # --- Load vars inside the function ---
    SECRET_KEY = os.getenv("JWT_SECRET")
    ALGORITHM = os.getenv("JWT_ALG", "HS256")
    REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_REFRESH_TTL_MIN", 43200))
    # ---
    
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set in environment")
        
    expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenPayload:
    # --- Load vars inside the function ---
    SECRET_KEY = os.getenv("JWT_SECRET")
    ALGORITHM = os.getenv("JWT_ALG", "HS256")
    # ---

    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set in environment")
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 'sub' (subject) is a standard claim for the user ID
        token_data = TokenPayload(sub=payload.get("sub"))
        if token_data.sub is None:
            raise CredentialsException
            
        return token_data
        
    except jwt.ExpiredSignatureError:
        #handle expired tokens
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        #Any other JWT error
        raise CredentialsException