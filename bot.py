```python
# bot.py
# ============================================
# Auto Rename + Upscale + Enhance Telegram Bot
# Automatic Plugin / Command Loader
# ============================================

import os
import sys
import asyncio
import importlib
import logging
from pathlib import Path

from pyrogram import Client, idle
from pyrogram.errors import RPCError

from config import API_ID, API_HASH, BOT_TOKEN


# ============================================
# LOGGING
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

LOGGER = logging.getLogger("AutoRenameBot")


# ============================================
# DIRECTORIES
# ============================================

BASE_DIR = Path(__file__).resolve().parent
PLUGINS_DIR = BASE_DIR / "plugins"


# Create plugins folder automatically
PLUGINS_DIR.mkdir(exist_ok=True)

# Make sure Python can find the plugins
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================
# BOT
# ============================================

app = Client(
    "auto_rename_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=20,
)


# ============================================
# PLUGIN LOADER
# ============================================

loaded_plugins = []


def load_plugins():
    """
    Automatically load every Python file inside
    the plugins folder.

    Example:

        plugins/
        ├── rename.py
        ├── upscale.py
        ├── enhance.py
        ├── start.py
        └── newcommand.py

    Adding a new .py file automatically loads it.
    """

    LOGGER.info("Loading plugins...")

    for file in sorted(PLUGINS_DIR.glob("*.py")):

        # Ignore __init__.py
        if file.name.startswith("_"):
            continue

        module_name = f"plugins.{file.stem}"

        try:
            importlib.import_module(module_name)

            loaded_plugins.append(file.stem)

            LOGGER.info(
                "Plugin loaded successfully: %s",
                file.stem
            )

        except Exception as error:

            LOGGER.exception(
                "Failed to load plugin %s: %s",
                file.name,
                error
            )


# ============================================
# PLUGIN STATUS
# ============================================

def plugin_count():
    return len(loaded_plugins)


def plugin_list():
    return loaded_plugins


# ============================================
# STARTUP MESSAGE
# ============================================

async def startup_message():
    """
    Prints bot information when starting.
    """

    LOGGER.info("=" * 50)
    LOGGER.info("AUTO RENAME BOT STARTED")
    LOGGER.info("Loaded Plugins: %s", plugin_count())

    if loaded_plugins:
        LOGGER.info(
            "Plugins: %s",
            ", ".join(loaded_plugins)
        )

    LOGGER.info("=" * 50)


# ============================================
# MAIN
# ============================================

async def main():

    # Load every plugin before starting bot
    load_plugins()

    try:

        await app.start()

        await startup_message()

        me = await app.get_me()

        LOGGER.info(
            "Bot username: @%s",
            me.username
        )

        LOGGER.info(
            "Bot ID: %s",
            me.id
        )

        LOGGER.info("Bot is online!")

        # Keep bot running
        await idle()

    except RPCError as error:

        LOGGER.error(
            "Telegram RPC Error: %s",
            error
        )

    except Exception as error:

        LOGGER.exception(
            "Bot crashed: %s",
            error
        )

    finally:

        try:
            await app.stop()

        except Exception:
            pass

        LOGGER.info("Bot stopped.")


# ============================================
# RUN
# ============================================

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:

        LOGGER.info("Bot stopped manually.")
```

