#!/usr/bin/env python3

import re
from pathlib import Path
from typing import List, Tuple

from .regex import RE_LRC_METADATA, RE_LRC_TIMESTAMP


def format_timestamp(time_ms: int) -> str:
    """Convert milliseconds to LRC timestamp [mm:ss.xx]."""
    minutes, rest = divmod(time_ms, 60_000)
    seconds, centiseconds = divmod(rest, 1000)
    centiseconds //= 10
    return f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]"


def strip_timestamps(lrc_content: str) -> str:
    """Strip LRC timestamps, keeping text lines in order."""
    result_lines: List[str] = []

    for line in lrc_content.splitlines():
        stripped = line.strip()
        if not stripped:
            result_lines.append("")
            continue

        timestamps = RE_LRC_TIMESTAMP.findall(stripped)
        text = RE_LRC_TIMESTAMP.sub("", stripped).strip()

        # Line is just a metadata tag like [ti:Title], skip it
        if RE_LRC_METADATA.match(text):
            continue

        if not timestamps:
            if text:
                result_lines.append(text)
            continue

        result_lines.append(text if text else "")

    while result_lines and result_lines[-1] == "":
        result_lines.pop()

    return "\n".join(result_lines)


def lrc_has_timestamps(lrc_path: Path) -> bool:
    """Return True if the LRC file has timestamp lines."""
    if not lrc_path.is_file():
        return False
    try:
        content = lrc_path.read_text(encoding="utf-8")
        return bool(RE_LRC_TIMESTAMP.search(content))
    except Exception:
        return False
