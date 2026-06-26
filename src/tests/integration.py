import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
BINARY_NAME = "lrc_tools.exe" if sys.platform == "win32" else "lrc_tools"
LRCTOOLS_BINARY = ROOT / "dist" / BINARY_NAME
if not LRCTOOLS_BINARY.is_file():
    pytest.exit(
        f"Binary not found: {LRCTOOLS_BINARY}\n" f"Build it with:  pyinstaller {ROOT / 'lrc_tools.spec'}",
        returncode=3,
    )

TESTS = ROOT / "src" / "tests"
FIXTURES = TESTS / "fixtures"
WORKDIR = TESTS / "tmp"

CLEAN_MP3 = FIXTURES / "test.mp3"
PLAIN_LRC = FIXTURES / "plain.ja.lrc"
TIMED_LRC = FIXTURES / "timed.ja.lrc"
EMPTY_LRC = FIXTURES / "empty.en.lrc"

PLAIN_LRC_CONTENT = PLAIN_LRC.read_text(encoding="utf-8")
TIMED_LRC_CONTENT = TIMED_LRC.read_text(encoding="utf-8")

KNOWN_TYPES = {
    "plain": "PLAIN",
    "timed": "TIMED",
    "timed_plus_plain": "TIMED+PLAIN",
    "no_lyrics": "NO_LYRICS",
}


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [str(LRCTOOLS_BINARY), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and result.returncode != 0:
        args_repr = " ".join(args)
        raise AssertionError(
            f"Command failed (exit={result.returncode}): {LRCTOOLS_BINARY} {args_repr}\n"
            f"  stdout: {result.stdout}\n"
            f"  stderr: {result.stderr}"
        )
    return result


def clean_mp3(name: str = "work.mp3") -> Path:
    WORKDIR.mkdir(parents=True, exist_ok=True)
    dst = WORKDIR / name
    shutil.copy2(CLEAN_MP3, dst)
    return dst


def embed_inplace(mp3: Path, lrc: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return run("embed", str(mp3), str(lrc), "--in-place", *extra_args)


@pytest.fixture(autouse=True)
def managed_workdir():
    WORKDIR.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(WORKDIR)


def assert_inspect_classification(mp3: Path, expected_class: str) -> None:
    assert expected_class in run("inspect", str(mp3)).stdout


def assert_lyric_content(result: subprocess.CompletedProcess, kind: str) -> None:
    expected = TIMED_LRC_CONTENT if kind == "timed" else PLAIN_LRC_CONTENT
    assert result.stdout.rstrip("\n") == expected.rstrip("\n")


class TestInspect:
    @pytest.mark.parametrize(
        "fixture, expected",
        [
            (PLAIN_LRC, KNOWN_TYPES["plain"]),
            (TIMED_LRC, KNOWN_TYPES["timed"]),
            (EMPTY_LRC, KNOWN_TYPES["no_lyrics"]),
        ],
        ids=["plain", "timed", "empty"],
    )
    def test_lrc_classification(self, fixture, expected):
        assert expected in run("inspect", str(fixture)).stdout

    def test_clean_mp3_no_lyrics(self):
        assert_inspect_classification(CLEAN_MP3, KNOWN_TYPES["no_lyrics"])

    def test_mp3_with_plain_lrc(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, PLAIN_LRC)
        assert_inspect_classification(mp3, KNOWN_TYPES["plain"])

    def test_mp3_with_timed_lrc_only(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, TIMED_LRC, "--no-plain")
        assert_inspect_classification(mp3, KNOWN_TYPES["timed"])

    def test_mp3_with_timed_and_plain(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, TIMED_LRC)
        assert_inspect_classification(mp3, KNOWN_TYPES["timed_plus_plain"])


class TestEmbed:
    @pytest.mark.parametrize(
        "lrc, kind, frame_ok, expected_type",
        [
            (PLAIN_LRC, "plain", "USLT: OK", "plain"),
            (TIMED_LRC, "timed", "SYLT: OK", "timed_plus_plain"),
        ],
    )
    def test_embed_and_verify(self, lrc, kind, frame_ok, expected_type):
        mp3 = clean_mp3()
        result = embed_inplace(mp3, lrc)
        assert frame_ok in result.stdout
        assert_inspect_classification(mp3, KNOWN_TYPES[expected_type])
        assert_lyric_content(run("read", str(mp3), kind), kind)

    def test_in_place(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, TIMED_LRC)
        assert KNOWN_TYPES["timed_plus_plain"] in run("inspect", str(mp3)).stdout

    def test_with_output_flag(self):
        mp3 = clean_mp3()
        output = WORKDIR / "tagged.mp3"
        run("embed", str(mp3), str(TIMED_LRC), "--output", str(output))
        assert output.is_file()
        assert KNOWN_TYPES["no_lyrics"] in run("inspect", str(mp3)).stdout
        assert KNOWN_TYPES["timed"] in run("inspect", str(output)).stdout

    def test_lang_override(self):
        mp3 = clean_mp3()
        result = embed_inplace(mp3, PLAIN_LRC, "--lang", "kor")
        assert "Language: kor" in result.stdout
        assert "Language: ko" in run("read", str(mp3), "plain", "--include-lang").stdout

    def test_no_timed_flag(self):
        mp3 = clean_mp3()
        result = embed_inplace(mp3, TIMED_LRC, "--no-timed")
        assert "SYLT: SKIPPED" in result.stdout
        assert "USLT: OK" in result.stdout

        stdout = run("inspect", str(mp3)).stdout
        assert KNOWN_TYPES["timed"] not in stdout
        assert KNOWN_TYPES["plain"] in stdout

    def test_no_plain_flag(self):
        mp3 = clean_mp3()
        result = embed_inplace(mp3, TIMED_LRC, "--no-plain")
        assert "SYLT: OK" in result.stdout
        assert "USLT: SKIPPED" in result.stdout

        stdout = run("inspect", str(mp3)).stdout
        assert KNOWN_TYPES["timed"] in stdout
        assert KNOWN_TYPES["plain"] not in stdout

    def test_dry_run_does_not_modify(self):
        mp3 = clean_mp3()
        run("embed", str(mp3), str(TIMED_LRC), "--dry-run")
        assert KNOWN_TYPES["no_lyrics"] in run("inspect", str(mp3)).stdout

    def test_auto_discover_lrc(self):
        mp3 = clean_mp3(name="test.ja.mp3")
        lrc = mp3.with_suffix(".ja.lrc")
        shutil.copy2(PLAIN_LRC, lrc)
        result = run("embed", str(mp3))
        assert "Auto-discovered" in result.stdout
        assert "USLT: OK" in result.stdout


class TestExtract:
    @pytest.mark.parametrize(
        "lrc, kind",
        [
            (PLAIN_LRC, "plain"),
            (TIMED_LRC, "timed"),
        ],
    )
    def test_extract_kind(self, lrc, kind):
        mp3 = clean_mp3()
        embed_inplace(mp3, lrc)
        result = run("extract", str(mp3), kind)
        frame = "SYLT" if kind == "timed" else "USLT"
        assert f"Found {frame}" in result.stdout

        stem_parts = lrc.stem.split(".")
        lang = stem_parts[-1] if len(stem_parts) > 1 else None
        suffix = f".{lang}.lrc" if lang else ".lrc"
        extracted_lrc = mp3.with_name(f"{mp3.stem}{suffix}")
        assert extracted_lrc.is_file()

        content = extracted_lrc.read_text(encoding="utf-8")
        expected = TIMED_LRC_CONTENT if kind == "timed" else PLAIN_LRC_CONTENT
        assert content.rstrip("\n") == expected.rstrip("\n")

    def test_auto_extract_prefers_sylt(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, TIMED_LRC)
        assert "Found SYLT" in run("extract", str(mp3)).stdout

    def test_dry_run_no_file_created(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, TIMED_LRC)
        result = run("extract", str(mp3), "--dry-run")
        assert "DRY RUN" in result.stdout


class TestRead:
    def test_summary_to_stderr(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, TIMED_LRC)
        result = run("read", str(mp3))
        assert "SYLT" in result.stderr
        assert "USLT" in result.stderr
        assert result.stdout == ""

    def test_no_lyrics_fails(self):
        mp3 = clean_mp3()
        assert run("read", str(mp3), check=False).returncode != 0

    def test_read_timed_matches_fixture(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, TIMED_LRC)
        assert_lyric_content(run("read", str(mp3), "timed"), "timed")

    def test_read_plain_matches_fixture(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, PLAIN_LRC)
        assert_lyric_content(run("read", str(mp3), "plain"), "plain")

    def test_with_include_lang(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, TIMED_LRC)
        assert "Language: ja" in run("read", str(mp3), "timed", "--include-lang").stdout


class TestClean:
    def test_timed_only(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, TIMED_LRC)
        run("clean", str(mp3), "--timed-only", "-y")
        assert KNOWN_TYPES["timed"] not in run("inspect", str(mp3)).stdout

    def test_all_lyrics(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, TIMED_LRC)
        run("clean", str(mp3), "-y")
        assert KNOWN_TYPES["no_lyrics"] in run("inspect", str(mp3)).stdout

    def test_dry_run_preserves_lyrics(self):
        mp3 = clean_mp3()
        embed_inplace(mp3, TIMED_LRC)
        run("clean", str(mp3), "--dry-run", "-y")
        assert KNOWN_TYPES["timed"] in run("inspect", str(mp3)).stdout

    def test_idempotent_on_clean_mp3(self):
        mp3 = clean_mp3()
        result = run("clean", str(mp3), "-y", check=False)
        assert ("Nothing to remove" in result.stdout) or (result.returncode == 0)


class TestCompletions:
    def test_outputs_bash_script(self):
        result = run("completions")
        assert "complete -F _lrc_tools" in result.stdout


class TestErrorCases:
    @pytest.mark.parametrize(
        "args",
        [
            ("embed", str(WORKDIR / "nonexistent.mp3")),
            ("embed", str(PLAIN_LRC)),
            ("clean", str(WORKDIR / "nonexistent.mp3")),
            ("extract", str(WORKDIR / "nonexistent.mp3")),
            ("inspect", str(WORKDIR / "nonexistent.mp3")),
        ],
    )
    def test_rejects_invalid_input(self, args):
        assert run(*args, check=False).returncode != 0

    def test_embed_no_lrc_discovered(self):
        mp3 = clean_mp3()
        result = run("embed", str(mp3), check=False)
        assert result.returncode != 0
        assert "No LRC file found" in (result.stdout or result.stderr)

    def test_embed_nonexistent_lrc(self):
        mp3 = clean_mp3()
        result = run("embed", str(mp3), str(WORKDIR / "nonexistent.lrc"), check=False)
        assert result.returncode != 0
