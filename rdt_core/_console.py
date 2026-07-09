"""rdt_core._console — force UTF-8 console output on all platforms.

Windows consoles default to cp1252, which raises UnicodeEncodeError on the ✓/Δ/φ/
≈/± glyphs used throughout the scripts' progress output (crash class observed
2026-07-04). Importing this module reconfigures stdout/stderr to UTF-8 with
backslash-replace fallback, so a stray glyph degrades to an escape rather than a
crash. No-op where already UTF-8. Import once at the top of any script that prints.
"""
import sys


def _utf8(stream):
    try:
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError):
        pass  # non-reconfigurable stream (e.g. captured pipe) — leave as is


_utf8(sys.stdout)
_utf8(sys.stderr)
