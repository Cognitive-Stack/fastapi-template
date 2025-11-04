from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.base import PyObjectId


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: str = Field(alias="_id")
    session_id: str
    user_id: str
    content: str
    role: str  # "user" or "assistant"
    created_at: datetime

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "session_id": "507f1f77bcf86cd799439010",
                "user_id": "507f1f77bcf86cd799439012",
                "content": "Hello, world!",
                "role": "user",
                "created_at": "2025-11-04T10:00:00Z"
            }
        }
