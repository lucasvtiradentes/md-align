from collections import Counter

from docalign.constants import BOX_CHARS, MAX_PAD_DRIFT
from docalign.parser import iter_code_blocks
from docalign.utils import _find_boxes, _is_tree_block


def check(lines):
    errors = []
    for _, code_lines in iter_code_blocks(lines):
        errors.extend(_check_padding(code_lines))
    return errors


def fix(lines):
    result = list(lines)
    for code_indices, _ in iter_code_blocks(lines):
        _fix_padding_in_block(code_indices, result)
    return result


def _get_left_padding(raw, col_left, col_right):
    if col_left >= len(raw) or raw[col_left] != "│":
        return None
    if col_right >= len(raw) or raw[col_right] not in BOX_CHARS:
        return None
    inner = raw[col_left + 1 : col_right]
    if not inner.strip():
        return None
    if any(c in BOX_CHARS for c in inner):
        return None
    pad = 0
    for c in inner:
        if c == " ":
            pad += 1
        else:
            break
    return pad


def _expected_padding(paddings):
    counts = Counter(paddings)
    max_count = max(counts.values())
    candidates = [p for p, c in counts.items() if c == max_count]
    if len(candidates) == 1:
        return candidates[0]
    if 0 in candidates:
        non_zero = [c for c in candidates if c > 0]
        return min(non_zero)
    return None


def _has_layout_intent(pad_values):
    return max(pad_values) - min(pad_values) >= MAX_PAD_DRIFT


def _check_padding(code_lines):
    errors = []
    if _is_tree_block(code_lines):
        return errors

    for col_left, col_right, _, _, content_indices in _find_boxes(code_lines):
        paddings = []
        for ci in content_indices:
            line_idx, raw = code_lines[ci]
            pad = _get_left_padding(raw, col_left, col_right)
            if pad is not None:
                paddings.append((line_idx, pad))

        if len(paddings) < 2 or _has_layout_intent([p for _, p in paddings]):
            continue

        expected = _expected_padding([p for _, p in paddings])
        if expected is None:
            continue

        for line_idx, pad in paddings:
            if pad != expected:
                errors.append(f"L{line_idx + 1} box padding={pad}, expected={expected}")

    return errors


def _fix_padding_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]
    if _is_tree_block(code_lines):
        return

    for col_left, col_right, _, _, content_indices in _find_boxes(code_lines):
        paddings = []
        for ci in content_indices:
            line_idx, raw = code_lines[ci]
            pad = _get_left_padding(raw, col_left, col_right)
            if pad is not None:
                paddings.append((ci, line_idx, pad))

        if len(paddings) < 2 or _has_layout_intent([p for _, _, p in paddings]):
            continue

        expected = _expected_padding([p for _, _, p in paddings])
        if expected is None:
            continue

        for ci, line_idx, pad in paddings:
            if pad == expected:
                continue
            raw = all_lines[line_idx].rstrip("\n")
            inner = raw[col_left + 1 : col_right]
            content = inner.strip()
            total_width = col_right - col_left - 1
            new_inner = " " * expected + content
            remaining = total_width - len(new_inner)
            if remaining < 1:
                continue
            new_inner = new_inner + " " * remaining
            new_raw = raw[: col_left + 1] + new_inner + raw[col_right:]
            all_lines[line_idx] = new_raw + "\n"
