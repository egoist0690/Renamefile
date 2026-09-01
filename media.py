import os
import time
import asyncio
import logging
from pathlib import Path

from pyrogram import Client
from pyrogram.types import Message

from config import Config
from database import (
    add_temporary_file,
    delete_temporary_file,
    get_thumbnail,
    get_caption,
)
from rename import rename_file


LOGGER = logging.getLogger(__name__)


# ============================================================
# SETTINGS
# ============================================================

DOWNLOAD_DIR = "downloads"
CLEANUP_DELAY = 5

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ============================================================
# HUMAN READABLE SIZE
# ============================================================

def human_size(size: int) -> str:

    if size is None:
        return "0 B"

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB"
    ]

    value = float(size)

    for unit in units:

        if value < 1024:
            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{value:.1f} PB"


# ============================================================
# PROGRESS
# ============================================================

def progress_callback(
    current,
    total,
    status_message,
    start_time,
    action="Downloading"
):

    try:

        now = time.time()

        elapsed = max(
            now - start_time,
            0.1
        )

        percentage = current * 100 / total

        speed = current / elapsed

        remaining = total - current

        eta = (
            remaining / speed
            if speed > 0
            else 0
        )

        speed_text = human_size(
            int(speed)
        ) + "/s"

        done_text = human_size(
            current
        )

        total_text = human_size(
            total
        )

        eta_text = (
            f"{int(eta)}s"
            if eta < 60
            else f"{int(eta / 60)}m"
        )

        text = (
            f"📁 <b>{action}</b>\n\n"
            f"▰▰▰▰▰▰▰▰▰▰\n"
            f"<b>{percentage:.1f}%</b>\n\n"
            f"📦 {done_text} / {total_text}\n"
            f"🚀 {speed_text}\n"
            f"⏱️ ETA: {eta_text}"
        )

        # Pyrogram progress callback can be called very frequently.
        # Schedule the Telegram edit asynchronously.
        asyncio.create_task(
            safe_edit(
                status_message,
                text
            )
        )

    except Exception as e:

        LOGGER.debug(
            f"Progress error: {e}"
        )


# ============================================================
# SAFE MESSAGE EDIT
# ============================================================

async def safe_edit(
    message,
    text
):

    try:

        await message.edit_text(
            text
        )

    except Exception:
        pass


# ============================================================
# DOWNLOAD
# ============================================================

async def download_file(
    client: Client,
    message: Message,
    status_message: Message
):

    start_time = time.time()

    path = await message.download(
        file_name=DOWNLOAD_DIR,
        progress=progress_callback,
        progress_args=(
            status_message,
            start_time,
            "Downloading"
        )
    )

    return path


# ============================================================
# FILE SIZE CHECK
# ============================================================

def get_message_size(message: Message):

    if message.document:
        return message.document.file_size

    if message.video:
        return message.video.file_size

    if message.audio:
        return message.audio.file_size

    if message.photo:
        return message.photo.file_size

    return 0


# ============================================================
# SEND RESULT
# ============================================================

async def send_result(
    client: Client,
    message: Message,
    file_path: str,
    caption: str | None,
    thumbnail: str | None
):

    extension = Path(
        file_path
    ).suffix.lower()

    # Telegram handles these as documents/videos.
    video_extensions = {
        ".mp4",
        ".mkv",
        ".webm",
        ".avi",
        ".mov",
        ".flv",
        ".m4v",
    }

    audio_extensions = {
        ".mp3",
        ".m4a",
        ".aac",
        ".flac",
        ".wav",
        ".ogg",
    }

    if extension in video_extensions:

        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=caption,
            thumb=thumbnail,
            supports_streaming=True,
        )

    elif extension in audio_extensions:

        await client.send_audio(
            chat_id=message.chat.id,
            audio=file_path,
            caption=caption,
        )

    else:

        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption=caption,
            thumb=thumbnail,
        )


# ============================================================
# CLEAN LOCAL FILE
# ============================================================

async def delete_local_file(
    file_path: str
):

    if not file_path:
        return

    try:

        if os.path.exists(file_path):

            os.remove(file_path)

            LOGGER.info(
                f"Deleted temporary file: {file_path}"
            )

    except Exception as e:

        LOGGER.error(
            f"Could not delete {file_path}: {e}"
        )


# ============================================================
# PROCESS FILE
# ============================================================

async def process_file(
    client: Client,
    message: Message,
    status_message: Message
):

    user_id = message.from_user.id

    downloaded_path = None
    renamed_path = None
    record_id = None

    try:

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        downloaded_path = await download_file(
            client,
            message,
            status_message
        )

        if not downloaded_path:

            raise RuntimeError(
                "Download failed."
            )

        # ----------------------------------------------------
        # REGISTER TEMPORARY FILE
        # ----------------------------------------------------

        record_id = await add_temporary_file(
            user_id=user_id,
            file_path=downloaded_path,
            seconds=30
        )

        # ----------------------------------------------------
        # GET ORIGINAL NAME
        # ----------------------------------------------------

        original_name = os.path.basename(
            downloaded_path
        )

        if message.document:
            original_name = (
                message.document.file_name
                or original_name
            )

        elif message.video:
            original_name = (
                message.video.file_name
                or original_name
            )

        elif message.audio:
            original_name = (
                message.audio.file_name
                or original_name
            )

        # ----------------------------------------------------
        # RENAME
        # ----------------------------------------------------

        await status_message.edit_text(
            "🦋 <b>Processing file...</b>\n\n"
            "🔄 Detecting episode and quality..."
        )

        new_name = await rename_file(
            user_id,
            original_name
        )

        renamed_path = os.path.join(
            DOWNLOAD_DIR,
            new_name
        )

        # Avoid accidentally overwriting another file.
        counter = 1

        base, extension = os.path.splitext(
            renamed_path
        )

        while os.path.exists(
            renamed_path
        ):

            renamed_path = (
                f"{base}_{counter}{extension}"
            )

            counter += 1

        os.rename(
            downloaded_path,
            renamed_path
        )

        downloaded_path = renamed_path

        # ----------------------------------------------------
        # GET USER SETTINGS
        # ----------------------------------------------------

        thumbnail = await get_thumbnail(
            user_id
        )

        caption = await get_caption(
            user_id
        )

        # ----------------------------------------------------
        # SEND
        # ----------------------------------------------------

        await status_message.edit_text(
            "🚀 <b>Uploading...</b>\n\n"
            f"📄 <code>{os.path.basename(renamed_path)}</code>"
        )

        await send_result(
            client,
            message,
            renamed_path,
            caption,
            thumbnail
        )

        await status_message.edit_text(
            "✅ <b>File sent successfully!</b>\n\n"
            "🗑️ Cleaning temporary data..."
        )

        # ----------------------------------------------------
        # REMOVE DB RECORD
        # ----------------------------------------------------

        if record_id:

            await delete_temporary_file(
                record_id
            )

        # ----------------------------------------------------
        # WAIT A FEW SECONDS
        # ----------------------------------------------------

        await asyncio.sleep(
            CLEANUP_DELAY
        )

    except Exception as e:

        LOGGER.exception(
            "File processing failed"
        )

        try:

            await status_message.edit_text(
                "❌ <b>File processing failed.</b>\n\n"
                f"<code>{str(e)[:1000]}</code>"
            )

        except Exception:
            pass

    finally:

        # ====================================================
        # IMPORTANT:
        # ALWAYS DELETE LOCAL FILES
        # ====================================================

        files_to_delete = {
            downloaded_path,
            renamed_path,
        }

        for file_path in files_to_delete:

            if file_path:

                await delete_local_file(
                    file_path
                )

        # ====================================================
        # REMOVE TEMP DB RECORD
        # ====================================================

        if record_id:

            try:

                await delete_temporary_file(
                    record_id
                )

            except Exception as e:

                LOGGER.error(
                    f"DB cleanup error: {e}"
                )
