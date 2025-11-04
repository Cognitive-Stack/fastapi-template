"""
Artifact controller for handling CRUD operations
"""
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.models.artifacts import ArtifactModel
from app.schemas.artifacts import Artifact, ArtifactCreate, ArtifactUpdate
from app.utils.object_storage import delete_artifact_files
from loguru import logger


class ArtifactController:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.get_collection("artifacts")

    async def create_artifact(
        self,
        session_id: str,
        user_id: str,
        artifact_data: ArtifactCreate,
        **additional_fields
    ) -> Artifact:
        """
        Create a new artifact

        Args:
            session_id: Chat session ID
            user_id: User ID
            artifact_data: Artifact creation data
            **additional_fields: Additional fields like files, metadata, size

        Returns:
            Created artifact
        """
        try:
            session_obj_id = ObjectId(session_id)
            user_obj_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session or user ID"
            )

        # Prepare artifact document
        artifact_dict = {
            "session_id": session_obj_id,
            "user_id": user_obj_id,
            "type": artifact_data.type,
            "name": artifact_data.name,
            "source": artifact_data.source,
            "files": None,
            "content": None,
            "metadata": {},
            "size": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "deleted": False,
            "deleted_at": None
        }

        # Add additional fields
        artifact_dict.update(additional_fields)

        # Insert into database
        result = await self.collection.insert_one(artifact_dict)

        # Return created artifact
        return await self.get_artifact(str(result.inserted_id), user_id)

    async def get_artifact(self, artifact_id: str, user_id: str) -> Artifact:
        """
        Get a single artifact by ID

        Args:
            artifact_id: Artifact ID
            user_id: User ID (for ownership verification)

        Returns:
            Artifact

        Raises:
            HTTPException: If artifact not found or access denied
        """
        try:
            artifact_obj_id = ObjectId(artifact_id)
            user_obj_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid artifact or user ID"
            )

        artifact = await self.collection.find_one({
            "_id": artifact_obj_id,
            "user_id": user_obj_id,
            "deleted": False
        })

        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact not found"
            )

        # Convert to Artifact schema
        return self._to_artifact_schema(artifact)

    async def get_artifacts_by_session(
        self,
        session_id: str,
        user_id: str,
        include_deleted: bool = False
    ) -> List[Artifact]:
        """
        Get all artifacts for a session

        Args:
            session_id: Chat session ID
            user_id: User ID
            include_deleted: Whether to include deleted artifacts

        Returns:
            List of artifacts
        """
        try:
            session_obj_id = ObjectId(session_id)
            user_obj_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session or user ID"
            )

        query = {
            "session_id": session_obj_id,
            "user_id": user_obj_id
        }

        if not include_deleted:
            query["deleted"] = False

        artifacts = await self.collection.find(query).sort("created_at", -1).to_list(length=100)

        return [self._to_artifact_schema(artifact) for artifact in artifacts]

    async def update_artifact(
        self,
        artifact_id: str,
        user_id: str,
        artifact_update: ArtifactUpdate
    ) -> Artifact:
        """
        Update an artifact

        Args:
            artifact_id: Artifact ID
            user_id: User ID
            artifact_update: Update data

        Returns:
            Updated artifact
        """
        try:
            artifact_obj_id = ObjectId(artifact_id)
            user_obj_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid artifact or user ID"
            )

        update_data = artifact_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        update_data["updated_at"] = datetime.now()

        result = await self.collection.update_one(
            {
                "_id": artifact_obj_id,
                "user_id": user_obj_id,
                "deleted": False
            },
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact not found"
            )

        return await self.get_artifact(artifact_id, user_id)

    async def delete_artifact(
        self,
        artifact_id: str,
        user_id: str,
        hard_delete: bool = False
    ) -> dict:
        """
        Delete an artifact (soft or hard delete)

        Args:
            artifact_id: Artifact ID
            user_id: User ID
            hard_delete: If True, permanently delete. If False, soft delete.

        Returns:
            Success message
        """
        try:
            artifact_obj_id = ObjectId(artifact_id)
            user_obj_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid artifact or user ID"
            )

        # Get artifact to check storage type
        artifact = await self.collection.find_one({
            "_id": artifact_obj_id,
            "user_id": user_obj_id,
            "deleted": False
        })

        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact not found"
            )

        if hard_delete:
            # Permanently delete from database
            result = await self.collection.delete_one({
                "_id": artifact_obj_id,
                "user_id": user_obj_id
            })
        else:
            # Soft delete
            result = await self.collection.update_one(
                {
                    "_id": artifact_obj_id,
                    "user_id": user_obj_id,
                    "deleted": False
                },
                {
                    "$set": {
                        "deleted": True,
                        "deleted_at": datetime.now()
                    }
                }
            )

        if result.matched_count == 0 and result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact not found"
            )

        # Delete files from object storage if applicable
        storage_type = artifact.get("metadata", {}).get("storage_type")
        if storage_type == "object":
            try:
                await delete_artifact_files(artifact_id)
                logger.info(f"Deleted object storage files for artifact {artifact_id}")
            except Exception as e:
                logger.error(f"Failed to delete object storage files: {e}")

        return {"message": "Artifact deleted successfully"}

    async def disable_session_artifacts(self, session_id: str) -> int:
        """
        Soft delete all artifacts for a session (cascade delete)

        Args:
            session_id: Chat session ID

        Returns:
            Number of artifacts disabled
        """
        try:
            session_obj_id = ObjectId(session_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID"
            )

        result = await self.collection.update_many(
            {
                "session_id": session_obj_id,
                "deleted": False
            },
            {
                "$set": {
                    "deleted": True,
                    "deleted_at": datetime.now()
                }
            }
        )

        logger.info(f"Disabled {result.modified_count} artifacts for session {session_id}")
        return result.modified_count

    def _to_artifact_schema(self, artifact_doc: dict) -> Artifact:
        """
        Convert MongoDB document to Artifact schema

        Args:
            artifact_doc: MongoDB document

        Returns:
            Artifact schema
        """
        artifact_doc["id"] = str(artifact_doc.pop("_id"))
        artifact_doc["session_id"] = str(artifact_doc["session_id"])
        artifact_doc["user_id"] = str(artifact_doc["user_id"])

        return Artifact(**artifact_doc)
