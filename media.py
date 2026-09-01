# ============================================================
# EGOIST6969 RENAME BOT
# media.py
#
# Download -> Rename -> Thumbnail/Caption -> Upload -> Cleanup
# ============================================================

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
)

from rename import rename_file


# ============================================================
# LOGGER
# ============================================================

LOGGER = logging.getLogger("EGOIST6969.MEDIA")


# ============================================================
# SETTINGS
# ============================================================

DOWNLOAD_DIR = Path("downloads")
CLEANUP_DELAY = 5

DOWNLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# HUMAN READABLE SIZE
# ============================================================

def human_size(size: int) -> str:

    if not size:
        return "0 B"

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    ]

    value = float(size)

    for unit in units:

        if value < 1024:

            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{value:.1f} PB"


# ============================================================
# SAFE MESSAGE EDIT
# ============================================================

async def safe_edit(
    message,
    text,
):

    if not message:
        return

    try:

        await message.edit_text(
            text
        )

    except Exception:

        pass


# ============================================================
# PROGRESS CALLBACK
# ============================================================

def progress_callback(
    current,
    total,
    status_message,
    start_time,
    action="Downloading",
):

    try:

        if not total:
            return

        now = time.time()

        elapsed = max(
            now - start_time,
            0.1,
        )

        percentage = (
            current * 100 / total
        )

        speed = (
            current / elapsed
        )

        remaining = (
            total - current
        )

        eta = (
            remaining / speed
            if speed > 0
            else 0
        )

        speed_text = (
            human_size(
                int(speed)
            )
            + "/s"
        )

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

        # Pyrogram calls this very frequently.
        # Schedule the edit instead of blocking download.
        asyncio.create_task(
            safe_edit(
                status_message,
                text,
            )
        )

    except Exception as e:

        LOGGER.debug(
            "Progress error: %s",
            e,
        )


# ============================================================
# DOWNLOAD
# ============================================================

async def download_file(
    client: Client,
    message: Message,
    status_message: Message,
):

    start_time = time.time()

    LOGGER.info(
        "Downloading file from user %s",
        message.from_user.id,
    )

    path = await message.download(
        file_name=str(
            DOWNLOAD_DIR
        ),
        progress=progress_callback,
        progress_args=(
            status_message,
            start_time,
            "Downloading",
        ),
    )

    if not path:

        raise RuntimeError(
            "Telegram download returned no path."
        )

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"Downloaded file not found: {path}"
        )

    if os.path.getsize(path) <= 0:

        raise RuntimeError(
            "Downloaded file is empty."
        )

    LOGGER.info(
        "Download complete: %s",
        path,
    )

    return path


# ============================================================
# ORIGINAL FILE NAME
# ============================================================

def get_original_filename(
    message: Message,
    downloaded_path: str,
) -> str:

    filename = os.path.basename(
        downloaded_path
    )

    if message.document:

        filename = (
            message.document.file_name
            or filename
        )

    elif message.video:

        filename = (
            message.video.file_name
            or filename
        )

    elif message.audio:

        filename = (
            message.audio.file_name
            or filename
        )

    return filename


# ============================================================
# SEND RESULT
# ============================================================

async def send_result(
    client: Client,
    message: Message,
    file_path: str,
    caption: str | None,
    thumbnail: str | None,
):

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"File to send does not exist: {file_path}"
        )

    extension = Path(
        file_path
    ).suffix.lower()

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

    # --------------------------------------------------------
    # VALIDATE THUMBNAIL
    # --------------------------------------------------------

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
                "Thumbnail not found: %s",
                thumbnail,
            )

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    if extension in video_extensions:

        LOGGER.info(
            "Sending video: %s",
            file_path,
        )

        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=caption,
            thumb=valid_thumbnail,
            supports_streaming=True,
        )

    # --------------------------------------------------------
    # AUDIO
    # --------------------------------------------------------

    elif extension in audio_extensions:

        LOGGER.info(
            "Sending audio: %s",
            file_path,
        )

        await client.send_audio(
            chat_id=message.chat.id,
            audio=file_path,
            caption=caption,
        )

    # --------------------------------------------------------
    # DOCUMENT
    # PDF / ZIP / RAR / APK / TXT / ETC.
    # --------------------------------------------------------

    else:

        LOGGER.info(
            "Sending document: %s",
            file_path,
        )

        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption=caption,
            thumb=valid_thumbnail,
        )


# ============================================================
# DELETE LOCAL FILE
# ============================================================

async def delete_local_file(
    file_path: str | None,
):

    if not file_path:
        return

    try:

        if os.path.exists(file_path):

            os.remove(
                file_path
            )

            LOGGER.info(
                "Deleted temporary file: %s",
                file_path,
            )

    except Exception as e:

        LOGGER.warning(
            "Could not delete %s: %s",
            file_path,
            e,
        )


# ============================================================
# PROCESS FILE
# ============================================================

async def process_file(
    client: Client,
    message: Message,
    status_message: Message,
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
            status_message,
        )

        # ----------------------------------------------------
        # DATABASE TEMP RECORD
        # ----------------------------------------------------

        record_id = await add_temporary_file(
            user_id=user_id,
            file_path=downloaded_path,
            seconds=300,
        )

        # ----------------------------------------------------
        # ORIGINAL NAME
        # ----------------------------------------------------

        original_name = get_original_filename(
            message,
            downloaded_path,
        )

        LOGGER.info(
            "Original filename: %s",
            original_name,
        )

        # ----------------------------------------------------
        # RENAME
        #
        # IMPORTANT:
        # Current rename.py expects:
        # rename_file(user_id, original_filename)
        #
        # It returns the new filename.
        # ----------------------------------------------------

        await safe_edit(
            status_message,
            "🦋 <b>Processing file...</b>\n\n"
            "🔄 Detecting episode and quality...",
        )

        new_name = await rename_file(
            user_id,
            original_name,
        )

        if not new_name:

            raise RuntimeError(
                "Rename function returned an empty filename."
            )

        # ----------------------------------------------------
        # SANITY CHECK
        # ----------------------------------------------------

        new_name = os.path.basename(
            new_name
        )

        if not new_name:

            raise RuntimeError(
                "Invalid renamed filename."
            )

        LOGGER.info(
            "Rename result: %s -> %s",
            original_name,
            new_name,
        )

        # ----------------------------------------------------
        # CREATE NEW PATH
        # ----------------------------------------------------

        renamed_path = str(
            DOWNLOAD_DIR / new_name
        )

        # ----------------------------------------------------
        # DON'T OVERWRITE EXISTING FILE
        # ----------------------------------------------------

        if os.path.abspath(
            renamed_path
        ) != os.path.abspath(
            downloaded_path
        ):

            base, extension = os.path.splitext(
                renamed_path
            )

            counter = 1

            while os.path.exists(
                renamed_path
            ):

                renamed_path = (
                    f"{base}_{counter}{extension}"
                )

                counter += 1

            os.rename(
                downloaded_path,
                renamed_path,
            )

            downloaded_path = renamed_path

        else:

            renamed_path = downloaded_path

        # ----------------------------------------------------
        # VERIFY RENAMED FILE
        # ----------------------------------------------------

        if not os.path.exists(
            renamed_path
        ):

            raise FileNotFoundError(
                "Renamed file was not created."
            )

        if os.path.getsize(
            renamed_path
        ) <= 0:

            raise RuntimeError(
                "Renamed file is empty."
            )

        # ----------------------------------------------------
        # USER SETTINGS
        # ----------------------------------------------------

        thumbnail = await get_thumbnail(
            user_id
        )

        caption = await get_caption(
            user_id
        )

        # ----------------------------------------------------
        # DEFAULT CAPTION
        # ----------------------------------------------------

        if not caption:

            caption = (
                f"📄 <b>{os.path.basename(renamed_path)}</b>"
            )

        # ----------------------------------------------------
        # UPLOAD
        # ----------------------------------------------------

        await safe_edit(
            status_message,
            "🚀 <b>Uploading...</b>\n\n"
            f"📄 <code>{os.path.basename(renamed_path)}</code>",
        )

        await send_result(
            client,
            message,
            renamed_path,
            caption,
            thumbnail,
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        LOGGER.info(
            "File sent successfully: %s",
            renamed_path,
        )

        await safe_edit(
            status_message,
            "✅ <b>File sent successfully!</b>\n\n"
            "🗑️ Cleaning temporary files...",
        )

        # ----------------------------------------------------
        # DELETE DB RECORD
        # ----------------------------------------------------

        if record_id:

            try:

                await delete_temporary_file(
                    record_id
                )

            except Exception as e:

                LOGGER.warning(
                    "Database cleanup failed: %s",
                    e,
                )

        # ----------------------------------------------------
        # SHORT DELAY
        # ----------------------------------------------------

        await asyncio.sleep(
            CLEANUP_DELAY
        )

        # ----------------------------------------------------
        # REMOVE STATUS MESSAGE
        # ----------------------------------------------------

        try:

            await status_message.delete()

        except Exception:

            pass

    except Exception as e:

        LOGGER.exception(
            "File processing failed: %s",
            e,
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
        # ALWAYS CLEAN LOCAL FILES
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
        # ALWAYS CLEAN DATABASE RECORD
        # ====================================================

        if record_id:

            try:

                await delete_temporary_file(
                    record_id
                )

            except Exception as e:

                LOGGER.warning(
                    "Final DB cleanup failed: %s",
                    e,
                )


# ============================================================
# OLD FILE CLEANUP WORKER
# ============================================================

async def cleanup_old_files(
    max_age: int = 600,
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

                        await delete_local_file(
                            str(file)
                        )

                except Exception:

                    continue

        except Exception as e:

            LOGGER.warning(
                "Cleanup worker error: %s",
                e,
            )

        await asyncio.sleep(
            60
        )
