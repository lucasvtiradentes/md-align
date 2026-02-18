from docalign.constants import ARROW_CHARS, ARROW_SEARCH_RANGE, BOX_CHARS, HORIZ_ARROW_CHARS
from docalign.parser import iter_code_blocks
from docalign.utils import _is_standalone_arrow


def check(lines):
    errors = []
    for _, code_lines in iter_code_blocks(lines):
        errors.extend(_check_arrows(code_lines))
    return errors


def fix(lines):
    result = list(lines)
    for code_indices, _ in iter_code_blocks(lines):
        _fix_arrows_in_block(code_indices, result)
    return result


def _check_arrows(code_lines):
    errors = []
    for idx, (i, raw) in enumerate(code_lines):
        for j, c in enumerate(raw):
            if c in ARROW_CHARS:
                if _is_standalone_arrow(raw, j):
                    expected = _find_arrow_target(code_lines, idx, j, c)
                    if expected is not None and expected != j:
                        errors.append(f"L{i + 1} arrow '{c}' at col {j}, expected col {expected}")
                elif _is_embedded_in_horiz_border(raw, j):
                    errors.append(f"L{i + 1} arrow '{c}' embedded in border at col {j}")
            elif c in HORIZ_ARROW_CHARS and _is_embedded_in_vert_border(code_lines, idx, j):
                errors.append(f"L{i + 1} arrow '{c}' embedded in border at col {j}")
    return errors


def _is_embedded_in_horiz_border(raw, j):
    left = raw[j - 1] if j > 0 else " "
    right = raw[j + 1] if j < len(raw) - 1 else " "
    return left == "─" or right == "─"


def _is_embedded_in_vert_border(code_lines, line_idx, col):
    above = line_idx - 1
    below = line_idx + 1
    has_above = above >= 0 and col < len(code_lines[above][1]) and code_lines[above][1][col] == "│"
    has_below = below < len(code_lines) and col < len(code_lines[below][1]) and code_lines[below][1][col] == "│"
    return has_above or has_below


def _find_arrow_target(code_lines, arrow_idx, arrow_col, arrow_char):
    search_range = range(arrow_idx - 1, -1, -1) if arrow_char == "v" else range(arrow_idx + 1, len(code_lines))
    for si in search_range:
        _, sraw = code_lines[si]
        for dc in [i for r in range(ARROW_SEARCH_RANGE + 1) for i in ([0] if r == 0 else [-r, r])]:
            col = arrow_col + dc
            if 0 <= col < len(sraw) and sraw[col] in BOX_CHARS:
                return col if dc != 0 else None
        break
    return None


def _fix_arrows_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]
    for idx, (i, raw) in enumerate(code_lines):
        arrows = [(j, c) for j, c in enumerate(raw) if c in ARROW_CHARS and _is_standalone_arrow(raw, j)]
        if not arrows:
            continue
        corrections = []
        for j, c in arrows:
            expected = _find_arrow_target(code_lines, idx, j, c)
            if expected is not None and expected != j:
                corrections.append((j, expected))
        if not corrections:
            continue
        new_raw = raw
        for j, expected in sorted(corrections, key=lambda x: -x[0]):
            delta = expected - j
            if delta > 0:
                spaces_after = 0
                for k in range(j + 1, len(new_raw)):
                    if new_raw[k] == " ":
                        spaces_after += 1
                    else:
                        break
                if spaces_after >= delta:
                    new_raw = new_raw[:j] + " " * delta + new_raw[j] + new_raw[j + 1 + delta :]
                elif j + 1 + spaces_after >= len(new_raw):
                    new_raw = new_raw[:j] + " " * delta + new_raw[j]
            elif delta < 0:
                remove = abs(delta)
                spaces_before = 0
                for k in range(j - 1, -1, -1):
                    if new_raw[k] == " ":
                        spaces_before += 1
                    else:
                        break
                if spaces_before >= remove:
                    new_raw = new_raw[: j - remove] + new_raw[j] + " " * remove + new_raw[j + 1 :]
        if new_raw != raw:
            all_lines[i] = new_raw + "\n"
