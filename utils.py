```python
# utils.py

import os
import re
import time
import asyncio
import shutil
from pathlib import Path


# =========================
# FOLDERS
# =========================

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
TEMP_DIR = BASE_DIR / "temp"

DOWNLOAD_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)


# =========================
# FILE NAME FUNCTIONS
# =========================

def clean_filename(filename: str) -> str:
    """
    Make a filename safe for Linux/Windows.
    """
    if not filename:
        return "file"

    filename = str(filename).strip()

    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename)

    # Replace multiple spaces
    filename = re.sub(r'\s+', ' ', filename)

    # Remove dots/spaces from the end
    filename = filename.strip(" .")

    return filename or "file"


def get_extension(filename: str) -> str:
    """
    Return file extension including the dot.
    Example: movie.pdf -> .pdf
    """
    return Path(filename).suffix.lower()


def get_filename_without_extension(filename: str) -> str:
    """
    Return filename without extension.
    """
    return Path(filename).stem


def add_extension(filename: str, extension: str) -> str:
    """
    Add extension if it is missing.
    """
    extension = extension.strip()

    if extension and not extension.startswith("."):
        extension = "." + extension

    if not filename.lower().endswith(extension.lower()):
        filename += extension

    return filename


# =========================
# PATH FUNCTIONS
# =========================

def get_download_path(filename: str) -> str:
    """
    Generate a safe path inside downloads folder.
    """
    filename = clean_filename(filename)
    return str(DOWNLOAD_DIR / filename)


def get_temp_path(filename: str) -> str:
    """
    Generate a safe path inside temp folder.
    """
    filename = clean_filename(filename)
    return str(TEMP_DIR / filename)


# =========================
# FILE SIZE
# =========================

def get_file_size(path: str) -> int:
    """
    Return file size in bytes.
    """
    try:
        return os.path.getsize(path)
    except (OSError, TypeError):
        return 0


def format_size(size: int) -> str:
    """
    Convert bytes into readable format.
    """
    if size < 1024:
        return f"{size} B"

    if size < 1024 ** 2:
        return f"{size / 1024:.2f} KB"

    if size < 1024 ** 3:
        return f"{size / (1024 ** 2):.2f} MB"

    return f"{size / (1024 ** 3):.2f} GB"


# =========================
# FILE CHECKS
# =========================

def file_exists(path: str) -> bool:
    """
    Check whether a file exists.
    """
    return os.path.isfile(path)


def is_image(filename: str) -> bool:
    """
    Check whether file is a supported image.
    """
    extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".tiff",
    }

    return get_extension(filename) in extensions


def is_pdf(filename: str) -> bool:
    """
    Check whether file is a PDF.
    """
    return get_extension(filename) == ".pdf"


# =========================
# DELETE FILE
# =========================

def delete_file(path: str) -> bool:
    """
    Delete a single file safely.
    """
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except Exception:
        pass

    return False


def delete_folder(path: str) -> bool:
    """
    Delete a folder and everything inside it.
    """
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            return True
    except Exception:
        pass

    return False


# =========================
# AUTO CLEANUP
# =========================

async def delete_after(path: str, seconds: int = 60):
    """
    Delete a file after a certain amount of time.

    Example:
        await delete_after("downloads/file.pdf", 60)
    """

    await asyncio.sleep(seconds)

    if os.path.isfile(path):
        delete_file(path)


def cleanup_old_files(folder: str, max_age: int = 300):
    """
    Delete files older than max_age seconds.

    Default:
        300 seconds = 5 minutes
    """

    if not os.path.isdir(folder):
        return

    current_time = time.time()

    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)

        try:
            if os.path.isfile(path):
                age = current_time - os.path.getmtime(path)

                if age > max_age:
                    os.remove(path)

        except Exception:
            continue


def cleanup_all():
    """
    Clean old files from bot folders.
    """

    cleanup_old_files(str(DOWNLOAD_DIR), 300)
    cleanup_old_files(str(TEMP_DIR), 300)


# =========================
# USER FILE NAME
# =========================

def create_output_filename(
    original_name: str,
    new_name: str,
) -> str:
    """
    Keep the original extension while changing the filename.

    Example:
        movie.pdf + MyMovie
        -> MyMovie.pdf
    """

    extension = get_extension(original_name)

    new_name = clean_filename(new_name)

    if extension and not new_name.lower().endswith(extension):
        new_name += extension

    return new_name


# =========================
# TELEGRAM CAPTION
# =========================

def trim_caption(caption: str, limit: int = 1024) -> str:
    """
    Telegram captions have a size limit.
    """
    if not caption:
        return ""

    return caption[:limit]


# =========================
# SAFE INTEGER
# =========================

def safe_int(value, default=0):
    """
    Safely convert something to integer.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# =========================
# STARTUP CLEANUP
# =========================

def startup_cleanup():
    """
    Remove old temporary files when the bot starts.
    """

    cleanup_old_files(str(DOWNLOAD_DIR), 300)
    cleanup_old_files(str(TEMP_DIR), 300)
```
