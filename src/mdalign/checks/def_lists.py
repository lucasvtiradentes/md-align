import re

_DEF_PATTERN = re.compile(r"^(\s*- \S+?): ")
_URL_COLON = re.compile(r"https?:")


def _parse_line(raw):
    if _URL_COLON.search(raw):
        return None
    m = _DEF_PATTERN.match(raw)
    if not m:
        return None
    key_part = m.group(0).rstrip(" ")
    value = raw[m.end():]
    return key_part, value


def _in_code_block(lines):
    inside = set()
    in_code = False
    for i, line in enumerate(lines):
        if line.rstrip("\n").strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            inside.add(i)
    return inside


def _collect_groups(lines):
    code_lines = _in_code_block(lines)
    groups = []
    current = []
    for i, line in enumerate(lines):
        if i in code_lines:
            if len(current) >= 2:
                groups.append(current)
            current = []
            continue
        raw = line.rstrip("\n")
        parsed = _parse_line(raw)
        if parsed:
            current.append((i, parsed[0], parsed[1]))
        else:
            if len(current) >= 2:
                groups.append(current)
            current = []
    if len(current) >= 2:
        groups.append(current)
    return groups


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
