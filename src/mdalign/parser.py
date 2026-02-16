from mdalign.constants import BOX_CHARS


def iter_code_blocks(lines):
    in_code = False
    code_indices = []
    code_lines = []
    for i, line in enumerate(lines):
        raw = line.rstrip("\n")
        if raw.strip().startswith("```"):
            if in_code:
                yield code_indices, code_lines
                code_indices = []
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_indices.append(i)
            code_lines.append((i, raw))


def in_code_block(lines):
    inside = set()
    in_code = False
    for i, line in enumerate(lines):
        if line.rstrip("\n").strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            inside.add(i)
    return inside


def group_box_lines(code_lines):
    groups = []
    current = []
    for i, raw in code_lines:
        if any(c in BOX_CHARS for c in raw):
            current.append((i, raw))
        else:
            if current:
                groups.append(current)
                current = []
    if current:
        groups.append(current)
    return groups
