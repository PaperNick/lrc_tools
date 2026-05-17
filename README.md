# lrc-tools

Unified CLI for reading, embedding, extracting, cleaning, and inspecting LRC lyrics in MP3 files.


## Requirements

- Python 3.10+
- [mutagen](https://mutagen.readthedocs.io/) - audio metadata library


## Install


### Pre-built binaries

> [!NOTE]
> Pre-built binaries for Linux, Windows, and macOS are available on the [releases page](https://github.com/PaperNick/lrc_tools/releases).


### Build from source

Create a virtual environment, install dependencies, and build with PyInstaller:

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pyinstaller lrc_tools.spec
```

The binary will be at `dist/lrc_tools`. Copy it anywhere on your `PATH`:

```shell
cp dist/lrc_tools ~/.local/bin/
deactivate
```

### Run with Python directly

Each script can be run without building:

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 src/lrc_tools.py --help
```

## Usage

All examples below assume the binary `lrc_tools` is on your `PATH`.
Replace `lrc_tools` with `python3 src/lrc_tools.py` if running from source.

```shell
# Show available subcommands
lrc_tools --help

# Get help for a specific subcommand
lrc_tools read --help
lrc_tools embed --help
lrc_tools extract --help
lrc_tools clean --help
lrc_tools inspect --help
```

---

### read

Read embedded lyrics from an MP3 directly to stdout. Ideal for piping into other tools.

```shell
# Print summary of available lyrics (to stderr)
lrc_tools read song.mp3

# Output timed lyrics (SYLT) as LRC format
lrc_tools read song.mp3 timed

# Output plain lyrics (USLT) as plain text
lrc_tools read song.mp3 plain

# Include language code header on the first line
lrc_tools read song.mp3 timed --include-lang
lrc_tools read song.mp3 plain --include-lang

# Pipe
lrc_tools read song.mp3 timed | grep "love"
```

When no `kind` is specified, a summary is printed to stderr showing which lyric types are available.

The `--include-lang` flag prepends a `Language: xx` header line using the resolved
2-letter ISO 639-1 code (e.g. `Language: ja` for Japanese, `Language: en` for English).

---

### embed

Embed LRC lyrics into an MP3 as SYLT (synchronized) and/or USLT (unsynchronized) frames.

```shell
# Embed with auto-discovered LRC file
lrc_tools embed song.mp3

# Specify LRC file explicitly
lrc_tools embed song.mp3 lyrics.lrc

# Override language (3-letter ISO 639-2 code)
lrc_tools embed song.mp3 --lang kor

# Modify original MP3 instead of creating a copy
lrc_tools embed song.mp3 --in-place

# Write to a specific output file
lrc_tools embed song.mp3 --output tagged.mp3

# Skip embedding timed (SYLT) or plain (USLT) lyrics
lrc_tools embed song.mp3 --no-timed
lrc_tools embed song.mp3 --no-plain

# Preview without writing
lrc_tools embed song.mp3 --dry-run
```

If no LRC file is provided, it auto-discovers one by globbing `{stem}*.lrc` (e.g. `son.ko.lrc` for `song.mp3`). Language is auto-detected from the filename suffix (e.g. `.ko.lrc` -> `kor`), and defaults to `eng`.

---

### extract

Extract embedded SYLT/USLT lyrics from an MP3 to an LRC file.

```shell
# Extract to auto-named file (e.g. Song.en.lrc)
lrc_tools extract song.mp3

# Specify output path
lrc_tools extract song.mp3 --output lyrics.lrc

# Preview what would be written
lrc_tools extract song.mp3 --dry-run
```

Output is named `{stem}.{lang_2letter}.lrc` by default (e.g. `Song.en.lrc`). SYLT is preferred over USLT when both are present.

---

### clean

Remove SYLT/USLT frames from an MP3.

```shell
# Remove all lyrics frames
lrc_tools clean song.mp3

# Remove only timed (SYLT) or only plain (USLT) lyrics
lrc_tools clean song.mp3 --timed-only
lrc_tools clean song.mp3 --plain-only

# Skip confirmation prompt
lrc_tools clean song.mp3 --yes

# Preview what would be removed
lrc_tools clean song.mp3 --dry-run
```

Confirms before modifying by default. Use `--yes` or `-y` to skip.

---

### inspect

Inspect an MP3 or LRC file and print its type classification.

```shell
# Check an MP3
lrc_tools inspect song.mp3
# → SYLT+USLT: song.mp3
# → SYLT_ONLY: song.mp3
# → USLT_ONLY: song.mp3
# → NO_LYRICS: song.mp3

# Check an LRC file
lrc_tools inspect lyrics.lrc
# → TIMED: lyrics.lrc
# → PLAIN: lyrics.lrc
# → EMPTY: lyrics.lrc
```
