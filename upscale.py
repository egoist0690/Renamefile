import os
import logging
import asyncio

import cv2
from PIL import Image

from pyrogram import Client
from pyrogram.types import Message


LOGGER = logging.getLogger(__name__)

TEMP_DIR = "downloads"
os.makedirs(TEMP_DIR, exist_ok=True)


# ============================================================
# UPSCALE IMAGE
# ============================================================

def upscale_image_file(
    input_path: str,
    output_path: str,
    scale: int = 2
):
    """
    Upscale an image using OpenCV.
    """

    image = cv2.imread(input_path)

    if image is None:
        raise ValueError("Unable to read image.")

    height, width = image.shape[:2]

    new_width = width * scale
    new_height = height * scale

    upscaled = cv2.resize(
        image,
        (new_width, new_height),
        interpolation=cv2.INTER_CUBIC
    )

    success = cv2.imwrite(
        output_path,
        upscaled
    )

    if not success:
        raise ValueError(
            "Unable to save upscaled image."
        )

    return output_path


# ============================================================
# DELETE FILE
# ============================================================

async def delete_file(path):

    try:

        if path and os.path.exists(path):
            os.remove(path)

            LOGGER.info(
                f"Deleted temporary file: {path}"
            )

    except Exception as e:

        LOGGER.error(
            f"Cleanup error: {e}"
        )


# ============================================================
# UPSCALE COMMAND
# ============================================================

async def upscale_image(
    client: Client,
    message: Message,
    reply: Message
):

    input_path = None
    output_path = None

    try:

        status = await message.reply_text(
            "🖼️ <b>Preparing image...</b>"
        )

        # ----------------------------------------------------
        # CHECK IMAGE
        # ----------------------------------------------------

        if not reply.photo and not reply.document:

            await status.edit_text(
                "❌ Please reply to an image."
            )

            return

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        await status.edit_text(
            "📥 <b>Downloading image...</b>"
        )

        input_path = await reply.download(
            file_name=TEMP_DIR
        )

        if not input_path:
            raise ValueError(
                "Image download failed."
            )

        # ----------------------------------------------------
        # OUTPUT NAME
        # ----------------------------------------------------

        base_name = os.path.splitext(
            os.path.basename(input_path)
        )[0]

        output_path = os.path.join(
            TEMP_DIR,
            f"{base_name}_2x.jpg"
        )

        # ----------------------------------------------------
        # UPSCALE
        # ----------------------------------------------------

        await status.edit_text(
            "🚀 <b>Upscaling image 2×...</b>\n\n"
            "Please wait..."
        )

        await asyncio.to_thread(
            upscale_image_file,
            input_path,
            output_path,
            2
        )

        # ----------------------------------------------------
        # SEND
        # ----------------------------------------------------

        await status.edit_text(
            "📤 <b>Uploading enhanced image...</b>"
        )

        await client.send_photo(
            chat_id=message.chat.id,
            photo=output_path,
            caption=(
                "✨ <b>Image Upscaled 2×</b>\n\n"
                "🦋 Powered by @EGOIST6969"
            )
        )

        await status.edit_text(
            "✅ <b>Upscale completed!</b>\n\n"
            "🗑️ Temporary files will be deleted."
        )

        await asyncio.sleep(3)

    except Exception as e:

        LOGGER.exception(
            "Upscale error"
        )

        try:

            await status.edit_text(
                "❌ <b>Upscale failed.</b>\n\n"
                f"<code>{str(e)[:800]}</code>"
            )

        except Exception:
            pass

    finally:

        # ----------------------------------------------------
        # ALWAYS CLEAN FILES
        # ----------------------------------------------------

        await delete_file(
            input_path
        )

        await delete_file(
            output_path
        )
