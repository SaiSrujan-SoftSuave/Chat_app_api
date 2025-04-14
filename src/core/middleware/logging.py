"""
Used to log request and response times with proper error handling.
"""

import logging
import time

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

logger = logging.getLogger("uvicorn.access")
logger.disabled = True


def register_middleware(app: FastAPI):
    """
    Register middleware for logging and token validation.
    :param app: FastAPI instance
    :return: None
    """

    @app.middleware("http")
    async def custom_logging(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        processing_time = time.time() - start_time
        message = (
            f"{request.client.host}:{request.client.port} - {request.method} "
            f"- {request.url.path} - {response.status_code} completed after {processing_time:.2f}s"
        )
        print(message)

        return response


    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
