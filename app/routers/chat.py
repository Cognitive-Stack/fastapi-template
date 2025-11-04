from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request, Query, HTTPException, status
from typing import List, Dict
from datetime import datetime
from app.schemas.messages import MessageCreate, MessageResponse
from app.models.messages import Message
from app.dependencies.auth import get_current_active_user
from app.schemas.users import User
from loguru import logger

router = APIRouter()

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)
        logger.info(f"Client connected to room: {room}. Total connections: {len(self.active_connections[room])}")

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.active_connections:
            self.active_connections[room].remove(websocket)
            logger.info(f"Client disconnected from room: {room}. Total connections: {len(self.active_connections[room])}")
            if not self.active_connections[room]:
                del self.active_connections[room]

    async def broadcast(self, message: dict, room: str):
        if room in self.active_connections:
            disconnected = []
            for connection in self.active_connections[room]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    disconnected.append(connection)

            # Remove disconnected connections
            for conn in disconnected:
                self.active_connections[room].remove(conn)

manager = ConnectionManager()


@router.websocket("/ws/{room}")
async def websocket_endpoint(
    websocket: WebSocket,
    room: str,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time chat"""
    try:
        # Validate token and get user
        from app.controllers.users import UserController

        controller = UserController(websocket.app.db)

        # Decode the token
        try:
            token_data = controller.decode_access_token(token)
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Get user by email from token
        user = await controller.get_user_by_email(token_data.email)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await manager.connect(websocket, room)

        # Send join notification
        await manager.broadcast({
            "type": "system",
            "content": f"{user.username} joined the room",
            "room": room,
            "timestamp": datetime.now().isoformat()
        }, room)

        try:
            while True:
                data = await websocket.receive_json()

                # Save message to database
                message = Message(
                    user_id=user.id,
                    username=user.username,
                    content=data.get("content", ""),
                    room=room
                )

                result = await websocket.app.db.messages.insert_one(message.model_dump(by_alias=True))
                message.id = result.inserted_id

                # Broadcast message to all clients in the room
                await manager.broadcast({
                    "type": "message",
                    "_id": str(message.id),
                    "user_id": str(user.id),
                    "username": user.username,
                    "content": message.content,
                    "room": room,
                    "created_at": message.created_at.isoformat()
                }, room)

        except WebSocketDisconnect:
            manager.disconnect(websocket, room)
            await manager.broadcast({
                "type": "system",
                "content": f"{user.username} left the room",
                "room": room,
                "timestamp": datetime.now().isoformat()
            }, room)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.get("/messages/{room}", response_model=List[MessageResponse])
async def get_messages(
    room: str,
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """Get chat message history for a room"""
    messages = await request.app.db.messages.find(
        {"room": room, "deleted": False}
    ).sort("created_at", -1).limit(limit).to_list(length=limit)

    # Reverse to get chronological order
    messages.reverse()

    return [MessageResponse(**msg) for msg in messages]


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a message (soft delete)"""
    from bson import ObjectId

    # Get the message
    message = await request.app.db.messages.find_one({"_id": ObjectId(message_id)})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Check if user owns the message
    if str(message["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this message")

    # Soft delete
    await request.app.db.messages.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": {"deleted": True, "deleted_at": datetime.now()}}
    )

    return {"message": "Message deleted successfully"}
