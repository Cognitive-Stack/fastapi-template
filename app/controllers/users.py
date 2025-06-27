import os
from datetime import datetime, timedelta
from typing import List, Optional, Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.models.users import UserModel
from app.schemas.auths import Token, TokenData, TokenPayload
from app.schemas.users import UserCreate, UserUpdate, UserRoles
from google.oauth2 import id_token
from google.auth.transport import requests
from app.schemas.users import AuthProvider
from app.core.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


class UserController:
    def __init__(self, db):
        self.settings = get_settings()
        self.db: AsyncIOMotorDatabase = db
        self.collection = self.db.get_collection("users")
        self.access_token_expires = timedelta(
            minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self.refresh_token_expires = timedelta(days=7)

    async def register_user(self, user: UserCreate):
        # Check if user already exists
        if await self.get_user_by_email(user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        user_data = user.model_dump(exclude={"password"})
        user_data.update(
            {
                "hashed_password": get_password_hash(user.password),
                "created_at": datetime.now().isoformat() + "Z",
                "updated_at": datetime.now().isoformat() + "Z",
                "role": UserRoles.USER.value,
                "disabled": False,
                "workspaces": [],
            }
        )
        result = await self.collection.insert_one(user_data)
        return await self.get_user(result.inserted_id)

    async def login_user(self, form_data: OAuth2PasswordRequestForm):
        user = await self.authenticate_user(form_data.username, form_data.password)

        access_token = self.create_token(
            user.email, "access", self.access_token_expires
        )
        refresh_token = self.create_token(
            user.email, "refresh", self.refresh_token_expires
        )

        # Update last login
        await self.collection.update_one(
            {"email": user.email},
            {"$set": {"last_login": datetime.now().isoformat() + "Z"}},
        )

        return Token(
            **user.model_dump(),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=(datetime.now() + self.access_token_expires).isoformat() + "Z",
        )

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = data.copy()
        expire = (
            datetime.now()
            + (
                expires_delta
                or timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
        ).isoformat() + "Z"
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM
        )
        return encoded_jwt

    def decode_access_token(self, token: str) -> TokenData:
        try:
            payload = jwt.decode(
                token, self.settings.SECRET_KEY, algorithms=[self.settings.ALGORITHM]
            )
            email: str = payload.get("sub")
            exp: datetime = datetime.fromtimestamp(payload.get("exp"))
            token_type = payload.get(
                "type", "access"
            )  # default to access if not specified

            if email is None:
                raise JWTError("Token does not contain 'sub'")

            return TokenData(email=email, exp=exp, token_type=token_type)
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            ) from e

    def create_token(
        self, email: str, token_type: str, expires_delta: timedelta
    ) -> str:
        expires_at = (datetime.now() + expires_delta).isoformat() + "Z"
        payload = TokenPayload(sub=email, exp=expires_at, type=token_type)
        return jwt.encode(
            payload.model_dump(),
            self.settings.SECRET_KEY,
            algorithm=self.settings.ALGORITHM,
        )

    async def refresh_token(self, refresh_token: str) -> Token:
        try:
            # Verify the token and its type
            token_data = self.decode_access_token(refresh_token)
            if token_data.token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )

            # Get the user
            user = await self.get_user_by_email(token_data.email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
                )

            # Create new tokens
            new_access_token = self.create_token(
                user.email, "access", self.access_token_expires
            )
            new_refresh_token = self.create_token(
                user.email, "refresh", self.refresh_token_expires
            )

            # Update last login
            await self.collection.update_one(
                {"email": user.email},
                {"$set": {"last_login": datetime.now().isoformat() + "Z"}},
            )

            return Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_at=(datetime.now() + self.access_token_expires).isoformat()
                + "Z",
            )

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

    async def authenticate_user(self, email: str, password: str) -> Optional[UserModel]:
        user = await self.get_user_by_email(email)
        if user and verify_password(password, user.hashed_password):
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        try:
            user = await self.collection.find_one({"email": email})
            if user:
                return UserModel(**user)
            return None
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving user: {str(e)}",
            )

    async def get_user(self, user_id: str) -> UserModel:
        try:
            object_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID"
            )
        user = await self.collection.find_one({"_id": object_id})
        if user:
            return UserModel(**user)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    async def update_user_info(
        self, user_id: str, user_update: UserUpdate
    ) -> UserModel:
        try:
            object_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID"
            )

        update_data = user_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        # Check if email is being updated
        if "email" in update_data:
            new_email = update_data["email"]
            # Check if new email already exists
            existing_user = await self.get_user_by_email(new_email)
            if existing_user and str(existing_user.id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

            # Reset email verification status for new email
            update_data["email_verified"] = False

        update_data["updated_at"] = datetime.now().isoformat() + "Z"
        result = await self.collection.update_one(
            {"_id": object_id}, {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return await self.get_user(user_id)

    async def update_user_info_by_email(
        self, email: str, user_update: UserUpdate
    ) -> UserModel:
        user = await self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        # Reuse existing method using user's ID
        return await self.update_user_info(str(user.id), user_update)

    async def delete_user(self, user_id: str):
        try:
            object_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID"
            )
        result = await self.collection.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return {"message": "User has been deleted successfully"}

    async def google_authenticate(self, token: str) -> Token:
        try:
            # Verify the Google token
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), self.settings.GOOGLE_CLIENT_ID
            )

            email = idinfo["email"]
            google_id = idinfo["sub"]

            # Check if user exists
            user = await self.get_user_by_email(email)
            if not user:
                # Create new user with Google data
                user_data = {
                    "email": email,
                    "full_name": idinfo.get("name", ""),
                    "email_verified": idinfo.get("email_verified", False),
                    "profile_image": idinfo.get("picture"),
                    "auth_provider": AuthProvider.GOOGLE,
                    "google_id": google_id,
                    "created_at": datetime.now().isoformat() + "Z",
                    "updated_at": datetime.now().isoformat() + "Z",
                    "role": UserRoles.USER,
                    "disabled": False,
                    "workspaces": [],
                }
                result = await self.collection.insert_one(user_data)
                user = await self.get_user(result.inserted_id)
            elif user.auth_provider != AuthProvider.GOOGLE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please use email/password to login",
                )

            # Create tokens
            access_token = self.create_token(
                user.email, "access", self.access_token_expires
            )
            refresh_token = self.create_token(
                user.email, "refresh", self.refresh_token_expires
            )
            # Update last login
            await self.collection.update_one(
                {"email": user.email},
                {"$set": {"last_login": datetime.now().isoformat() + "Z"}},
            )

            return Token(
                **user.model_dump(),
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=(datetime.now() + self.access_token_expires).isoformat()
                + "Z",
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to authenticate with Google token: {str(e)}",
            ) from e

    def create_token_for_interview(
        self, interview_id: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Creates a special token for interview access.

        Args:
            interview_id: The ID of the interview
            expires_delta: Optional expiration time delta, defaults to access token expiry

        Returns:
            str: JWT token for interview access
        """
        expires = expires_delta or self.access_token_expires
        expires_at = datetime.now() + expires

        payload = {
            "sub": interview_id,
            "exp": int(expires_at.timestamp()),  # Convert to Unix timestamp (integer)
            "type": "interview",
        }

        return jwt.encode(
            payload, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM
        )
