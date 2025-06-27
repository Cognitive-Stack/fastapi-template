from fastapi import Depends, HTTPException, status, Request, WebSocket
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

from app.controllers.users import UserController
from app.schemas.auths import TokenData
from app.models.users import UserModel
from app.core.settings import get_settings

security = HTTPBearer()


def get_db(request: Request):
    return request.app.db


async def get_current_user(
    credentials=Depends(security), db=Depends(get_db)
) -> UserModel:
    user_controller = UserController(db)
    try:
        token_data: TokenData = user_controller.decode_access_token(
            credentials.credentials
        )
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not token_data or not token_data.email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    user = await user_controller.get_user_by_email(token_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return user


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user