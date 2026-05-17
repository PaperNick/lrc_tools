#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from utils.id3 import LyricsData, read_lyrics
from utils.language import lang_3to2
from utils.parsing import sylt_to_lrc
from utils.timestamps import format_timestamp


def validate_args(args, parser) -> Path:
    """Validate CLI args and return resolved mp3 Path, or exit."""
    if not args.mp3_file:
        parser.print_help()
        sys.exit(1)

    mp3_path = Path(args.mp3_file)
    if not mp3_path.is_file():
        print(f"Error: File not found: {mp3_path}", file=sys.stderr)
        sys.exit(1)
    if mp3_path.suffix.lower() != ".mp3":
        print(f"Error: Not an MP3 file: {mp3_path}", file=sys.stderr)
        sys.exit(1)

    return mp3_path


def _language_header(lang_code: str | None) -> str:
    """Resolve language code into a 'Language: xx' header line."""
    lang = lang_code or "eng"
    return f"Language: {lang_3to2(lang)}"


def output_timed(data: LyricsData, include_lang: bool) -> None:
    """Print timed lyrics (SYLT) to stdout."""
    if not data.has_sylt:
        print("No timed lyrics (SYLT) found.", file=sys.stderr)
        sys.exit(1)

    output = sylt_to_lrc(data.sylt_entries)
    if include_lang:
        output = f"{_language_header(data.sylt_lang)}\n{output}"
    print(output)


def output_plain(data: LyricsData, include_lang: bool) -> None:
    """Print plain lyrics (USLT) to stdout."""
    if not data.has_uslt:
        print("No plain lyrics (USLT) found.", file=sys.stderr)
        sys.exit(1)

    output = data.uslt_text.strip()
    if include_lang:
        output = f"{_language_header(data.uslt_lang)}\n{output}"
    print(output)


def print_summary(mp3_path: Path, data: LyricsData) -> None:
    """Print a human-readable summary of available lyrics to stderr."""
    if not data.has_sylt and not data.has_uslt:
        print("No embedded lyrics found (no SYLT or USLT frames).", file=sys.stderr)
        sys.exit(1)

    print(mp3_path, file=sys.stderr)

    if data.has_sylt:
        sylt_lang = data.sylt_lang or "eng"
        lang_2letter = lang_3to2(sylt_lang)
        count = len(data.sylt_entries)
        print(
            f"  SYLT (timed, {count} entries, lang: {sylt_lang} -> {lang_2letter})",
            file=sys.stderr,
        )

    if data.has_uslt:
        uslt_lang = data.uslt_lang or "eng"
        lang_2letter = lang_3to2(uslt_lang)
        text_len = len(data.uslt_text)
        print(
            f"  USLT (plain, {text_len} chars, lang: {uslt_lang} -> {lang_2letter})",
            file=sys.stderr,
        )

    print(file=sys.stderr)
    print("Use 'timed' or 'plain' to output lyrics content.", file=sys.stderr)


def build_parser(subparser) -> None:
    subparser.add_argument("mp3_file", nargs="?", help="MP3 file to read lyrics from")
    subparser.add_argument(
        "kind",
        nargs="?",
        choices=["plain", "timed"],
        default=None,
        help="Type of lyrics to read: 'plain' (USLT) or 'timed' (SYLT). If omitted, prints summary.",
    )
    subparser.add_argument(
        "--include-lang",
        action="store_true",
        help="Prepend a 'Language: xx' header line using the resolved or fallback language code",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read embedded lyrics (SYLT/USLT) from MP3 to stdout",
    )
    build_parser(parser)
    args = parser.parse_args()

    mp3_path = validate_args(args, parser)
    data = read_lyrics(mp3_path)

    if args.kind == "timed":
        output_timed(data, args.include_lang)
    elif args.kind == "plain":
        output_plain(data, args.include_lang)
    else:
        print_summary(mp3_path, data)


if __name__ == "__main__":
    main()
