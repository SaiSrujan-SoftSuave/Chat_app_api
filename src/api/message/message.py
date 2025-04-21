from typing import List
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_db
from src.model.message import Message, MessageRead
from src.model.user import User
from src.services.user_service import get_current_user
from src.websocket_manager.websocker_manger import manager

router = APIRouter(tags=["Message Management"], prefix="/message")


# routes/chat.py
@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        user=Depends(get_current_user),
        session: AsyncSession = Depends(get_db)
):
    await manager.connect(websocket, user.id)

    try:
        while True:
            data = await websocket.receive_json()

            # Save message to database
            message = Message(
                content=data['content'],
                sender_id=user.id,
                receiver_id=data['receiver_id']
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)

            # Send through WebSocket
            await manager.send_personal_message(
                message.content,
                data['receiver_id']
            )

    except WebSocketDisconnect:
        manager.disconnect(user.id)


router = APIRouter(tags=["Message Management"], prefix="/message")


@router.get("/messages/{receiver_id}", response_model=List[MessageRead])
async def get_past_messages(
        receiver_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db),
) -> List[Message]:
    # A plain SQLModel select (no .options)
    stmt = (
        select(Message)
        .where(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == current_user.id))
        )
        .order_by(Message.timestamp)
    )

    # this `exec()` call is happy with a bare select(...)
    result = await session.exec(stmt)
    messages = result.all()  # → Sequence[Message]

    # if you still want a list for your annotation:
    return list(messages)
