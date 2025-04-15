"""
This file contains all router added to main router
"""

from fastapi import APIRouter

from src.api.auth.user_auth import auth_router

main_router = APIRouter()

main_router.include_router(auth_router)