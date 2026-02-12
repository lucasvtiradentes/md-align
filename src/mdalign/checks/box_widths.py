from mdalign.parser import group_box_lines, iter_code_blocks
from mdalign.utils import BOX_CHARS, BOX_CLOSERS, BOX_OPENERS, _is_tree_block


def check(lines):
    errors = []
    for _, code_lines in iter_code_blocks(lines):
        errors.extend(_check_widths(code_lines))
    return errors


def fix(lines):
    result = list(lines)
    for code_indices, _ in iter_code_blocks(lines):
        _fix_widths_in_block(code_indices, result)
    return result


def _check_widths(code_lines):
    errors = []
    if _is_tree_block(code_lines):
        return errors

    for group in group_box_lines(code_lines):
        by_extent = {}
        for i, raw in group:
            box_positions = [j for j, c in enumerate(raw) if c in BOX_CHARS]
            if len(box_positions) < 2:
                continue
            first = box_positions[0]
            last = box_positions[-1]
            by_extent.setdefault((first, last), []).append((i, raw))

        for (first, last), lines_in_group in by_extent.items():
            lengths = {}
            for i, raw in lines_in_group:
                after_box = raw[last + 1 :]
                effective_len = last + 1 if after_box.strip() else len(raw)
                lengths.setdefault(effective_len, []).append(i + 1)

            if len(lengths) > 1:
                most_common = max(lengths.keys(), key=lambda k: len(lengths[k]))
                for length, line_nums in lengths.items():
                    if length != most_common:
                        for ln in line_nums:
                            errors.append(
                                f"L{ln} width={length}, expected={most_common} (box group at cols {first}-{last})"
                            )

    return errors


def _fix_widths_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]

    if _is_tree_block(code_lines):
        return

    for group in group_box_lines(code_lines):
        by_extent = {}
        for i, raw in group:
            box_positions = [j for j, c in enumerate(raw) if c in BOX_CHARS]
            if len(box_positions) < 2:
                continue
            first = box_positions[0]
            last = box_positions[-1]
            by_extent.setdefault((first, last), []).append((i, raw))

        for (first, last), lines_in_group in by_extent.items():
            lengths = {}
            for i, raw in lines_in_group:
                after_box = raw[last + 1 :]
                effective_len = last + 1 if after_box.strip() else len(raw)
                lengths.setdefault(effective_len, []).append(i)

            if len(lengths) <= 1:
                continue

            most_common = max(lengths.keys(), key=lambda k: len(lengths[k]))

            for length, line_indices in lengths.items():
                if length == most_common:
                    continue
                for idx in line_indices:
                    raw = all_lines[idx].rstrip("\n")
                    fixed = _fix_line_width(raw, most_common)
                    if fixed != raw:
                        all_lines[idx] = fixed + "\n"


def _fix_line_width(raw, target_width):
    current = len(raw)
    delta = target_width - current
    if delta == 0:
        return raw

    stripped = raw.strip()
    if not stripped:
        return raw

    first_char = stripped[0]
    last_char = stripped[-1]

    if first_char in BOX_OPENERS and last_char in BOX_CLOSERS:
        close_idx = raw.rindex(last_char)
        run_end = close_idx
        run_start = run_end - 1
        while run_start >= 0 and raw[run_start] == "─":
            run_start -= 1
        run_start += 1
        run_length = run_end - run_start

        if run_length == 0:
            return raw
        new_length = run_length + delta
        if new_length < 1:
            return raw

        return raw[:run_start] + "─" * new_length + raw[run_end:]

    if "│" in raw:
        close_idx = raw.rindex("│")
        if delta > 0:
            return raw[:close_idx] + " " * delta + raw[close_idx:]
        else:
            remove = abs(delta)
            if close_idx - remove < 0:
                return raw
            region = raw[close_idx - remove : close_idx]
            if region == " " * remove:
                return raw[: close_idx - remove] + raw[close_idx:]
            return raw

    return raw
