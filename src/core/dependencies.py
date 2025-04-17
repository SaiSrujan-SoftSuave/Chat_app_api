from fastapi import HTTPException,Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from jwt import ExpiredSignatureError
from starlette import status

from src.core.security import get_id_from_token


class AccessTokenBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        creds = await super().__call__(request)
        if not creds or not creds.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate the token
        try:
            payload = get_id_from_token(creds.credentials)
            request.state.user = payload
            return creds
        except JWTError as e:
            if e is ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail= {"error":"Token has expired"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": str(e)},
                headers={"WWW-Authenticate": "Bearer"},
            )
