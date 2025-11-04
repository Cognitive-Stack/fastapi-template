from fastapi import APIRouter, Depends, Request, HTTPException, status, UploadFile, File, Response
from typing import List
from datetime import datetime
from bson import ObjectId
from pathlib import Path

from app.schemas.artifacts import ArtifactCreate, ArtifactUpdate, ArtifactResponse, ArtifactListResponse, RepositoryContextCreate
from app.dependencies.auth import get_current_active_user
from app.schemas.users import User
from app.utils.object_storage import (
    initialize_storage,
    get_repository_files,
    get_repository_file_content,
    get_uploaded_file,
    delete_artifact_files
)
from app.utils.artifact_helpers import (
    handle_repository_upload,
    handle_zip_upload,
    handle_document_upload,
    handle_text_upload,
    convert_artifact_to_response
)
from loguru import logger

# Initialize storage on module load
initialize_storage()

router = APIRouter()


@router.post("/sessions/{session_id}/context/repository", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def add_repository_context(
    session_id: str,
    repo_data: RepositoryContextCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Add repository context (compatibility endpoint) - Clones and stores repository code"""
    logger.info(f"Received repository context request: {repo_data}")

    # Extract URL from various possible field names
    repo_url = repo_data.url or repo_data.source or repo_data.repo_url
    if not repo_url:
        logger.error("Repository URL is missing from request")
        raise HTTPException(status_code=400, detail="Repository URL is required")

    # Ensure URL has protocol
    if not repo_url.startswith('http://') and not repo_url.startswith('https://'):
        repo_url = f"https://{repo_url}"
        logger.info(f"Added https:// prefix to URL: {repo_url}")

    # Verify session exists and belongs to user
    try:
        session_obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    session = await request.app.db.chat_sessions.find_one({
        "_id": session_obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Handle repository upload using helper function
    try:
        artifact = await handle_repository_upload(
            db=request.app.db,
            session_id=session_id,
            user_id=current_user.id,
            repo_url=repo_url,
            repo_name=repo_data.name
        )

        # Convert to response format
        artifact = convert_artifact_to_response(artifact)
        return ArtifactResponse(**artifact)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing repository: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process repository: {str(e)}")


@router.post("/sessions/{session_id}/artifacts", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    session_id: str,
    artifact_data: ArtifactCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new artifact (e.g., repository URL)"""
    try:
        session_obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # Verify session exists and belongs to user
    session = await request.app.db.chat_sessions.find_one({
        "_id": session_obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate URL if type is repository
    if artifact_data.type == "repository" and artifact_data.source:
        if not (artifact_data.source.startswith('http://') or artifact_data.source.startswith('https://')):
            logger.error(f"Invalid repository URL format: {artifact_data.source}")
            raise HTTPException(status_code=400, detail=f"Invalid repository URL. Must start with http:// or https://. Received: {artifact_data.source}")

    # Create artifact document
    artifact_dict = {
        "session_id": session_obj_id,
        "user_id": ObjectId(current_user.id),
        "type": artifact_data.type,
        "name": artifact_data.name,
        "source": artifact_data.source,
        "files": [] if artifact_data.type in ["repository", "zip"] else None,
        "content": None,
        "metadata": {},
        "size": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "deleted": False,
        "deleted_at": None
    }

    result = await request.app.db.artifacts.insert_one(artifact_dict)

    # Fetch created artifact
    created_artifact = await request.app.db.artifacts.find_one({"_id": result.inserted_id})

    # Convert ObjectIds to strings and rename _id to id
    created_artifact["id"] = str(created_artifact.pop("_id"))
    created_artifact["session_id"] = str(created_artifact["session_id"])
    created_artifact["user_id"] = str(created_artifact["user_id"])

    return ArtifactResponse(**created_artifact)


@router.post("/sessions/{session_id}/artifacts/upload", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def upload_artifact(
    session_id: str,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file artifact (zip, pdf, doc, text)"""
    # Verify session exists and belongs to user
    try:
        session_obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    session = await request.app.db.chat_sessions.find_one({
        "_id": session_obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Determine artifact type from file extension
    file_ext = Path(file.filename).suffix.lower()
    artifact_type = "file"

    if file_ext == ".zip":
        artifact_type = "zip"
    elif file_ext == ".pdf":
        artifact_type = "pdf"
    elif file_ext in [".doc", ".docx"]:
        artifact_type = "doc"
    elif file_ext in [".txt", ".md"]:
        artifact_type = "text"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")

    # Read file contents
    contents = await file.read()

    # Handle different artifact types using helper functions
    try:
        if artifact_type == "zip":
            artifact = await handle_zip_upload(
                db=request.app.db,
                session_id=session_id,
                user_id=current_user.id,
                filename=file.filename,
                content_type=file.content_type,
                contents=contents
            )
        elif artifact_type in ["pdf", "doc"]:
            artifact = await handle_document_upload(
                db=request.app.db,
                session_id=session_id,
                user_id=current_user.id,
                filename=file.filename,
                content_type=file.content_type,
                contents=contents,
                artifact_type=artifact_type
            )
        elif artifact_type == "text":
            artifact = await handle_text_upload(
                db=request.app.db,
                session_id=session_id,
                user_id=current_user.id,
                filename=file.filename,
                content_type=file.content_type,
                contents=contents
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported artifact type: {artifact_type}")

        # Convert to response format
        artifact = convert_artifact_to_response(artifact)
        return ArtifactResponse(**artifact)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading artifact: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload artifact: {str(e)}")


@router.get("/sessions/{session_id}/artifacts", response_model=List[ArtifactResponse])
async def get_artifacts(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Get all artifacts for a session"""
    try:
        session_obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # Verify session belongs to user
    session = await request.app.db.chat_sessions.find_one({
        "_id": session_obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get artifacts
    artifacts = await request.app.db.artifacts.find({
        "session_id": session_obj_id,
        "deleted": False
    }).sort("created_at", -1).to_list(length=100)

    # Convert ObjectIds to strings for all artifacts
    result = [convert_artifact_to_response(artifact.copy()) for artifact in artifacts]

    return [ArtifactResponse(**artifact) for artifact in result]


@router.get("/sessions/{session_id}/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    session_id: str,
    artifact_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific artifact"""
    try:
        session_obj_id = ObjectId(session_id)
        artifact_obj_id = ObjectId(artifact_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    # Verify session belongs to user
    session = await request.app.db.chat_sessions.find_one({
        "_id": session_obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get artifact
    artifact = await request.app.db.artifacts.find_one({
        "_id": artifact_obj_id,
        "session_id": session_obj_id,
        "deleted": False
    })

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Convert to response format
    artifact = convert_artifact_to_response(artifact)
    return ArtifactResponse(**artifact)


@router.put("/sessions/{session_id}/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def update_artifact(
    session_id: str,
    artifact_id: str,
    artifact_update: ArtifactUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Update an artifact"""
    try:
        session_obj_id = ObjectId(session_id)
        artifact_obj_id = ObjectId(artifact_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    update_data = artifact_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.now()

    result = await request.app.db.artifacts.update_one(
        {
            "_id": artifact_obj_id,
            "session_id": session_obj_id,
            "user_id": ObjectId(current_user.id),
            "deleted": False
        },
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Fetch updated artifact
    artifact = await request.app.db.artifacts.find_one({"_id": artifact_obj_id})

    # Convert to response format
    artifact = convert_artifact_to_response(artifact)
    return ArtifactResponse(**artifact)


@router.delete("/sessions/{session_id}/artifacts/{artifact_id}")
async def delete_artifact(
    session_id: str,
    artifact_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Delete an artifact (soft delete + remove files from storage)"""
    try:
        session_obj_id = ObjectId(session_id)
        artifact_obj_id = ObjectId(artifact_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    # Get artifact to check storage type
    artifact = await request.app.db.artifacts.find_one({
        "_id": artifact_obj_id,
        "session_id": session_obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Soft delete in database
    result = await request.app.db.artifacts.update_one(
        {
            "_id": artifact_obj_id,
            "session_id": session_obj_id,
            "user_id": ObjectId(current_user.id),
            "deleted": False
        },
        {
            "$set": {
                "deleted": True,
                "deleted_at": datetime.now()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Delete files from object storage if applicable
    storage_type = artifact.get('metadata', {}).get('storage_type')
    if storage_type == "object":
        try:
            await delete_artifact_files(artifact_id)
            logger.info(f"Deleted object storage files for artifact {artifact_id}")
        except Exception as e:
            logger.error(f"Failed to delete object storage files: {e}")
            # Continue even if file deletion fails

    return {"message": "Artifact deleted successfully"}


@router.get("/sessions/{session_id}/artifacts/{artifact_id}/files")
async def get_artifact_files(
    session_id: str,
    artifact_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    limit: int = 100,
    offset: int = 0
):
    """Get files from an artifact with pagination"""
    try:
        session_obj_id = ObjectId(session_id)
        artifact_obj_id = ObjectId(artifact_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    # Verify session belongs to user
    session = await request.app.db.chat_sessions.find_one({
        "_id": session_obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get artifact metadata
    artifact = await request.app.db.artifacts.find_one({
        "_id": artifact_obj_id,
        "session_id": session_obj_id,
        "deleted": False
    })

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifact_type = artifact.get('type')
    storage_type = artifact.get('metadata', {}).get('storage_type')

    # For object storage, get files from filesystem (works for both repository and zip)
    if storage_type == "object" and artifact_type in ["repository", "zip"]:
        try:
            result = await get_repository_files(artifact_id, limit, offset)
            return {
                "artifact_id": artifact_id,
                "artifact_name": artifact.get('name'),
                "artifact_type": artifact_type,
                "total_files": result['total_files'],
                "offset": result['offset'],
                "limit": result['limit'],
                "files": result['files']
            }
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Artifact files not found")

    # Legacy: files stored in MongoDB
    files = artifact.get('files', [])
    total_files = len(files) if files else 0

    # Apply pagination
    paginated_files = files[offset:offset + limit] if files else []

    return {
        "artifact_id": str(artifact_obj_id),
        "artifact_name": artifact.get('name'),
        "artifact_type": artifact_type,
        "total_files": total_files,
        "offset": offset,
        "limit": limit,
        "files": paginated_files
    }


@router.get("/sessions/{session_id}/artifacts/{artifact_id}/files/{file_path:path}")
async def get_artifact_file_content(
    session_id: str,
    artifact_id: str,
    file_path: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Get specific file content from an artifact"""
    try:
        session_obj_id = ObjectId(session_id)
        artifact_obj_id = ObjectId(artifact_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    # Get artifact
    artifact = await request.app.db.artifacts.find_one({
        "_id": artifact_obj_id,
        "session_id": session_obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifact_type = artifact.get('type')
    storage_type = artifact.get('metadata', {}).get('storage_type')

    # For object storage (works for both repository and zip)
    if storage_type == "object" and artifact_type in ["repository", "zip"]:
        try:
            result = await get_repository_file_content(artifact_id, file_path)
            return {
                "path": result['path'],
                "content": result['content'],
                "size": result['size']
            }
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")

    # Legacy: files in MongoDB
    files = artifact.get('files', [])
    file_content = None

    if files:
        for f in files:
            if f['path'] == file_path:
                file_content = f
                break

    if not file_content:
        raise HTTPException(status_code=404, detail="File not found in artifact")

    return {
        "path": file_content['path'],
        "content": file_content['content'],
        "size": file_content['size']
    }


@router.get("/sessions/{session_id}/artifacts/{artifact_id}/download")
async def download_artifact(
    session_id: str,
    artifact_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Download an uploaded file (PDF, DOC, etc.)"""
    try:
        session_obj_id = ObjectId(session_id)
        artifact_obj_id = ObjectId(artifact_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    # Get artifact
    artifact = await request.app.db.artifacts.find_one({
        "_id": artifact_obj_id,
        "session_id": session_obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifact_type = artifact.get('type')
    storage_type = artifact.get('metadata', {}).get('storage_type')

    # For uploaded files (PDF, DOC, etc.)
    if storage_type == "object" and artifact_type in ["pdf", "doc"]:
        try:
            result = await get_uploaded_file(artifact_id)

            # Determine content type
            content_type = artifact.get('metadata', {}).get('content_type', 'application/octet-stream')

            return Response(
                content=result['content'],
                media_type=content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={result['filename']}"
                }
            )
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")

    raise HTTPException(status_code=400, detail="Artifact type not supported for download")
