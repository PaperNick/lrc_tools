#!/usr/bin/env python3

import re
from pathlib import Path
from typing import List, Tuple

from .regex import RE_LRC_METADATA, RE_LRC_TIMESTAMP
from .timestamps import format_timestamp


def sylt_to_lrc(entries: List[Tuple[str, int]]) -> str:
    """Convert SYLT entries [(text, ms)] to LRC format string."""
    lines = []
    for text, time_ms in entries:
        if time_ms == 0:
            lines.append(text)
        elif text:
            lines.append(f"{format_timestamp(time_ms)} {text}")
        else:
            lines.append(f"{format_timestamp(time_ms)} ")
    return "\n".join(lines)


def parse_lrc_timestamps(lrc_content: str) -> List[Tuple[str, int]]:
    """Parse LRC content into [(text, timestamp_ms)] tuples."""
    entries: List[Tuple[str, int]] = []

    for line in lrc_content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        timestamps = re.findall(r"\[(\d+):(\d+(?:\.\d+)?)\]", stripped)
        text = RE_LRC_TIMESTAMP.sub("", stripped).strip()

        # Line is just a metadata tag like [ti:Title], skip it
        if RE_LRC_METADATA.match(text):
            continue

        if not timestamps:
            if text:
                entries.append((text, 0))
            continue

        # Use last timestamp
        min_str, sec_str = timestamps[-1]
        time_ms = int(int(min_str) * 60_000 + float(sec_str) * 1000)
        entries.append((text, time_ms))

    return entries
