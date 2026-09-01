import os
import logging
import asyncio

import cv2
import numpy as np

from pyrogram import Client
from pyrogram.types import Message


LOGGER = logging.getLogger(__name__)

TEMP_DIR = "downloads"
os.makedirs(TEMP_DIR, exist_ok=True)


# ============================================================
# IMAGE ENHANCEMENT
# ============================================================

def enhance_image_file(
    input_path: str,
    output_path: str
):
    """
    Enhance image quality using:
    - Noise reduction
    - Contrast improvement
    - Sharpness improvement
    - Detail enhancement
    """

    image = cv2.imread(
        input_path,
        cv2.IMREAD_COLOR
    )

    if image is None:
        raise ValueError(
            "Unable to read image."
        )

    # --------------------------------------------------------
    # 1. Denoising
    # --------------------------------------------------------

    denoised = cv2.fastNlMeansDenoisingColored(
        image,
        None,
        5,
        5,
        7,
        21
    )

    # --------------------------------------------------------
    # 2. Improve local contrast
    # --------------------------------------------------------

    lab = cv2.cvtColor(
        denoised,
        cv2.COLOR_BGR2LAB
    )

    l_channel, a_channel, b_channel = cv2.split(
        lab
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced_l = clahe.apply(
        l_channel
    )

    enhanced_lab = cv2.merge(
        (
            enhanced_l,
            a_channel,
            b_channel
        )
    )

    enhanced = cv2.cvtColor(
        enhanced_lab,
        cv2.COLOR_LAB2BGR
    )

    # --------------------------------------------------------
    # 3. Gentle sharpening
    # --------------------------------------------------------

    blurred = cv2.GaussianBlur(
        enhanced,
        (0, 0),
        1.2
    )

    sharpened = cv2.addWeighted(
        enhanced,
        1.35,
        blurred,
        -0.35,
        0
    )

    # --------------------------------------------------------
    # 4. Keep valid pixel range
    # --------------------------------------------------------

    sharpened = np.clip(
        sharpened,
        0,
        255
    ).astype(np.uint8)

    # --------------------------------------------------------
    # 5. Save high quality JPEG
    # --------------------------------------------------------

    success = cv2.imwrite(
        output_path,
        sharpened,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            95
        ]
    )

    if not success:
        raise ValueError(
            "Unable to save enhanced image."
        )

    return output_path


# ============================================================
# DELETE TEMP FILE
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
# ENHANCE COMMAND
# ============================================================

async def enhance_image(
    client: Client,
    message: Message,
    reply: Message
):

    input_path = None
    output_path = None
    status = None

    try:

        status = await message.reply_text(
            "🖼️ <b>Preparing image enhancement...</b>"
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
        # OUTPUT
        # ----------------------------------------------------

        base_name = os.path.splitext(
            os.path.basename(input_path)
        )[0]

        output_path = os.path.join(
            TEMP_DIR,
            f"{base_name}_enhanced.jpg"
        )

        # ----------------------------------------------------
        # PROCESS
        # ----------------------------------------------------

        await status.edit_text(
            "✨ <b>Enhancing image...</b>\n\n"
            "🔹 Removing noise\n"
            "🔹 Improving contrast\n"
            "🔹 Increasing sharpness\n"
            "🔹 Improving details"
        )

        await asyncio.to_thread(
            enhance_image_file,
            input_path,
            output_path
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
                "✨ <b>Image Enhanced Successfully</b>\n\n"
                "🦋 Powered by @EGOIST6969"
            )
        )

        await status.edit_text(
            "✅ <b>Enhancement completed!</b>\n\n"
            "🗑️ Cleaning temporary files..."
        )

        await asyncio.sleep(3)

    except Exception as e:

        LOGGER.exception(
            "Enhancement error"
        )

        if status:

            try:

                await status.edit_text(
                    "❌ <b>Enhancement failed.</b>\n\n"
                    f"<code>{str(e)[:800]}</code>"
                )

            except Exception:
                pass

    finally:

        # ----------------------------------------------------
        # ALWAYS DELETE TEMPORARY FILES
        # ----------------------------------------------------

        await delete_file(
            input_path
        )

        await delete_file(
            output_path
        )
