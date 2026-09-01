import asyncio
import logging
import os

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
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

LOGGER = logging.getLogger("RenameFileBot")


# ============================================================
# BOT
# ============================================================

app = Client(
    "rename_file_bot",
    api_id=int(Config.API_ID),
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=20
)


# ============================================================
# START
# ============================================================

@app.on_message(filters.command("start"))
async def start_handler(client, message):

    user = message.from_user

    name = user.first_name if user else "User"

    await get_user(message.from_user.id)

    await message.reply_text(
        Txt.START_TXT.format(name),
        disable_web_page_preview=True
    )


# ============================================================
# HELP
# ============================================================

@app.on_message(filters.command("help"))
async def help_handler(client, message):

    await message.reply_text(
        f"""
<b>🦋 SHINOBU RENAME BOT</b>

<b>📁 FILE</b>
• Send any document/video/audio
• Bot automatically renames it

<b>📝 RENAME</b>
/autorename <code>your format</code>

<b>🖼 THUMBNAIL</b>
/setthumb
/viewthumb
/delthumb

<b>✏️ CAPTION</b>
/set_caption
/see_caption
/del_caption

<b>✨ IMAGE TOOLS</b>
/upscale
/enhance

<b>ℹ️ OTHER</b>
/about
/ping

<b>💜 Developer:</b> @EGOIST6969
""",
        disable_web_page_preview=True
    )


# ============================================================
# ABOUT
# ============================================================

@app.on_message(filters.command("about"))
async def about_handler(client, message):

    await message.reply_text(
        Txt.ABOUT_TXT,
        disable_web_page_preview=True
    )


# ============================================================
# PING
# ============================================================

@app.on_message(filters.command("ping"))
async def ping_handler(client, message):

    await message.reply_text(
        "🏓 <b>Pong!</b>\n\n"
        "🟢 Bot is online."
    )


# ============================================================
# AUTO RENAME FORMAT
# ============================================================

@app.on_message(filters.command("autorename"))
async def autorename_handler(client, message):

    user_id = message.from_user.id

    if len(message.command) < 2:

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
            "❌ Please provide a rename format."
        )

        return

    await set_format(
        user_id,
        new_format
    )

    await message.reply_text(
        "✅ <b>Auto rename format updated!</b>\n\n"
        f"<code>{new_format}</code>"
    )


# ============================================================
# SET THUMBNAIL
# ============================================================

@app.on_message(filters.command("setthumb"))
async def setthumb_handler(client, message):

    reply = message.reply_to_message

    if not reply or not reply.photo:

        await message.reply_text(
            "🖼️ <b>Reply to a photo with /setthumb</b>"
        )

        return

    user_id = message.from_user.id

    os.makedirs("downloads", exist_ok=True)

    status = await message.reply_text(
        "📥 Downloading thumbnail..."
    )

    try:

        path = await reply.download(
            file_name=f"downloads/thumb_{user_id}.jpg"
        )

        await set_thumbnail(
            user_id,
            path
        )

        await status.edit_text(
            "✅ <b>Thumbnail saved successfully!</b>"
        )

    except Exception as error:

        LOGGER.exception(
            "Thumbnail error: %s",
            error
        )

        await status.edit_text(
            "❌ Failed to save thumbnail."
        )


# ============================================================
# VIEW THUMBNAIL
# ============================================================

@app.on_message(filters.command("viewthumb"))
async def viewthumb_handler(client, message):

    user_id = message.from_user.id

    thumbnail = await get_thumbnail(
        user_id
    )

    if not thumbnail or not os.path.exists(thumbnail):

        await message.reply_text(
            "❌ You don't have a thumbnail set."
        )

        return

    try:

        await message.reply_photo(
            thumbnail,
            caption="🖼️ <b>Your current thumbnail</b>"
        )

    except Exception as error:

        LOGGER.exception(
            "View thumbnail error: %s",
            error
        )

        await message.reply_text(
            "❌ Unable to send your thumbnail."
        )


# ============================================================
# DELETE THUMBNAIL
# ============================================================

@app.on_message(filters.command("delthumb"))
async def delthumb_handler(client, message):

    user_id = message.from_user.id

    thumbnail = await get_thumbnail(
        user_id
    )

    await delete_thumbnail(
        user_id
    )

    if thumbnail and os.path.exists(thumbnail):

        try:
            os.remove(thumbnail)
        except Exception:
            pass

    await message.reply_text(
        "🗑️ <b>Thumbnail deleted.</b>"
    )


# ============================================================
# SET CAPTION
# ============================================================

@app.on_message(filters.command("set_caption"))
async def setcaption_handler(client, message):

    user_id = message.from_user.id

    if len(message.command) < 2:

        await message.reply_text(
            "✏️ Usage:\n\n"
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


# ============================================================
# SEE CAPTION
# ============================================================

@app.on_message(filters.command("see_caption"))
async def seecaption_handler(client, message):

    user_id = message.from_user.id

    caption = await get_caption(
        user_id
    )

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

@app.on_message(filters.command("del_caption"))
async def delcaption_handler(client, message):

    user_id = message.from_user.id

    await delete_caption(
        user_id
    )

    await message.reply_text(
        "🗑️ <b>Caption deleted.</b>"
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

    await upscale_image(
        client,
        message,
        reply
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

    if message.from_user and message.from_user.is_bot:
        return

    status = await message.reply_text(
        "📥 <b>File received...</b>\n\n"
        "Preparing your file..."
    )

    try:

        await process_file(
            client,
            message,
            status
        )

    except Exception as error:

        LOGGER.exception(
            "File processing error: %s",
            error
        )

        try:

            await status.edit_text(
                "❌ <b>File processing failed.</b>\n\n"
                f"<code>{error}</code>"
            )

        except Exception:
            pass


# ============================================================
# PHOTO HANDLER
# ============================================================

@app.on_message(filters.photo)
async def photo_handler(client, message):

    # Photos are processed only through
    # /upscale or /enhance.
    return


# ============================================================
# STARTUP
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
