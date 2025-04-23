from typing import List
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, WebSocketException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_db
from src.model.message import Message, MessageRead
from src.model.user import User
from src.services.user_service import get_current_user, get_current_user_ws
from src.websocket_manager.websocker_manger import manager

router = APIRouter(tags=["Message Management"], prefix="/message")


@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        session: AsyncSession = Depends(get_db)
):
    try:
        # Get the current user based on the WebSocket request
        user = await get_current_user_ws(websocket, session)
        # Add user to the connection manager
        await manager.connect(websocket, user.id)

        try:
            while True:
                # Receive data as JSON
                data = await websocket.receive_json()
                if "type" in data or "content" in data or "receiver_id" in data:
                    message_type = data['type']
                    match message_type:
                        case "message":
                            message = Message(
                                content=data['content'],
                                sender_id=user.id,
                                receiver_id=data['receiver_id']
                            )
                            session.add(message)
                            await session.commit()
                            await session.refresh(message)

                            # Send the message to the receiver through WebSocket
                            await manager.send_personal_message(
                                message.content,
                                data['receiver_id']
                            )
                        case "image":
                            print("image asds")
                            await websocket.send_text("image received")
                        case "video":
                            print("video asds")
                            await websocket.send_text("video received")
                        case default:
                            await websocket.send_text("Please send valid type")

                else:
                    # Handle case where no data is received or invalid data
                    await websocket.send_text("Please send valid JSON data")

        except Exception as e:
            # Handle errors during message receiving or processing
            print(f"Error: {e}")
            await websocket.send_text(f"Error while processing your message,we accept only json")

    except WebSocketDisconnect:
        # Handle disconnection
        await manager.disconnect(user.id)
        print(f"User {user.id} disconnected.")


@router.websocket("/hello")
async def hello(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


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
