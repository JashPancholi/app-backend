from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    referral_code: Optional[str] = Field(None, description="Referral code if applicable")
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone_number": "1234567890",
                "referral_code": "ABCD"
            }
        }

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe Updated",
                "email": "john.updated@example.com"
            }
        }

class UserResponse(BaseModel):
    unique_id: str
    first_name: str
    last_name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    role: str
    credits: int
    balance: int
    referral_code: str
    referred_by: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    limit: int
    has_more: bool

