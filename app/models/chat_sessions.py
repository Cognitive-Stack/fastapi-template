from typing import Optional
from datetime import datetime
from pydantic import Field
from app.models.base import BaseModel as Base, PyObjectId


class ChatSession(Base):
    user_id: PyObjectId
    title: str = Field(default="New Chat")
    message_count: int = Field(default=0)
    last_message_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "title": "My Chat Session",
                "message_count": 5,
                "last_message_at": "2025-11-04T10:00:00Z"
            }
        }
