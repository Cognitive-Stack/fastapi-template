# auth_api.py

from fastapi import APIRouter, Depends, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from app.controllers.users import UserController
from app.schemas.users import UserCreate, User
from app.schemas.auths import Token

router = APIRouter()


def get_user_controller(request: Request):
    return UserController(request.app.db)


@router.post("/login", response_model=Token)
async def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    controller: UserController = Depends(get_user_controller),
):
    return await controller.login_user(form_data)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    refresh_token: str = Body(..., embed=True),
    controller: UserController = Depends(get_user_controller),
) -> Token:
    return await controller.refresh_token(refresh_token)


@router.post("/reset-password-request", response_model=dict)
async def reset_password_request(
    email: str,
    request: Request,
    controller: UserController = Depends(get_user_controller),
):
    return await controller.reset_password_request(email)


@router.post("/reset-password", response_model=dict)
async def reset_password(
    token: str,
    new_password: str,
    request: Request,
    controller: UserController = Depends(get_user_controller),
):
    return await controller.reset_password(token, new_password)


@router.post("/verify-email", response_model=dict)
async def verify_email(
    token: str,
    request: Request,
    controller: UserController = Depends(get_user_controller),
):
    return await controller.verify_email(token)
