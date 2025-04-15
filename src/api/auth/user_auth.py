from http.client import HTTPException

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from src.core.base_response.base_response import ChatAppResponse
from src.core.errors import UserAlreadyExists, DataBaseException, ChatAppException
from src.core.security import validate_email, validate_password
from src.database import get_db
from src.model.request_models.request_models import UserCreate, UserLogin
from src.services.user_service import create_new_user, authenticate_user, create_user_token

auth_router = APIRouter(
    prefix="/auth",
    tags=["user auth"]
)


@auth_router.post("/sign-up")
async def user_sign_up(user: UserCreate, db: AsyncSession = Depends(get_db)):
    is_valid_email, email_message = validate_email(user.email_id)
    is_valid_password, password_message = validate_password(user.password)

    if not is_valid_password:
        raise HTTPException(status_code=400, detail=password_message)
    if not is_valid_email:
        raise HTTPException(status_code=400, detail=email_message)

    try:
        user = await create_new_user(user, db)
        if user is not None:
            return ChatAppResponse(
                status_code=status.HTTP_201_CREATED,
                message={
                    "message": "User created successfully"
                },
                data={"user": user},
            )
    except ChatAppException as e:
        raise e


@auth_router.post("/sign-in")
async def user_sign_in(user: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(user=user, db=db)
    if user is not None:
        access_token = await create_user_token(user, db)
        return ChatAppResponse(
            status_code=status.HTTP_200_OK,
            message={
                "message": "user logged in successfully"
            },
            data={
                "access_token": access_token,
                "user": user
            }
        )
    else:
        return status.HTTP_503_SERVICE_UNAVAILABLE
