import os
import asyncio
from pyrogram import Client, filters
from database import (
    get_user_config, set_target_channel, set_format_config, 
    set_thumbnail, get_thumbnail, start_database
)
from upscale import upscale_image
from enhance import enhance_image
from media import process_file

# --- COMMAND: /FORMAT ---
@Client.on_message(filters.command("format") & filters.private)
async def cmd_format(client, message):
    """Usage: /format {chapter} {title} {channel name}"""
    args = message.text.split(maxsplit=3)
    user_id = message.from_user.id
    
    if len(args) < 4:
        await message.reply_text(
            "<b>Usage Pattern:</b>\n"
            "<code>/format {chapter} {title} {channel_name}</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/format {chapter} Solo Leveling @MangaVault</code>\n"
            "<i>Leave title as '{title}' to auto-detect from input filename.</i>"
        )
        return

    _, raw_chapter, raw_title, raw_channel = args
    
    # Store dynamic formatting structure
    title_val = None if raw_title.lower() == "{title}" else raw_title
    template_fmt = f"{raw_title} - Ch {raw_chapter} [{raw_channel}]"
    
    await set_format_config(
        user_id=user_id, 
        template=template_fmt, 
        title=title_val, 
        channel_name=raw_channel
    )
    
    await message.reply_text(
        "✅ <b>Rename Template Configured!</b>\n\n"
        f"<b>Format:</b> <code>{template_fmt}</code>\n"
        f"<b>Auto-Title:</b> <code>{'Enabled' if not title_val else title_val}</code>"
    )

# --- COMMAND: /SET_CHANNEL ---
@Client.on_message(filters.command("set_channel") & filters.private)
async def cmd_set_channel(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ Provide a valid Target Channel ID.\nExample: <code>/set_channel -100xxxxxxxxx</code>")
        return

    try:
        channel_id = int(message.command[1])
        await set_target_channel(message.from_user.id, channel_id)
        await message.reply_text(f"✅ Target channel configured to: <code>{channel_id}</code>")
    except ValueError:
        await message.reply_text("❌ Invalid Channel ID format. Ensure it is an integer.")

# --- COMMAND: /SET_THUMB ---
@Client.on_message(filters.command("set_thumb") & filters.private)
async def cmd_set_thumb(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.photo or reply.document):
        await message.reply_text("📸 Reply to an image/thumbnail document with /set_thumb")
        return

    user_id = message.from_user.id
    path = await reply.download(file_name=f"thumbnails/{user_id}.jpg")
    await set_thumbnail(user_id, path)
    await message.reply_text("🖼️ Custom Manga/Doc Thumbnail updated!")

# --- COMMANDS: /UPSCALE & /ENHANCE ---
@Client.on_message(filters.command("upscale") & filters.private)
async def cmd_upscale(client, message):
    reply = message.reply_to_message
    if not reply:
        await message.reply_text("🖼️ Reply to an image with /upscale")
        return
    await upscale_image(client, message, reply)

@Client.on_message(filters.command("enhance") & filters.private)
async def cmd_enhance(client, message):
    reply = message.reply_to_message
    if not reply:
        await message.reply_text("✨ Reply to an image with /enhance")
        return
    await enhance_image(client, message, reply)
