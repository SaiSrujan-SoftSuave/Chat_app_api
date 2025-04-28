import asyncio
from uuid import UUID
from typing import Dict, Set, Optional

from fastapi import WebSocket
from src.database import get_redis  # you'll still use this in your WS endpoint

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, WebSocket] = {}
        self.online_users: Set[UUID] = set()
        self.redis_conn: Optional = None

    async def connect(
        self,
        websocket: WebSocket,
        user_id: UUID,
        # redis_conn  # pass this in from your endpoint
    ):
        await websocket.accept()
        # self.redis_conn = redis_conn
        self.active_connections[user_id] = websocket
        self.online_users.add(user_id)
        print(f"Connected: {self.active_connections.keys()}")
        await self.broadcast_status(user_id, is_online=True)

    def disconnect(self, user_id: UUID):
        ws = self.active_connections.pop(user_id, None)
        if ws:
            self.online_users.discard(user_id)
            # schedule the status broadcast without blocking
            asyncio.create_task(self.broadcast_status(user_id, is_online=False))

    async def send_personal_message(self, message: str, user_id: UUID):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_text(message)
        else:
            # fallback: push to Redis list for offline delivery
            await self.redis_conn.lpush(f"user:{user_id}:messages", message)

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

# instantiate without DI
manager = ConnectionManager()
