from fastapi import APIRouter, Depends, Request, HTTPException, status, UploadFile, File, BackgroundTasks, Response
from typing import List
from datetime import datetime
from bson import ObjectId
import zipfile
import io
from pathlib import Path
from app.schemas.artifacts import ArtifactCreate, ArtifactUpdate, ArtifactResponse, ArtifactListResponse, RepositoryContextCreate
from app.models.artifacts import ArtifactModel
from app.dependencies.auth import get_current_active_user
from app.schemas.users import User
from app.utils.repository import clone_and_extract_repository, validate_repository_url, get_repository_info
from app.utils.object_storage import (
    initialize_storage,
    save_repository_files,
    save_uploaded_file,
    get_repository_files,
    get_repository_file_content,
    get_uploaded_file,
    delete_artifact_files
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
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """Add repository context (compatibility endpoint for old API) - Clones and stores repository code"""
    logger.info(f"Received repository context request: {repo_data}")

    # Extract URL from various possible field names
    repo_url = repo_data.url or repo_data.source or repo_data.repo_url
    if not repo_url:
        logger.error("Repository URL is missing from request")
        raise HTTPException(status_code=400, detail="Repository URL is required")

    logger.info(f"Repository URL: {repo_url}")

    # Ensure URL has protocol
    if not repo_url.startswith('http://') and not repo_url.startswith('https://'):
        repo_url = f"https://{repo_url}"
        logger.info(f"Added https:// prefix to URL: {repo_url}")

    # Validate repository URL
    if not validate_repository_url(repo_url):
        logger.error(f"Invalid repository URL: {repo_url}")
        raise HTTPException(status_code=400, detail="Invalid repository URL")

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

    # Get repository info
    repo_info = get_repository_info(repo_url)
    repo_name = repo_data.name or repo_info['name'] or "Repository"

    logger.info(f"Cloning repository: {repo_name} from {repo_url}")

    # Clone and extract repository
    try:
        result = await clone_and_extract_repository(repo_url)

        if result['error']:
            logger.error(f"Failed to clone repository: {result['error']}")
            raise HTTPException(status_code=400, detail=f"Failed to clone repository: {result['error']}")

        if not result['files']:
            raise HTTPException(status_code=400, detail="No code files found in repository")

        logger.info(f"Successfully extracted {result['total_files']} files from repository")

        # Calculate total size
        total_size = sum(f['size'] for f in result['files'])

        # First, create artifact in database to get ID
        artifact_dict = {
            "session_id": session_obj_id,
            "user_id": ObjectId(current_user.id),
            "type": "repository",
            "name": repo_name,
            "source": repo_url,
            "files": None,  # Files stored in object storage, not MongoDB
            "content": None,
            "metadata": {
                "repo_info": repo_info,
                "total_files": result['total_files'],
                "host": repo_info['host'],
                "owner": repo_info['owner'],
                "storage_type": "object"
            },
            "size": total_size,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "deleted": False,
            "deleted_at": None
        }

        insert_result = await request.app.db.artifacts.insert_one(artifact_dict)
        artifact_id = str(insert_result.inserted_id)

        # Save files to object storage
        storage_result = await save_repository_files(artifact_id, result['files'])

        # Update artifact with storage path
        await request.app.db.artifacts.update_one(
            {"_id": insert_result.inserted_id},
            {"$set": {"metadata.storage_path": storage_result["storage_path"]}}
        )

        # Fetch created artifact
        created_artifact = await request.app.db.artifacts.find_one({"_id": insert_result.inserted_id})

        # Convert ObjectIds to strings and rename _id to id
        artifact_id = str(created_artifact.pop("_id"))
        created_artifact["id"] = artifact_id
        created_artifact["session_id"] = str(created_artifact["session_id"])
        created_artifact["user_id"] = str(created_artifact["user_id"])

        logger.info(f"Repository artifact created successfully: {artifact_id}")

        return ArtifactResponse(**created_artifact)

    except HTTPException:
        raise
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
    """Upload a file artifact (zip, pdf, doc, etc.)"""
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

    # Determine artifact type from file extension
    file_ext = Path(file.filename).suffix.lower()

    artifact_type = "file"
    if file_ext == ".zip":
        artifact_type = "zip"
    elif file_ext in [".pdf"]:
        artifact_type = "pdf"
    elif file_ext in [".doc", ".docx"]:
        artifact_type = "doc"
    elif file_ext in [".txt", ".md"]:
        artifact_type = "text"

    # Read file contents
    contents = await file.read()
    file_size = len(contents)

    # For PDF and binary files, save to object storage
    if artifact_type in ["pdf", "doc"]:
        # Create artifact document first
        artifact_dict = {
            "session_id": session_obj_id,
            "user_id": ObjectId(current_user.id),
            "type": artifact_type,
            "name": file.filename,
            "source": file.filename,
            "files": None,
            "content": None,
            "metadata": {
                "filename": file.filename,
                "content_type": file.content_type,
                "storage_type": "object"
            },
            "size": file_size,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "deleted": False,
            "deleted_at": None
        }

        insert_result = await request.app.db.artifacts.insert_one(artifact_dict)
        artifact_id = str(insert_result.inserted_id)

        # Save file to object storage
        storage_result = await save_uploaded_file(artifact_id, file.filename, contents)

        # Update artifact with storage path
        await request.app.db.artifacts.update_one(
            {"_id": insert_result.inserted_id},
            {"$set": {"metadata.storage_path": storage_result["storage_path"]}}
        )

        # Fetch created artifact
        created_artifact = await request.app.db.artifacts.find_one({"_id": insert_result.inserted_id})

        # Convert ObjectIds to strings and rename _id to id
        created_artifact["id"] = str(created_artifact.pop("_id"))
        created_artifact["session_id"] = str(created_artifact["session_id"])
        created_artifact["user_id"] = str(created_artifact["user_id"])

        return ArtifactResponse(**created_artifact)

    files_data = []
    content = None

    # Process based on type for ZIP and text files
    if artifact_type == "zip":
        # Extract code files from zip
        try:
            with zipfile.ZipFile(io.BytesIO(contents)) as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.is_dir():
                        continue

                    # Skip files larger than 1MB
                    if file_info.file_size > 1024 * 1024:
                        continue

                    # Get file extension
                    ext = Path(file_info.filename).suffix.lower()

                    # Only process code files
                    code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h',
                                     '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
                                     '.sql', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
                                     '.md', '.txt', '.sh', '.bash'}

                    if ext in code_extensions:
                        try:
                            file_content = zip_ref.read(file_info.filename).decode('utf-8', errors='ignore')
                            files_data.append({
                                "path": file_info.filename,
                                "content": file_content,
                                "size": file_info.file_size
                            })
                        except Exception as e:
                            logger.warning(f"Failed to read file {file_info.filename}: {e}")
                            continue

        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid zip file")

    elif artifact_type == "text":
        # Extract text content
        content = contents.decode('utf-8', errors='ignore')

    # Create artifact document
    artifact_dict = {
        "session_id": session_obj_id,
        "user_id": ObjectId(current_user.id),
        "type": artifact_type,
        "name": file.filename,
        "source": file.filename,
        "files": files_data if files_data else None,
        "content": content,
        "metadata": {
            "filename": file.filename,
            "content_type": file.content_type
        },
        "size": file_size,
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

    # Convert ObjectIds to strings and rename _id to id
    result = []
    for artifact in artifacts:
        artifact["id"] = str(artifact.pop("_id"))  # Rename _id to id
        artifact["session_id"] = str(artifact["session_id"])
        artifact["user_id"] = str(artifact["user_id"])
        result.append(artifact)

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

    # Convert ObjectIds to strings and rename _id to id
    artifact["id"] = str(artifact.pop("_id"))
    artifact["session_id"] = str(artifact["session_id"])
    artifact["user_id"] = str(artifact["user_id"])

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

    # Convert ObjectIds to strings and rename _id to id
    artifact["id"] = str(artifact.pop("_id"))
    artifact["session_id"] = str(artifact["session_id"])
    artifact["user_id"] = str(artifact["user_id"])

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

    # For object storage, get files from filesystem
    if storage_type == "object" and artifact_type == "repository":
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
            raise HTTPException(status_code=404, detail="Repository files not found")

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

    # For object storage
    if storage_type == "object" and artifact_type == "repository":
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
