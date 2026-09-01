import os
import asyncio
import logging
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient

from config import Config


LOGGER = logging.getLogger(__name__)


# ============================================================
# MONGODB CONNECTION
# ============================================================

mongo = AsyncIOMotorClient(Config.DB_URL)

db = mongo[Config.DB_NAME]

users = db["users"]
temporary = db["temporary"]


# ============================================================
# USER
# ============================================================

async def get_user(user_id: int):
    """
    Get user settings.
    Creates the user automatically if it doesn't exist.
    """

    user = await users.find_one({"_id": user_id})

    if user:
        return user

    user = {
        "_id": user_id,

        # Rename settings
        "format": "Episode episode - quality",

        # Media settings
        "thumbnail": None,
        "caption": None,

        # Timestamps
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    await users.insert_one(user)

    return user


# ============================================================
# UPDATE USER
# ============================================================

async def update_user(user_id: int, data: dict):

    data["updated_at"] = datetime.utcnow()

    await users.update_one(
        {"_id": user_id},
        {"$set": data},
        upsert=True
    )


# ============================================================
# RENAME FORMAT
# ============================================================

async def set_format(user_id: int, file_format: str):

    await update_user(
        user_id,
        {
            "format": file_format
        }
    )


async def get_format(user_id: int):

    user = await get_user(user_id)

    return user.get(
        "format",
        "Episode episode - quality"
    )


# ============================================================
# THUMBNAIL
# ============================================================

async def set_thumbnail(user_id: int, thumbnail_path: str):

    await update_user(
        user_id,
        {
            "thumbnail": thumbnail_path
        }
    )


async def get_thumbnail(user_id: int):

    user = await get_user(user_id)

    return user.get("thumbnail")


async def delete_thumbnail(user_id: int):

    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "thumbnail": None,
                "updated_at": datetime.utcnow()
            }
        }
    )


# ============================================================
# CAPTION
# ============================================================

async def set_caption(user_id: int, caption: str):

    await update_user(
        user_id,
        {
            "caption": caption
        }
    )


async def get_caption(user_id: int):

    user = await get_user(user_id)

    return user.get("caption")


async def delete_caption(user_id: int):

    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "caption": None,
                "updated_at": datetime.utcnow()
            }
        }
    )


# ============================================================
# TEMPORARY FILE RECORDS
# ============================================================

async def add_temporary_file(
    user_id: int,
    file_path: str,
    seconds: int = 30
):

    expires_at = datetime.utcnow() + timedelta(
        seconds=seconds
    )

    result = await temporary.insert_one(
        {
            "user_id": user_id,
            "file_path": file_path,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
        }
    )

    return result.inserted_id


# ============================================================
# DELETE TEMPORARY RECORD
# ============================================================

async def delete_temporary_file(record_id):

    await temporary.delete_one(
        {
            "_id": record_id
        }
    )


# ============================================================
# CLEAN EXPIRED RECORDS
# ============================================================

async def cleanup_expired_records():

    while True:

        try:

            now = datetime.utcnow()

            expired = temporary.find(
                {
                    "expires_at": {
                        "$lte": now
                    }
                }
            )

            async for record in expired:

                record_id = record["_id"]

                await temporary.delete_one(
                    {
                        "_id": record_id
                    }
                )

                LOGGER.info(
                    f"Deleted temporary DB record: {record_id}"
                )

        except Exception as e:

            LOGGER.error(
                f"Temporary database cleanup error: {e}"
            )

        # Check every 10 seconds
        await asyncio.sleep(10)


# ============================================================
# DATABASE INDEX
# ============================================================

async def setup_database():

    try:

        await users.create_index(
            "updated_at"
        )

        await temporary.create_index(
            "expires_at",
            expireAfterSeconds=0
        )

        LOGGER.info(
            "MongoDB indexes configured successfully."
        )

    except Exception as e:

        LOGGER.error(
            f"Database setup error: {e}"
        )


# ============================================================
# DATABASE STARTUP
# ============================================================

async def start_database():

    await setup_database()

    # Start cleanup worker
    asyncio.create_task(
        cleanup_expired_records()
    )

    LOGGER.info(
        "Database system started."
    )
