# user_api.py

from fastapi import APIRouter, Depends, Request, HTTPException, status
from app.controllers.users import UserController
from app.schemas.users import UserUpdate, User, UserCreate, UserRoles
from app.dependencies.auth import get_current_active_user
from app.models.base import PyObjectId
from typing import List

router = APIRouter()


def get_user_controller(request: Request):
    return UserController(request.app.db)


@router.post("/", response_model=User)
async def create_user(
    user: UserCreate,
    user_controller: UserController = Depends(get_user_controller),
):
    return await user_controller.register_user(user)


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    return current_user


@router.get("/{id}", response_model=User)
async def get_user_info(
    id: str,
    controller: UserController = Depends(get_user_controller),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRoles.ADMIN and str(current_user.id) != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return await controller.get_user(id)


@router.put("/{id}", response_model=User)
async def update_user_info(
    id: str,
    user_update: UserUpdate,
    controller: UserController = Depends(get_user_controller),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRoles.ADMIN and str(current_user.id) != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Only admin can update tier
    if user_update.tier is not None and current_user.role != UserRoles.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can update user tier",
        )

    return await controller.update_user_info(id, user_update)


@router.put("/email/{email}", response_model=User)
async def update_user_info_by_email(
    email: str,
    user_update: UserUpdate,
    controller: UserController = Depends(get_user_controller),
    current_user: User = Depends(get_current_active_user),
):
    # Get the user by email
    user = await controller.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Access control checks
    if current_user.role != UserRoles.ADMIN and current_user.email != email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Only admin can update tier
    if user_update.tier is not None and current_user.role != UserRoles.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can update user tier",
        )

    return await controller.update_user_info_by_email(email, user_update)


@router.delete("/{id}", response_model=dict)
async def delete_user(
    id: str,  # Changed from user_id to id to match the path parameter
    controller: UserController = Depends(get_user_controller),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRoles.ADMIN and str(current_user.id) != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return await controller.delete_user(id)