#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import List

from mutagen.id3 import ID3, ID3NoHeaderError

SYLT = "SYLT"
USLT = "USLT"


def remove_lyrics(mp3_path: Path, *, remove_sylt: bool, remove_uslt: bool) -> str:
    """Remove SYLT/USLT frames from an MP3. Returns a human-readable result."""
    try:
        audio = ID3(mp3_path)
    except ID3NoHeaderError:
        return "No ID3 tag found"
    except Exception as exc:
        return f"Cannot read MP3: {exc}"

    removed = []
    if remove_sylt and audio.getall(SYLT):
        audio.delall(SYLT)
        removed.append(SYLT)
    if remove_uslt and audio.getall(USLT):
        audio.delall(USLT)
        removed.append(USLT)

    if not removed:
        return "Nothing to remove (requested types not found)"

    try:
        audio.save(mp3_path)
    except Exception as exc:
        return f"Cannot save after removal: {exc}"

    return f"Removed: {', '.join(removed)}"


def find_lyrics_frames(mp3_path: Path) -> List[str]:
    """Return list of lyrics frame types in the MP3."""
    try:
        audio = ID3(mp3_path)
    except Exception:
        return []

    found = []
    if audio.getall(SYLT):
        found.append(SYLT)
    if audio.getall(USLT):
        found.append(USLT)
    return found


def confirm_action(description: str) -> bool:
    print(f"\nAre you sure you want to {description}?")
    return input("Continue? [y/N] ").strip().lower() in ("y", "yes")


def build_parser(subparser) -> None:
    subparser.add_argument("mp3_file", nargs="?", help="MP3 file to clean lyric metadata from")
    subparser.add_argument(
        "--timed-only",
        action="store_true",
        help="Only remove timed lyrics (SYLT), keep plain (USLT)",
    )
    subparser.add_argument(
        "--plain-only",
        action="store_true",
        help="Only remove plain lyrics (USLT), keep timed (SYLT)",
    )
    subparser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be removed without modifying files",
    )
    subparser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove embedded lyrics (SYLT/USLT) from MP3 files",
    )
    build_parser(parser)
    args = parser.parse_args()

    if not args.mp3_file:
        parser.print_help()
        sys.exit(1)

    if args.timed_only and args.plain_only:
        print("Error: Both --timed-only and --plain-only specified, nothing would be removed.")
        sys.exit(1)

    mp3_path = Path(args.mp3_file)
    if not mp3_path.is_file():
        print(f"Error: File not found: {mp3_path}")
        sys.exit(1)
    if mp3_path.suffix.lower() != ".mp3":
        print(f"Error: Not an MP3 file: {mp3_path}")
        sys.exit(1)

    if args.timed_only:
        remove_sylt, remove_uslt = True, False
    elif args.plain_only:
        remove_sylt, remove_uslt = False, True
    else:
        remove_sylt, remove_uslt = True, True

    present_frames = find_lyrics_frames(mp3_path)

    sylt_status = "present" if SYLT in present_frames else "not-found"
    uslt_status = "present" if USLT in present_frames else "not-found"
    print(f"{mp3_path.name}  SYLT={sylt_status}  USLT={uslt_status}")

    will_remove = []
    if remove_sylt and SYLT in present_frames:
        will_remove.append(SYLT)
    if remove_uslt and USLT in present_frames:
        will_remove.append(USLT)

    if not will_remove:
        print(f"No remaining lyrics found to clean in {mp3_path.name}")
        sys.exit(0)

    if args.dry_run:
        print(f"[DRY RUN] Would remove: {', '.join(will_remove)}")
        return

    if not args.yes and not confirm_action(f"remove lyric metadata from '{mp3_path}'"):
        print("Aborted.")
        sys.exit(0)

    result = remove_lyrics(mp3_path, remove_sylt=remove_sylt, remove_uslt=remove_uslt)
    print(result)
    if result.startswith("Cannot") or result.startswith("No ID3"):
        sys.exit(1)


if __name__ == "__main__":
    main()
