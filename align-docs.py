#!/usr/bin/env python3
# Run: python3 align-docs.py <file_or_folder>
# Run: python3 align-docs.py --check <file_or_folder>
import sys
import os
import re
import unicodedata


def visual_width(s):
    w = 0
    for c in s:
        cat = unicodedata.east_asian_width(c)
        if cat in ('W', 'F'):
            w += 2
        elif ord(c) > 0xFFFF:
            w += 2
        else:
            w += 1
    return w


BOX_CHARS = set('│┌└├┐┘┤┬┴┼')
BOX_CLOSERS = {'┐', '┘', '┤'}
BOX_OPENERS = {'┌', '└', '├'}


def _is_tree_block(code_lines):
    has_branches = any('├──' in raw or '└──' in raw for _, raw in code_lines)
    has_box_borders = any('┌' in raw or '┐' in raw for _, raw in code_lines)
    return has_branches and not has_box_borders


def check_tables(fname, lines):
    errors = []
    sep_widths = None
    sep_line = None
    for i, line in enumerate(lines):
        raw = line.rstrip('\n')
        if raw.startswith('|') and raw.endswith('|') and len(raw) > 2:
            cells = raw.split('|')
            widths = [len(c) for c in cells[1:-1]]
            if widths and all(c.strip().replace('-', '') == '' for c in cells[1:-1]):
                sep_widths = widths
                sep_line = i + 1
            elif sep_widths:
                for ci, (w, ew) in enumerate(zip(widths, sep_widths)):
                    if w != ew:
                        errors.append(
                            f"L{i+1} table col{ci}: width={w} expected={ew} "
                            f"(separator at L{sep_line})"
                        )
        else:
            sep_widths = None
    return errors


def check_line_widths_in_boxes(fname, lines):
    errors = []
    in_code = False
    code_lines = []

    for i, line in enumerate(lines):
        raw = line.rstrip('\n')
        if raw.strip().startswith('```'):
            if in_code:
                errors.extend(_check_widths(code_lines))
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append((i, raw))

    return errors


def _check_widths(code_lines):
    errors = []
    is_tree = _is_tree_block(code_lines)
    if is_tree:
        return errors

    groups = []
    current = []
    for i, raw in code_lines:
        has_box = any(c in BOX_CHARS for c in raw)
        if has_box:
            current.append((i, raw))
        else:
            if current:
                groups.append(current)
                current = []
    if current:
        groups.append(current)

    for group in groups:
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
                lengths.setdefault(len(raw), []).append(i + 1)

            if len(lengths) > 1:
                most_common = max(lengths.keys(), key=lambda k: len(lengths[k]))
                for length, line_nums in lengths.items():
                    if length != most_common:
                        for ln in line_nums:
                            errors.append(
                                f"L{ln} width={length}, expected={most_common} "
                                f"(box group at cols {first}-{last})"
                            )

    return errors


def check_rail_alignment(fname, lines):
    errors = []
    in_code = False
    code_lines = []

    for i, line in enumerate(lines):
        raw = line.rstrip('\n')
        if raw.strip().startswith('```'):
            if in_code:
                errors.extend(_check_rails(code_lines))
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append((i, raw))

    return errors


RAIL_THRESHOLD = 1
RAIL_MAX_GAP = 1
CLUSTER_THRESHOLD = 3


def _cluster_by_positions(items, threshold=CLUSTER_THRESHOLD):
    clusters = []
    for item in items:
        positions = item[2]
        fitted = False
        for cluster in clusters:
            ref = cluster[0][2]
            if all(abs(a - b) <= threshold for a, b in zip(positions, ref)):
                cluster.append(item)
                fitted = True
                break
        if not fitted:
            clusters.append([item])
    return [c for c in clusters if len(c) >= 2]


def _check_rails_by_index(group):
    errors = []
    flagged = set()
    by_count = {}
    for i, raw in group:
        positions = tuple(j for j, c in enumerate(raw) if c in BOX_CHARS)
        by_count.setdefault(len(positions), []).append((i, raw, positions))

    for count, items in by_count.items():
        if count < 2:
            continue
        for cluster in _cluster_by_positions(items):
            for pos_idx in range(count):
                col_counts = {}
                for i, raw, positions in cluster:
                    col = positions[pos_idx]
                    col_counts.setdefault(col, []).append(i)
                if len(col_counts) <= 1:
                    continue
                most_common = max(col_counts.keys(), key=lambda k: len(col_counts[k]))
                for col, line_indices in col_counts.items():
                    if col != most_common:
                        for li in line_indices:
                            flagged.add((li, col))
                            errors.append(
                                f"L{li+1} box char at col {col}, "
                                f"expected col {most_common}"
                            )
    return errors, flagged


def _identify_rails(group):
    all_entries = []
    for gi, (line_idx, raw) in enumerate(group):
        for j, c in enumerate(raw):
            if c in BOX_CHARS:
                all_entries.append((gi, j, line_idx, c))

    sorted_entries = sorted(all_entries, key=lambda x: x[1])
    if not sorted_entries:
        return []

    col_clusters = []
    current = [sorted_entries[0]]
    for entry in sorted_entries[1:]:
        if entry[1] - current[0][1] <= RAIL_THRESHOLD:
            current.append(entry)
        else:
            if len(current) >= 2:
                col_clusters.append(current)
            current = [entry]
    if len(current) >= 2:
        col_clusters.append(current)

    rails = []
    for cluster in col_clusters:
        cluster.sort(key=lambda x: x[0])
        segments = []
        current_seg = [cluster[0]]
        for entry in cluster[1:]:
            if entry[0] - current_seg[-1][0] <= RAIL_MAX_GAP:
                current_seg.append(entry)
            else:
                if len(current_seg) >= 2:
                    segments.append(current_seg)
                current_seg = [entry]
        if len(current_seg) >= 2:
            segments.append(current_seg)

        for seg in segments:
            rails.append([(line_idx, col, char) for _, col, line_idx, char in seg])

    return rails


def _rail_errors(rail, already_flagged=None):
    errors = []
    col_data = {}
    for line_idx, col, char in rail:
        col_data.setdefault(col, []).append((line_idx, char))

    if len(col_data) <= 1:
        return errors

    pipe_origins = {col: sum(1 for _, c in entries if c in ('┬', '┴'))
                    for col, entries in col_data.items()}
    structural = {col: sum(1 for _, c in entries if c not in ('│', '┼'))
                  for col, entries in col_data.items()}
    earliest = {col: min(li for li, _ in entries)
                for col, entries in col_data.items()}
    has_pipe = any(v > 0 for v in pipe_origins.values())
    has_structural = any(v > 0 for v in structural.values())
    if has_pipe:
        most_common = max(col_data.keys(),
                          key=lambda k: (pipe_origins[k], structural[k], len(col_data[k]), -earliest[k]))
    elif has_structural:
        most_common = max(col_data.keys(),
                          key=lambda k: (structural[k], len(col_data[k]), -earliest[k]))
    else:
        most_common = max(col_data.keys(), key=lambda k: len(col_data[k]))
    minority = len(rail) - len(col_data[most_common])
    if not has_structural and not has_pipe and minority * 3 > len(rail):
        return errors

    for col, entries in col_data.items():
        if col != most_common:
            for li, _ in entries:
                if already_flagged and (li, col) in already_flagged:
                    continue
                errors.append(
                    f"L{li+1} box char at col {col}, "
                    f"expected col {most_common}"
                )
    return errors


def _check_rails_by_column(group, already_flagged):
    errors = []
    for rail in _identify_rails(group):
        errors.extend(_rail_errors(rail, already_flagged))
    return errors


def _check_rails(code_lines):
    errors = []
    is_tree = _is_tree_block(code_lines)
    if is_tree:
        return errors

    groups = []
    current = []
    for i, raw in code_lines:
        has_box = any(c in BOX_CHARS for c in raw)
        if has_box:
            current.append((i, raw))
        else:
            if current:
                groups.append(current)
                current = []
    if current:
        groups.append(current)

    for group in groups:
        index_errors, already_flagged = _check_rails_by_index(group)
        errors.extend(index_errors)
        errors.extend(_check_rails_by_column(group, already_flagged))

    return errors


def fix_tables(lines):
    result = list(lines)
    i = 0
    while i < len(result):
        raw = result[i].rstrip('\n')
        if raw.startswith('|') and raw.endswith('|') and len(raw) > 2:
            table_start = i
            table_rows = []
            while i < len(result):
                raw = result[i].rstrip('\n')
                if raw.startswith('|') and raw.endswith('|') and len(raw) > 2:
                    table_rows.append(i)
                    i += 1
                else:
                    break

            all_cells = []
            sep_idx = None
            for ri, row_idx in enumerate(table_rows):
                raw = result[row_idx].rstrip('\n')
                cells = raw.split('|')[1:-1]
                all_cells.append(cells)
                if cells and all(c.strip().replace('-', '') == '' for c in cells):
                    sep_idx = ri

            if sep_idx is None:
                continue

            num_cols = max(len(c) for c in all_cells)
            max_widths = [0] * num_cols
            for cells in all_cells:
                for ci, cell in enumerate(cells):
                    w = len(cell.rstrip(' '))
                    if w > max_widths[ci]:
                        max_widths[ci] = w

            for ri, row_idx in enumerate(table_rows):
                cells = all_cells[ri]
                is_sep = (ri == sep_idx)
                new_cells = []
                for ci, cell in enumerate(cells):
                    target = max_widths[ci]
                    if is_sep:
                        new_cells.append('-' * target)
                    else:
                        content = cell.rstrip(' ')
                        new_cells.append(content + ' ' * (target - len(content)))
                result[row_idx] = '|' + '|'.join(new_cells) + '|\n'
        else:
            i += 1
    return result


def fix_box_widths(lines):
    result = list(lines)
    in_code = False
    code_start = 0
    code_indices = []

    for i, line in enumerate(lines):
        raw = line.rstrip('\n')
        if raw.strip().startswith('```'):
            if in_code:
                _fix_widths_in_block(code_indices, result)
                code_indices = []
            in_code = not in_code
            code_start = i
            continue
        if in_code:
            code_indices.append(i)

    return result


def _fix_widths_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip('\n')) for i in code_indices]

    is_tree = _is_tree_block(code_lines)
    if is_tree:
        return

    groups = []
    current = []
    for i, raw in code_lines:
        has_box = any(c in BOX_CHARS for c in raw)
        if has_box:
            current.append((i, raw))
        else:
            if current:
                groups.append(current)
                current = []
    if current:
        groups.append(current)

    for group in groups:
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
                lengths.setdefault(len(raw), []).append(i)

            if len(lengths) <= 1:
                continue

            most_common = max(lengths.keys(), key=lambda k: len(lengths[k]))

            for length, line_indices in lengths.items():
                if length == most_common:
                    continue
                for idx in line_indices:
                    raw = all_lines[idx].rstrip('\n')
                    fixed = _fix_line_width(raw, most_common)
                    if fixed != raw:
                        all_lines[idx] = fixed + '\n'


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
        while run_start >= 0 and raw[run_start] == '─':
            run_start -= 1
        run_start += 1
        run_length = run_end - run_start

        if run_length == 0:
            return raw
        new_length = run_length + delta
        if new_length < 1:
            return raw

        return raw[:run_start] + '─' * new_length + raw[run_end:]

    if '│' in raw:
        close_idx = raw.rindex('│')
        if delta > 0:
            return raw[:close_idx] + ' ' * delta + raw[close_idx:]
        else:
            remove = abs(delta)
            if close_idx - remove < 0:
                return raw
            region = raw[close_idx - remove:close_idx]
            if region == ' ' * remove:
                return raw[:close_idx - remove] + raw[close_idx:]
            return raw

    return raw


def fix_rail_alignment(lines):
    result = list(lines)
    in_code = False
    code_indices = []

    for i, line in enumerate(lines):
        raw = line.rstrip('\n')
        if raw.strip().startswith('```'):
            if in_code:
                _fix_rails_in_block(code_indices, result)
                code_indices = []
            in_code = not in_code
            continue
        if in_code:
            code_indices.append(i)

    return result


def _fix_rails_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip('\n')) for i in code_indices]

    is_tree = _is_tree_block(code_lines)
    if is_tree:
        return

    groups = []
    current = []
    for i, raw in code_lines:
        has_box = any(c in BOX_CHARS for c in raw)
        if has_box:
            current.append((i, raw))
        else:
            if current:
                groups.append(current)
                current = []
    if current:
        groups.append(current)

    for group in groups:
        _fix_rails_by_index(group, all_lines)
        group = [(i, all_lines[i].rstrip('\n')) for i, _ in group]
        _fix_rails_by_column(group, all_lines)


def _build_corrections(rails):
    corrections = {}
    for rail in rails:
        col_data = {}
        for line_idx, col, char in rail:
            col_data.setdefault(col, []).append((line_idx, char))
        if len(col_data) <= 1:
            continue
        pipe_origins = {col: sum(1 for _, c in entries if c in ('┬', '┴'))
                        for col, entries in col_data.items()}
        structural = {col: sum(1 for _, c in entries if c not in ('│', '┼'))
                      for col, entries in col_data.items()}
        earliest = {col: min(li for li, _ in entries)
                    for col, entries in col_data.items()}
        has_pipe = any(v > 0 for v in pipe_origins.values())
        has_structural = any(v > 0 for v in structural.values())
        if has_pipe:
            most_common = max(col_data.keys(),
                              key=lambda k: (pipe_origins[k], structural[k], len(col_data[k]), -earliest[k]))
        elif has_structural:
            most_common = max(col_data.keys(),
                              key=lambda k: (structural[k], len(col_data[k]), -earliest[k]))
        else:
            most_common = max(col_data.keys(), key=lambda k: len(col_data[k]))
        minority = len(rail) - len(col_data[most_common])
        if not has_structural and not has_pipe and minority * 3 > len(rail):
            continue
        for col, entries in col_data.items():
            if col != most_common:
                for li, _ in entries:
                    corrections[(li, col)] = most_common
    return corrections


def _apply_corrections(group, all_lines, corrections):
    for i, raw in group:
        actual = [j for j, c in enumerate(raw) if c in BOX_CHARS]
        expected = [corrections.get((i, j), j) for j in actual]
        if actual == expected:
            continue
        fixed = _realign_box_chars(raw, actual, expected)
        if fixed != raw:
            all_lines[i] = fixed + '\n'


def _fix_rails_by_index(group, all_lines):
    by_count = {}
    for i, raw in group:
        positions = tuple(j for j, c in enumerate(raw) if c in BOX_CHARS)
        by_count.setdefault(len(positions), []).append((i, raw, positions))

    corrections = {}
    for count, items in by_count.items():
        if count < 2:
            continue
        for cluster in _cluster_by_positions(items):
            for pos_idx in range(count):
                col_counts = {}
                for i, raw, positions in cluster:
                    col = positions[pos_idx]
                    col_counts.setdefault(col, []).append(i)
                if len(col_counts) <= 1:
                    continue
                most_common = max(col_counts.keys(), key=lambda k: len(col_counts[k]))
                for col, line_indices in col_counts.items():
                    if col != most_common:
                        for li in line_indices:
                            corrections[(li, col)] = most_common

    _apply_corrections(group, all_lines, corrections)


def _fix_rails_by_column(group, all_lines):
    corrections = _build_corrections(_identify_rails(group))
    _apply_corrections(group, all_lines, corrections)


def _realign_box_chars(raw, actual, expected):
    n = len(actual)
    segments = []
    chars = []
    prev = 0
    for p in actual:
        segments.append(raw[prev:p])
        chars.append(raw[p])
        prev = p + 1
    segments.append(raw[prev:])

    expected_widths = []
    for i in range(n + 1):
        if i == 0:
            expected_widths.append(expected[0])
        elif i < n:
            expected_widths.append(expected[i] - expected[i - 1] - 1)
        else:
            expected_widths.append(len(raw) - expected[-1] - 1)

    new_segments = []
    for seg, exp_w in zip(segments, expected_widths):
        cur_w = len(seg)
        if cur_w == exp_w:
            new_segments.append(seg)
        elif cur_w < exp_w:
            delta = exp_w - cur_w
            if seg and all(c == '─' for c in seg):
                new_segments.append(seg + '─' * delta)
            else:
                new_segments.append(seg + ' ' * delta)
        else:
            delta = cur_w - exp_w
            trailing_spaces = len(seg) - len(seg.rstrip(' '))
            if trailing_spaces >= delta:
                new_segments.append(seg[:cur_w - delta])
            else:
                trailing_dashes = len(seg) - len(seg.rstrip('─'))
                if trailing_dashes >= delta:
                    new_segments.append(seg[:cur_w - delta])
                else:
                    return raw

    result = []
    for i, seg in enumerate(new_segments):
        result.append(seg)
        if i < len(chars):
            result.append(chars[i])

    return ''.join(result)


ARROW_CHARS = {'v', '^'}


def check_arrow_alignment(fname, lines):
    errors = []
    in_code = False
    code_lines = []

    for i, line in enumerate(lines):
        raw = line.rstrip('\n')
        if raw.strip().startswith('```'):
            if in_code:
                errors.extend(_check_arrows(code_lines))
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append((i, raw))

    return errors


def _is_standalone_arrow(raw, j):
    return ((j == 0 or raw[j - 1] == ' ') and
            (j == len(raw) - 1 or raw[j + 1] == ' '))


def _check_arrows(code_lines):
    errors = []
    for idx, (i, raw) in enumerate(code_lines):
        for j, c in enumerate(raw):
            if c not in ARROW_CHARS or not _is_standalone_arrow(raw, j):
                continue
            expected = _find_arrow_target(code_lines, idx, j, c)
            if expected is not None and expected != j:
                errors.append(
                    f"L{i+1} arrow '{c}' at col {j}, "
                    f"expected col {expected}"
                )
    return errors


def _find_arrow_target(code_lines, arrow_idx, arrow_col, arrow_char):
    search_range = range(arrow_idx - 1, -1, -1) if arrow_char == 'v' else range(arrow_idx + 1, len(code_lines))
    for si in search_range:
        _, sraw = code_lines[si]
        for dc in [0, -1, 1, -2, 2]:
            col = arrow_col + dc
            if 0 <= col < len(sraw) and sraw[col] in BOX_CHARS:
                return col if dc != 0 else None
        break
    return None


def fix_arrow_alignment(lines):
    result = list(lines)
    in_code = False
    code_indices = []

    for i, line in enumerate(lines):
        raw = line.rstrip('\n')
        if raw.strip().startswith('```'):
            if in_code:
                _fix_arrows_in_block(code_indices, result)
                code_indices = []
            in_code = not in_code
            continue
        if in_code:
            code_indices.append(i)

    return result


def _fix_arrows_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip('\n')) for i in code_indices]
    for idx, (i, raw) in enumerate(code_lines):
        arrows = [(j, c) for j, c in enumerate(raw)
                  if c in ARROW_CHARS and _is_standalone_arrow(raw, j)]
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
                    if new_raw[k] == ' ':
                        spaces_after += 1
                    else:
                        break
                if spaces_after >= delta:
                    new_raw = new_raw[:j] + ' ' * delta + new_raw[j] + new_raw[j + 1 + delta:]
            elif delta < 0:
                remove = abs(delta)
                spaces_before = 0
                for k in range(j - 1, -1, -1):
                    if new_raw[k] == ' ':
                        spaces_before += 1
                    else:
                        break
                if spaces_before >= remove:
                    new_raw = new_raw[:j - remove] + new_raw[j] + ' ' * remove + new_raw[j + 1:]
        if new_raw != raw:
            all_lines[i] = new_raw + '\n'


PIPE_DRIFT_MAX = 5


def _find_nearby_isolated_pipe(raw, expected_col, max_drift):
    for dc in range(1, max_drift + 1):
        for sign in [-1, 1]:
            nc = expected_col + sign * dc
            if 0 <= nc < len(raw) and raw[nc] == '│':
                left_ok = (nc == 0 or raw[nc - 1] == ' ')
                right_ok = (nc == len(raw) - 1 or raw[nc + 1] == ' ')
                if left_ok and right_ok:
                    return nc
    return None


def check_pipe_continuity(fname, lines):
    errors = []
    in_code = False
    code_lines = []

    for i, line in enumerate(lines):
        raw = line.rstrip('\n')
        if raw.strip().startswith('```'):
            if in_code:
                errors.extend(_check_pipe_continuity(code_lines))
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append((i, raw))

    return errors


def _check_pipe_continuity(code_lines):
    errors = []
    is_tree = _is_tree_block(code_lines)
    if is_tree:
        return errors

    flagged = set()

    for idx, (i, raw) in enumerate(code_lines):
        for j, c in enumerate(raw):
            if c == '┬':
                _trace_pipe_check(code_lines, idx, j, 1, flagged, errors)
            elif c == '┴':
                _trace_pipe_check(code_lines, idx, j, -1, flagged, errors)

    return errors


def _trace_pipe_check(code_lines, start_idx, col, direction, flagged, errors):
    line_range = (range(start_idx + 1, len(code_lines)) if direction == 1
                  else range(start_idx - 1, -1, -1))
    for si in line_range:
        line_idx, sraw = code_lines[si]
        if col < len(sraw) and sraw[col] in BOX_CHARS:
            if sraw[col] == '│':
                continue
            break
        found = _find_nearby_isolated_pipe(sraw, col, PIPE_DRIFT_MAX)
        if found is not None:
            if (line_idx, found) not in flagged:
                flagged.add((line_idx, found))
                errors.append(
                    f"L{line_idx+1} pipe '│' at col {found}, "
                    f"expected col {col}"
                )
        else:
            break


def fix_pipe_continuity(lines):
    result = list(lines)
    in_code = False
    code_indices = []

    for i, line in enumerate(lines):
        raw = line.rstrip('\n')
        if raw.strip().startswith('```'):
            if in_code:
                _fix_pipes_in_block(code_indices, result)
                code_indices = []
            in_code = not in_code
            continue
        if in_code:
            code_indices.append(i)

    return result


def _fix_pipes_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip('\n')) for i in code_indices]
    is_tree = _is_tree_block(code_lines)
    if is_tree:
        return

    corrections = {}
    for idx, (i, raw) in enumerate(code_lines):
        for j, c in enumerate(raw):
            if c == '┬':
                _trace_pipe_fix(code_lines, idx, j, 1, corrections)
            elif c == '┴':
                _trace_pipe_fix(code_lines, idx, j, -1, corrections)

    by_line = {}
    for (line_idx, current_col), expected_col in corrections.items():
        by_line.setdefault(line_idx, []).append((current_col, expected_col))

    for line_idx, line_corrections in by_line.items():
        raw = all_lines[line_idx].rstrip('\n')
        for current_col, expected_col in sorted(line_corrections, key=lambda x: -x[0]):
            raw = _shift_pipe(raw, current_col, expected_col)
        all_lines[line_idx] = raw + '\n'


def _trace_pipe_fix(code_lines, start_idx, col, direction, corrections):
    line_range = (range(start_idx + 1, len(code_lines)) if direction == 1
                  else range(start_idx - 1, -1, -1))
    for si in line_range:
        line_idx, sraw = code_lines[si]
        if col < len(sraw) and sraw[col] in BOX_CHARS:
            if sraw[col] == '│':
                continue
            break
        found = _find_nearby_isolated_pipe(sraw, col, PIPE_DRIFT_MAX)
        if found is not None:
            corrections[(line_idx, found)] = col
        else:
            break


def _shift_pipe(raw, current_col, expected_col):
    if current_col >= len(raw) or raw[current_col] != '│':
        return raw
    delta = expected_col - current_col
    if delta == 0:
        return raw
    if delta > 0:
        spaces_after = 0
        for k in range(current_col + 1, len(raw)):
            if raw[k] == ' ':
                spaces_after += 1
            else:
                break
        if spaces_after >= delta:
            return raw[:current_col] + ' ' * delta + '│' + raw[current_col + 1 + delta:]
    else:
        remove = abs(delta)
        spaces_before = 0
        for k in range(current_col - 1, -1, -1):
            if raw[k] == ' ':
                spaces_before += 1
            else:
                break
        if spaces_before >= remove:
            result = raw[:current_col - remove] + '│' + ' ' * remove + raw[current_col + 1:]
            return result.rstrip(' ')
    return raw


BOX_WALL_DRIFT = 8


def _find_box_closer(raw, open_char, close_char, start_col):
    depth = 0
    for k in range(start_col, len(raw)):
        if raw[k] == open_char:
            depth += 1
        elif raw[k] == close_char:
            depth -= 1
            if depth == 0:
                return k
    return None


def _find_nearby_wall(raw, expected_col, max_drift):
    for dc in range(1, max_drift + 1):
        for sign in [-1, 1]:
            nc = expected_col + sign * dc
            if 0 <= nc < len(raw) and raw[nc] == '│':
                left_ok = (nc == 0 or raw[nc - 1] == ' ')
                right_ok = (nc == len(raw) - 1 or raw[nc + 1] == ' ')
                if left_ok and right_ok:
                    return nc
    return None


def check_box_walls(fname, lines):
    errors = []
    in_code = False
    code_lines = []

    for i, line in enumerate(lines):
        raw = line.rstrip('\n')
        if raw.strip().startswith('```'):
            if in_code:
                errors.extend(_check_box_walls(code_lines))
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append((i, raw))

    return errors


def _check_box_walls(code_lines):
    errors = []
    is_tree = _is_tree_block(code_lines)
    if is_tree:
        return errors

    for idx, (line_idx, raw) in enumerate(code_lines):
        j = 0
        while j < len(raw):
            if raw[j] != '┌':
                j += 1
                continue

            col_left = j
            col_right_open = _find_box_closer(raw, '┌', '┐', j)
            if col_right_open is None or col_right_open - col_left < 4:
                j += 1
                continue

            closing_idx = None
            for si in range(idx + 1, len(code_lines)):
                _, sraw = code_lines[si]
                if col_left < len(sraw) and sraw[col_left] == '└':
                    closing_idx = si
                    break

            if closing_idx is None or closing_idx - idx < 3:
                j = col_right_open + 1
                continue

            closing_line_idx, closing_raw = code_lines[closing_idx]
            col_right_close = _find_box_closer(closing_raw, '└', '┘', col_left)

            if col_right_close is not None:
                if abs(col_right_close - col_right_open) > BOX_WALL_DRIFT:
                    j = col_right_open + 1
                    continue
                expected_right = max(col_right_open, col_right_close)
            else:
                expected_right = col_right_open

            if col_right_open != expected_right:
                errors.append(
                    f"L{line_idx+1} box ┐ at col {col_right_open}, "
                    f"expected col {expected_right}"
                )

            if col_right_close is not None and col_right_close != expected_right:
                errors.append(
                    f"L{closing_line_idx+1} box ┘ at col {col_right_close}, "
                    f"expected col {expected_right}"
                )

            for mi in range(idx + 1, closing_idx):
                m_line_idx, m_raw = code_lines[mi]
                right_ok = (expected_right < len(m_raw) and
                            m_raw[expected_right] in BOX_CHARS)
                if not right_ok:
                    found = _find_nearby_wall(m_raw, expected_right, BOX_WALL_DRIFT)
                    if found is not None:
                        errors.append(
                            f"L{m_line_idx+1} box wall │ at col {found}, "
                            f"expected col {expected_right} "
                            f"(box ┌ at L{line_idx+1} col {col_left})"
                        )
                if col_left < len(m_raw):
                    if m_raw[col_left] not in BOX_CHARS:
                        found = _find_nearby_wall(m_raw, col_left, BOX_WALL_DRIFT)
                        if found is not None:
                            errors.append(
                                f"L{m_line_idx+1} box wall │ at col {found}, "
                                f"expected col {col_left} "
                                f"(box ┌ at L{line_idx+1} col {col_left})"
                            )

            j = col_right_open + 1

    return errors


def fix_box_walls(lines):
    result = list(lines)
    in_code = False
    code_indices = []

    for i, line in enumerate(lines):
        raw = line.rstrip('\n')
        if raw.strip().startswith('```'):
            if in_code:
                _fix_box_walls_in_block(code_indices, result)
                code_indices = []
            in_code = not in_code
            continue
        if in_code:
            code_indices.append(i)

    return result


def _fix_closer(raw, current_col, expected_col, closer_char):
    if current_col >= len(raw) or raw[current_col] != closer_char:
        return raw
    delta = expected_col - current_col
    if delta == 0:
        return raw

    run_end = current_col
    run_start = run_end - 1
    while run_start >= 0 and raw[run_start] == '─':
        run_start -= 1
    run_start += 1
    run_length = run_end - run_start
    if run_length == 0:
        return raw

    new_run_length = run_length + delta
    if new_run_length < 1:
        return raw

    before = raw[:run_start]
    after = raw[current_col + 1:]

    if delta > 0:
        space_count = 0
        for ch in after:
            if ch == ' ':
                space_count += 1
            else:
                break
        if space_count >= delta:
            return before + '─' * new_run_length + closer_char + after[delta:]
    else:
        return before + '─' * new_run_length + closer_char + ' ' * abs(delta) + after

    return raw


def _shift_wall(raw, current_col, expected_col):
    if current_col >= len(raw) or raw[current_col] != '│':
        return raw
    delta = expected_col - current_col
    if delta == 0:
        return raw
    if delta > 0:
        spaces_after = 0
        for k in range(current_col + 1, len(raw)):
            if raw[k] == ' ':
                spaces_after += 1
            else:
                break
        if spaces_after >= delta:
            return raw[:current_col] + ' ' * delta + '│' + raw[current_col + 1 + delta:]
        elif current_col >= len(raw) - 1:
            return raw[:current_col] + ' ' * delta + '│'
    else:
        remove = abs(delta)
        spaces_before = 0
        for k in range(current_col - 1, -1, -1):
            if raw[k] == ' ':
                spaces_before += 1
            else:
                break
        if spaces_before >= remove:
            return raw[:current_col - remove] + '│' + ' ' * remove + raw[current_col + 1:]
    return raw


def _fix_box_walls_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip('\n')) for i in code_indices]
    is_tree = _is_tree_block(code_lines)
    if is_tree:
        return

    for idx, (line_idx, raw) in enumerate(code_lines):
        j = 0
        while j < len(raw):
            if raw[j] != '┌':
                j += 1
                continue

            col_left = j
            col_right_open = _find_box_closer(raw, '┌', '┐', j)
            if col_right_open is None or col_right_open - col_left < 4:
                j += 1
                continue

            closing_idx = None
            for si in range(idx + 1, len(code_lines)):
                si_idx = code_lines[si][0]
                sraw = all_lines[si_idx].rstrip('\n')
                if col_left < len(sraw) and sraw[col_left] == '└':
                    closing_idx = si
                    break

            if closing_idx is None or closing_idx - idx < 3:
                j = col_right_open + 1
                continue

            closing_line_idx = code_lines[closing_idx][0]
            closing_raw = all_lines[closing_line_idx].rstrip('\n')
            col_right_close = _find_box_closer(closing_raw, '└', '┘', col_left)

            if col_right_close is not None:
                if abs(col_right_close - col_right_open) > BOX_WALL_DRIFT:
                    j = col_right_open + 1
                    continue
                expected_right = max(col_right_open, col_right_close)
            else:
                expected_right = col_right_open

            changed = False

            if col_right_open != expected_right:
                fixed = _fix_closer(raw, col_right_open, expected_right, '┐')
                if fixed != raw:
                    all_lines[line_idx] = fixed + '\n'
                    changed = True

            if col_right_close is not None and col_right_close != expected_right:
                cur = all_lines[closing_line_idx].rstrip('\n')
                fixed = _fix_closer(cur, col_right_close, expected_right, '┘')
                if fixed != cur:
                    all_lines[closing_line_idx] = fixed + '\n'
                    changed = True

            for mi in range(idx + 1, closing_idx):
                m_line_idx = code_lines[mi][0]
                m_raw = all_lines[m_line_idx].rstrip('\n')
                right_ok = (expected_right < len(m_raw) and
                            m_raw[expected_right] in BOX_CHARS)
                if not right_ok:
                    found = _find_nearby_wall(m_raw, expected_right, BOX_WALL_DRIFT)
                    if found is not None:
                        fixed = _shift_wall(m_raw, found, expected_right)
                        if fixed != m_raw:
                            all_lines[m_line_idx] = fixed + '\n'
                            m_raw = fixed
                            changed = True
                if col_left < len(m_raw):
                    if m_raw[col_left] not in BOX_CHARS:
                        found = _find_nearby_wall(m_raw, col_left, BOX_WALL_DRIFT)
                        if found is not None:
                            fixed = _shift_wall(m_raw, found, col_left)
                            if fixed != m_raw:
                                all_lines[m_line_idx] = fixed + '\n'
                                changed = True

            if changed:
                code_lines = [(i, all_lines[i].rstrip('\n')) for i in code_indices]
                raw = all_lines[line_idx].rstrip('\n')

            j = col_right_open + 1


def print_help():
    print("""align-docs.py - Auto-fix alignment issues in markdown documentation files.

Checks and fixes:
  1. Tables          - pads cells so every column matches the separator row width
  2. Box widths      - ensures all lines in a box group have the same total length
  3. Rail alignment  - aligns vertically adjacent box chars to the same column
  4. Arrow alignment - aligns standalone v/^ arrows with the nearest box char above/below
  5. Pipe continuity - traces from T-junctions to detect drifted connector pipes
  6. Box walls       - verifies nested box right walls match their opening/closing borders

Usage:
  python3 align-docs.py <path>               # auto-fix file or all .md in folder
  python3 align-docs.py --check <path>       # detect-only, no writes

Exit codes:
  0 - all docs aligned (or all issues auto-fixed)
  1 - unfixable issues remain (fix mode) or errors found (check mode)""")


def _collect_files(path):
    path = os.path.abspath(path)
    if os.path.isfile(path):
        return [path]
    if os.path.isdir(path):
        files = []
        for root, dirs, filenames in os.walk(path):
            for fn in sorted(filenames):
                if fn.endswith('.md'):
                    files.append(os.path.join(root, fn))
        return files
    print(f"error: '{path}' is not a valid file or directory")
    sys.exit(1)


def main():
    check_only = '--check' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--check']

    if len(args) == 0:
        print_help()
        sys.exit(0)

    files = []
    for a in args:
        files.extend(_collect_files(a))

    total_errors = 0
    total_fixed = 0

    for fpath in sorted(files):
        with open(fpath) as f:
            lines = f.readlines()

        rel = os.path.relpath(fpath)
        errs = []
        errs.extend(check_tables(rel, lines))
        errs.extend(check_line_widths_in_boxes(rel, lines))
        errs.extend(check_box_walls(rel, lines))
        errs.extend(check_rail_alignment(rel, lines))
        errs.extend(check_arrow_alignment(rel, lines))
        errs.extend(check_pipe_continuity(rel, lines))

        if errs:
            if check_only:
                print(f"\n{rel}:")
                for e in errs:
                    print(f"  {e}")
                total_errors += len(errs)
            else:
                fixed_lines = fix_tables(lines)
                fixed_lines = fix_box_widths(fixed_lines)
                for _ in range(3):
                    prev = list(fixed_lines)
                    fixed_lines = fix_box_walls(fixed_lines)
                    fixed_lines = fix_rail_alignment(fixed_lines)
                    fixed_lines = fix_pipe_continuity(fixed_lines)
                    if fixed_lines == prev:
                        break
                fixed_lines = fix_arrow_alignment(fixed_lines)
                with open(fpath, 'w') as f:
                    f.writelines(fixed_lines)

                with open(fpath) as f:
                    recheck_lines = f.readlines()
                remaining = []
                remaining.extend(check_tables(rel, recheck_lines))
                remaining.extend(check_line_widths_in_boxes(rel, recheck_lines))
                remaining.extend(check_box_walls(rel, recheck_lines))
                remaining.extend(check_rail_alignment(rel, recheck_lines))
                remaining.extend(check_arrow_alignment(rel, recheck_lines))
                remaining.extend(check_pipe_continuity(rel, recheck_lines))

                fixed_count = len(errs) - len(remaining)
                if fixed_count > 0:
                    print(f"{rel}: fixed {fixed_count} issue(s)")
                    total_fixed += fixed_count
                if remaining:
                    print(f"\n{rel}: {len(remaining)} unfixable issue(s):")
                    for e in remaining:
                        print(f"  {e}")
                    total_errors += len(remaining)

    if check_only:
        if total_errors == 0:
            print("ALL DOCS ALIGNED - no errors found")
        else:
            print(f"\n{total_errors} error(s) found")
            sys.exit(1)
    else:
        if total_fixed > 0:
            print(f"\n{total_fixed} issue(s) auto-fixed")
        if total_errors > 0:
            print(f"{total_errors} issue(s) could not be auto-fixed")
            sys.exit(1)
        elif total_fixed == 0:
            print("ALL DOCS ALIGNED - no errors found")


if __name__ == '__main__':
    main()
