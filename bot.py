# bot.py
# ============================================================
# EGOIST6969 - ADVANCED TELEGRAM RENAME BOT
# Rename + Thumbnail + Caption + Upscale + Enhance
# ============================================================

import asyncio
import logging
from pathlib import Path

from pyrogram import Client, filters, idle
from pyrogram.errors import RPCError

from config import Config, Txt

from database import (
    start_database,
    get_user,
    set_format,
    get_format,
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
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

LOGGER = logging.getLogger("EGOIST6969")


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"

DOWNLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# PYROGRAM CLIENT
# ============================================================

app = Client(
    "egoist_rename_bot",
    api_id=int(Config.API_ID),
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=20,
)


# ============================================================
# START
# ============================================================

@app.on_message(filters.command("start"))
async def start_handler(client, message):

    try:
        user = message.from_user

        if not user:
            return

        await get_user(user.id)

        name = user.first_name or "User"

        await message.reply_text(
            Txt.START_TXT.format(name),
            disable_web_page_preview=True,
        )

    except Exception as e:

        LOGGER.exception("Start error: %s", e)

        await message.reply_text(
            "❌ Something went wrong while starting the bot."
        )


# ============================================================
# HELP
# ============================================================

@app.on_message(filters.command("help"))
async def help_handler(client, message):

    await message.reply_text(
        """
<b>🦋 EGOIST6969 RENAME BOT</b>

<b>📁 FILE</b>
Send me a document, video or audio and I will process it.

<b>📝 RENAME</b>
<code>/autorename Your Name episode quality</code>

<b>🖼 THUMBNAIL</b>
<code>/setthumb</code>
<code>/viewthumb</code>
<code>/delthumb</code>

<b>✏️ CAPTION</b>
<code>/set_caption Your caption</code>
<code>/see_caption</code>
<code>/del_caption</code>

<b>✨ IMAGE TOOLS</b>
Reply to an image:
<code>/upscale</code>
<code>/enhance</code>

<b>ℹ️ OTHER</b>
<code>/about</code>
<code>/ping</code>

━━━━━━━━━━━━━━━━━━

<b>🦋 Developer:</b> @EGOIST6969
""",
        disable_web_page_preview=True,
    )


# ============================================================
# ABOUT
# ============================================================

@app.on_message(filters.command("about"))
async def about_handler(client, message):

    await message.reply_text(
        Txt.ABOUT_TXT,
        disable_web_page_preview=True,
    )


# ============================================================
# PING
# ============================================================

@app.on_message(filters.command("ping"))
async def ping_handler(client, message):

    await message.reply_text(
        "🏓 <b>PONG!</b>\n\n"
        "🟢 Bot is online."
    )


# ============================================================
# AUTORENAME
# ============================================================

@app.on_message(filters.command("autorename"))
async def autorename_handler(client, message):

    try:

        user_id = message.from_user.id

        await get_user(user_id)

        # No argument → show current format
        if len(message.command) == 1:

            current = await get_format(user_id)

            await message.reply_text(
                Txt.FILE_NAME_TXT.format(
                    format_template=current
                )
            )

            return

        new_format = message.text.split(
            None,
            1
        )[1].strip()

        if not new_format:

            await message.reply_text(
                "❌ Please enter a rename format."
            )

            return

        await set_format(
            user_id,
            new_format
        )

        await message.reply_text(
            "✅ <b>Auto rename format updated!</b>\n\n"
            f"📝 <code>{new_format}</code>"
        )

    except Exception as e:

        LOGGER.exception(
            "Autorename error: %s",
            e
        )

        await message.reply_text(
            "❌ Failed to update rename format."
        )


# ============================================================
# SET THUMBNAIL
# ============================================================

@app.on_message(filters.command("setthumb"))
async def setthumb_handler(client, message):

    status = None

    try:

        reply = message.reply_to_message

        if not reply or not reply.photo:

            await message.reply_text(
                "🖼️ <b>How to use:</b>\n\n"
                "1. Send a photo\n"
                "2. Reply to that photo\n"
                "3. Send <code>/setthumb</code>"
            )

            return

        user_id = message.from_user.id

        status = await message.reply_text(
            "📥 <b>Downloading thumbnail...</b>"
        )

        DOWNLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        thumbnail_path = await reply.download(
            file_name=str(
                DOWNLOAD_DIR /
                f"thumb_{user_id}.jpg"
            )
        )

        if not thumbnail_path:

            raise RuntimeError(
                "Thumbnail download failed."
            )

        # Delete old thumbnail if present
        old_thumbnail = await get_thumbnail(
            user_id
        )

        if (
            old_thumbnail
            and old_thumbnail != thumbnail_path
        ):
            old_path = Path(old_thumbnail)

            if old_path.exists():

                try:
                    old_path.unlink()

                except Exception:
                    pass

        await set_thumbnail(
            user_id,
            thumbnail_path
        )

        await status.edit_text(
            "✅ <b>Thumbnail saved successfully!</b>"
        )

    except Exception as e:

        LOGGER.exception(
            "Set thumbnail error: %s",
            e
        )

        if status:

            try:

                await status.edit_text(
                    "❌ <b>Failed to save thumbnail.</b>\n\n"
                    f"<code>{str(e)[:500]}</code>"
                )

            except Exception:
                pass


# ============================================================
# VIEW THUMBNAIL
# ============================================================

@app.on_message(filters.command("viewthumb"))
async def viewthumb_handler(client, message):

    try:

        user_id = message.from_user.id

        thumbnail = await get_thumbnail(
            user_id
        )

        if not thumbnail:

            await message.reply_text(
                "❌ You don't have a thumbnail set."
            )

            return

        thumbnail_path = Path(thumbnail)

        if not thumbnail_path.exists():

            await delete_thumbnail(
                user_id
            )

            await message.reply_text(
                "❌ Your saved thumbnail is no longer available."
            )

            return

        await message.reply_photo(
            photo=str(thumbnail_path),
            caption="🖼️ <b>Your current thumbnail</b>",
        )

    except Exception as e:

        LOGGER.exception(
            "View thumbnail error: %s",
            e
        )

        await message.reply_text(
            "❌ Failed to show thumbnail."
        )


# ============================================================
# DELETE THUMBNAIL
# ============================================================

@app.on_message(filters.command("delthumb"))
async def delthumb_handler(client, message):

    try:

        user_id = message.from_user.id

        thumbnail = await get_thumbnail(
            user_id
        )

        await delete_thumbnail(
            user_id
        )

        if thumbnail:

            thumbnail_path = Path(
                thumbnail
            )

            if thumbnail_path.exists():

                try:
                    thumbnail_path.unlink()

                except Exception:
                    pass

        await message.reply_text(
            "🗑️ <b>Thumbnail deleted successfully.</b>"
        )

    except Exception as e:

        LOGGER.exception(
            "Delete thumbnail error: %s",
            e
        )

        await message.reply_text(
            "❌ Failed to delete thumbnail."
        )


# ============================================================
# SET CAPTION
# ============================================================

@app.on_message(filters.command("set_caption"))
async def setcaption_handler(client, message):

    try:

        user_id = message.from_user.id

        if len(message.command) == 1:

            await message.reply_text(
                "📝 <b>Usage:</b>\n\n"
                "<code>/set_caption Your caption here</code>"
            )

            return

        caption = message.text.split(
            None,
            1
        )[1].strip()

        await set_caption(
            user_id,
            caption
        )

        await message.reply_text(
            "✅ <b>Caption saved!</b>\n\n"
            f"{caption}"
        )

    except Exception as e:

        LOGGER.exception(
            "Set caption error: %s",
            e
        )

        await message.reply_text(
            "❌ Failed to save caption."
        )


# ============================================================
# SEE CAPTION
# ============================================================

@app.on_message(filters.command("see_caption"))
async def seecaption_handler(client, message):

    try:

        user_id = message.from_user.id

        caption = await get_caption(
            user_id
        )

        if not caption:

            await message.reply_text(
                "❌ No custom caption is currently set."
            )

            return

        await message.reply_text(
            "📝 <b>Your current caption:</b>\n\n"
            f"{caption}"
        )

    except Exception as e:

        LOGGER.exception(
            "See caption error: %s",
            e
        )

        await message.reply_text(
            "❌ Failed to get caption."
        )


# ============================================================
# DELETE CAPTION
# ============================================================

@app.on_message(filters.command("del_caption"))
async def delcaption_handler(client, message):

    try:

        user_id = message.from_user.id

        await delete_caption(
            user_id
        )

        await message.reply_text(
            "🗑️ <b>Caption deleted successfully.</b>"
        )

    except Exception as e:

        LOGGER.exception(
            "Delete caption error: %s",
            e
        )

        await message.reply_text(
            "❌ Failed to delete caption."
        )


# ============================================================
# UPSCALE
# ============================================================

@app.on_message(
    filters.command("upscale") &
    filters.private
)
async def upscale_handler(client, message):

    reply = message.reply_to_message

    if not reply:

        await message.reply_text(
            "🖼️ <b>Reply to an image with /upscale</b>"
        )

        return

    try:

        await upscale_image(
            client,
            message,
            reply
        )

    except Exception as e:

        LOGGER.exception(
            "Upscale handler error: %s",
            e
        )

        await message.reply_text(
            "❌ Upscale failed."
        )


# ============================================================
# ENHANCE
# ============================================================

@app.on_message(
    filters.command("enhance") &
    filters.private
)
async def enhance_handler(client, message):

    reply = message.reply_to_message

    if not reply:

        await message.reply_text(
            "✨ <b>Reply to an image with /enhance</b>"
        )

        return

    try:

        await enhance_image(
            client,
            message,
            reply
        )

    except Exception as e:

        LOGGER.exception(
            "Enhance handler error: %s",
            e
        )

        await message.reply_text(
            "❌ Enhancement failed."
        )


# ============================================================
# FILE PROCESSOR
# ============================================================

@app.on_message(
    filters.document |
    filters.video |
    filters.audio
)
async def file_handler(client, message):

    # Ignore messages generated by bots
    if message.from_user and message.from_user.is_bot:
        return

    status = None

    try:

        status = await message.reply_text(
            "📥 <b>File received...</b>\n\n"
            "Preparing your file..."
        )

        await process_file(
            client,
            message,
            status
        )

    except Exception as e:

        LOGGER.exception(
            "File handler error: %s",
            e
        )

        if status:

            try:

                await status.edit_text(
                    "❌ <b>File processing failed.</b>\n\n"
                    f"<code>{str(e)[:800]}</code>"
                )

            except Exception:
                pass


# ============================================================
# STARTUP
# ============================================================

async def startup():

    LOGGER.info(
        "Starting database..."
    )

    await start_database()

    LOGGER.info(
        "Database started successfully."
    )


# ============================================================
# MAIN
# ============================================================

async def main():

    LOGGER.info("=" * 60)
    LOGGER.info(
        "🦋 EGOIST6969 RENAME BOT"
    )
    LOGGER.info(
        "Starting..."
    )
    LOGGER.info("=" * 60)

    try:

        await startup()

        await app.start()

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

    except RPCError as e:

        LOGGER.exception(
            "Telegram RPC error: %s",
            e
        )

    except Exception as e:

        LOGGER.exception(
            "Fatal startup error: %s",
            e
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
