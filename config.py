import re
import os
import time

id_pattern = re.compile(r'^.\d+$')


class Config(object):
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🦋 SHINOBU BOT CONFIGURATION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # Pyrogram client config
    API_ID = os.environ.get("API_ID", "31963776")
    API_HASH = os.environ.get("API_HASH", "d352f599aff861566030a3cbba3a0f75")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8776604643:AAHAArtcoI8ifzTQ0Z_UnCzkItCGuFJhXu8")

    # Database config
    DB_NAME = os.environ.get("DB_NAME", "autorenamefile")
    DB_URL = os.environ.get("DB_URL", "mongodb+srv://lkgprepration_db_user:XZDCxt5C0bpSCPcP@autorenamefile.rnh65rg.mongodb.net/?appName=autorenamefile")

    # Other configs
    BOT_UPTIME = time.time()

    START_PIC = os.environ.get(
        "START_PIC",
        "https://graph.org/file/4b306f4b15c23a8f22e58.jpg"
    )

    ADMIN = [
        int(admin) if id_pattern.search(admin) else admin
        for admin in os.environ.get("ADMIN", "7974236970").split()
    ]

    FORCE_SUB = os.environ.get("FORCE_SUB", "@mangaisland_acn")

    LOG_CHANNEL = int(
        os.environ.get("LOG_CHANNEL", "-1003796992309")
    )

    # Web response configuration
    WEBHOOK = bool(
        os.environ.get("WEBHOOK", "True")
    )


class Txt(object):
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🦋 SHINOBU KOCHO × EGOIST6969
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    START_TXT = """<b>🦋 Welcome, {}~</b>

🌸 I am your <b>Shinobu-themed Advanced Rename Bot</b>.

╭───────────────⪼
│ 🦋 <b>Auto Rename</b>
│ 🌸 <b>Custom Thumbnail</b>
│ 📝 <b>Custom Caption</b>
│ 📁 <b>File Processing</b>
╰───────────────⪼

🌷 Send me your file and I'll take care of the rest.

<b>🦋 Use /help to see all available commands.</b>

<blockquote>Made with 💜 by @EGOIST6969</blockquote>"""


    FILE_NAME_TXT = """<b>🦋 <u>SETUP AUTO RENAME FORMAT</u></b>

🌸 Use these keywords to create your custom file name:

✓ <code>episode</code> → Replace Episode Number
✓ <code>quality</code> → Replace Video Resolution

<b>🦋 Example:</b>

<code>/autorename Naruto Shippuden S02 - EPepisode - quality [Dual Audio] - @EGOIST6969</code>

<b>🌸 Your Current Auto Rename Format:</b>

<code>{format_template}</code>

<blockquote>🦋 Shinobu is ready to rename your files~</blockquote>"""


    ABOUT_TXT = """<b>🦋 ABOUT MYSELF</b>

<b>🤖 Bot Name:</b> <a href="https://t.me/EGOIST6969">Shinobu Rename Bot</a>

<b>📝 Language:</b> <a href="https://python.org">Python 3</a>

<b>📚 Library:</b> <a href="https://pyrogram.org">Pyrogram 2.0</a>

<b>🚀 Theme:</b> <b>Shinobu Kocho 🦋</b>

<b>🧑‍💻 Developer:</b> <a href="https://t.me/EGOIST6969">@EGOIST6969</a>

<b>💜 Bot Made By:</b> @EGOIST6969

<blockquote>🌸 "A little poison can be quite useful~" 🦋</blockquote>"""


    THUMBNAIL_TXT = """<b><u>🦋 HOW TO SET THUMBNAIL</u></b>

🌸 Send or reply to a photo and use the thumbnail command.

⦿ <code>/viewthumb</code> → View your current thumbnail

⦿ <code>/delthumb</code> → Delete your current thumbnail

<blockquote>🦋 Your files deserve a beautiful thumbnail~</blockquote>"""


    CAPTION_TXT = """<b><u>🌸 HOW TO SET CAPTION</u></b>

⦿ <code>/set_caption</code> → Set your custom caption

⦿ <code>/see_caption</code> → View your current caption

⦿ <code>/del_caption</code> → Delete your current caption

<blockquote>🦋 Customize your files however you like~</blockquote>"""


    PROGRESS_BAR = """\n
<b>📁 Size</b> : {1} | {2}
<b>⏳️ Done</b> : {0}%
<b>🚀 Speed</b> : {3}/s
<b>⏰️ ETA</b> : {4}
"""


    DONATE_TXT = """<b>🦋 Thanks for showing interest in supporting me! 💜</b>

If you enjoy this bot and my projects, you can support the development with any amount you wish.

<b>🧑‍💻 Developer:</b> @EGOIST6969

<blockquote>🌸 Your support keeps the project alive~</blockquote>"""


    HELP_TXT = """<b>🦋 Hey, {}~</b>

<b>Welcome to the Shinobu-themed Help Centre.</b>

╭───────────────⪼
│ 🌸 Use the available commands
│ 🦋 Configure your rename format
│ 🖼️ Set your thumbnail
│ 📝 Set your caption
│ 📁 Send your files
╰───────────────⪼

<b>💜 Developer:</b> @EGOIST6969

<blockquote>🦋 Need something? Just ask~</blockquote>"""
