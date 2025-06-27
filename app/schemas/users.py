from datetime import datetime
from typing import Optional, List, Any
from enum import Enum

from pydantic import BaseModel, EmailStr, Field
from app.models.base import PyObjectId


class UserRoles(str, Enum):
    ADMIN = "admin"
    USER = "user"

class AuthProvider(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"


class UserTier(str, Enum):
    FREE = "free"
    ENTERPRISE = "enterprise"


class GoogleAuthRequest(BaseModel):
    token: str


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    birth_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    disabled: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    auth_provider: AuthProvider = AuthProvider.LOCAL
    google_id: Optional[str] = None
    completed_onboarding: bool = False
    tier: UserTier = UserTier.FREE


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    birth_date: datetime
    phone_number: str
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    birth_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    role: Optional[UserRoles] = None
    disabled: Optional[bool] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    completed_onboarding: Optional[bool] = False
    tier: Optional[UserTier] = None


class User(UserBase):
    id: PyObjectId
    role: UserRoles = UserRoles.USER
    email_verified: bool = False
    last_login: Optional[datetime] = None
