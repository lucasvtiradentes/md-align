import unicodedata

from docalign.constants import SAFE_BOX_AND_ARROW
from docalign.parser import iter_code_blocks


def check(lines):
    errors = []
    for _, code_lines in iter_code_blocks(lines):
        for line_idx, raw in code_lines:
            for col, ch in enumerate(raw):
                if _is_wide_char(ch):
                    errors.append(f"L{line_idx + 1} wide char '{ch}' (U+{ord(ch):04X}) at col {col}")
    return errors


def fix(lines):
    return lines


def _is_wide_char(ch):
    if ch.isascii():
        return False
    if ch in SAFE_BOX_AND_ARROW:
        return False
    cat = unicodedata.east_asian_width(ch)
    if cat in ("W", "F"):
        return True
    if cat == "A" and not ch.isalpha():
        return True
    return False
