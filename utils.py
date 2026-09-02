import os
import re
import time
import asyncio
import shutil
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
TEMP_DIR = BASE_DIR / "temp"

DOWNLOAD_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)


def clean_filename(filename: str) -> str:
    if not filename:
        return "file"

    filename = str(filename).strip()
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename)
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename.strip(" .")

    return filename or "file"


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def get_filename_without_extension(filename: str) -> str:
    return Path(filename).stem


def add_extension(filename: str, extension: str) -> str:
    extension = extension.strip()

    if extension and not extension.startswith("."):
        extension = "." + extension

    if not filename.lower().endswith(extension.lower()):
        filename += extension

    return filename


def get_download_path(filename: str) -> str:
    filename = clean_filename(filename)
    return str(DOWNLOAD_DIR / filename)


def get_temp_path(filename: str) -> str:
    filename = clean_filename(filename)
    return str(TEMP_DIR / filename)


def get_file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except (OSError, TypeError):
        return 0


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"

    if size < 1024 ** 2:
        return f"{size / 1024:.2f} KB"

    if size < 1024 ** 3:
        return f"{size / (1024 ** 2):.2f} MB"

    return f"{size / (1024 ** 3):.2f} GB"


def file_exists(path: str) -> bool:
    return os.path.isfile(path)


def is_image(filename: str) -> bool:
    extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    return get_extension(filename) in extensions


def is_pdf(filename: str) -> bool:
    return get_extension(filename) == ".pdf"


def delete_file(path: str) -> bool:
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except Exception:
        pass

    return False


def delete_folder(path: str) -> bool:
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            return True
    except Exception:
        pass

    return False


async def delete_after(path: str, seconds: int = 60):
    await asyncio.sleep(seconds)

    if os.path.isfile(path):
        delete_file(path)


def cleanup_old_files(folder: str, max_age: int = 300):
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
    cleanup_old_files(str(DOWNLOAD_DIR), 300)
    cleanup_old_files(str(TEMP_DIR), 300)


def create_output_filename(original_name: str, new_name: str) -> str:
    extension = get_extension(original_name)
    new_name = clean_filename(new_name)

    if extension and not new_name.lower().endswith(extension):
        new_name += extension

    return new_name


def trim_caption(caption: str, limit: int = 1024) -> str:
    if not caption:
        return ""

    return caption[:limit]


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def startup_cleanup():
    cleanup_old_files(str(DOWNLOAD_DIR), 300)
    cleanup_old_files(str(TEMP_DIR), 300)
