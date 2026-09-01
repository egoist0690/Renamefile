import asyncio
import logging
import os

from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config, Txt

# Feature modules
from database import (
    get_user,
    set_format,
    set_thumbnail,
    get_thumbnail,
    delete_thumbnail,
    set_caption,
    get_caption,
    delete_caption,
)

from rename import rename_file
from media import process_file
from upscale import upscale_image
from enhance import enhance_image


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

LOGGER = logging.getLogger(__name__)


# ============================================================
# BOT
# ============================================================

app = Client(
    "EgoistRenameBot",
    api_id=int(Config.API_ID),
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
)


# ============================================================
# START
# ============================================================

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):

    user = message.from_user

    if not user:
        return

    await get_user(user.id)

    name = user.first_name or "User"

    try:
        await message.reply_text(
            Txt.START_TXT.format(name),
            disable_web_page_preview=True
        )
    except Exception as e:
        LOGGER.error(f"Start error: {e}")


# ============================================================
# HELP
# ============================================================

@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):

    name = message.from_user.first_name if message.from_user else "User"

    await message.reply_text(
        Txt.HELP_TXT.format(name),
        disable_web_page_preview=True
    )


# ============================================================
# FORMAT
# ============================================================

@app.on_message(filters.command(["format", "autorename"]))
async def format_command(client: Client, message: Message):

    user_id = message.from_user.id

    text = message.text or ""

    parts = text.split(maxsplit=1)

    if len(parts) == 1:
        user = await get_user(user_id)

        current_format = user.get(
            "format",
            "Episode episode - quality"
        )

        await message.reply_text(
            Txt.FILE_NAME_TXT.format(
                format_template=current_format
            )
        )
        return

    new_format = parts[1].strip()

    if not new_format:
        await message.reply_text(
            "❌ Please provide a rename format."
        )
        return

    await set_format(user_id, new_format)

    await message.reply_text(
        "✅ <b>Rename format updated!</b>\n\n"
        f"<code>{new_format}</code>"
    )


# ============================================================
# SET THUMBNAIL
# ============================================================

@app.on_message(filters.command(["setthumb", "setthumbnail"]))
async def setthumb_command(client: Client, message: Message):

    if not message.reply_to_message:
        await message.reply_text(
            "🖼️ Reply to a photo with <code>/setthumb</code>."
        )
        return

    reply = message.reply_to_message

    if not reply.photo:
        await message.reply_text(
            "❌ Please reply to a photo."
        )
        return

    try:
        file = await reply.download()

        await set_thumbnail(
            message.from_user.id,
            file
        )

        if os.path.exists(file):
            os.remove(file)

        await message.reply_text(
            "✅ <b>Thumbnail saved!</b>"
        )

    except Exception as e:

        LOGGER.error(f"Thumbnail error: {e}")

        await message.reply_text(
            "❌ Failed to save thumbnail."
        )


# ============================================================
# VIEW THUMBNAIL
# ============================================================

@app.on_message(filters.command("viewthumb"))
async def viewthumb_command(client: Client, message: Message):

    thumb = await get_thumbnail(message.from_user.id)

    if not thumb:
        await message.reply_text(
            "❌ You don't have a thumbnail set."
        )
        return

    try:
        await message.reply_photo(
            thumb,
            caption="🖼️ Your current thumbnail."
        )

    except Exception as e:

        LOGGER.error(f"View thumbnail error: {e}")

        await message.reply_text(
            "❌ Unable to display thumbnail."
        )


# ============================================================
# DELETE THUMBNAIL
# ============================================================

@app.on_message(filters.command(["delthumb", "delthumbnail"]))
async def delthumb_command(client: Client, message: Message):

    await delete_thumbnail(message.from_user.id)

    await message.reply_text(
        "🗑️ <b>Thumbnail deleted.</b>"
    )


# ============================================================
# SET CAPTION
# ============================================================

@app.on_message(filters.command(["setcaption", "set_caption"]))
async def setcaption_command(client: Client, message: Message):

    parts = (message.text or "").split(maxsplit=1)

    if len(parts) == 1:
        await message.reply_text(
            "❌ Usage:\n"
            "<code>/setcaption Your caption here</code>"
        )
        return

    caption = parts[1].strip()

    await set_caption(
        message.from_user.id,
        caption
    )

    await message.reply_text(
        "✅ <b>Caption saved!</b>"
    )


# ============================================================
# VIEW CAPTION
# ============================================================

@app.on_message(filters.command(["seecaption", "see_caption"]))
async def seecaption_command(client: Client, message: Message):

    caption = await get_caption(message.from_user.id)

    if not caption:
        await message.reply_text(
            "❌ No custom caption is set."
        )
        return

    await message.reply_text(
        "📝 <b>Your current caption:</b>\n\n"
        f"{caption}"
    )


# ============================================================
# DELETE CAPTION
# ============================================================

@app.on_message(filters.command(["delcaption", "del_caption"]))
async def delcaption_command(client: Client, message: Message):

    await delete_caption(message.from_user.id)

    await message.reply_text(
        "🗑️ <b>Caption deleted.</b>"
    )


# ============================================================
# UPSCALE
# ============================================================

@app.on_message(filters.command("upscale"))
async def upscale_command(client: Client, message: Message):

    if not message.reply_to_message:
        await message.reply_text(
            "🖼️ Reply to an image with <code>/upscale</code>."
        )
        return

    await upscale_image(
        client,
        message,
        message.reply_to_message
    )


# ============================================================
# ENHANCE
# ============================================================

@app.on_message(filters.command("enhance"))
async def enhance_command(client: Client, message: Message):

    if not message.reply_to_message:
        await message.reply_text(
            "🖼️ Reply to an image with <code>/enhance</code>."
        )
        return

    await enhance_image(
        client,
        message,
        message.reply_to_message
    )


# ============================================================
# AUTOMATIC FILE PROCESSING
# ============================================================

@app.on_message(
    filters.private
    & (
        filters.document
        | filters.video
        | filters.audio
    )
    & ~filters.command(
        [
            "start",
            "help",
            "format",
            "autorename",
            "setthumb",
            "setthumbnail",
            "viewthumb",
            "delthumb",
            "delthumbnail",
            "setcaption",
            "set_caption",
            "seecaption",
            "see_caption",
            "delcaption",
            "del_caption",
            "upscale",
            "enhance",
        ]
    )
)
async def file_handler(client: Client, message: Message):

    try:

        status = await message.reply_text(
            "📥 <b>Downloading...</b>"
        )

        await process_file(
            client,
            message,
            status
        )

    except Exception as e:

        LOGGER.exception("File processing error")

        try:
            await status.edit_text(
                "❌ <b>Something went wrong.</b>\n\n"
                f"<code>{e}</code>"
            )
        except Exception:
            await message.reply_text(
                "❌ Something went wrong while processing the file."
            )


# ============================================================
# START BOT
# ============================================================

async def main():

    LOGGER.info("Starting Egoist Rename Bot...")

    await app.start()

    me = await app.get_me()

    LOGGER.info(
        f"Bot started successfully: @{me.username}"
    )

    await asyncio.Event().wait()


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        LOGGER.info("Bot stopped.")

    except Exception:
        LOGGER.exception("Bot crashed.")
