# ============================================================
# 🦋 RENAMEFILE BOT
# AUTO RENAME + THUMBNAIL + CAPTION + UPSCALE + ENHANCE
# ============================================================

import asyncio
import logging
import os

from pyrogram import Client, filters, idle
from pyrogram.errors import RPCError

from config import Config
from database import (
    start_database,
    get_user,
    get_format,
    set_format,
    set_thumbnail,
    get_thumbnail,
    delete_thumbnail,
    set_caption,
    get_caption,
    delete_caption,
)

from media import process_file
from upscale import upscale_image
from enhance import enhance_image


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

LOGGER = logging.getLogger("RenameFileBot")


# ============================================================
# DIRECTORIES
# ============================================================

os.makedirs("downloads", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)


# ============================================================
# BOT CLIENT
# ============================================================

app = Client(
    "rename_file_bot",
    api_id=int(Config.API_ID),
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=20
)


# ============================================================
# /START
# ============================================================

@app.on_message(filters.command("start"))
async def start_command(client, message):

    user = message.from_user
    name = user.first_name if user else "User"

    await get_user(message.from_user.id)

    await message.reply_text(
        f"🦋 <b>Hello {name}!</b>\n\n"
        "Welcome to <b>RenameFile Bot</b>.\n\n"

        "📁 <b>Auto Rename</b>\n"
        "Send me a document, video or audio file.\n\n"

        "⚙️ <b>Rename Commands</b>\n"
        "• /autorename <code>format</code>\n"
        "• /format\n\n"

        "🖼️ <b>Thumbnail</b>\n"
        "• /setthumb\n"
        "• /viewthumb\n"
        "• /delthumb\n\n"

        "📝 <b>Caption</b>\n"
        "• /set_caption <code>text</code>\n"
        "• /see_caption\n"
        "• /del_caption\n\n"

        "✨ <b>Image Tools</b>\n"
        "• /upscale\n"
        "• /enhance\n\n"

        "🏓 /ping\n"
        "❓ /help\n\n"

        "🦋 <b>Powered by @EGOIST6969</b>"
    )


# ============================================================
# /HELP
# ============================================================

@app.on_message(filters.command("help"))
async def help_command(client, message):

    await message.reply_text(
        "🦋 <b>RenameFile Bot Help</b>\n\n"

        "📁 <b>FILE RENAME</b>\n"
        "Send a document/video/audio and it will be renamed automatically.\n\n"

        "⚙️ <b>RENAME SETTINGS</b>\n"
        "/autorename <code>format</code>\n"
        "/format\n\n"

        "Example:\n"
        "<code>/autorename Naruto S02 - EPepisode - quality</code>\n\n"

        "Available keywords:\n"
        "• <code>episode</code> → episode number\n"
        "• <code>quality</code> → detected quality\n\n"

        "🖼️ <b>THUMBNAIL</b>\n"
        "Reply to a photo with /setthumb\n"
        "/viewthumb\n"
        "/delthumb\n\n"

        "📝 <b>CAPTION</b>\n"
        "/set_caption Your caption\n"
        "/see_caption\n"
        "/del_caption\n\n"

        "✨ <b>IMAGE</b>\n"
        "Reply to an image:\n"
        "/upscale\n"
        "/enhance\n\n"

        "🏓 /ping\n\n"

        "🦋 @EGOIST6969"
    )


# ============================================================
# /PING
# ============================================================

@app.on_message(filters.command("ping"))
async def ping_command(client, message):

    await message.reply_text(
        "🏓 <b>Pong!</b>\n\n"
        "🟢 Bot is online."
    )


# ============================================================
# /AUTORENAME
# ============================================================

@app.on_message(filters.command("autorename"))
async def autorename_command(client, message):

    user_id = message.from_user.id

    if len(message.command) < 2:
        current = await get_format(user_id)

        await message.reply_text(
            "⚙️ <b>Auto Rename Format</b>\n\n"
            "Usage:\n"
            "<code>/autorename Your Format</code>\n\n"

            "Keywords:\n"
            "• <code>episode</code>\n"
            "• <code>quality</code>\n\n"

            f"📌 <b>Current format:</b>\n"
            f"<code>{current}</code>"
        )
        return

    new_format = message.text.split(None, 1)[1].strip()

    if not new_format:
        await message.reply_text(
            "❌ Please provide a rename format."
        )
        return

    if len(new_format) > 200:
        await message.reply_text(
            "❌ Format is too long. Maximum 200 characters."
        )
        return

    await set_format(user_id, new_format)

    await message.reply_text(
        "✅ <b>Auto rename format updated!</b>\n\n"
        f"📁 <code>{new_format}</code>\n\n"
        "Send a file to test it."
    )


# ============================================================
# /FORMAT
# ============================================================

@app.on_message(filters.command("format"))
async def format_command(client, message):

    user_id = message.from_user.id
    current = await get_format(user_id)

    await message.reply_text(
        "🦋 <b>Your Current Rename Format</b>\n\n"
        f"<code>{current}</code>\n\n"

        "📝 Change it with:\n"
        "<code>/autorename Your Format</code>\n\n"

        "Available keywords:\n"
        "• <code>episode</code>\n"
        "• <code>quality</code>"
    )


# ============================================================
# /SETTHUMB
# ============================================================

@app.on_message(filters.command("setthumb"))
async def setthumb_command(client, message):

    user_id = message.from_user.id
    reply = message.reply_to_message

    if not reply or not reply.photo:
        await message.reply_text(
            "🖼️ <b>Usage:</b>\n\n"
            "Send a photo and reply to it with /setthumb."
        )
        return

    try:

        path = await reply.download(
            file_name=f"thumbnails/{user_id}.jpg"
        )

        await set_thumbnail(
            user_id,
            path
        )

        await message.reply_text(
            "✅ <b>Thumbnail saved successfully!</b>\n\n"
            "Your future renamed files will use this thumbnail."
        )

    except Exception as e:

        LOGGER.exception("Thumbnail error")

        await message.reply_text(
            "❌ Failed to save thumbnail.\n\n"
            f"<code>{str(e)[:500]}</code>"
        )


# ============================================================
# /VIEWTHUMB
# ============================================================

@app.on_message(filters.command("viewthumb"))
async def viewthumb_command(client, message):

    user_id = message.from_user.id

    thumbnail = await get_thumbnail(user_id)

    if not thumbnail or not os.path.exists(thumbnail):

        await message.reply_text(
            "❌ <b>No thumbnail is set.</b>\n\n"
            "Reply to a photo with /setthumb."
        )
        return

    try:

        await client.send_photo(
            chat_id=message.chat.id,
            photo=thumbnail,
            caption="🖼️ <b>Your current thumbnail</b>"
        )

    except Exception as e:

        await message.reply_text(
            f"❌ Could not send thumbnail:\n<code>{str(e)[:500]}</code>"
        )


# ============================================================
# /DELTHUMB
# ============================================================

@app.on_message(filters.command("delthumb"))
async def delthumb_command(client, message):

    user_id = message.from_user.id

    thumbnail = await get_thumbnail(user_id)

    if thumbnail and os.path.exists(thumbnail):

        try:
            os.remove(thumbnail)
        except Exception:
            pass

    await delete_thumbnail(user_id)

    await message.reply_text(
        "🗑️ <b>Thumbnail deleted.</b>"
    )


# ============================================================
# /SET_CAPTION
# ============================================================

@app.on_message(filters.command("set_caption"))
async def setcaption_command(client, message):

    user_id = message.from_user.id

    if len(message.command) < 2:

        await message.reply_text(
            "📝 <b>Usage:</b>\n\n"
            "<code>/set_caption Your caption here</code>"
        )
        return

    caption = message.text.split(None, 1)[1].strip()

    if len(caption) > 1000:

        await message.reply_text(
            "❌ Caption is too long. Maximum 1000 characters."
        )
        return

    await set_caption(
        user_id,
        caption
    )

    await message.reply_text(
        "✅ <b>Caption saved!</b>\n\n"
        f"{caption}"
    )


# ============================================================
# /SEE_CAPTION
# ============================================================

@app.on_message(filters.command("see_caption"))
async def seecaption_command(client, message):

    user_id = message.from_user.id

    caption = await get_caption(user_id)

    if not caption:

        await message.reply_text(
            "❌ <b>No caption is set.</b>"
        )
        return

    await message.reply_text(
        "📝 <b>Current Caption:</b>\n\n"
        f"{caption}"
    )


# ============================================================
# /DEL_CAPTION
# ============================================================

@app.on_message(filters.command("del_caption"))
async def delcaption_command(client, message):

    user_id = message.from_user.id

    await delete_caption(user_id)

    await message.reply_text(
        "🗑️ <b>Caption deleted.</b>"
    )


# ============================================================
# /UPSCALE
# ============================================================

@app.on_message(
    filters.command("upscale") &
    filters.private
)
async def upscale_command(client, message):

    reply = message.reply_to_message

    if not reply:

        await message.reply_text(
            "🖼️ <b>Reply to an image with /upscale</b>"
        )
        return

    await upscale_image(
        client,
        message,
        reply
    )


# ============================================================
# /ENHANCE
# ============================================================

@app.on_message(
    filters.command("enhance") &
    filters.private
)
async def enhance_command(client, message):

    reply = message.reply_to_message

    if not reply:

        await message.reply_text(
            "✨ <b>Reply to an image with /enhance</b>"
        )
        return

    await enhance_image(
        client,
        message,
        reply
    )


# ============================================================
# AUTOMATIC FILE HANDLER
# ============================================================

@app.on_message(
    filters.document |
    filters.video |
    filters.audio
)
async def file_handler(client, message):

    if message.from_user and message.from_user.is_bot:
        return

    status = await message.reply_text(
        "📥 <b>File received...</b>\n\n"
        "Preparing your file..."
    )

    await process_file(
        client,
        message,
        status
    )


# ============================================================
# PHOTO HANDLER
# ============================================================

@app.on_message(filters.photo)
async def photo_handler(client, message):

    # Photos are handled by /setthumb,
    # /upscale and /enhance.
    return


# ============================================================
# START DATABASE
# ============================================================

async def startup():

    LOGGER.info("=" * 60)
    LOGGER.info("🦋 RenameFile Bot starting...")
    LOGGER.info("=" * 60)

    try:

        await start_database()

        LOGGER.info(
            "✅ MongoDB system started."
        )

    except Exception as error:

        LOGGER.exception(
            "❌ MongoDB startup failed: %s",
            error
        )

        LOGGER.warning(
            "⚠️ Continuing without database startup."
        )


# ============================================================
# MAIN
# ============================================================

async def main():

    try:

        await app.start()

        await startup()

        me = await app.get_me()

        LOGGER.info("=" * 60)
        LOGGER.info("🟢 BOT ONLINE")
        LOGGER.info(
            "Username: @%s",
            me.username
        )
        LOGGER.info(
            "Bot ID: %s",
            me.id
        )
        LOGGER.info("=" * 60)

        await idle()

    except RPCError as error:

        LOGGER.exception(
            "❌ Telegram error: %s",
            error
        )

    except Exception as error:

        LOGGER.exception(
            "❌ Fatal bot error: %s",
            error
        )

    finally:

        try:
            await app.stop()
        except Exception:
            pass

        LOGGER.info(
            "🔴 Bot stopped."
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        LOGGER.info(
            "Bot stopped manually."
        )
