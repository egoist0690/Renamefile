# media.py
# ============================================================
# EGOIST6969 RENAME BOT - MEDIA PROCESSOR
# Download -> Rename -> Caption -> Thumbnail -> Send -> Cleanup
# ============================================================

import asyncio
import logging
import os
import time
from pathlib import Path

from pyrogram import enums
from pyrogram.types import Message

from config import Config
from database import get_format, get_thumbnail, get_caption
from rename import rename_file


LOGGER = logging.getLogger("EGOIST6969.MEDIA")

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"

DOWNLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# SAFE DELETE
# ============================================================

def safe_delete(path):

    if not path:
        return

    try:

        file_path = Path(path)

        if file_path.exists():
            file_path.unlink()

    except Exception as e:

        LOGGER.warning(
            "Could not delete %s: %s",
            path,
            e,
        )


# ============================================================
# GET FILE INFORMATION
# ============================================================

def get_message_file(message: Message):

    if message.document:
        return (
            message.document.file_name
            or f"document_{message.id}",
            message.document.file_size or 0,
        )

    if message.video:
        return (
            message.video.file_name
            or f"video_{message.id}.mp4",
            message.video.file_size or 0,
        )

    if message.audio:
        return (
            message.audio.file_name
            or f"audio_{message.id}",
            message.audio.file_size or 0,
        )

    return (
        f"file_{message.id}",
        0,
    )


# ============================================================
# DOWNLOAD
# ============================================================

async def download_file(
    message: Message,
    destination: str,
):

    LOGGER.info(
        "Downloading file: %s",
        destination,
    )

    downloaded = await message.download(
        file_name=destination
    )

    if not downloaded:

        raise RuntimeError(
            "Telegram returned an empty download path."
        )

    downloaded_path = Path(
        downloaded
    )

    if not downloaded_path.exists():

        raise FileNotFoundError(
            f"Downloaded file does not exist: {downloaded}"
        )

    if downloaded_path.stat().st_size == 0:

        raise RuntimeError(
            "Downloaded file is empty."
        )

    LOGGER.info(
        "Download complete: %s",
        downloaded_path,
    )

    return str(downloaded_path)


# ============================================================
# PROCESS FILE
# ============================================================

async def process_file(
    client,
    message: Message,
    status_message=None,
):

    user_id = message.from_user.id

    original_path = None
    renamed_path = None

    try:

        # ----------------------------------------------------
        # FILE INFO
        # ----------------------------------------------------

        original_name, file_size = get_message_file(
            message
        )

        LOGGER.info(
            "Processing user=%s file=%s size=%s",
            user_id,
            original_name,
            file_size,
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if status_message:

            try:

                await status_message.edit_text(
                    "📥 <b>Downloading file...</b>\n\n"
                    f"📄 <code>{original_name}</code>"
                )

            except Exception:
                pass

        # ----------------------------------------------------
        # UNIQUE TEMP NAME
        # ----------------------------------------------------

        timestamp = int(
            time.time() * 1000
        )

        safe_name = (
            original_name
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
        )

        temp_name = (
            f"{user_id}_{timestamp}_{safe_name}"
        )

        original_path = str(
            DOWNLOAD_DIR / temp_name
        )

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        original_path = await download_file(
            message,
            original_path
        )

        # ----------------------------------------------------
        # GET USER SETTINGS
        # ----------------------------------------------------

        rename_format = await get_format(
            user_id
        )

        thumbnail = await get_thumbnail(
            user_id
        )

        caption = await get_caption(
            user_id
        )

        # ----------------------------------------------------
        # RENAME
        # ----------------------------------------------------

        if status_message:

            try:

                await status_message.edit_text(
                    "⚙️ <b>Processing file...</b>\n\n"
                    "🔄 Applying rename format..."
                )

            except Exception:
                pass

        LOGGER.info(
            "Rename format for user %s: %s",
            user_id,
            rename_format,
        )

        renamed_path = await rename_file(
            original_path,
            rename_format,
        )

        # ----------------------------------------------------
        # VALIDATE RENAMED FILE
        # ----------------------------------------------------

        if not renamed_path:

            raise RuntimeError(
                "rename_file() returned no file."
            )

        renamed_path = str(
            renamed_path
        )

        renamed_file = Path(
            renamed_path
        )

        if not renamed_file.exists():

            raise FileNotFoundError(
                f"Renamed file does not exist: {renamed_path}"
            )

        if renamed_file.stat().st_size == 0:

            raise RuntimeError(
                "Renamed file is empty."
            )

        LOGGER.info(
            "Renamed file ready: %s",
            renamed_path,
        )

        # ----------------------------------------------------
        # FINAL FILENAME
        # ----------------------------------------------------

        final_filename = renamed_file.name

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if status_message:

            try:

                await status_message.edit_text(
                    "📤 <b>Uploading...</b>\n\n"
                    f"📄 <code>{final_filename}</code>"
                )

            except Exception:
                pass

        # ----------------------------------------------------
        # CAPTION
        # ----------------------------------------------------

        if not caption:

            caption = (
                f"📄 <b>{final_filename}</b>"
            )

        # ----------------------------------------------------
        # THUMBNAIL VALIDATION
        # ----------------------------------------------------

        valid_thumbnail = None

        if thumbnail:

            thumbnail_path = Path(
                thumbnail
            )

            if thumbnail_path.exists():

                valid_thumbnail = str(
                    thumbnail_path
                )

            else:

                LOGGER.warning(
                    "Thumbnail does not exist: %s",
                    thumbnail
                )

        # ----------------------------------------------------
        # SEND FILE
        # ----------------------------------------------------

        sent_message = None

        # VIDEO
        if message.video:

            sent_message = await client.send_video(
                chat_id=message.chat.id,
                video=renamed_path,
                caption=caption,
                thumb=valid_thumbnail,
                supports_streaming=True,
                parse_mode=enums.ParseMode.HTML,
            )

        # AUDIO
        elif message.audio:

            sent_message = await client.send_audio(
                chat_id=message.chat.id,
                audio=renamed_path,
                caption=caption,
                thumb=valid_thumbnail,
                parse_mode=enums.ParseMode.HTML,
            )

        # DOCUMENT / PDF / ZIP / APK / ETC.
        else:

            sent_message = await client.send_document(
                chat_id=message.chat.id,
                document=renamed_path,
                thumb=valid_thumbnail,
                caption=caption,
                parse_mode=enums.ParseMode.HTML,
                force_document=True,
            )

        # ----------------------------------------------------
        # VERIFY SEND
        # ----------------------------------------------------

        if not sent_message:

            raise RuntimeError(
                "Telegram did not return the sent message."
            )

        LOGGER.info(
            "File successfully sent: %s",
            final_filename,
        )

        # ----------------------------------------------------
        # DELETE STATUS MESSAGE
        # ----------------------------------------------------

        if status_message:

            try:
                await status_message.delete()

            except Exception:
                pass

        return sent_message

    # ========================================================
    # ERRORS
    # ========================================================

    except Exception as e:

        LOGGER.exception(
            "Media processing failed: %s",
            e,
        )

        if status_message:

            try:

                await status_message.edit_text(
                    "❌ <b>File processing failed.</b>\n\n"
                    f"<code>{str(e)[:1000]}</code>"
                )

            except Exception:
                pass

        return None

    # ========================================================
    # CLEANUP
    # ========================================================

    finally:

        # Never leave downloaded/renamed files behind.
        if original_path:
            safe_delete(
                original_path
            )

        if (
            renamed_path
            and renamed_path != original_path
        ):
            safe_delete(
                renamed_path
            )

        LOGGER.info(
            "Temporary files cleaned."
        )


# ============================================================
# CLEAN OLD DOWNLOADS
# ============================================================

async def cleanup_old_files(
    max_age=300
):

    while True:

        try:

            now = time.time()

            for file in DOWNLOAD_DIR.iterdir():

                if not file.is_file():
                    continue

                try:

                    age = (
                        now -
                        file.stat().st_mtime
                    )

                    if age > max_age:

                        safe_delete(
                            str(file)
                        )

                        LOGGER.info(
                            "Old file removed: %s",
                            file
                        )

                except Exception:
                    continue

        except Exception as e:

            LOGGER.warning(
                "Cleanup worker error: %s",
                e
            )

        await asyncio.sleep(
            60
        )
