from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field(default="New Chat", max_length=100)


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)


class ChatSessionResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    title: str
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439010",
                "user_id": "507f1f77bcf86cd799439011",
                "title": "My Chat Session",
                "message_count": 5,
                "last_message_at": "2025-11-04T10:00:00Z",
                "created_at": "2025-11-04T09:00:00Z",
                "updated_at": "2025-11-04T10:00:00Z"
            }
        }
