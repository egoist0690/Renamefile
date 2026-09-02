import asyncio
import logging
import os
import time
from pathlib import Path

from pyrogram import Client
from pyrogram.types import Message

from database import (
    add_temporary_file,
    delete_temporary_file,
    get_thumbnail,
    get_caption,
    get_user_config,
)
from rename import rename_file

LOGGER = logging.getLogger("EGOIST6969.MEDIA")

DOWNLOAD_DIR = Path("downloads")
CLEANUP_DELAY = 5
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Throttles progress edits to prevent Telegram FloodWait rate limits
LAST_UPDATE_TIME = {}

def human_size(size: int) -> str:
    if not size:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


async def safe_edit(message, text):
    if not message:
        return
    try:
        await message.edit_text(text)
    except Exception:
        pass


def progress_callback(current, total, status_message, start_time, action="Downloading"):
    if not total:
        return
    
    now = time.time()
    msg_id = status_message.id
    
    # Throttle edits to once every 4 seconds
    if msg_id in LAST_UPDATE_TIME and (now - LAST_UPDATE_TIME[msg_id]) < 4:
        return
    
    LAST_UPDATE_TIME[msg_id] = now
    
    elapsed = max(now - start_time, 0.1)
    percentage = (current * 100 / total)
    speed = (current / elapsed)
    remaining = (total - current)
    eta = (remaining / speed) if speed > 0 else 0

    speed_text = human_size(int(speed)) + "/s"
    done_text = human_size(current)
    total_text = human_size(total)
    eta_text = f"{int(eta)}s" if eta < 60 else f"{int(eta / 60)}m"

    text = (
        f"📁 <b>{action}</b>\n\n"
        f"<b>Progress:</b> {percentage:.1f}%\n"
        f"📦 {done_text} / {total_text}\n"
        f"🚀 {speed_text}\n"
        f"⏱️ ETA: {eta_text}"
    )

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(safe_edit(status_message, text))
    except Exception as e:
        LOGGER.debug("Progress error: %s", e)


async def download_file(client: Client, message: Message, status_message: Message):
    start_time = time.time()
    path = await message.download(
        file_name=str(DOWNLOAD_DIR) + "/",
        progress=progress_callback,
        progress_args=(status_message, start_time, "Downloading"),
    )

    if not path or not os.path.exists(path) or os.path.getsize(path) <= 0:
        raise RuntimeError("Downloaded file is invalid or empty.")

    return path


def get_original_filename(message: Message, downloaded_path: str) -> str:
    filename = os.path.basename(downloaded_path)
    if message.document:
        filename = message.document.file_name or filename
    elif message.video:
        filename = message.video.file_name or filename
    elif message.audio:
        filename = message.audio.file_name or filename
    return filename


async def send_result(
    client: Client,
    message: Message,
    file_path: str,
    caption: str | None,
    thumbnail: str | None,
):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File to send does not exist: {file_path}")

    user_id = message.from_user.id
    config = await get_user_config(user_id)
    target_channel_id = config.get("target_channel_id")

    destinations = [message.chat.id]
    if target_channel_id:
        destinations.append(target_channel_id)

    valid_thumbnail = thumbnail if thumbnail and os.path.exists(thumbnail) else None
    extension = Path(file_path).suffix.lower()

    video_extensions = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".m4v"}
    audio_extensions = {".mp3", ".m4a", ".aac", ".flac", ".wav", ".ogg"}

    for chat_id in destinations:
        try:
            if extension in video_extensions:
                await client.send_video(
                    chat_id=chat_id,
                    video=file_path,
                    caption=caption,
                    thumb=valid_thumbnail,
                    supports_streaming=True,
                )
            elif extension in audio_extensions:
                await client.send_audio(
                    chat_id=chat_id,
                    audio=file_path,
                    caption=caption,
                )
            else:
                await client.send_document(
                    chat_id=chat_id,
                    document=file_path,
                    caption=caption,
                    thumb=valid_thumbnail,
                )
        except Exception as e:
            LOGGER.error(f"Failed to send output to chat_id {chat_id}: {e}")


async def delete_local_file(file_path: str | None):
    if not file_path:
        return
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        LOGGER.warning("Could not delete %s: %s", file_path, e)


async def process_file(client: Client, message: Message, status_message: Message):
    user_id = message.from_user.id
    downloaded_path = None
    renamed_path = None
    record_id = None

    try:
        downloaded_path = await download_file(client, message, status_message)
        record_id = await add_temporary_file(user_id=user_id, file_path=downloaded_path, seconds=300)
        original_name = get_original_filename(message, downloaded_path)

        await safe_edit(status_message, "🦋 <b>Processing file...</b>\n\n🔄 Applying formatting patterns...")

        new_name = await rename_file(user_id, original_name)
        new_name = os.path.basename(new_name)

        renamed_path = str(DOWNLOAD_DIR / new_name)

        # Only rename if output path is different from downloaded path
        if os.path.abspath(renamed_path) != os.path.abspath(downloaded_path):
            base, extension = os.path.splitext(renamed_path)
            counter = 1
            while os.path.exists(renamed_path):
                renamed_path = f"{base}_{counter}{extension}"
                counter += 1

            os.rename(downloaded_path, renamed_path)
        else:
            renamed_path = downloaded_path

        thumbnail = await get_thumbnail(user_id)
        caption = await get_caption(user_id) or f"📄 <b>{os.path.basename(renamed_path)}</b>"

        await safe_edit(status_message, f"🚀 <b>Uploading...</b>\n\n📄 <code>{os.path.basename(renamed_path)}</code>")
        await send_result(client, message, renamed_path, caption, thumbnail)

        await safe_edit(status_message, "✅ <b>File processed successfully!</b>")
        if record_id:
            await delete_temporary_file(record_id)

        await asyncio.sleep(CLEANUP_DELAY)
        try:
            await status_message.delete()
        except Exception:
            pass

    except Exception as e:
        LOGGER.exception("File processing failed: %s", e)
        try:
            await status_message.edit_text(f"❌ <b>File processing failed.</b>\n\n<code>{str(e)[:1000]}</code>")
        except Exception:
            pass
    finally:
        for path in {downloaded_path, renamed_path}:
            if path and path != downloaded_path:
                await delete_local_file(path)
        await delete_local_file(downloaded_path)
        if record_id:
            await delete_temporary_file(record_id)
