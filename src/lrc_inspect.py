#!/usr/bin/env python3

import argparse
import re
import sys
from pathlib import Path

from mutagen.id3 import ID3, ID3NoHeaderError

# LRC classification results
TIMED = "TIMED"
PLAIN = "PLAIN"
EMPTY = "EMPTY"

# MP3 classification results
SYLT_PLUS_USLT = "SYLT+USLT"
SYLT_ONLY = "SYLT_ONLY"
USLT_ONLY = "USLT_ONLY"
NO_LYRICS = "NO_LYRICS"

ERROR = "ERROR"
UNKNOWN = "UNKNOWN"


def classify_lrc(lrc_path: Path) -> str:
    if not lrc_path.is_file():
        return ERROR

    try:
        content = lrc_path.read_text(encoding="utf-8")
    except Exception:
        return ERROR

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"\[[a-z]+:.*\]", stripped, re.IGNORECASE):
            continue
        if re.match(r"\[\d+:\d+\.?\d*\]", stripped):
            return TIMED
        return PLAIN

    return EMPTY


def classify_mp3(mp3_path: Path) -> str:
    if not mp3_path.is_file():
        return ERROR

    try:
        audio = ID3(mp3_path)
    except (ID3NoHeaderError, Exception):
        return NO_LYRICS

    has_sylt = len(audio.getall("SYLT")) > 0
    has_uslt = len(audio.getall("USLT")) > 0

    if has_sylt and has_uslt:
        return SYLT_PLUS_USLT
    if has_sylt:
        return SYLT_ONLY
    if has_uslt:
        return USLT_ONLY
    return NO_LYRICS


def result_line(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".lrc":
        return f"{classify_lrc(path)}: {path}"
    if suffix == ".mp3":
        return f"{classify_mp3(path)}: {path}"
    return f"{UNKNOWN}: {path}  (unsupported file extension)"


def build_parser(subparser) -> None:
    subparser.add_argument("target", nargs="?", help="MP3 or LRC file to inspect")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Identify type of MP3 file (lyrics tags) and LRC file (timed/plain)",
    )
    build_parser(parser)
    args = parser.parse_args()

    if not args.target:
        parser.print_help()
        sys.exit(1)

    path = Path(args.target)
    suffix = path.suffix.lower()

    if suffix not in (".lrc", ".mp3"):
        print(f"Error: {path}  (unsupported file extension)")
        sys.exit(1)
    if not path.is_file():
        print(f"Error: {path}  (not found)")
        sys.exit(1)

    print(result_line(path))


if __name__ == "__main__":
    main()
