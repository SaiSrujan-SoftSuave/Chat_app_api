import uuid
from datetime import datetime

from asyncpg import UniqueViolationError
from fastapi import Depends, HTTPException, WebSocketException,WebSocket
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError
from redis import Redis
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from starlette import status
from src.core.dependencies import AccessTokenBearer
from src.core.errors import UserAlreadyExists, DataBaseException, UserNotFound, InvalidCredentials
from src.core.middleware.logging import logger
from src.core.security import get_hashed_password, verify_password, create_access_token, get_id_from_token
from src.database import get_db, get_redis
from src.model import Message
from src.model.request_models.request_models import UserCreate, UserLogin
from src.model.user import User
import json



access_bearer_token = AccessTokenBearer()
async def create_new_user(user: UserCreate, db: AsyncSession) -> User:
    """
    Create and save a new user in the database.

    :param user: UserCreate schema object
    :param db: Async SQLAlchemy session
    :return: User object
    :raises: UserAlreadyExists, DataBaseException
    """
    try:
        hash_password = get_hashed_password(user.password)
        user_id = uuid.uuid4()

        db_user = User(
            id=user_id,
            name=user.name,
            email=user.email_id,
            password_hash=hash_password,
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    except SQLAlchemyError as e:
        await db.rollback()
        if e is UniqueViolationError or IntegrityError:
            raise UserAlreadyExists()
        else:
            raise DataBaseException(detail=e)



async def authenticate_user(user:UserLogin ,db: AsyncSession) -> User:
    """
    Authenticate user credentials.

    :param db: Async SQLAlchemy session
    :param user: UserLogin schema object
    :return: User object if authentication is successful, None otherwise
    """
    try:
        statement = select(User).where(User.email == user.email_id)
        result = await db.execute(statement)
        user_db = result.scalars().first()
        if user_db is None:
            raise UserNotFound()
        verify_user_password = verify_password(user.password, user_db.password_hash)
        if not verify_user_password:
            raise InvalidCredentials()
        return user_db
    except SQLAlchemyError as e:
        raise DataBaseException(detail=str(e))

async def create_user_token(user: User, db: AsyncSession) -> str:
    """
    Create a token for the user.

    :param user: User object
    :param db: Async SQLAlchemy session
    :return: JWT token as string
    """
    # This function should create a JWT token for the user
    # The implementation of this function is not provided in the original code
    return create_access_token(subject= str(user.id))


async def get_current_user(token_details: HTTPAuthorizationCredentials = Depends(access_bearer_token),
                           db: AsyncSession = Depends(get_db)):
    try:
        user_id = get_id_from_token(token_details.credentials)
        statement = select(User).where(User.id == user_id)
        result = await db.execute(statement)
        db_user = result.scalars().first()

        if not db_user:
            raise UserNotFound()

        return db_user

    except SQLAlchemyError as e:
        raise DataBaseException(detail=e)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def get_current_user_ws(websocket: WebSocket, db: AsyncSession = Depends(get_db)) -> User:
    token = websocket.query_params.get("token")  # or websocket.headers.get("Authorization")
    print(token,"----> token")
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")

    try:
        user_id = get_id_from_token(token)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        print(user,"----> User")
        if not user:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")

        return user

    except JWTError as e:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
    except Exception as e:
        raise WebSocketException(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))

async def get_all_users(db: AsyncSession = Depends(get_db),redis:Redis = Depends(get_redis)):
    """
    Get all users from the database.

    :param db: Async SQLAlchemy session
    :return: List of User objects
    """
    try:
        statement = select(User)
        result = await db.execute(statement)
        users = result.scalars().all()
        return users
    except SQLAlchemyError as e:
        raise DataBaseException(detail=str(e))


def serialize_user(user: User) -> dict:
    """Convert User SQLModel to dict with UUIDs as strings"""
    user_dict = user.model_dump()
    user_dict["id"] = str(user.id)
    return user_dict
    #
    # local_users = await redis.get("users")
    #     if local_users:
    #         # Deserialize JSON string back to Python objects (dicts)
    #         return json.loads(local_users)
    #     else:
    #         statement = select(User)
    #         result = await db.execute(statement)
    #         users = result.scalars().all()
    #
    #         # Serialize list of user dicts for Redis (SQLModel -> dict -> JSON string)
    #         users_data =  [serialize_user(user) for user in users]
    #         await redis.set("users", json.dumps(users_data))
    #
    #         print("TAG --- ", users_data)
    #         return users_data


async def make_user_online(db: AsyncSession, user_id: uuid.UUID):
    """
    Mark a user as online in the database.

    :param db: AsyncSession instance
    :param user_id: UUID of the user
    """
    user = await db.get(User, user_id)
    if not user:
        raise UserNotFound()
    try:
        user.is_online = True
        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError as e:
        raise DataBaseException(detail=str(e))

async def make_user_offline(db: AsyncSession, user_id: uuid.UUID):
    """
    Mark a user as offline in the database.

    :param db: AsyncSession instance
    :param user_id: UUID of the user
    """
    user = await db.get(User, user_id)
    if not user:
        raise UserNotFound()
    try:
        user.is_online = False
        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError as e:
        raise DataBaseException(detail=str(e))

async def set_message_seen_timestamp(db: AsyncSession, message_id: uuid.UUID):
    """
    Set the seen timestamp for a message.

    :param db: AsyncSession instance
    :param message_id: UUID of the message
    """
    message = await db.get(Message, message_id)
    if not message:
        raise UserNotFound()
    try:
        message.seen_timestamp = datetime.now()
        await db.commit()
        await db.refresh(message)
        return message
    except SQLAlchemyError as e:
        raise DataBaseException(detail=str(e))
