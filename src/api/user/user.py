"""
Routes for user management.
"""
from fastapi import APIRouter, Depends, HTTPException
from src.core.base_response.base_response import ChatAppResponse
from src.database import get_db, get_redis
from src.services.user_service import get_current_user, get_all_users
from src.websocket_manager.websocker_manger import manager

user_router = APIRouter(prefix="/user", tags=["User Management"])


@user_router.get("/get_all_users")
async def get_user(db=Depends(get_db), current_user=Depends(get_current_user), redis_conn=Depends(get_redis)):
    """
    Route to get all users.
    """
    try:
        users = await get_all_users(db, redis=redis_conn)
        return ChatAppResponse(
            status_code="200",
            message="Users retrieved successfully",
            data={"users": users}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@user_router.get("/active_users")
async def get_all_active_users(current_user=Depends(get_current_user)):
    """
    Route to get all active users.
    """
    try:
        # Assuming you have a function to get all users
        users = await manager.send_active_users()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@user_router.post("/update_user")
async def update_user(user_name: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    """
    Route to update a user.
    """
    try:
        current_user.name = user_name
        await db.commit()
        await db.refresh(current_user)
        return ChatAppResponse(
            status_code="200",
            message="User updated successfully",
            data={"user_id": current_user.id,
                  "user_name": current_user.name
                  }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@user_router.delete("/delete_user/{user_id}")
async def delete_user(user_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    """
    Route to delete a user. works as soft delete
    """
    try:
        current_user.is_deleted = True
        await db.commit()
        return ChatAppResponse(
            status_code="200",
            message="User deleted successfully",
            data={"user_id": user_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
