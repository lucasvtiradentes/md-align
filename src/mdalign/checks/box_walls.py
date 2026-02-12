from mdalign.parser import iter_code_blocks
from mdalign.utils import (
    BOX_CHARS,
    BOX_WALL_DRIFT,
    _find_box_closer,
    _find_nearby_wall,
    _fix_closer,
    _is_tree_block,
    _shift_wall,
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
            if col_right_open is None or col_right_open - col_left < 4:
                j += 1
                continue

            closing_idx = None
            for si in range(idx + 1, len(code_lines)):
                _, sraw = code_lines[si]
                if col_left < len(sraw) and sraw[col_left] == "└":
                    closing_idx = si
                    break

            if closing_idx is None or closing_idx - idx < 3:
                j = col_right_open + 1
                continue

            closing_line_idx, closing_raw = code_lines[closing_idx]
            col_right_close = _find_box_closer(closing_raw, "└", "┘", col_left)

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
                    found = _find_nearby_wall(m_raw, expected_right, BOX_WALL_DRIFT)
                    if found is not None:
                        errors.append(
                            f"L{m_line_idx + 1} box wall │ at col {found}, "
                            f"expected col {expected_right} "
                            f"(box ┌ at L{line_idx + 1} col {col_left})"
                        )
                if col_left < len(m_raw):
                    if m_raw[col_left] not in BOX_CHARS:
                        found = _find_nearby_wall(m_raw, col_left, BOX_WALL_DRIFT)
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
            if col_right_open is None or col_right_open - col_left < 4:
                j += 1
                continue

            closing_idx = None
            for si in range(idx + 1, len(code_lines)):
                si_idx = code_lines[si][0]
                sraw = all_lines[si_idx].rstrip("\n")
                if col_left < len(sraw) and sraw[col_left] == "└":
                    closing_idx = si
                    break

            if closing_idx is None or closing_idx - idx < 3:
                j = col_right_open + 1
                continue

            closing_line_idx = code_lines[closing_idx][0]
            closing_raw = all_lines[closing_line_idx].rstrip("\n")
            col_right_close = _find_box_closer(closing_raw, "└", "┘", col_left)

            if col_right_close is not None:
                if abs(col_right_close - col_right_open) > BOX_WALL_DRIFT:
                    j = col_right_open + 1
                    continue
                expected_right = max(col_right_open, col_right_close)
            else:
                expected_right = col_right_open

            changed = False

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

            for mi in range(idx + 1, closing_idx):
                m_line_idx = code_lines[mi][0]
                m_raw = all_lines[m_line_idx].rstrip("\n")
                right_ok = expected_right < len(m_raw) and m_raw[expected_right] in BOX_CHARS
                if not right_ok:
                    found = _find_nearby_wall(m_raw, expected_right, BOX_WALL_DRIFT)
                    if found is not None:
                        fixed = _shift_wall(m_raw, found, expected_right)
                        if fixed != m_raw:
                            all_lines[m_line_idx] = fixed + "\n"
                            m_raw = fixed
                            changed = True
                if col_left < len(m_raw):
                    if m_raw[col_left] not in BOX_CHARS:
                        found = _find_nearby_wall(m_raw, col_left, BOX_WALL_DRIFT)
                        if found is not None:
                            fixed = _shift_wall(m_raw, found, col_left)
                            if fixed != m_raw:
                                all_lines[m_line_idx] = fixed + "\n"
                                changed = True

            if changed:
                code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]
                raw = all_lines[line_idx].rstrip("\n")

            j = col_right_open + 1
