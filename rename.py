import os
import re
import logging
from database import get_format, get_user_config

LOGGER = logging.getLogger(__name__)

# Pattern matchers for detecting chapter/episode numbers
EPISODE_PATTERNS = [
    r"\bCh(?:apter)?[\s._-]*(\d+(?:\.\d+)?)\b",
    r"\bVol(?:ume)?[\s._-]*\d+[\s._-]*Ch(?:apter)?[\s._-]*(\d+(?:\.\d+)?)\b",
    r"\bS\d{1,2}\s*E(\d{1,4})\b",
    r"\bS\d{1,2}\s*-\s*E(\d{1,4})\b",
    r"\bEP(?:ISODE)?[\s._-]*(\d{1,4})\b",
    r"\bE[\s._-]*(\d{1,4})\b",
    r"\bEpisode[\s._-]*(\d{1,4})\b",
]


def detect_chapter(filename: str) -> str:
    """
    Detect chapter or episode number from a filename.
    """
    stem = os.path.splitext(filename)[0]

    for pattern in EPISODE_PATTERNS:
        match = re.search(pattern, stem, re.IGNORECASE)
        if match:
            return match.group(1)

    # Fallback: standalone or last numerical sequence
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", stem)
    if numbers:
        return numbers[-1]

    return "01"


def detect_quality(filename: str) -> str:
    """
    Detect video/image resolution or quality.
    """
    name = filename.lower()
    qualities = [
        "4320p", "2160p", "1440p", "1080p", "900p",
        "720p", "576p", "480p", "360p", "240p",
    ]

    for quality in qualities:
        if quality in name:
            return quality

    aliases = {
        "4k": "2160p",
        "2k": "1440p",
        "fhd": "1080p",
        "hd": "720p",
    }

    for alias, value in aliases.items():
        if re.search(rf"\b{re.escape(alias)}\b", name):
            return value

    return "HD"


def extract_title(filename: str) -> str:
    """
    Extract title by removing chapter markers and clean formatting.
    """
    stem = os.path.splitext(filename)[0]
    clean = re.sub(r'(?i)\b(ch|chapter|vol|volume|ep|episode)\b[\s._-]*\d+', '', stem)
    clean = clean.replace("_", " ").replace(".", " ")
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean or "Manga"


def safe_filename(filename: str) -> str:
    """
    Sanitize filename for file systems.
    """
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename or "Renamed_File"


async def rename_file(user_id: int, original_filename: str) -> str:
    try:
        extension = os.path.splitext(original_filename)[1].lower()
        config = await get_user_config(user_id)

        template = config.get("format", "{title} - Ch {chapter} [{channel}]")
        stored_title = config.get("title", None)
        channel_name = config.get("channel_name", "@MangaChannel")

        chapter = detect_chapter(original_filename)
        quality = detect_quality(original_filename)
        
        # Determine title: custom setting or auto-extracted
        title = stored_title if stored_title else extract_title(original_filename)

        # Map replacements
        replacements = {
            "{chapter}": chapter,
            "{title}": title,
            "{channel}": channel_name,
            "chapter": chapter,
            "title": title,
            "channel": channel_name,
            "episode": chapter,
            "quality": quality,
        }

        new_name = template
        for key, value in replacements.items():
            new_name = new_name.replace(key, str(value))

        new_name = safe_filename(new_name)
        new_name = os.path.splitext(new_name)[0] + extension

        LOGGER.info(f"Rename: {original_filename} -> {new_name}")
        return new_name

    except Exception as e:
        LOGGER.error(f"Rename error: {e}")
        return original_filename
