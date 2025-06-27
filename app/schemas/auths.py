from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.users import User


class Token(User):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime


class TokenData(BaseModel):
    email: str
    exp: datetime
    token_type: Literal["access", "refresh", "reset", "verify"]


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    type: Literal["access", "refresh", "reset", "verify"]
