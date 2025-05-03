from typing import List
import uuid

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from mako.codegen import mangle_mako_loop
from redis import Redis
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.core.errors import DataBaseException
from src.database import get_db, get_redis
from src.model.message import Message, MessageRead, MesageUpdate
from src.model.user import User
from src.services.message_service import updateMessage, deleteMessage
from src.services.user_service import get_current_user, get_current_user_ws
from src.websocket_manager.websocker_manger import manager

router = APIRouter(tags=["Message Management"], prefix="/message")


# Example JSON
# {
#     "type": "message",
#     "content": "hello",
#     "receiver_id": "b80746f2-c937-4087-b76b-03e010675a74"
# }
# {
#     "type": "message_seen",
#     "message_id": "uuid.UUID",
#     "receiver_id": "b80746f2-c937-4087-b76b-03e010675a74"
# }
@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        session: AsyncSession = Depends(get_db),
        redis_conn: Redis = Depends(get_redis),
):
    # 1) authenticate
    user = await get_current_user_ws(websocket, session)
    # 2) register connection
    await manager.connect(websocket, user.id, db=session,redis_conn=redis_conn)
    try:
        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                break

            if not any(k in data for k in ("type", "content", "receiver_id")):
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid payload – must include type, content, and receiver_id"
                })
                continue

            msg_type = data["type"]
            if msg_type == "message":
                receiver_uuid = uuid.UUID(data["receiver_id"])

                if user.id == receiver_uuid:
                    await websocket.send_json({
                        "type": "error",
                        "message": "You cannot send a message to yourself"
                    })
                    continue

                msg = Message(
                    content=data["content"],
                    sender_id=user.id,
                    receiver_id=receiver_uuid
                )
                session.add(msg)
                await session.commit()
                await session.refresh(msg)

                await manager.send_personal_message(
                    msg.content,
                    receiver_uuid,
                    user.id,
                    msg.id
                )
            elif msg_type == "message_seen":
                message_id = uuid.UUID(data["message_id"])
                await manager.make_message_read(message_id=message_id)
            elif msg_type == "active_typing":
                receiver_uuid = uuid.UUID(data["receiver_id"])
                typing_status = data["typing_status"]
                print(f"--------------hh----------- {typing_status}")
                sender_id = user.id
                await manager.post_active_typing(receiver_id = receiver_uuid,typing_status = typing_status,sender_id=sender_id)

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
        await websocket.send_json({
            "type": "error",
            "message": "Server error processing your message"
        })
        print(f"[ws error] {e!r}")

    finally:
        await manager.disconnect(user.id)
        print(f"User {user.id} disconnected.")


@router.get(
    "/chats/{receiver_id}",
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


@router.post(
    path="/update-message",
    response_model=Message
)
async def update_message(
        message_update: MesageUpdate,
        db: AsyncSession = Depends(get_db)
):
    try:
        msg = await updateMessage(
            message_id=update_message.id,
            update_message=message_update.content,
            db=db
        )
        return msg
    except SQLAlchemyError as e:
        raise DataBaseException(detail=str(e))


@router.delete(
    path="/delete-message",
    response_model=bool
)
async def delete_message(
        message_id: uuid.UUID,
        db: AsyncSession = Depends(get_db)
):
    try:
        return await deleteMessage(message_id=message_id, db=db)
    except SQLAlchemyError as e:
        raise DataBaseException(detail=str(e))
