#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from mutagen.id3 import ID3, ID3NoHeaderError


@dataclass
class LyricsData:
    """Container for SYLT/USLT lyrics extracted from an MP3."""

    has_sylt: bool = False
    has_uslt: bool = False
    sylt_entries: List[Tuple[str, int]] | None = None
    sylt_lang: str | None = None
    uslt_text: str | None = None
    uslt_lang: str | None = None


def read_lyrics(mp3_path: Path) -> LyricsData:
    result = LyricsData()

    try:
        audio = ID3(mp3_path)
    except ID3NoHeaderError:
        return result

    sylt = audio.getall("SYLT")
    if sylt:
        result.has_sylt = True
        result.sylt_entries = sylt[0].text
        result.sylt_lang = sylt[0].lang

    uslt = audio.getall("USLT")
    if uslt:
        result.has_uslt = True
        result.uslt_text = uslt[0].text
        result.uslt_lang = uslt[0].lang

    return result
