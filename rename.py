import os
import re
import logging
from database import get_format, get_user_config

LOGGER = logging.getLogger(__name__)

EPISODE_PATTERNS = [
    r"\bCh(?:apter)?[\s._-]*(\d+(?:\.\d+)?)\b",
    r"\bVol(?:ume)?[\s._-]*\d+[\s._-]*Ch(?:apter)?[\s._-]*(\d+(?:\.\d+)?)\b",
    r"\bS\d{1,2}\s*E(\d{1,4})\b",
    r"\bEP(?:ISODE)?[\s._-]*(\d{1,4})\b",
]

def extract_chapter_number(filename: str) -> str:
    """Extract chapter/episode number from file stem."""
    stem = os.path.splitext(filename)[0]
    for pattern in EPISODE_PATTERNS:
        match = re.search(pattern, stem, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # Fallback to last isolated digit group
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", stem)
    return numbers[-1] if numbers else "01"

def parse_title_fallback(filename: str) -> str:
    """Extract readable clean title from filename stem."""
    stem = os.path.splitext(filename)[0]
    # Remove chapter markers and clean characters
    clean = re.sub(r'(?i)\b(ch|chapter|vol|volume|ep|episode)\b[\s._-]*\d+', '', stem)
    clean = re.sub(r'[\._-]', ' ', clean)
    return re.sub(r'\s+', ' ', clean).strip() or "Manga"

async def rename_file(user_id: int, original_filename: str) -> str:
    try:
        ext = os.path.splitext(original_filename)[1].lower()
        config = await get_user_config(user_id)
        
        template = config.get("format", "{title} - Ch {chapter} [{channel}]")
        custom_title = config.get("title", None)
        channel_name = config.get("channel_name", "@MangaChannel")

        chapter = extract_chapter_number(original_filename)
        title = custom_title if custom_title else parse_title_fallback(original_filename)

        # Apply substitutions
        formatted = template
        replacements = {
            "{chapter}": chapter,
            "{title}": title,
            "{channel}": channel_name,
            "episode": chapter,  # Legacy fallback
            "quality": "HD"
        }
        
        for key, val in replacements.items():
            formatted = formatted.replace(key, str(val))

        # Sanitize output filename
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', formatted)
        safe_name = re.sub(r'\s+', ' ', safe_name).strip()
        
        return f"{safe_name}{ext}"

    except Exception as e:
        LOGGER.error(f"Rename pipeline error: {e}")
        return original_filename
