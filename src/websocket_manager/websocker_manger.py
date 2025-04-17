import uuid

from fastapi import WebSocket
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[uuid.UUID, WebSocket] = {}
        self.online_users = set()

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.online_users.add(user_id)

    def disconnect(self, user_id: uuid.UUID):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            self.online_users.remove(user_id)

    async def send_personal_message(self, message: str, user_id: uuid.UUID):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()