#!/usr/bin/env python3

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import List, Tuple

from mutagen.id3 import ID3, SYLT, USLT, Encoding, ID3NoHeaderError
from mutagen.mp3 import MP3

from utils.language import lang_2to3, FALLBACK_LANG3
from utils.parsing import parse_lrc_timestamps
from utils.timestamps import lrc_has_timestamps, strip_timestamps


def detect_lang_from_filename(lrc_path: Path) -> str | None:
    """Detect 2-letter code from filename like 'Song.ja.lrc' -> 'jpn'."""
    stem = lrc_path.stem
    match = re.search(r"\.([a-z]{2})$", stem, re.IGNORECASE)
    if match:
        return lang_2to3(match.group(1).lower())
    return None


def resolve_lang(cli_lang: str | None, lrc_path: Path) -> str:
    """Resolve language: --lang flag, filename detection."""
    if cli_lang:
        return cli_lang
    return detect_lang_from_filename(lrc_path) or FALLBACK_LANG3


def open_or_create_id3(mp3_path: Path):
    """Open existing ID3 tags or create new ones."""
    try:
        return ID3(mp3_path)
    except ID3NoHeaderError:
        audio = MP3(mp3_path)
        audio.add_tags()
        return ID3(mp3_path)


def has_frame(mp3_path: Path, frame_id: str) -> bool:
    """Check if an MP3 already has a given frame type."""
    try:
        return len(ID3(mp3_path).getall(frame_id)) > 0
    except Exception:
        return False


def find_matching_lrc(mp3_path: Path) -> Path | None:
    """Auto-discover an LRC file by globbing {stem}*.lrc."""
    matches = sorted(mp3_path.parent.glob(f"{mp3_path.stem}*.lrc"))
    return matches[0] if matches else None


def resolve_target(mp3_path: Path, output_arg: str | None, in_place: bool) -> Path:
    """Determine the output file path."""
    if output_arg:
        return Path(output_arg)
    if in_place:
        return mp3_path
    return mp3_path.with_name(mp3_path.stem + " (lyrics)" + mp3_path.suffix)


def copy_mp3(src: Path, dst: Path, dry_run: bool) -> str | None:
    """Copy MP3 from src to dst if they differ. Returns None on success, error string on failure."""
    if dst.resolve() == src.resolve():
        return None
    if dry_run:
        return None
    try:
        shutil.copy2(src, dst)
        return None
    except Exception as e:
        return f"Copy error: {e}"


def embed_sylt(target: Path, lrc_path: Path, lang: str, dry_run: bool) -> Tuple[bool, str]:
    """Embed SYLT frame. Returns (success, message)."""
    lrc_content = lrc_path.read_text(encoding="utf-8", errors="replace")
    entries = parse_lrc_timestamps(lrc_content)

    if not entries:
        return False, "No timed entries found in LRC file"

    if dry_run:
        return True, "Dry run"

    try:
        audio = open_or_create_id3(target)
        audio.delall("SYLT")
        audio["SYLT"] = SYLT(
            encoding=Encoding.UTF8,
            lang=lang,
            format=2,
            type=1,
            desc="",
            text=list(entries),
        )
        audio.save(target)
        return True, "SYLT embedded"
    except Exception as e:
        return False, f"mutagen SYLT error: {e}"


def embed_uslt(target: Path, plain_text: str, lang: str, dry_run: bool) -> Tuple[bool, str]:
    """Embed USLT frame. Returns (success, message)."""
    if dry_run:
        return True, "Dry run"

    try:
        audio = open_or_create_id3(target)
        audio.delall("USLT")
        audio["USLT"] = USLT(
            encoding=Encoding.UTF8,
            lang=lang,
            desc="",
            text=plain_text,
        )
        audio.save(target)
        return True, "USLT embedded"
    except Exception as e:
        return False, f"mutagen error: {e}"


def _embed_sylt_or_skip(target: Path, lrc_path: Path, lang: str, dry_run: bool, skip: bool) -> None:
    """Embed SYLT if requested, report skip or failure."""
    if skip:
        print("  SYLT: SKIPPED - Already present in MP3")
        return

    ok, msg = embed_sylt(target, lrc_path, lang, dry_run)
    print(f"  SYLT: {'OK' if ok else 'FAIL'} - {msg}")


def _embed_uslt_or_skip(
    target: Path, lrc_path: Path, lang: str, dry_run: bool, skip: bool, lrc_timed: bool
) -> None:
    """Embed USLT if requested, report skip or failure."""
    if skip:
        print("  USLT: SKIPPED - Already present in MP3")
        return

    lrc_content = lrc_path.read_text(encoding="utf-8")
    plain_text = strip_timestamps(lrc_content) if lrc_timed else lrc_content.strip()
    if not plain_text.strip():
        print("  USLT: FAIL - No lyrics text found")
        return

    ok, msg = embed_uslt(target, plain_text, lang, dry_run)
    print(f"  USLT: {'OK' if ok else 'FAIL'} - {msg}")


def build_parser(subparser) -> None:
    subparser.add_argument("mp3_file", help="MP3 file to embed lyrics into")
    subparser.add_argument(
        "lrc_file", nargs="?", help="LRC lyrics file (auto-discovered if omitted)"
    )
    subparser.add_argument(
        "--lang",
        help=f"3-letter ISO 639-2 language code (auto-detected from filename, fallback '{FALLBACK_LANG3}')",
    )
    subparser.add_argument(
        "--no-timed", action="store_true", help="Skip embedding timed lyrics (SYLT)"
    )
    subparser.add_argument(
        "--no-plain", action="store_true", help="Skip embedding plain lyrics (USLT)"
    )
    subparser.add_argument(
        "--output", "-o", help='Output file path (default: "source (lyrics).mp3")'
    )
    subparser.add_argument(
        "--in-place",
        action="store_true",
        help="Modify original MP3 directly instead of creating a copy",
    )
    subparser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without modifying files",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed LRC lyrics into MP3 as SYLT + USLT (Lyrics tag)",
    )
    build_parser(parser)
    args = parser.parse_args()

    if not args.mp3_file:
        parser.print_help()
        sys.exit(1)

    if args.no_timed and args.no_plain:
        print("Error: Both --no-timed and --no-plain specified. Nothing to do.")
        sys.exit(1)

    mp3_path = Path(args.mp3_file)
    if mp3_path.suffix.lower() != ".mp3":
        print(f"Error: First argument must be an MP3 file: {mp3_path}")
        sys.exit(1)
    if not mp3_path.is_file():
        print(f"Error: MP3 file not found: {mp3_path}")
        sys.exit(1)

    print(mp3_path)

    if args.lrc_file:
        lrc_path = Path(args.lrc_file)
        if not lrc_path.is_file():
            print(f"  Error: LRC file not found: {lrc_path}")
            sys.exit(1)
        if lrc_path.suffix.lower() != ".lrc":
            print(f"  Error: Second argument must be an LRC file: {lrc_path}")
            sys.exit(1)
    else:
        lrc_path = find_matching_lrc(mp3_path)
        if lrc_path is None:
            print(f"  Error: No LRC file found matching '{mp3_path.stem}*.lrc'")
            sys.exit(1)
        print(f"  Auto-discovered LRC: {lrc_path}")

    lang = resolve_lang(args.lang, lrc_path)
    print(f"  Language: {lang}")

    target = resolve_target(mp3_path, args.output, args.in_place)
    label = " (in-place)" if target == mp3_path else ""
    print(f"  Output: {target}{label}")

    lrc_timed = lrc_has_timestamps(lrc_path)
    print(f"  LRC type: {'TIMED' if lrc_timed else 'PLAIN'}")

    do_sylt = not args.no_timed and lrc_timed
    do_uslt = not args.no_plain

    # Check what the source already has before any copy
    skip_sylt = do_sylt and has_frame(mp3_path, "SYLT")
    skip_uslt = do_uslt and has_frame(mp3_path, "USLT")

    if skip_sylt and skip_uslt:
        print("  SKIPPED: All requested lyrics types already present")
        return

    err = copy_mp3(mp3_path, target, args.dry_run)
    if err:
        print(f"  ERROR: {err}")
        sys.exit(1)

    if do_sylt:
        _embed_sylt_or_skip(target, lrc_path, lang, args.dry_run, skip_sylt)
    else:
        print("  SYLT: SKIPPED - Not requested or LRC has no timestamps")

    if do_uslt:
        _embed_uslt_or_skip(target, lrc_path, lang, args.dry_run, skip_uslt, lrc_timed)
    else:
        print("  USLT: SKIPPED - Not requested")


if __name__ == "__main__":
    main()
