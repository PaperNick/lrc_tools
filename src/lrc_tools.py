#!/usr/bin/env python3

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LRC Tools - unified CLI for LRC lyrics and MP3 files",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    import lrc_read
    import lrc_embed
    import lrc_extract
    import lrc_clean
    import lrc_type

    read_p = subparsers.add_parser(
        "read", help="Read embedded lyrics (SYLT/USLT) from MP3 to stdout"
    )
    lrc_read.build_parser(read_p)

    embed_p = subparsers.add_parser("embed", help="Embed LRC lyrics into MP3 as SYLT + USLT frames")
    lrc_embed.build_parser(embed_p)

    extract_p = subparsers.add_parser(
        "extract", help="Extract embedded lyrics (SYLT/USLT) from MP3 to LRC file"
    )
    lrc_extract.build_parser(extract_p)

    clean_p = subparsers.add_parser(
        "clean", help="Remove embedded lyrics (SYLT/USLT) from MP3 files"
    )
    lrc_clean.build_parser(clean_p)

    type_p = subparsers.add_parser(
        "type", help="Identify type of MP3 file (lyrics tags) and LRC file (timed/plain)"
    )
    lrc_type.build_parser(type_p)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        exit(1)

    # Replace sys.argv so submodule main() works (strip command name)
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    dispatch = {
        "read": lrc_read.main,
        "embed": lrc_embed.main,
        "extract": lrc_extract.main,
        "clean": lrc_clean.main,
        "type": lrc_type.main,
    }
    dispatch[args.command]()


if __name__ == "__main__":
    main()
