from uuid import UUID

from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import DataBaseException
from src.database import get_db
from src.model import Message


async def updateMessage(message_id: UUID, update_message: str, db: AsyncSession = Depends(get_db)):
    """
    Update a message in the database.
    """
    try:
        db_msg = await db.get(Message, message_id)
        db_msg.content = update_message
        await db.commit()
        await db.refresh(db_msg)
        return db_msg
    except SQLAlchemyError as e:
        raise DataBaseException(detail=str(e))


async def deleteMessage(message_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Delete a message from the database.
    """
    db_msg = await db.get(Message, message_id)
    try:
        db_msg.is_deleted = True
        await db.commit()
        await db.refresh(db_msg)
        return True
    except SQLAlchemyError as e:
        raise DataBaseException(detail=str(e))
