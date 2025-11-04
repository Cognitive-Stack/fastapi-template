from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ArtifactCreate(BaseModel):
    """Schema for creating an artifact"""
    type: str = Field(description="Type of artifact: 'repository', 'zip', 'pdf', 'doc', etc.")
    name: str = Field(description="Display name for the artifact")
    source: Optional[str] = Field(default=None, description="Source URL or path")


class RepositoryContextCreate(BaseModel):
    """Schema for adding repository context (flexible for compatibility)"""
    url: Optional[str] = Field(default=None, description="Repository URL")
    source: Optional[str] = Field(default=None, description="Repository source URL")
    name: Optional[str] = Field(default=None, description="Repository name")
    repo_url: Optional[str] = Field(default=None, description="Alternative field for repository URL")


class ArtifactUpdate(BaseModel):
    """Schema for updating an artifact"""
    name: Optional[str] = Field(None, description="Updated name")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class Artifact(BaseModel):
    """Base artifact schema"""
    id: str
    session_id: str
    user_id: str
    type: str
    name: str
    source: Optional[str] = None
    files: Optional[List[Dict[str, Any]]] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    size: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    deleted: bool = False
    deleted_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439010",
                "session_id": "507f1f77bcf86cd799439011",
                "user_id": "507f1f77bcf86cd799439012",
                "type": "repository",
                "name": "My Project",
                "source": "https://github.com/user/repo",
                "files": None,
                "content": None,
                "metadata": {"language": "python"},
                "size": 1024000,
                "created_at": "2025-11-04T10:00:00Z",
                "updated_at": "2025-11-04T10:00:00Z",
                "deleted": False,
                "deleted_at": None
            }
        }


# Alias for backwards compatibility
ArtifactResponse = Artifact


class ArtifactListResponse(BaseModel):
    """Schema for listing artifacts"""
    artifacts: List[Artifact]
    total: int
