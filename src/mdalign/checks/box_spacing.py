from mdalign.constants import (
    BORDER_CHARS,
    BOX_CHARS,
    LARGE_SPACE_GAP,
    MAX_FIX_ITERATIONS,
    MIN_PAD,
)
from mdalign.parser import iter_code_blocks
from mdalign.utils import _find_boxes, _is_tree_block


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
    return len(inner) - len(inner.lstrip())


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
            lpad = _get_left_padding(raw, col_left, col_right)
            if lpad is not None and lpad < MIN_PAD:
                errors.append(f"L{line_idx + 1} box left spacing={lpad}, minimum={MIN_PAD}")

    return errors


def _find_connectors_in_range(raw, col_left, col_right):
    connectors = []
    for col in range(col_left, col_right + 1):
        if col < len(raw) and raw[col] in ("┬", "┴"):
            connectors.append(col)
    return connectors


def _collect_box_insertions(code_lines):
    all_boxes = list(_find_boxes(code_lines))

    def get_parent_info(col_left, col_right):
        for other_left, other_right, opening_ci, *_ in all_boxes:
            if other_left < col_left and col_right < other_right:
                return (other_left, other_right, opening_ci)
        return None

    def has_sibling_after(col_right, opener_raw):
        after = opener_raw[col_right + 1 :]
        if "┌" not in after:
            return False
        corner_pos = after.index("┌")
        between = after[:corner_pos]
        return LARGE_SPACE_GAP in between

    box_insertions = []
    for col_left, col_right, opening_ci, closing_ci, content_indices in all_boxes:
        parent_info = get_parent_info(col_left, col_right)
        if parent_info is not None:
            _, parent_right, parent_opening_ci = parent_info
            parent_opener_raw = code_lines[parent_opening_ci][1]
            if has_sibling_after(parent_right, parent_opener_raw):
                continue

        min_rpad = None
        min_lpad = None
        for ci in content_indices:
            _, raw = code_lines[ci]
            rpad = _get_right_padding(raw, col_left, col_right)
            if rpad is not None:
                if min_rpad is None or rpad < min_rpad:
                    min_rpad = rpad
            lpad = _get_left_padding(raw, col_left, col_right)
            if lpad is not None:
                if min_lpad is None or lpad < min_lpad:
                    min_lpad = lpad

        all_ci = [opening_ci] + content_indices + [closing_ci]
        line_indices = [code_lines[ci][0] for ci in all_ci]

        opener_raw = code_lines[opening_ci][1]
        closer_raw = code_lines[closing_ci][1]
        connectors = _find_connectors_in_range(opener_raw, col_left, col_right)
        connectors.extend(_find_connectors_in_range(closer_raw, col_left, col_right))

        if min_rpad is not None and min_rpad < MIN_PAD:
            deficit = MIN_PAD - min_rpad
            box_insertions.append((col_right, deficit, "right", line_indices, []))

        if min_lpad is not None and min_lpad < MIN_PAD:
            deficit = MIN_PAD - min_lpad
            box_insertions.append((col_left + 1, deficit, "left", line_indices, connectors))

    return box_insertions


def _trace_connected_pipes(code_indices, all_lines, box_lines, connector_col):
    connected = set()
    max_box = max(box_lines)
    for line_idx in code_indices:
        if line_idx <= max_box:
            continue
        raw = all_lines[line_idx].rstrip("\n")
        if connector_col >= len(raw):
            break
        char = raw[connector_col]
        if char == "│":
            connected.add(line_idx)
        elif char in ("┬", "┴"):
            if "┌" in raw or "└" in raw:
                break
            connected.add(line_idx)
            break
        else:
            break
    return connected


def _is_complex_multi_column(box_insertions):
    left_insertions = [ins for ins in box_insertions if ins[2] == "left"]
    if len(left_insertions) <= 1:
        return False
    cols = set(ins[0] for ins in left_insertions)
    if len(cols) <= 1:
        return False
    line_sets = [set(ins[3]) for ins in left_insertions]
    for i, lines_a in enumerate(line_sets):
        for lines_b in line_sets[i + 1 :]:
            if not lines_a & lines_b:
                return True
    return False


def _apply_box_insertions(all_lines, box_insertions, code_indices):
    if not box_insertions:
        return False

    if _is_complex_multi_column(box_insertions):
        return False

    sorted_insertions = sorted(box_insertions, key=lambda x: -x[0])

    for col, deficit, ins_type, line_indices, connectors in sorted_insertions:
        extended = set(line_indices)
        if ins_type == "left" and connectors:
            for connector_col in connectors:
                connected = _trace_connected_pipes(code_indices, all_lines, set(line_indices), connector_col)
                extended.update(connected)

        for line_idx in extended:
            raw = all_lines[line_idx].rstrip("\n")
            if col > len(raw):
                continue
            if col == 0:
                insert = " " * deficit
            elif col <= len(raw) and raw[col - 1] in BORDER_CHARS:
                insert = "─" * deficit
            else:
                insert = " " * deficit
            new_raw = raw[:col] + insert + raw[col:]
            all_lines[line_idx] = new_raw + "\n"

    return True


def _fix_spacing_in_block(code_indices, all_lines):
    if _is_tree_block([(i, all_lines[i].rstrip("\n")) for i in code_indices]):
        return

    for _ in range(MAX_FIX_ITERATIONS):
        code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]
        box_insertions = _collect_box_insertions(code_lines)
        if not _apply_box_insertions(all_lines, box_insertions, code_indices):
            break
