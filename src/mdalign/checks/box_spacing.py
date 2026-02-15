from mdalign.parser import iter_code_blocks
from mdalign.utils import BOX_CHARS, _find_box_closer, _is_tree_block

MIN_PAD = 1


def check(lines):
    errors = []
    for _, code_lines in iter_code_blocks(lines):
        errors.extend(_check_spacing(code_lines))
    return errors


def fix(lines):
    result = list(lines)
    for code_indices, _ in iter_code_blocks(result):
        _fix_spacing_in_block(code_indices, result)
    return result


def _find_boxes(code_lines):
    boxes = []
    for idx, (line_idx, raw) in enumerate(code_lines):
        j = 0
        while j < len(raw):
            if raw[j] != "┌":
                j += 1
                continue
            col_left = j
            col_right = _find_box_closer(raw, "┌", "┐", j)
            if col_right is None or col_right - col_left < 4:
                j += 1
                continue
            closing_idx = None
            for si in range(idx + 1, len(code_lines)):
                _, sraw = code_lines[si]
                if col_left < len(sraw) and sraw[col_left] == "└":
                    cr = _find_box_closer(sraw, "└", "┘", col_left)
                    if cr is not None:
                        closing_idx = si
                        break
            if closing_idx is not None and closing_idx - idx >= 2:
                content_indices = list(range(idx + 1, closing_idx))
                boxes.append((col_left, col_right, idx, closing_idx, content_indices))
            j = col_right + 1
    return boxes


def _get_right_padding(raw, col_left, col_right):
    if col_left >= len(raw) or raw[col_left] != "│":
        return None
    if col_right >= len(raw) or raw[col_right] not in BOX_CHARS:
        return None
    inner = raw[col_left + 1 : col_right]
    if not inner.strip():
        return None
    if any(c in BOX_CHARS for c in inner):
        return None
    return len(inner) - len(inner.rstrip())


def _check_spacing(code_lines):
    errors = []
    if _is_tree_block(code_lines):
        return errors

    for col_left, col_right, _, _, content_indices in _find_boxes(code_lines):
        for ci in content_indices:
            line_idx, raw = code_lines[ci]
            rpad = _get_right_padding(raw, col_left, col_right)
            if rpad is not None and rpad < MIN_PAD:
                errors.append(f"L{line_idx + 1} box right spacing={rpad}, minimum={MIN_PAD}")

    return errors


def _fix_spacing_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]
    if _is_tree_block(code_lines):
        return

    for col_left, col_right, opening_ci, closing_ci, content_indices in reversed(_find_boxes(code_lines)):
        min_rpad = None
        for ci in content_indices:
            _, raw = code_lines[ci]
            rpad = _get_right_padding(raw, col_left, col_right)
            if rpad is not None:
                if min_rpad is None or rpad < min_rpad:
                    min_rpad = rpad

        if min_rpad is None or min_rpad >= MIN_PAD:
            continue

        deficit = MIN_PAD - min_rpad
        all_ci = [opening_ci] + content_indices + [closing_ci]
        for ci in all_ci:
            line_idx = code_lines[ci][0]
            raw = all_lines[line_idx].rstrip("\n")
            if col_right >= len(raw):
                continue
            char = raw[col_right]
            insert = "─" * deficit if char in {"┐", "┘"} else " " * deficit
            new_raw = raw[:col_right] + insert + raw[col_right:]
            all_lines[line_idx] = new_raw + "\n"
