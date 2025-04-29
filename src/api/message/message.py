from typing import List
import uuid

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_db
from src.model.message import Message, MessageRead
from src.model.user import User
from src.services.user_service import get_current_user, get_current_user_ws
from src.websocket_manager.websocker_manger import manager

router = APIRouter(tags=["Message Management"], prefix="/message")

# Example JSON
# {
#     "type": "message",
#     "content": "hello",
#     "receiver_id": "b80746f2-c937-4087-b76b-03e010675a74"
# }

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session: AsyncSession = Depends(get_db),
):
    # 1) authenticate
    user = await get_current_user_ws(websocket, session)
    # 2) register connection
    await manager.connect(websocket, user.id)

    try:
        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                # client closed the socket
                break

            # 3) validate payload has all required fields
            if not all(k in data for k in ("type", "content", "receiver_id")):
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid payload – must include type, content, and receiver_id"
                })
                continue

            # 4) dispatch by message type
            msg_type = data["type"]
            if msg_type == "message":
                receiver_uuid = uuid.UUID(data["receiver_id"])

                if user.id == receiver_uuid:
                    await websocket.send_json({
                        "type": "error",
                        "message": "You cannot send a message to yourself"
                    })
                    continue

                # persist
                msg = Message(
                    content=data["content"],
                    sender_id=user.id,
                    receiver_id=receiver_uuid
                )
                session.add(msg)
                await session.commit()
                await session.refresh(msg)

                # send
                await manager.send_personal_message(
                    msg.content,
                    receiver_uuid,
                    user.id
                )

            elif msg_type == "image":
                # handle image...
                await websocket.send_json({"type": "ack", "message": "image received"})

            elif msg_type == "video":
                # handle video...
                await websocket.send_json({"type": "ack", "message": "video received"})

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })

    except Exception as e:
        # unexpected server error
        await websocket.send_json({
            "type": "error",
            "message": "Server error processing your message"
        })
        print(f"[ws error] {e!r}")

    finally:
        # cleanup on disconnect
        await manager.disconnect(user.id)
        print(f"User {user.id} disconnected.")


@router.websocket("/hello")
async def hello(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {text}")
    except WebSocketDisconnect:
        print("Hello socket disconnected.")


@router.get(
    "/messages/{receiver_id}",
    response_model=List[MessageRead],
)
async def get_past_messages(
    receiver_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[MessageRead]:
    stmt = (
        select(Message)
        .options(
            selectinload(Message.sender),
            selectinload(Message.receiver),
        )
        .where(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == current_user.id))
        )
        .order_by(Message.timestamp)
    )

    result = await session.execute(stmt)
    return result.scalars().all()
