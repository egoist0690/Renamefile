import os
import asyncio
import logging
from datetime import datetime, timedelta, timezone
import certifi

from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

LOGGER = logging.getLogger(__name__)

mongo = AsyncIOMotorClient(Config.DB_URL, tlsCAFile=certifi.where())
db = mongo[Config.DB_NAME]

users = db["users"]
temporary = db["temporary"]


async def get_user(user_id: int):
    user = await users.find_one({"_id": user_id})

    if user:
        return user

    user = {
        "_id": user_id,
        "format": "{title} - Ch {chapter} [{channel}]",
        "title": None,
        "channel_name": "@ChannelName",
        "target_channel_id": None,
        "thumbnail": None,
        "caption": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await users.insert_one(user)
    return user


async def get_user_config(user_id: int) -> dict:
    return await get_user(user_id)


async def update_user(user_id: int, data: dict):
    data["updated_at"] = datetime.now(timezone.utc)
    await users.update_one(
        {"_id": user_id},
        {"$set": data},
        upsert=True
    )


async def set_format_config(user_id: int, template: str, title: str = None, channel_name: str = None):
    payload = {"format": template}
    if title is not None:
        payload["title"] = title
    if channel_name is not None:
        payload["channel_name"] = channel_name
        
    await update_user(user_id, payload)


async def set_format(user_id: int, file_format: str):
    await update_user(user_id, {"format": file_format})


async def get_format(user_id: int):
    user = await get_user(user_id)
    return user.get("format", "{title} - Ch {chapter} [{channel}]")


async def set_target_channel(user_id: int, channel_id: int):
    await update_user(user_id, {"target_channel_id": channel_id})


async def get_target_channel(user_id: int):
    user = await get_user(user_id)
    return user.get("target_channel_id")


async def set_thumbnail(user_id: int, thumbnail_path: str):
    await update_user(user_id, {"thumbnail": thumbnail_path})


async def get_thumbnail(user_id: int):
    user = await get_user(user_id)
    return user.get("thumbnail")


async def delete_thumbnail(user_id: int):
    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "thumbnail": None,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )


async def set_caption(user_id: int, caption: str):
    await update_user(user_id, {"caption": caption})


async def get_caption(user_id: int):
    user = await get_user(user_id)
    return user.get("caption")


async def delete_caption(user_id: int):
    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "caption": None,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )


async def add_temporary_file(user_id: int, file_path: str, seconds: int = 30):
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    result = await temporary.insert_one(
        {
            "user_id": user_id,
            "file_path": file_path,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
        }
    )
    return result.inserted_id


async def delete_temporary_file(record_id):
    await temporary.delete_one({"_id": record_id})


async def cleanup_expired_records():
    while True:
        try:
            now = datetime.now(timezone.utc)
            expired = temporary.find({"expires_at": {"$lte": now}})
            async for record in expired:
                await temporary.delete_one({"_id": record["_id"]})
        except Exception as e:
            LOGGER.error(f"Temporary database cleanup error: {e}")
        await asyncio.sleep(10)


async def setup_database():
    try:
        await users.create_index("updated_at")
        await temporary.create_index("expires_at", expireAfterSeconds=0)
        LOGGER.info("MongoDB indexes configured successfully.")
    except Exception as e:
        LOGGER.error(f"Database setup error: {e}")


async def start_database():
    await setup_database()
    asyncio.create_task(cleanup_expired_records())
    LOGGER.info("Database system started.")
