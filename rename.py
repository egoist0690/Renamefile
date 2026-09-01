import os
import re
import logging

from database import get_format


LOGGER = logging.getLogger(__name__)


# ============================================================
# EPISODE DETECTION
# ============================================================

EPISODE_PATTERNS = [
    r"\bS\d{1,2}\s*E(\d{1,4})\b",
    r"\bS\d{1,2}\s*-\s*E(\d{1,4})\b",
    r"\bEP(?:ISODE)?[\s._-]*(\d{1,4})\b",
    r"\bE[\s._-]*(\d{1,4})\b",
    r"\bEpisode[\s._-]*(\d{1,4})\b",
]


def detect_episode(filename: str) -> str:
    """
    Detect episode number from a filename.
    """

    name = os.path.splitext(filename)[0]

    for pattern in EPISODE_PATTERNS:

        match = re.search(
            pattern,
            name,
            re.IGNORECASE
        )

        if match:
            return match.group(1)

    # Fallback: standalone number
    numbers = re.findall(
        r"\b\d{1,4}\b",
        name
    )

    if numbers:
        return numbers[-1]

    return "0"


# ============================================================
# QUALITY DETECTION
# ============================================================

def detect_quality(filename: str) -> str:
    """
    Detect video/image quality.
    """

    name = filename.lower()

    qualities = [
        "4320p",
        "2160p",
        "1440p",
        "1080p",
        "900p",
        "720p",
        "576p",
        "480p",
        "360p",
        "240p",
    ]

    for quality in qualities:

        if quality in name:
            return quality

    # Common aliases
    aliases = {
        "4k": "2160p",
        "2k": "1440p",
        "fhd": "1080p",
        "hd": "720p",
    }

    for alias, value in aliases.items():

        if re.search(
            rf"\b{re.escape(alias)}\b",
            name
        ):
            return value

    return "Unknown"


# ============================================================
# CLEAN FILENAME
# ============================================================

def clean_filename(filename: str) -> str:
    """
    Remove unnecessary characters from a filename.
    """

    name, extension = os.path.splitext(filename)

    # Replace underscores and dots with spaces
    name = name.replace("_", " ")
    name = name.replace(".", " ")

    # Remove repeated spaces
    name = re.sub(
        r"\s+",
        " ",
        name
    ).strip()

    return name + extension


# ============================================================
# REMOVE OLD EXTENSION
# ============================================================

def get_extension(filename: str) -> str:

    return os.path.splitext(filename)[1].lower()


# ============================================================
# FORMAT PROCESSOR
# ============================================================

def apply_format(
    template: str,
    episode: str,
    quality: str
) -> str:

    result = template

    replacements = {

        "episode": episode,

        "Episode": episode,

        "EPISODE": episode,

        "quality": quality,

        "Quality": quality,

        "QUALITY": quality,
    }

    for key, value in replacements.items():

        result = result.replace(
            key,
            value
        )

    return result


# ============================================================
# SAFE FILENAME
# ============================================================

def safe_filename(filename: str) -> str:
    """
    Make filename safe for Linux/Telegram.
    """

    filename = re.sub(
        r'[<>:"/\\|?*\x00-\x1F]',
        "",
        filename
    )

    filename = re.sub(
        r"\s+",
        " ",
        filename
    ).strip()

    # Prevent empty filename
    if not filename:
        filename = "Renamed_File"

    return filename


# ============================================================
# MAIN RENAME FUNCTION
# ============================================================

async def rename_file(
    user_id: int,
    original_filename: str
) -> str:

    try:

        extension = get_extension(
            original_filename
        )

        clean_name = clean_filename(
            original_filename
        )

        episode = detect_episode(
            clean_name
        )

        quality = detect_quality(
            clean_name
        )

        template = await get_format(
            user_id
        )

        new_name = apply_format(
            template,
            episode,
            quality
        )

        new_name = safe_filename(
            new_name
        )

        # Keep original extension
        new_name = os.path.splitext(
            new_name
        )[0]

        new_name += extension

        LOGGER.info(
            f"Rename: {original_filename} -> {new_name}"
        )

        return new_name

    except Exception as e:

        LOGGER.error(
            f"Rename error: {e}"
        )

        # Safe fallback
        extension = get_extension(
            original_filename
        )

        return "Renamed_File" + extension
