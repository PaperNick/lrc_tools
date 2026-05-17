#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import Tuple

from utils.id3 import LyricsData, read_lyrics
from utils.language import lang_3to2, FALLBACK_LANG3
from utils.parsing import sylt_to_lrc


def _extract_timed(data: LyricsData) -> Tuple[str, str]:
    """Extract SYLT as LRC content."""
    if not data.has_sylt:
        print("  No timed lyrics (SYLT) found.")
        sys.exit(1)

    lang_2letter = lang_3to2(data.sylt_lang or FALLBACK_LANG3)
    count = len(data.sylt_entries)
    print(f"  Found SYLT: {count} timed entries (lang: {data.sylt_lang} -> {lang_2letter})")
    return sylt_to_lrc(data.sylt_entries), lang_2letter


def _extract_plain(data: LyricsData) -> Tuple[str, str]:
    """Extract USLT as LRC content."""
    if not data.has_uslt:
        print("  No plain lyrics (USLT) found.")
        sys.exit(1)

    lang_2letter = lang_3to2(data.uslt_lang or FALLBACK_LANG3)
    print(f"  Found USLT: plain lyrics (lang: {data.uslt_lang} -> {lang_2letter})")
    return data.uslt_text.strip() + "\n", lang_2letter


def _extract_auto(data: LyricsData) -> Tuple[str, str]:
    """Prefer SYLT, fall back to USLT."""
    if not data.has_sylt and not data.has_uslt:
        print("No embedded lyrics found (no SYLT or USLT frames).")
        sys.exit(1)

    if data.has_sylt:
        if data.has_uslt:
            print(f"  Also has USLT (lang: {data.uslt_lang}) - using SYLT as primary source")
        return _extract_timed(data)
    return _extract_plain(data)


def _resolve_output(mp3_path: Path, lang_2letter: str, output_path: str | None) -> Path:
    if output_path:
        return Path(output_path)

    return mp3_path.with_name(f"{mp3_path.stem}.{lang_2letter}.lrc")


def _write_lrc(out: Path, content: str, dry_run: bool) -> None:
    print(f"  Output: {out}")

    if out.exists():
        print("  WARNING: Output file already exists, will overwrite")

    if dry_run:
        print(f"  [DRY RUN] Would write {len(content)} bytes to {out}")
        return

    out.write_text(content, encoding="utf-8")
    print(f"  Written: {out} ({len(content)} bytes, {content.count('\n')} lines)")


def build_parser(subparser) -> None:
    subparser.add_argument("mp3_file", nargs="?", help="MP3 file to extract lyrics from")
    subparser.add_argument(
        "kind",
        nargs="?",
        choices=["timed", "plain"],
        default=None,
        help="Type of lyrics to extract: 'timed' (SYLT) or 'plain' (USLT). If omitted, extracts SYLT with fallback to USLT.",
    )
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

    print(mp3_path)

    data = read_lyrics(mp3_path)

    extract = {"timed": _extract_timed, "plain": _extract_plain}.get(args.kind, _extract_auto)
    lrc_content, lang_2letter = extract(data)

    out = _resolve_output(mp3_path, lang_2letter, args.output)
    _write_lrc(out, lrc_content, args.dry_run)


if __name__ == "__main__":
    main()
