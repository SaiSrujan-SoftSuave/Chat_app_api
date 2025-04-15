"""
This file contains all custom error messages.
"""
from typing import Any, Callable

from fastapi import FastAPI
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse


class ChatAppException(Exception):
    """
    Application Global Exception
    """

class UserAlreadyExists(ChatAppException):
    """
    if UserAlreadyExists in DB
    """


class DataBaseException(ChatAppException):
    """
     Database exception
     """

    def __init__(self, detail):
        super().__init__(detail)


class UserNotFound(ChatAppException):
    """
    UserNotFound in DB
    """
class InvalidCredentials(ChatAppException):
    """
    Provided incorrect Credentials
    """
def create_exception_handler(
        status_code: int, initial_detail: Any
) -> Callable[[Request, Exception], JSONResponse]:
    """
    Reusable function to create a custom exception
    :param status_code:
    :param initial_detail:
    :return:
    """

    async def exception_handler(request: Request, exc: ChatAppException):
        detail = initial_detail.copy()
        if hasattr(exc, "detail") and exc.detail:
            detail["message"] = f"{detail['message']} {str(exc.detail)}"
        elif str(exc):
            detail["message"] = f"{detail['message']} {str(exc)}"

        return JSONResponse(content=detail, status_code=status_code)

    return exception_handler


def register_all_errors(app: FastAPI):
    """
    This function register all custom exception with fastAPi application instance
    :param app:
    :return:
    """
    app.add_exception_handler(
        UserAlreadyExists,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                "message": "User with email already exists",
                "error_code": "user_exists",
            },
        ),
    )
    app.add_exception_handler(
        DataBaseException,
        create_exception_handler(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            initial_detail={
                "message": f"data base execution failed:",
                "error_code": "database_exception",
            },
        )
    )
    app.add_exception_handler(
        UserNotFound,
        create_exception_handler(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            initial_detail={
                "message": f"User not found, please check the details",
                "error_code": "user_not_found",
            },
        )
    )
    app.add_exception_handler(
        InvalidCredentials,
        create_exception_handler(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            initial_detail={
                "message": f"invalid credentials, please check the details",
                "error_code": "user_not_found",
            },
        )
    )
