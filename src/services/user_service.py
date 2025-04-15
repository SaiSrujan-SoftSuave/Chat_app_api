import uuid


from asyncpg import UniqueViolationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.errors import UserAlreadyExists, DataBaseException, UserNotFound, InvalidCredentials
from src.core.middleware.logging import logger
from src.core.security import get_hashed_password, verify_password, create_access_token
from src.model.request_models.request_models import UserCreate, UserLogin
from src.model.user import User


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
            email_id=user.email_id,
            password_hash=hash_password,
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    except (IntegrityError, UniqueViolationError) as e:
        # Assuming email_id is unique, raise conflict error
        await db.rollback()
        raise UserAlreadyExists()

    except SQLAlchemyError as e:
        await db.rollback()
        raise DataBaseException(detail=str(e))



async def authenticate_user(user:UserLogin ,db: AsyncSession) -> User:
    """
    Authenticate user credentials.

    :param db: Async SQLAlchemy session
    :param user: UserLogin schema object
    :return: User object if authentication is successful, None otherwise
    """
    try:
        statement = select(User).where(User.email_id == user.email_id)
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