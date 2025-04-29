"""
Routes for user management.
"""
from fastapi import APIRouter, Depends, HTTPException

from src.core.base_response.base_response import ChatAppResponse
from src.database import get_db, get_redis
from src.services.user_service import get_current_user, get_all_users
from src.websocket_manager.websocker_manger import manager

user_router = APIRouter(prefix="/user",tags=["User Management"])

@user_router.get("/get_all_users")
async def get_user(db = Depends(get_db),current_user = Depends(get_current_user),redis_conn = Depends(get_redis)):
    """
    Route to get all users.
    """
    try:
        # Assuming you have a function to get all users
        users = await get_all_users(db,redis=redis_conn)
        # return {"users": "hell"}
        return ChatAppResponse(
            status_code="200",
            message="Users retrieved successfully",
            data={"users": users}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.get("/active_users")
async def get_all_active_users(current_user = Depends(get_current_user)):
    """
    Route to get all active users.
    """
    try:
        # Assuming you have a function to get all users
        users = await manager.send_active_users()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))