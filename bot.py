
# bot.py
# ============================================================
# 🦋 AUTO RENAME + UPSCALE + ENHANCE BOT
# ============================================================

import asyncio
import logging
import os

from pyrogram import Client, filters, idle
from pyrogram.errors import RPCError

from config import Config
from database import start_database

# Existing modules
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
# COMMAND REGISTRATION
# ============================================================

@app.on_message(
    filters.command("upscale") &
    filters.private
)
async def upscale_command(client, message):
    """
    /upscale

    Usage:
    Reply to an image with /upscale
    """

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

@app.on_message(
    filters.command("enhance") &
    filters.private
)
async def enhance_command(client, message):
    """
    /enhance

    Usage:
    Reply to an image with /enhance
    """

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
# FILE HANDLER
# ============================================================

@app.on_message(
    filters.document |
    filters.video |
    filters.audio
)
async def file_handler(client, message):
    """
    Automatically processes supported files.

    Files are:
        Downloaded
        Renamed
        Uploaded
        Deleted
    """

    # Ignore bot messages
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

@app.on_message(
    filters.photo
)
async def photo_handler(client, message):
    """
    Photos are not automatically renamed.
    They are handled by /upscale and /enhance.
    """

    return


# ============================================================
# START COMMAND
# ============================================================

@app.on_message(
    filters.command("start")
)
async def start_command(client, message):

    user = message.from_user

    name = (
        user.first_name
        if user
        else "User"
    )

    await message.reply_text(
        f"🦋 <b>Hello {name}!</b>\n\n"

        "Welcome to <b>RenameFile Bot</b>.\n\n"

        "📁 <b>File Renaming</b>\n"
        "Send a document, video or audio file "
        "and I'll rename it automatically.\n\n"

        "🖼️ <b>Image Tools</b>\n"
        "• /upscale — Upscale image 2×\n"
        "• /enhance — Enhance image quality\n\n"

        "⚙️ <b>Rename Settings</b>\n"
        "Use the available rename settings "
        "commands to customize your files.\n\n"

        "🦋 <b>Powered by @EGOIST6969</b>"
    )


# ============================================================
# HELP COMMAND
# ============================================================

@app.on_message(
    filters.command("help")
)
async def help_command(client, message):

    await message.reply_text(
        "🦋 <b>RenameFile Bot Help</b>\n\n"

        "📁 <b>Files</b>\n"
        "Send a document/video/audio and "
        "the bot will process it automatically.\n\n"

        "🖼️ <b>Image Commands</b>\n"
        "/upscale — Upscale an image 2×\n"
        "/enhance — Enhance image quality\n\n"

        "⚙️ <b>Other</b>\n"
        "/start — Start the bot\n"
        "/help — Show this help\n\n"

        "🦋 @EGOIST6969"
    )


# ============================================================
# ERROR HANDLER
# ============================================================

@app.on_message(
    filters.command("ping")
)
async def ping_command(client, message):

    await message.reply_text(
        "🏓 <b>Pong!</b>\n\n"
        "🟢 Bot is online."
    )


# ============================================================
# STARTUP
# ============================================================

async def startup():

    LOGGER.info("=" * 60)
    LOGGER.info("🦋 RenameFile Bot starting...")
    LOGGER.info("=" * 60)

    # Start MongoDB system
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

        # Don't immediately kill the bot.
        # Telegram functionality can still start.
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
        LOGGER.info(
            "🟢 BOT ONLINE"
        )
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
