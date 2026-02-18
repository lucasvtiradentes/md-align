from docalign.constants import BOX_CHARS, PIPE_DRIFT_MAX
from docalign.parser import iter_code_blocks
from docalign.utils import _find_nearby_pipe, _is_tree_block, _shift_pipe


def check(lines):
    errors = []
    for _, code_lines in iter_code_blocks(lines):
        errors.extend(_check_pipe_continuity(code_lines))
    return errors


def fix(lines):
    result = list(lines)
    for code_indices, _ in iter_code_blocks(lines):
        _fix_pipes_in_block(code_indices, result)
    return result


def _check_pipe_continuity(code_lines):
    errors = []
    if _is_tree_block(code_lines):
        return errors

    flagged = set()

    for idx, (i, raw) in enumerate(code_lines):
        for j, c in enumerate(raw):
            if c == "┬":
                _trace_pipe_check(code_lines, idx, j, 1, flagged, errors)
            elif c == "┴":
                _trace_pipe_check(code_lines, idx, j, -1, flagged, errors)

    return errors


def _trace_pipe_check(code_lines, start_idx, col, direction, flagged, errors):
    line_range = range(start_idx + 1, len(code_lines)) if direction == 1 else range(start_idx - 1, -1, -1)
    for si in line_range:
        line_idx, sraw = code_lines[si]
        if col < len(sraw) and sraw[col] in BOX_CHARS:
            if sraw[col] == "│":
                continue
            break
        found = _find_nearby_pipe(sraw, col, PIPE_DRIFT_MAX)
        if found is not None:
            if (line_idx, found) not in flagged:
                flagged.add((line_idx, found))
                errors.append(f"L{line_idx + 1} pipe '│' at col {found}, expected col {col}")
        else:
            break


def _fix_pipes_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]
    if _is_tree_block(code_lines):
        return

    corrections = {}
    for idx, (i, raw) in enumerate(code_lines):
        for j, c in enumerate(raw):
            if c == "┬":
                _trace_pipe_fix(code_lines, idx, j, 1, corrections)
            elif c == "┴":
                _trace_pipe_fix(code_lines, idx, j, -1, corrections)

    by_line = {}
    for (line_idx, current_col), expected_col in corrections.items():
        by_line.setdefault(line_idx, []).append((current_col, expected_col))

    for line_idx, line_corrections in by_line.items():
        raw = all_lines[line_idx].rstrip("\n")
        for current_col, expected_col in sorted(line_corrections, key=lambda x: -x[0]):
            raw = _shift_pipe(raw, current_col, expected_col, strip_trailing=True)
        all_lines[line_idx] = raw + "\n"


def _trace_pipe_fix(code_lines, start_idx, col, direction, corrections):
    line_range = range(start_idx + 1, len(code_lines)) if direction == 1 else range(start_idx - 1, -1, -1)
    for si in line_range:
        line_idx, sraw = code_lines[si]
        if col < len(sraw) and sraw[col] in BOX_CHARS:
            if sraw[col] == "│":
                continue
            break
        found = _find_nearby_pipe(sraw, col, PIPE_DRIFT_MAX)
        if found is not None:
            corrections[(line_idx, found)] = col
        else:
            break
