from datetime import datetime
from pydantic import Field
from typing import Optional, List
from app.models.base import BaseModel, PyObjectId
from app.schemas.users import User, AuthProvider 


class UserModel(BaseModel, User):
    auth_provider: AuthProvider = AuthProvider.LOCAL
    hashed_password: str
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None