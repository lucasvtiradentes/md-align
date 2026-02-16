import re

from mdalign.constants import MAX_KEY_WORDS, MIN_GROUP_SIZE
from mdalign.parser import in_code_block

_PREFIX = re.compile(r"^(\s*- )")
_URL_COLON = re.compile(r"https?:|ftp:|file:")


def _find_colon_sep(text):
    in_backtick = False
    for i, c in enumerate(text):
        if c == "`":
            in_backtick = not in_backtick
        elif c == ":" and not in_backtick and i + 1 < len(text) and text[i + 1] == " ":
            return i
    return -1


def _parse_line(raw):
    m = _PREFIX.match(raw)
    if not m:
        return None
    after_prefix = raw[m.end() :]
    colon_idx = _find_colon_sep(after_prefix)
    if colon_idx < 0:
        return None
    key_text = after_prefix[:colon_idx]
    if len(key_text.split()) > MAX_KEY_WORDS:
        return None
    key_part = raw[: m.end() + colon_idx + 1]
    if _URL_COLON.search(key_part):
        return None
    value = after_prefix[colon_idx + 2 :]
    return key_part, value


def _is_list_item(raw):
    return bool(_PREFIX.match(raw))


def _is_embedded(group, lines, code_lines):
    first_idx = group[0][0]
    last_idx = group[-1][0]
    if first_idx > 0 and first_idx - 1 not in code_lines:
        prev = lines[first_idx - 1].rstrip("\n")
        if _is_list_item(prev):
            return True
    if last_idx + 1 < len(lines) and last_idx + 1 not in code_lines:
        nxt = lines[last_idx + 1].rstrip("\n")
        if _is_list_item(nxt):
            return True
    return False


def _collect_groups(lines):
    code_lines = in_code_block(lines)
    groups = []
    current = []
    for i, line in enumerate(lines):
        if i in code_lines:
            if len(current) >= MIN_GROUP_SIZE:
                groups.append(current)
            current = []
            continue
        raw = line.rstrip("\n")
        parsed = _parse_line(raw)
        if parsed:
            current.append((i, parsed[0], parsed[1]))
        else:
            if len(current) >= MIN_GROUP_SIZE:
                groups.append(current)
            current = []
    if len(current) >= MIN_GROUP_SIZE:
        groups.append(current)
    return [g for g in groups if not _is_embedded(g, lines, code_lines)]


def check(lines):
    errors = []
    for group in _collect_groups(lines):
        max_w = max(len(key) for _, key, _ in group)
        for i, key, value in group:
            if len(key) < max_w:
                padded = key + " " * (max_w - len(key))
                fixed_line = padded + " " + value.lstrip(" ")
                if fixed_line != lines[i].rstrip("\n"):
                    errors.append(f"L{i + 1} def list key: col={len(key)} expected={max_w}")
    return errors


def fix(lines):
    result = list(lines)
    for group in _collect_groups(lines):
        max_w = max(len(key) for _, key, _ in group)
        for i, key, value in group:
            padded = key + " " * (max_w - len(key))
            result[i] = padded + " " + value.lstrip(" ") + "\n"
    return result
