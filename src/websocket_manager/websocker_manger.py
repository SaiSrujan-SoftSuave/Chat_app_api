import uuid

import asyncio
from fastapi import WebSocket, Depends
from typing import Dict
from src.database import get_redis


class ConnectionManager:
    def __init__(self,redis_conn = Depends(get_redis)):
        self.active_connections: Dict[ uuid.UUID, WebSocket] = {}
        self.online_users = set()
        self.redis_conn = redis_conn

    async def connect(self, websocket: WebSocket,  user_id: uuid.UUID):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.online_users.add(user_id)
        await self.broadcast_status(user_id, True)

    def disconnect(self,  user_id: uuid.UUID):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            self.online_users.remove(user_id)
            asyncio.create_task(self.broadcast_status(user_id, False))

    async def send_personal_message(self, message: str, user_id: uuid.UUID):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

    async def broadcast_status(self, user_id: uuid.UUID, is_online: bool):
        message = {
            "type": "status_update",
            "user_id": user_id,
            "is_online": is_online
        }
        for connection in self.active_connections.values():
            await connection.send_json(message)

    async def send_active_users(self):
        active_users = list(self.online_users)
        # for connection in self.active_connections.values():
        #     await connection.send_json({
        #         "type": "active_users",
        #         "active_users": active_users
        #     })
        return active_users


manager = ConnectionManager()