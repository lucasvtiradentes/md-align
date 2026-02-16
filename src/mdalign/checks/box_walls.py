from mdalign.constants import (
    BOX_CHARS,
    BOX_WALL_DRIFT,
    LARGE_SPACE_GAP,
    MIN_BOX_WIDTH,
    MIN_PIPES_FOR_ADJACENT,
)
from mdalign.parser import iter_code_blocks
from mdalign.utils import (
    _find_box_closer,
    _find_nearby_closer_start,
    _find_nearby_pipe,
    _fix_closer,
    _is_tree_block,
    _shift_pipe,
)


def check(lines):
    errors = []
    for _, code_lines in iter_code_blocks(lines):
        errors.extend(_check_box_walls(code_lines))
    return errors


def fix(lines):
    result = list(lines)
    for code_indices, _ in iter_code_blocks(lines):
        _fix_box_walls_in_block(code_indices, result)
    return result


def _has_independent_box_after(raw, col):
    after = raw[col + 1 :] if col + 1 < len(raw) else ""
    if not after:
        return False
    has_box_structure = "┌" in after or "└" in after
    if not has_box_structure:
        return False
    pipe_indices = [i for i, c in enumerate(after) if c == "│"]
    if len(pipe_indices) < MIN_PIPES_FOR_ADJACENT:
        return False
    first_pipe = pipe_indices[0]
    second_pipe = pipe_indices[1]
    between_pipes = after[first_pipe + 1 : second_pipe]
    return LARGE_SPACE_GAP in between_pipes


def _check_box_walls(code_lines):
    errors = []
    if _is_tree_block(code_lines):
        return errors

    for idx, (line_idx, raw) in enumerate(code_lines):
        j = 0
        while j < len(raw):
            if raw[j] != "┌":
                j += 1
                continue

            col_left = j
            col_right_open = _find_box_closer(raw, "┌", "┐", j)
            if col_right_open is None or col_right_open - col_left < MIN_BOX_WIDTH:
                j += 1
                continue

            closing_idx = None
            fuzzy_col_left = None
            for si in range(idx + 1, len(code_lines)):
                _, sraw = code_lines[si]
                if col_left < len(sraw) and sraw[col_left] == "└":
                    closing_idx = si
                    break
                nc = _find_nearby_closer_start(sraw, col_left, col_right_open)
                if nc is not None:
                    closing_idx = si
                    fuzzy_col_left = nc
                    break

            if closing_idx is None or closing_idx - idx < 3:
                j = col_right_open + 1
                continue

            closing_line_idx, closing_raw = code_lines[closing_idx]
            actual_col_left = fuzzy_col_left if fuzzy_col_left is not None else col_left
            col_right_close = _find_box_closer(closing_raw, "└", "┘", actual_col_left)

            if fuzzy_col_left is not None:
                errors.append(
                    f"L{closing_line_idx + 1} box └ at col {fuzzy_col_left}, "
                    f"expected col {col_left} "
                    f"(box ┌ at L{line_idx + 1} col {col_left})"
                )

            if col_right_close is not None:
                if abs(col_right_close - col_right_open) > BOX_WALL_DRIFT:
                    j = col_right_open + 1
                    continue
                expected_right = max(col_right_open, col_right_close)
            else:
                expected_right = col_right_open

            if col_right_open != expected_right:
                errors.append(f"L{line_idx + 1} box ┐ at col {col_right_open}, expected col {expected_right}")

            if col_right_close is not None and col_right_close != expected_right:
                errors.append(f"L{closing_line_idx + 1} box ┘ at col {col_right_close}, expected col {expected_right}")

            for mi in range(idx + 1, closing_idx):
                m_line_idx, m_raw = code_lines[mi]
                right_ok = expected_right < len(m_raw) and m_raw[expected_right] in BOX_CHARS
                if not right_ok:
                    found = _find_nearby_pipe(m_raw, expected_right, BOX_WALL_DRIFT)
                    if found is not None:
                        errors.append(
                            f"L{m_line_idx + 1} box wall │ at col {found}, "
                            f"expected col {expected_right} "
                            f"(box ┌ at L{line_idx + 1} col {col_left})"
                        )
                if col_left < len(m_raw):
                    if m_raw[col_left] not in BOX_CHARS:
                        found = _find_nearby_pipe(m_raw, col_left, BOX_WALL_DRIFT)
                        if found is not None:
                            errors.append(
                                f"L{m_line_idx + 1} box wall │ at col {found}, "
                                f"expected col {col_left} "
                                f"(box ┌ at L{line_idx + 1} col {col_left})"
                            )

            j = col_right_open + 1

    return errors


def _fix_box_walls_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]
    if _is_tree_block(code_lines):
        return

    for idx, (line_idx, raw) in enumerate(code_lines):
        j = 0
        while j < len(raw):
            if raw[j] != "┌":
                j += 1
                continue

            col_left = j
            col_right_open = _find_box_closer(raw, "┌", "┐", j)
            if col_right_open is None or col_right_open - col_left < MIN_BOX_WIDTH:
                j += 1
                continue

            closing_idx = None
            fuzzy_col_left = None
            for si in range(idx + 1, len(code_lines)):
                si_idx = code_lines[si][0]
                sraw = all_lines[si_idx].rstrip("\n")
                if col_left < len(sraw) and sraw[col_left] == "└":
                    closing_idx = si
                    break
                nc = _find_nearby_closer_start(sraw, col_left, col_right_open)
                if nc is not None:
                    closing_idx = si
                    fuzzy_col_left = nc
                    break

            if closing_idx is None or closing_idx - idx < 3:
                j = col_right_open + 1
                continue

            closing_line_idx = code_lines[closing_idx][0]
            closing_raw = all_lines[closing_line_idx].rstrip("\n")
            actual_col_left = fuzzy_col_left if fuzzy_col_left is not None else col_left
            col_right_close = _find_box_closer(closing_raw, "└", "┘", actual_col_left)

            if col_right_close is not None:
                if abs(col_right_close - col_right_open) > BOX_WALL_DRIFT:
                    j = col_right_open + 1
                    continue
                expected_right = max(col_right_open, col_right_close)
            else:
                expected_right = col_right_open

            changed = False

            if fuzzy_col_left is not None:
                from mdalign.utils import _realign_box_chars

                cur = all_lines[closing_line_idx].rstrip("\n")
                actual_positions = [k for k, c in enumerate(cur) if c in BOX_CHARS]
                expected_positions = []
                for ap in actual_positions:
                    if ap == fuzzy_col_left:
                        expected_positions.append(col_left)
                    elif ap == col_right_close and col_right_close is not None:
                        expected_positions.append(col_right_open)
                    else:
                        expected_positions.append(ap)
                fixed = _realign_box_chars(cur, actual_positions, expected_positions).rstrip(" ")
                if fixed != cur:
                    all_lines[closing_line_idx] = fixed + "\n"
                    closing_raw = fixed
                    col_right_close = col_right_open
                    expected_right = col_right_open
                    changed = True

            if col_right_open != expected_right:
                fixed = _fix_closer(raw, col_right_open, expected_right, "┐")
                if fixed != raw:
                    all_lines[line_idx] = fixed + "\n"
                    changed = True

            if col_right_close is not None and col_right_close != expected_right:
                cur = all_lines[closing_line_idx].rstrip("\n")
                fixed = _fix_closer(cur, col_right_close, expected_right, "┘")
                if fixed != cur:
                    all_lines[closing_line_idx] = fixed + "\n"
                    changed = True

            has_adjacent_box_on_line = "┌" in raw[col_right_open + 1 :]

            for mi in range(idx + 1, closing_idx):
                m_line_idx = code_lines[mi][0]
                m_raw = all_lines[m_line_idx].rstrip("\n")
                has_box_after_right = _has_independent_box_after(m_raw, expected_right)
                has_box_after_left = _has_independent_box_after(m_raw, col_left)
                right_ok = expected_right < len(m_raw) and m_raw[expected_right] in BOX_CHARS
                if not right_ok:
                    found = _find_nearby_pipe(m_raw, expected_right, BOX_WALL_DRIFT)
                    if found is not None and not has_box_after_right and not has_adjacent_box_on_line:
                        fixed = _shift_pipe(m_raw, found, expected_right)
                        if fixed != m_raw:
                            all_lines[m_line_idx] = fixed + "\n"
                            m_raw = fixed
                            changed = True
                if col_left < len(m_raw):
                    if m_raw[col_left] not in BOX_CHARS:
                        found = _find_nearby_pipe(m_raw, col_left, BOX_WALL_DRIFT)
                        if found is not None and not has_box_after_left and not has_adjacent_box_on_line:
                            fixed = _shift_pipe(m_raw, found, col_left)
                            if fixed != m_raw:
                                all_lines[m_line_idx] = fixed + "\n"
                                changed = True

            if changed:
                code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]
                raw = all_lines[line_idx].rstrip("\n")

            j = col_right_open + 1
