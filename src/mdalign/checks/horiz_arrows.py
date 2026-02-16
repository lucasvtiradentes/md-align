import re

from mdalign.constants import BOX_CORNERS
from mdalign.parser import iter_code_blocks
from mdalign.utils import _is_tree_block

_RIGHT_ARROW = re.compile(r"─+(>)")
_LEFT_ARROW = re.compile(r"(<)─+")


def check(lines):
    errors = []
    for _, code_lines in iter_code_blocks(lines):
        errors.extend(_check_horiz_arrows(code_lines))
    return errors


def fix(lines):
    result = list(lines)
    for code_indices, _ in iter_code_blocks(lines):
        _fix_horiz_arrows_in_block(code_indices, result)
    return result


def _is_box_wall_col(code_lines, col):
    for _, raw in code_lines:
        if col < len(raw) and raw[col] in BOX_CORNERS:
            return True
    return False


def _check_horiz_arrows(code_lines):
    errors = []
    if _is_tree_block(code_lines):
        return errors

    for _, (line_idx, raw) in enumerate(code_lines):
        for m in _RIGHT_ARROW.finditer(raw):
            tip_col = m.end() - 1
            wall_col = _right_wall_col(raw, tip_col)
            if wall_col is None or not _is_box_wall_col(code_lines, wall_col):
                continue
            src_col = m.start() - 1
            if src_col < 0 or raw[src_col] != "│" or not _is_box_wall_col(code_lines, src_col):
                continue
            gap = wall_col - tip_col - 1
            if gap > 0:
                errors.append(f"L{line_idx + 1} arrow '>' at col {tip_col}, gap={gap} to box wall")

        for m in _LEFT_ARROW.finditer(raw):
            tip_col = m.start()
            wall_col = _left_wall_col(raw, tip_col)
            if wall_col is None or not _is_box_wall_col(code_lines, wall_col):
                continue
            src_col = m.end()
            if src_col >= len(raw) or raw[src_col] != "│" or not _is_box_wall_col(code_lines, src_col):
                continue
            gap = tip_col - wall_col - 1
            if gap > 0:
                errors.append(f"L{line_idx + 1} arrow '<' at col {tip_col}, gap={gap} to box wall")

    return errors


def _right_wall_col(raw, tip_col):
    pos = tip_col + 1
    while pos < len(raw) and raw[pos] == " ":
        pos += 1
    if pos < len(raw) and raw[pos] == "│":
        return pos
    return None


def _left_wall_col(raw, tip_col):
    pos = tip_col - 1
    while pos >= 0 and raw[pos] == " ":
        pos -= 1
    if pos >= 0 and raw[pos] == "│":
        return pos
    return None


def _fix_horiz_arrows_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]
    if _is_tree_block(code_lines):
        return

    for _, (line_idx, raw) in enumerate(code_lines):
        new_raw = raw

        for m in reversed(list(_RIGHT_ARROW.finditer(new_raw))):
            tip_col = m.end() - 1
            wall_col = _right_wall_col(new_raw, tip_col)
            if wall_col is None or not _is_box_wall_col(code_lines, wall_col):
                continue
            src_col = m.start() - 1
            if src_col < 0 or new_raw[src_col] != "│" or not _is_box_wall_col(code_lines, src_col):
                continue
            gap = wall_col - tip_col - 1
            if gap > 0:
                new_raw = new_raw[: m.start()] + "─" * (m.end() - m.start() - 1 + gap) + ">" + new_raw[wall_col:]

        changed = True
        while changed:
            changed = False
            for m in _LEFT_ARROW.finditer(new_raw):
                tip_col = m.start()
                wall_col = _left_wall_col(new_raw, tip_col)
                if wall_col is None or not _is_box_wall_col(code_lines, wall_col):
                    continue
                src_col = m.end()
                if src_col >= len(new_raw) or new_raw[src_col] != "│" or not _is_box_wall_col(code_lines, src_col):
                    continue
                gap = tip_col - wall_col - 1
                if gap > 0:
                    dash_len = m.end() - m.start() - 1 + gap
                    new_raw = new_raw[: wall_col + 1] + "<" + "─" * dash_len + new_raw[m.end() :]
                    changed = True
                    break

        if new_raw != raw:
            all_lines[line_idx] = new_raw + "\n"
