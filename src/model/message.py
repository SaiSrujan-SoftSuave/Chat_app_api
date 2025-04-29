import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

# if TYPE_CHECKING:
from src.model.user import User
from src.model.user import UserRead



# from src.model import User
# from src.model.user import UserRead


class MessageBase(SQLModel):
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class Message(MessageBase, table=True):
    __tablename__ = "messages"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    sender_id: uuid.UUID = Field(foreign_key="user.id")
    receiver_id: uuid.UUID = Field(foreign_key="user.id")

    # Relationships
    sender: User = Relationship(back_populates="sent_messages")
    receiver: User = Relationship(back_populates="received_messages")


class MessageRead(MessageBase):
    id: uuid.UUID
    sender: UserRead
    receiver: UserRead