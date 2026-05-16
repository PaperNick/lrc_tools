#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

from mutagen.id3 import ID3, ID3NoHeaderError

from language import lang_3to2


def format_timestamp(time_ms: int) -> str:
    """Convert milliseconds to LRC timestamp [mm:ss.xx]."""
    minutes, rest = divmod(time_ms, 60_000)
    seconds, centiseconds = divmod(rest, 1000)
    centiseconds //= 10
    return f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]"


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


def extract_lyrics(mp3_path: Path) -> dict:
    result = {
        "has_sylt": False,
        "has_uslt": False,
        "sylt_entries": None,
        "sylt_lang": None,
        "uslt_text": None,
        "uslt_lang": None,
    }

    try:
        audio = ID3(mp3_path)
    except ID3NoHeaderError:
        return result

    sylt = audio.getall("SYLT")
    if sylt:
        result["has_sylt"] = True
        result["sylt_entries"] = sylt[0].text
        result["sylt_lang"] = sylt[0].lang

    uslt = audio.getall("USLT")
    if uslt:
        result["has_uslt"] = True
        result["uslt_text"] = uslt[0].text
        result["uslt_lang"] = uslt[0].lang

    return result


def output_path(mp3_path: Path, lang_2letter: str, output_arg: str | None) -> Path:
    if output_arg:
        return Path(output_arg)
    return mp3_path.with_name(f"{mp3_path.stem}.{lang_2letter}.lrc")


def build_parser(subparser) -> None:
    subparser.add_argument("mp3_file", nargs="?", help="MP3 file to extract lyrics from")
    subparser.add_argument(
        "--output",
        "-o",
        help="Write to a specific output path (default: auto-named based on language)",
    )
    subparser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be extracted without writing files",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract embedded lyrics (SYLT/USLT) from MP3 to LRC file",
    )
    build_parser(parser)
    args = parser.parse_args()

    if not args.mp3_file:
        parser.print_help()
        sys.exit(1)

    mp3_path = Path(args.mp3_file)
    if not mp3_path.is_file():
        print(f"Error: File not found: {mp3_path}")
        sys.exit(1)
    if mp3_path.suffix.lower() != ".mp3":
        print(f"Error: Not an MP3 file: {mp3_path}")
        sys.exit(1)

    data = extract_lyrics(mp3_path)

    if not data["has_sylt"] and not data["has_uslt"]:
        print("No embedded lyrics found (no SYLT or USLT frames).")
        sys.exit(1)

    print(mp3_path)

    if data["has_sylt"]:
        sylt_lang = data["sylt_lang"] or "eng"
        lang_2letter = lang_3to2(sylt_lang)
        lrc_content = sylt_to_lrc(data["sylt_entries"])
        print(
            f"  Found SYLT: {len(data['sylt_entries'])} timed entries (lang: {sylt_lang} -> {lang_2letter})"
        )
        if data["has_uslt"]:
            print(f"  Also has USLT (lang: {data['uslt_lang']}) - using SYLT as primary source")
    else:
        uslt_lang = data["uslt_lang"] or "eng"
        lang_2letter = lang_3to2(uslt_lang)
        lrc_content = data["uslt_text"].strip() + "\n"
        print(f"  Found USLT: plain lyrics (lang: {uslt_lang} -> {lang_2letter})")

    out = output_path(mp3_path, lang_2letter, args.output)
    print(f"  Output: {out}")

    if out.exists():
        print("  WARNING: Output file already exists, will overwrite")

    if args.dry_run:
        print(f"  [DRY RUN] Would write {len(lrc_content)} bytes to {out}")
        return

    out.write_text(lrc_content, encoding="utf-8")
    print(f"  Written: {out} ({len(lrc_content)} bytes, {lrc_content.count('\n')} lines)")


if __name__ == "__main__":
    main()
