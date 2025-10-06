from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    STAFF = "staff"
    ADMIN = "admin"
    

class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: str

class UserCreate(UserBase):
    name: str
    email: EmailStr
    password: str
    role: UserRole
    zone_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_deleted: bool = Field(default=False)


class UserInDB(UserBase):
    id: str = Field(..., alias="_id")
    role: UserRole = UserRole.USER
    password: str
    created_at: datetime = Field(default_factory=datetime.now)
    purchased_passes: List[str] = []
    otp_verified: bool = False
    otp_code: Optional[str] = None
    otp_expiry: Optional[datetime] = None
    otp_attempts: int = 0
    zone_id: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class User(UserBase):
    id: str = Field(..., alias="_id")
    role: UserRole
    created_at: datetime

class UserLogin(BaseModel):
    email: str 
    password: str

class OTPVerify(BaseModel):
    phone: str
    otp_code: str
