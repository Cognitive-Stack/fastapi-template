"""
Helper functions for artifact creation and management
"""
import os
import shutil
import zipfile
import io
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from loguru import logger

from app.utils.repository import clone_and_extract_repository, validate_repository_url, get_repository_info
from app.utils.object_storage import save_repository_files, save_uploaded_file


# Code file extensions to extract
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
    '.sql', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
    '.md', '.txt', '.sh', '.bash', '.r', '.m', '.vue', '.svelte',
    '.dart', '.lua', '.pl', '.pm', '.gradle', '.proto', '.thrift'
}


async def create_base_artifact(
    db: AsyncIOMotorDatabase,
    session_id: str,
    user_id: str,
    artifact_type: str,
    name: str,
    source: str,
    size: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a base artifact document in database

    Args:
        db: Database connection
        session_id: Chat session ID
        user_id: User ID
        artifact_type: Type of artifact (repository, zip, pdf, doc, text)
        name: Display name
        source: Source URL or filename
        size: File size in bytes (optional)
        metadata: Additional metadata (optional)

    Returns:
        Artifact ID as string
    """
    session_obj_id = ObjectId(session_id)
    user_obj_id = ObjectId(user_id)

    artifact_dict = {
        "session_id": session_obj_id,
        "user_id": user_obj_id,
        "type": artifact_type,
        "name": name,
        "source": source,
        "files": None,
        "content": None,
        "metadata": metadata or {},
        "size": size,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "deleted": False,
        "deleted_at": None
    }

    result = await db.artifacts.insert_one(artifact_dict)
    artifact_id = str(result.inserted_id)

    logger.info(f"Created base artifact {artifact_id} of type {artifact_type}")
    return artifact_id


async def update_artifact_status(
    db: AsyncIOMotorDatabase,
    artifact_id: str,
    status: str,
    **additional_fields
) -> None:
    """
    Update artifact status and additional fields

    Args:
        db: Database connection
        artifact_id: Artifact ID
        status: Status to set (cloning, extracting, completed, failed)
        **additional_fields: Additional fields to update
    """
    update_data = {"metadata.status": status}
    update_data.update(additional_fields)

    await db.artifacts.update_one(
        {"_id": ObjectId(artifact_id)},
        {"$set": update_data}
    )

    logger.debug(f"Updated artifact {artifact_id} status to {status}")


async def handle_repository_upload(
    db: AsyncIOMotorDatabase,
    session_id: str,
    user_id: str,
    repo_url: str,
    repo_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle repository cloning and artifact creation

    Args:
        db: Database connection
        session_id: Chat session ID
        user_id: User ID
        repo_url: Repository URL
        repo_name: Optional repository name

    Returns:
        Created artifact document
    """
    # Validate repository URL
    if not validate_repository_url(repo_url):
        raise ValueError(f"Invalid repository URL: {repo_url}")

    # Get repository info
    repo_info = get_repository_info(repo_url)
    name = repo_name or repo_info['name'] or "Repository"

    # Create artifact with initial status
    artifact_id = await create_base_artifact(
        db=db,
        session_id=session_id,
        user_id=user_id,
        artifact_type="repository",
        name=name,
        source=repo_url,
        metadata={
            "repo_info": repo_info,
            "host": repo_info['host'],
            "owner": repo_info['owner'],
            "storage_type": "object",
            "status": "cloning"
        }
    )

    temp_dir = None
    try:
        # Clone repository with streaming mode
        logger.info(f"Cloning repository {name} from {repo_url}")
        result = await clone_and_extract_repository(repo_url, artifact_id=artifact_id)

        if result['error']:
            logger.error(f"Failed to clone repository: {result['error']}")
            await update_artifact_status(
                db, artifact_id, "failed",
                **{"metadata.error": result['error']}
            )
            raise ValueError(f"Failed to clone repository: {result['error']}")

        if not result['files']:
            await update_artifact_status(
                db, artifact_id, "failed",
                **{"metadata.error": "No code files found"}
            )
            raise ValueError("No code files found in repository")

        logger.info(f"Extracted {result['total_files']} files from repository")

        # Calculate total size
        total_size = sum(f['size'] for f in result['files'])

        # Save files to object storage
        storage_result = await save_repository_files(artifact_id, result['files'])
        temp_dir = result.get('temp_dir')

        # Update artifact with completion status
        await update_artifact_status(
            db, artifact_id, "completed",
            size=total_size,
            **{
                "metadata.total_files": result['total_files'],
                "metadata.storage_path": storage_result["storage_path"]
            }
        )

        logger.info(f"Repository artifact {artifact_id} created successfully")

    except Exception as e:
        logger.error(f"Error processing repository: {e}")
        await update_artifact_status(
            db, artifact_id, "failed",
            **{"metadata.error": str(e)}
        )
        raise
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup temp directory: {cleanup_error}")

    # Fetch and return created artifact
    artifact = await db.artifacts.find_one({"_id": ObjectId(artifact_id)})
    return artifact


async def handle_zip_upload(
    db: AsyncIOMotorDatabase,
    session_id: str,
    user_id: str,
    filename: str,
    content_type: str,
    contents: bytes
) -> Dict[str, Any]:
    """
    Handle ZIP file upload and extraction

    Args:
        db: Database connection
        session_id: Chat session ID
        user_id: User ID
        filename: Original filename
        content_type: MIME content type
        contents: File contents as bytes

    Returns:
        Created artifact document
    """
    file_size = len(contents)

    # Create artifact with initial status
    artifact_id = await create_base_artifact(
        db=db,
        session_id=session_id,
        user_id=user_id,
        artifact_type="zip",
        name=filename,
        source=filename,
        size=file_size,
        metadata={
            "filename": filename,
            "content_type": content_type,
            "storage_type": "object",
            "status": "extracting"
        }
    )

    try:
        # Extract code files from zip
        files_data = []
        with zipfile.ZipFile(io.BytesIO(contents)) as zip_ref:
            for file_info in zip_ref.filelist:
                if file_info.is_dir():
                    continue

                # Skip files larger than 5MB
                if file_info.file_size > 5 * 1024 * 1024:
                    logger.debug(f"Skipping large file: {file_info.filename}")
                    continue

                # Get file extension
                ext = Path(file_info.filename).suffix.lower()

                # Only process code files
                if ext in CODE_EXTENSIONS:
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

        logger.info(f"Extracted {len(files_data)} code files from ZIP")

        # Save files to object storage
        if files_data:
            storage_result = await save_repository_files(artifact_id, files_data)
            await update_artifact_status(
                db, artifact_id, "completed",
                **{
                    "metadata.total_files": len(files_data),
                    "metadata.storage_path": storage_result["storage_path"]
                }
            )
        else:
            # No code files found
            await update_artifact_status(
                db, artifact_id, "completed",
                **{"metadata.total_files": 0}
            )

        logger.info(f"ZIP artifact {artifact_id} created successfully")

    except zipfile.BadZipFile:
        logger.error("Invalid zip file")
        await update_artifact_status(
            db, artifact_id, "failed",
            **{"metadata.error": "Invalid zip file"}
        )
        raise ValueError("Invalid zip file")
    except Exception as e:
        logger.error(f"Error processing ZIP file: {e}")
        await update_artifact_status(
            db, artifact_id, "failed",
            **{"metadata.error": str(e)}
        )
        raise

    # Fetch and return created artifact
    artifact = await db.artifacts.find_one({"_id": ObjectId(artifact_id)})
    return artifact


async def handle_document_upload(
    db: AsyncIOMotorDatabase,
    session_id: str,
    user_id: str,
    filename: str,
    content_type: str,
    contents: bytes,
    artifact_type: str  # pdf, doc, etc.
) -> Dict[str, Any]:
    """
    Handle document file upload (PDF, DOC, etc.)

    Args:
        db: Database connection
        session_id: Chat session ID
        user_id: User ID
        filename: Original filename
        content_type: MIME content type
        contents: File contents as bytes
        artifact_type: Type of document (pdf, doc)

    Returns:
        Created artifact document
    """
    file_size = len(contents)

    # Create artifact
    artifact_id = await create_base_artifact(
        db=db,
        session_id=session_id,
        user_id=user_id,
        artifact_type=artifact_type,
        name=filename,
        source=filename,
        size=file_size,
        metadata={
            "filename": filename,
            "content_type": content_type,
            "storage_type": "object"
        }
    )

    try:
        # Save file to object storage
        storage_result = await save_uploaded_file(artifact_id, filename, contents)

        # Update artifact with storage path
        await db.artifacts.update_one(
            {"_id": ObjectId(artifact_id)},
            {"$set": {"metadata.storage_path": storage_result["storage_path"]}}
        )

        logger.info(f"Document artifact {artifact_id} created successfully")

    except Exception as e:
        logger.error(f"Error saving document: {e}")
        raise

    # Fetch and return created artifact
    artifact = await db.artifacts.find_one({"_id": ObjectId(artifact_id)})
    return artifact


async def handle_text_upload(
    db: AsyncIOMotorDatabase,
    session_id: str,
    user_id: str,
    filename: str,
    content_type: str,
    contents: bytes
) -> Dict[str, Any]:
    """
    Handle text file upload (stored in MongoDB)

    Args:
        db: Database connection
        session_id: Chat session ID
        user_id: User ID
        filename: Original filename
        content_type: MIME content type
        contents: File contents as bytes

    Returns:
        Created artifact document
    """
    file_size = len(contents)
    content = contents.decode('utf-8', errors='ignore')

    session_obj_id = ObjectId(session_id)
    user_obj_id = ObjectId(user_id)

    # Create artifact with content stored in MongoDB
    artifact_dict = {
        "session_id": session_obj_id,
        "user_id": user_obj_id,
        "type": "text",
        "name": filename,
        "source": filename,
        "files": None,
        "content": content,  # Store content in MongoDB for small text files
        "metadata": {
            "filename": filename,
            "content_type": content_type
        },
        "size": file_size,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "deleted": False,
        "deleted_at": None
    }

    result = await db.artifacts.insert_one(artifact_dict)

    logger.info(f"Text artifact {result.inserted_id} created successfully")

    # Fetch and return created artifact
    artifact = await db.artifacts.find_one({"_id": result.inserted_id})
    return artifact


def convert_artifact_to_response(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB artifact document to response format

    Args:
        artifact: MongoDB document

    Returns:
        Artifact dict with id field instead of _id
    """
    artifact["id"] = str(artifact.pop("_id"))
    artifact["session_id"] = str(artifact["session_id"])
    artifact["user_id"] = str(artifact["user_id"])
    return artifact
