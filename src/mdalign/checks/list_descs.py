import re


def _parse_line(raw):
    prefix_match = re.match(r"^(\s*- )", raw)
    if not prefix_match:
        return None
    after_prefix = raw[prefix_match.end() :]
    sep_idx = after_prefix.find(" - ")
    if sep_idx < 0:
        return None
    item = raw[: prefix_match.end() + sep_idx]
    desc = after_prefix[sep_idx + 1 :]
    return item, desc


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
        max_w = max(len(item) for _, item, _ in group)
        for i, item, _ in group:
            if len(item) < max_w:
                errors.append(f"L{i + 1} list desc separator: col={len(item)} expected={max_w}")
    return errors


def fix(lines):
    result = list(lines)
    for group in _collect_groups(lines):
        max_w = max(len(item) for _, item, _ in group)
        for i, item, desc in group:
            padded = item + " " * (max_w - len(item))
            result[i] = padded + " " + desc.lstrip(" ") + "\n"
    return result
