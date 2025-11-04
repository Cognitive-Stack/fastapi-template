from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import Field
from app.models.base import BaseModel as Base, PyObjectId


class ArtifactModel(Base):
    """
    Artifact model representing code repositories, PDF files, documents, etc.
    that can be attached to chat sessions.
    """
    session_id: PyObjectId = Field(description="ID of the chat session this artifact belongs to")
    user_id: PyObjectId = Field(description="ID of the user who owns this artifact")

    # Artifact type: 'repository', 'zip', 'pdf', 'doc', 'text', etc.
    type: str = Field(description="Type of artifact")

    # Display name for the artifact
    name: str = Field(description="Display name of the artifact")

    # Source information (URL, filename, etc.)
    source: Optional[str] = Field(default=None, description="Source URL or filename")

    # For code artifacts: list of files with content
    files: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of files (for code artifacts)")

    # For document artifacts: extracted text content
    content: Optional[str] = Field(default=None, description="Extracted content (for document artifacts)")

    # Metadata (file size, page count, etc.)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    # File size in bytes
    size: Optional[int] = Field(default=None, description="Size in bytes")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "session_id": "507f1f77bcf86cd799439011",
                "user_id": "507f1f77bcf86cd799439012",
                "type": "repository",
                "name": "My Project",
                "source": "https://github.com/user/repo",
                "files": [],
                "content": None,
                "metadata": {"language": "python"},
                "size": 1024000,
                "created_at": "2025-11-04T10:00:00Z",
                "updated_at": "2025-11-04T10:00:00Z"
            }
        }
