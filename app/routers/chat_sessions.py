from fastapi import APIRouter, Depends, Request, HTTPException, status
from typing import List
from datetime import datetime
from bson import ObjectId
from app.schemas.chat_sessions import ChatSessionCreate, ChatSessionUpdate, ChatSessionResponse
from app.schemas.messages import MessageCreate, MessageResponse
from app.models.chat_sessions import ChatSession
from app.models.messages import Message
from app.dependencies.auth import get_current_active_user
from app.schemas.users import User
from app.controllers.artifacts import ArtifactController
from loguru import logger

router = APIRouter()


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: ChatSessionCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new chat session"""
    from bson import ObjectId

    # Create session document directly without using model
    session_dict = {
        "user_id": ObjectId(current_user.id),
        "title": session_data.title or "New Chat",
        "message_count": 0,
        "last_message_at": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "deleted": False,
        "deleted_at": None
    }

    result = await request.app.db.chat_sessions.insert_one(session_dict)

    # Fetch the created session
    created_session = await request.app.db.chat_sessions.find_one({"_id": result.inserted_id})

    # Convert ObjectIds to strings for the response
    created_session["_id"] = str(created_session["_id"])
    created_session["user_id"] = str(created_session["user_id"])

    return ChatSessionResponse(**created_session)


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    limit: int = 50
):
    """Get all chat sessions for the current user"""
    sessions = await request.app.db.chat_sessions.find(
        {"user_id": ObjectId(current_user.id), "deleted": False}
    ).sort("updated_at", -1).limit(limit).to_list(length=limit)

    # Convert ObjectIds to strings
    for session in sessions:
        session["_id"] = str(session["_id"])
        session["user_id"] = str(session["user_id"])

    return [ChatSessionResponse(**session) for session in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific chat session"""
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    session = await request.app.db.chat_sessions.find_one({
        "_id": obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Convert ObjectIds to strings
    session["_id"] = str(session["_id"])
    session["user_id"] = str(session["user_id"])

    return ChatSessionResponse(**session)


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: str,
    session_update: ChatSessionUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Update a chat session (e.g., rename)"""
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    update_data = session_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.now()

    result = await request.app.db.chat_sessions.update_one(
        {"_id": obj_id, "user_id": ObjectId(current_user.id), "deleted": False},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    session = await request.app.db.chat_sessions.find_one({"_id": obj_id})

    # Convert ObjectIds to strings
    session["_id"] = str(session["_id"])
    session["user_id"] = str(session["user_id"])

    return ChatSessionResponse(**session)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a chat session (soft delete) and disable all related artifacts"""
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # Soft delete the session
    result = await request.app.db.chat_sessions.update_one(
        {"_id": obj_id, "user_id": ObjectId(current_user.id), "deleted": False},
        {"$set": {"deleted": True, "deleted_at": datetime.now()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    # Cascade soft-delete: Disable all artifacts for this session
    try:
        artifact_controller = ArtifactController(request.app.db)
        artifacts_disabled = await artifact_controller.disable_session_artifacts(session_id)
        logger.info(f"Session {session_id} deleted. Disabled {artifacts_disabled} artifacts.")
    except Exception as e:
        logger.error(f"Failed to disable artifacts for session {session_id}: {e}")
        # Continue even if artifact deletion fails

    return {
        "message": "Session deleted successfully",
        "artifacts_disabled": artifacts_disabled if 'artifacts_disabled' in locals() else 0
    }


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    session_id: str,
    message_data: MessageCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Send a message in a chat session"""
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # Verify session exists and belongs to user
    session = await request.app.db.chat_sessions.find_one({
        "_id": obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create message document directly without using model
    message_dict = {
        "session_id": obj_id,
        "user_id": ObjectId(current_user.id),
        "content": message_data.content,
        "role": "user",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "deleted": False,
        "deleted_at": None
    }

    result = await request.app.db.messages.insert_one(message_dict)

    # Update session
    await request.app.db.chat_sessions.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "last_message_at": datetime.now(),
                "updated_at": datetime.now()
            },
            "$inc": {"message_count": 1}
        }
    )

    # Fetch the created message
    created_message = await request.app.db.messages.find_one({"_id": result.inserted_id})

    # Convert ObjectIds to strings for the response
    created_message["_id"] = str(created_message["_id"])
    created_message["session_id"] = str(created_message["session_id"])
    created_message["user_id"] = str(created_message["user_id"])

    return MessageResponse(**created_message)


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    limit: int = 100
):
    """Get all messages in a chat session"""
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # Verify session belongs to user
    session = await request.app.db.chat_sessions.find_one({
        "_id": obj_id,
        "user_id": ObjectId(current_user.id),
        "deleted": False
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get messages
    messages = await request.app.db.messages.find(
        {"session_id": obj_id, "deleted": False}
    ).sort("created_at", 1).limit(limit).to_list(length=limit)

    # Convert ObjectIds to strings
    for msg in messages:
        msg["_id"] = str(msg["_id"])
        msg["session_id"] = str(msg["session_id"])
        msg["user_id"] = str(msg["user_id"])

    return [MessageResponse(**msg) for msg in messages]


@router.delete("/sessions/{session_id}/messages/{message_id}")
async def delete_message(
    session_id: str,
    message_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a message (soft delete)"""
    try:
        session_obj_id = ObjectId(session_id)
        message_obj_id = ObjectId(message_id)
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

    # Verify message exists in this session
    message = await request.app.db.messages.find_one({
        "_id": message_obj_id,
        "session_id": session_obj_id
    })

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Soft delete
    await request.app.db.messages.update_one(
        {"_id": message_obj_id},
        {"$set": {"deleted": True, "deleted_at": datetime.now()}}
    )

    # Decrement message count
    await request.app.db.chat_sessions.update_one(
        {"_id": session_obj_id},
        {"$inc": {"message_count": -1}}
    )

    return {"message": "Message deleted successfully"}
