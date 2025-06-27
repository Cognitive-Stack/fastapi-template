import os
from loguru import logger
from app.controllers.users import UserController
from app.schemas.users import UserCreate, UserTier


async def init_superuser(db):
    user_controller = UserController(db)
    admin_email = os.getenv("SUPERUSER_EMAIL")
    admin_password = os.getenv("SUPERUSER_PASSWORD")
    admin_full_name = os.getenv("SUPERUSER_FULL_NAME", "Admin User")

    if not admin_email or not admin_password:
        logger.warning("Superuser email or password not provided")
        return

    existing_user = await user_controller.get_user_by_email(admin_email)
    if not existing_user:
        admin = UserCreate(
            email=admin_email,
            full_name=admin_full_name,
            password=admin_password,
            birth_date="2024-12-05T13:10:36.141Z",
            phone_number="1234567890",
        )
        await user_controller.register_user(admin)
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"role": "admin", "tier": UserTier.ENTERPRISE}},
        )
        logger.info("Superuser created successfully")
