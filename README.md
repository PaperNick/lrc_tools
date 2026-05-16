# lrc-tools

Unified CLI for embedding, extracting, cleaning, and inspecting LRC lyrics in MP3 files.


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
lrc_tools embed --help
lrc_tools extract --help
lrc_tools clean --help
lrc_tools type --help
```

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

# Skip SYLT or USLT
lrc_tools embed song.mp3 --no-sylt
lrc_tools embed song.mp3 --no-uslt

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

# Remove only SYLT or only USLT
lrc_tools clean song.mp3 --sylt-only
lrc_tools clean song.mp3 --uslt-only

# Skip confirmation prompt
lrc_tools clean song.mp3 --yes

# Preview what would be removed
lrc_tools clean song.mp3 --dry-run
```

Confirms before modifying by default. Use `--yes` or `-y` to skip.

---

### type

Inspect an MP3 or LRC file and print its type classification.

```shell
# Check an MP3
lrc_tools type song.mp3
# → SYLT+USLT: song.mp3
# → SYLT_ONLY: song.mp3
# → USLT_ONLY: song.mp3
# → NO_LYRICS: song.mp3

# Check an LRC file
lrc_tools type lyrics.lrc
# → TIMED: lyrics.lrc
# → PLAIN: lyrics.lrc
# → EMPTY: lyrics.lrc
```
