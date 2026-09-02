import asyncio
import logging
import os

from pyrogram import Client, filters, idle
from pyrogram.errors import RPCError

from config import Config
from database import (
    start_database,
    get_user,
    set_format_config,
    set_target_channel,
    set_thumbnail,
    get_thumbnail,
    delete_thumbnail,
    set_caption,
    get_caption,
    delete_caption,
    get_user_config,
)

from media import process_file
from upscale import upscale_image
from enhance import enhance_image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
LOGGER = logging.getLogger("RenameFileBot")

os.makedirs("downloads", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)

app = Client(
    "rename_file_bot",
    api_id=int(Config.API_ID),
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=20
)


@app.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    name = user.first_name if user else "User"
    await get_user(message.from_user.id)

    await message.reply_text(
        f"🦋 <b>Hello {name}!</b>\n\n"
        "Welcome to <b>RenameFile Bot</b>.\n\n"
        "⚙️ <b>Commands:</b>\n"
        "• <code>/format {title} - Ch {chapter} [{channel}]</code>\n"
        "• <code>/set_thumb</code> - Reply to photo\n"
        "• <code>/set_channel {{channel_id}}</code>\n"
        "• <code>/upscale</code> - Reply to photo\n"
        "• <code>/enhance</code> - Reply to photo\n"
    )


@app.on_message(filters.command("format") & filters.private)
async def format_command(client, message):
    user_id = message.from_user.id
    
    if len(message.command) < 2:
        config = await get_user_config(user_id)
        current = config.get("format", "{title} - Ch {chapter} [{channel}]")
        await message.reply_text(
            "<b>Usage Pattern:</b>\n"
            "<code>/format {title} - Ch {chapter} [{channel}]</code>\n\n"
            "<b>Available Variables:</b>\n"
            "• <code>{title}</code> - Original filename / Title\n"
            "• <code>{chapter}</code> - Detected Chapter / Episode\n"
            "• <code>{channel}</code> - Channel Tag\n"
            "• <code>{quality}</code> - Video/Image Quality\n\n"
            f"<b>Current Format:</b> <code>{current}</code>"
        )
        return

    # Extract format directly after '/format '
    template_fmt = message.text.split(maxsplit=1)[1]

    await set_format_config(
        user_id=user_id,
        template=template_fmt
    )

    await message.reply_text(
        "✅ <b>Rename Template Configured!</b>\n\n"
        f"<b>Format:</b> <code>{template_fmt}</code>"
    )


@app.on_message(filters.command("set_channel") & filters.private)
async def set_channel_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ Provide a valid Target Channel ID.\nExample: <code>/set_channel -100123456789</code>")
        return

    try:
        channel_id = int(message.command[1])
        await set_target_channel(message.from_user.id, channel_id)
        await message.reply_text(f"✅ Target channel set to: <code>{channel_id}</code>")
    except ValueError:
        await message.reply_text("❌ Invalid Channel ID format. Must be an integer.")


@app.on_message(filters.command(["set_thumb", "setthumb"]))
async def setthumb_command(client, message):
    user_id = message.from_user.id
    reply = message.reply_to_message

    if not reply or not (reply.photo or reply.document):
        await message.reply_text("🖼️ Reply to a photo or image file with /set_thumb")
        return

    try:
        path = await reply.download(file_name=f"thumbnails/{user_id}.jpg")
        await set_thumbnail(user_id, path)
        await message.reply_text("✅ <b>Thumbnail saved successfully!</b>")
    except Exception as e:
        await message.reply_text(f"❌ Failed to save thumbnail: <code>{str(e)[:500]}</code>")


@app.on_message(filters.command("upscale") & filters.private)
async def upscale_command(client, message):
    reply = message.reply_to_message
    if not reply:
        await message.reply_text("🖼️ Reply to an image with /upscale")
        return
    await upscale_image(client, message, reply)


@app.on_message(filters.command("enhance") & filters.private)
async def enhance_command(client, message):
    reply = message.reply_to_message
    if not reply:
        await message.reply_text("✨ Reply to an image with /enhance")
        return
    await enhance_image(client, message, reply)


@app.on_message(filters.document | filters.video | filters.audio)
async def file_handler(client, message):
    if message.from_user and message.from_user.is_bot:
        return

    status = await message.reply_text("📥 <b>File received... Processing...</b>")
    await process_file(client, message, status)


async def main():
    try:
        await app.start()
        await start_database()
        me = await app.get_me()
        LOGGER.info(f"🟢 BOT ONLINE: @{me.username}")
        await idle()
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
