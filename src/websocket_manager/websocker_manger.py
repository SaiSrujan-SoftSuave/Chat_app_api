import asyncio
from datetime import datetime
from uuid import UUID
from typing import Dict, Set, Optional
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from src.model import Message
from src.services.user_service import make_user_online, make_user_offline, set_message_seen_timestamp


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, WebSocket] = {}
        self.online_users: Set[UUID] = set()
        self.redis_conn: Optional = None
        self.db: Optional[AsyncSession] = None

    async def connect(
            self,
            websocket: WebSocket,
            user_id: UUID,
            db: AsyncSession,
            redis_conn: Optional = None
    ):
        await websocket.accept()
        self.redis_conn = redis_conn
        self.db = db
        self.active_connections[user_id] = websocket
        self.online_users.add(user_id)
        await make_user_online(db=self.db, user_id=user_id)
        await self.broadcast_status(user_id, is_online=True)

    async def disconnect(self, user_id: UUID):
        ws = self.active_connections.pop(user_id, None)
        if ws:
            self.online_users.discard(user_id)
            await make_user_offline(self.db, user_id)
            asyncio.create_task(self.broadcast_status(user_id, is_online=False))

    async def send_personal_message(self, message: str, user_id: UUID, sender_id: UUID, message_id: UUID):
        ws = self.active_connections.get(user_id)
        sender_ws = self.active_connections.get(sender_id)
        if ws:
            msg = {
                "type": "personal_message",
                "message": message,
                "user_id": str(sender_id),
                "message_id": str(message_id)
            }
            sender_msg = {
                "type": "message_ack",
                "message_id": str(message_id)
            }
            await ws.send_json(msg)
            await sender_ws.send_json(sender_msg)
        else:
            await self.redis_conn.lpush(f"user:{user_id}:messages", message)

    async def make_message_read(self, message_id: UUID):
        msg = await set_message_seen_timestamp(self.db, message_id)
        if msg:
            # Notify the sender that the message has been seen
            sender_ws = self.active_connections.get(msg.sender_id)
            if sender_ws:
                seen_msg = {
                    "type": "message_seen",
                    "message_id": str(message_id),
                    "seen_timestamp": str(msg.seen_timestamp)
                }
                await sender_ws.send_json(seen_msg)
        else:
            raise Exception("Message not found")

    async def broadcast_status(self, user_id: UUID, is_online: bool):
        msg = {
            "type": "status_update",
            "user_id": str(user_id),
            "is_online": is_online
        }
        for ws in self.active_connections.values():
            await ws.send_json(msg)

    async def send_active_users(self):
        """Broadcast the current set of online users to everyone."""
        payload = {
            "type": "active_users",
            "active_users": [str(u) for u in self.online_users]
        }
        for ws in self.active_connections.values():
            await ws.send_json(payload)
        return list(self.online_users)

    async def post_active_typing(self, receiver_id: UUID, typing_status: bool, sender_id: UUID):
        ws = self.active_connections.get(receiver_id)
        if ws:
            msg = {
                "type": "typing_status",
                "sender_id": str(sender_id),
                "typing_status": typing_status
            }
            await ws.send_json(msg)
        else:
            print("user not found")
            await self.redis_conn.lpush(f"user:{receiver_id}:typing_status", typing_status)

manager = ConnectionManager()
