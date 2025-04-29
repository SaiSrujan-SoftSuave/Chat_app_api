import os
import re
from datetime import timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from src.config import Config

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UnauthorizedError(RuntimeError):
    pass


class TokenSchema(BaseModel):
    access_token: str


class TokenPayload(BaseModel):
    sub: str
    exp: int = 60


def create_access_token(
        subject: str,
        expires_delta: int | None = None,
) -> str:
    """
    :param subject:
    :param expires_delta:
    :return:
    """
    if expires_delta is not None:
        exp = datetime.now() + timedelta(minutes=expires_delta)
    else:
        exp = datetime.now() + timedelta(
            minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": exp, "sub": subject}
    encoded_jwt = jwt.encode(to_encode, Config.JWT_SECRET_KEY, Config.ALGORITHM)
    return encoded_jwt


def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def get_verify_token(token_payload: TokenPayload):
    subject = token_payload.sub
    exp = datetime.now() + timedelta(
        minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    to_encode = {"exp": exp, "sub": subject}
    verify_token = jwt.encode(to_encode, Config.JWT_SECRET_KEY, Config.ALGORITHM)
    print("verify_token", verify_token)
    return verify_token


def get_id_from_token(token):
    payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=Config.ALGORITHM)
    user_id = payload.get('sub')
    return user_id


def validate_email(email: str) -> tuple[bool, str]:
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(email_regex, email):
        return True, "Valid email"
    return False, "Invalid email format"


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 6:
        return False, "Password should be at least 6 characters long"
    if not re.search(r"[A-Z]", password):  # Check for uppercase letter
        return False, "Password should contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):  # Check for lowercase letter
        return False, "Password should contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):  # Check for digit
        return False, "Password should contain at least one digit"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):  # Check for special character
        return False, "Password should contain at least one special character"

    return True, "Valid password"


from datetime import datetime


def make_naive(dt: datetime) -> datetime:
    """Convert a timezone-aware datetime to naive (UTC) datetime."""
    if dt.tzinfo is not None:
        return dt.astimezone().replace(tzinfo=None)
    return dt


def is_test_env():
    if os.getenv('TEST_ENV'):
        return True
    return False
