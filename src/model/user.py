import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
  # avoids circular import at runtime

class UserBase(SQLModel):
    name: str = Field(index=True)
    email: str = Field(
        unique=True,
        regex=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    )
    is_online: bool = Field(default=False)

class User(UserBase, table=True):
    __tablename__ = "user"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    password_hash: str
    is_deleted: bool = Field(default=False,nullable=False)
    # Relationships (forward references as strings)
    sent_messages: List["Message"] = Relationship(
        back_populates="sender",
        sa_relationship_kwargs={"foreign_keys": "[Message.sender_id]"}
    )
    received_messages: List["Message"] = Relationship(
        back_populates="receiver",
        sa_relationship_kwargs={"foreign_keys": "[Message.receiver_id]"}
    )


class UserRead(UserBase):
    id: uuid.UUID  # should match the actual id type used in your User model
