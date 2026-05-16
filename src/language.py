import json
import sys
from pathlib import Path

_COUNTRY_TO_LANG = json.loads((Path(__file__).parent / "data" / "language_codes.json").read_text())[
    "COUNTRY_TO_LANG"
]
_LANG_TO_COUNTRY = {v: k for k, v in _COUNTRY_TO_LANG.items()}


def lang_3to2(lang3: str) -> str:
    """Convert 3-letter ISO 639-2/B to 2-letter ISO 639-1. Fallback to original."""
    return _LANG_TO_COUNTRY.get(lang3.lower(), lang3)


def lang_2to3(lang2: str) -> str | None:
    """Convert 2-letter ISO 639-1 to 3-letter ISO 639-2/B. Fallback to None."""
    return _COUNTRY_TO_LANG.get(lang2.lower())
