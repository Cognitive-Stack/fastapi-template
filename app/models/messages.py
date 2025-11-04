from typing import Optional
from pydantic import Field
from app.models.base import BaseModel as Base, PyObjectId


class Message(Base):
    session_id: PyObjectId
    user_id: PyObjectId
    content: str
    role: str = Field(default="user")  # "user" or "assistant"

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "session_id": "507f1f77bcf86cd799439010",
                "user_id": "507f1f77bcf86cd799439011",
                "content": "Hello, world!",
                "role": "user"
            }
        }
