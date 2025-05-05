import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship

# if TYPE_CHECKING:
# from src.model.user import User
from src.model.user import UserRead

if TYPE_CHECKING:
    from .message import Message


# from src.model import User
# from src.model.user import UserRead


class MessageBase(SQLModel):
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    seen_timestamp: Optional[datetime] = Field(default=None, nullable=True)
    is_deleted: bool = Field(default=False, nullable=False)


class Message(MessageBase, table=True):
    __tablename__ = "messages"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    sender_id: uuid.UUID = Field(foreign_key="user.id")
    receiver_id: uuid.UUID = Field(foreign_key="user.id")

    sender: "User" = Relationship(
        back_populates="sent_messages",
        sa_relationship_kwargs={"foreign_keys": "[Message.sender_id]"}
    )
    receiver: "User" = Relationship(
        back_populates="received_messages",
        sa_relationship_kwargs={"foreign_keys": "[Message.receiver_id]"}
    )


class MessageRead(MessageBase):
    id: uuid.UUID
    sender: UserRead
    receiver: UserRead


class MesageUpdate(BaseModel):
    id: uuid.UUID
    new_message: str
