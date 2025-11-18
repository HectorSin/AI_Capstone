from pathlib import Path
from typing import Optional

from app.config import settings

UPLOAD_DIR = Path(settings.upload_dir)


def resolve_podcast_path(audio_path: str) -> Optional[Path]:
    """Return absolute path to an audio file if it exists."""
    candidate = Path(audio_path)
    if candidate.exists():
        return candidate
    candidate = (UPLOAD_DIR / audio_path.lstrip('/')).resolve()
    if candidate.exists():
        return candidate
    return None
