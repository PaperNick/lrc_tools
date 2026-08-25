import json
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE = Path(sys._MEIPASS)
else:
    BASE = Path(__file__).resolve().parent.parent

_COUNTRY_TO_LANG = json.loads((BASE / "data" / "language_codes.json").read_text())[
    "COUNTRY_TO_LANG"
]
_LANG_TO_COUNTRY = {v: k for k, v in _COUNTRY_TO_LANG.items()}


FALLBACK_LANG2 = "en"
FALLBACK_LANG3 = "eng"


def lang_3to2(lang3: str) -> str | None:
    """Convert 3-letter ISO 639-2/B to 2-letter ISO 639-1."""
    return _LANG_TO_COUNTRY.get(lang3.lower())


def lang_2to3(lang2: str) -> str | None:
    """Convert 2-letter ISO 639-1 to 3-letter ISO 639-2/B."""
    return _COUNTRY_TO_LANG.get(lang2.lower())


def is_valid_lang(lang: str) -> bool:
    """Validate the provided ISO 639 code (2 or 3 letters)."""
    if len(lang) == 2:
        return lang_2to3(lang) is not None
    if len(lang) == 3:
        return lang_3to2(lang) is not None
    return False
