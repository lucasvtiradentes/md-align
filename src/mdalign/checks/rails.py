from mdalign.parser import group_box_lines, iter_code_blocks
from mdalign.utils import (
    BOX_CHARS,
    BOX_CLOSERS,
    BOX_OPENERS,
    CLUSTER_THRESHOLD,
    RAIL_MAX_GAP,
    RAIL_THRESHOLD,
    _is_tree_block,
    _realign_box_chars,
)


def check(lines):
    errors = []
    for _, code_lines in iter_code_blocks(lines):
        errors.extend(_check_rails(code_lines))
    return errors


def fix(lines):
    result = list(lines)
    for code_indices, _ in iter_code_blocks(lines):
        _fix_rails_in_block(code_indices, result)
    return result


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


def _has_adjacent_support(group, line_idx, col):
    gi_map = {li: gi for gi, (li, _) in enumerate(group)}
    gi = gi_map.get(line_idx)
    if gi is None:
        return False
    for dgi in [-1, 1]:
        adj = gi + dgi
        if 0 <= adj < len(group):
            _, raw = group[adj]
            if col < len(raw) and raw[col] in BOX_CHARS:
                return True
    return False


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
                            if _has_adjacent_support(group, li, col):
                                continue
                            flagged.add((li, col))
                            errors.append(f"L{li + 1} box char at col {col}, expected col {most_common}")
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


def _resolve_rail(rail, group=None):
    col_data = {}
    for line_idx, col, char in rail:
        col_data.setdefault(col, []).append((line_idx, char))

    if len(col_data) <= 1:
        return None, col_data

    outer_cols = _detect_outer_columns(group) if group else set()
    gi_map = {li: gi for gi, (li, _) in enumerate(group)} if group else {}

    anchored = {}
    for col, entries in col_data.items():
        count = 0
        for li, c in entries:
            if c in ("┬", "┴") and group:
                gi = gi_map.get(li)
                if gi is not None:
                    _, raw = group[gi]
                    if _is_anchored_connector(raw, col, outer_cols):
                        count += 1
        anchored[col] = count

    latest_anchored = {col: max((li for li, c in entries if c in ("┬", "┴")), default=-1) for col, entries in col_data.items()}

    pipe_origins = {col: sum(1 for _, c in entries if c in ("┬", "┴")) for col, entries in col_data.items()}
    structural = {col: sum(1 for _, c in entries if c not in ("│", "┼")) for col, entries in col_data.items()}
    earliest = {col: min(li for li, _ in entries) for col, entries in col_data.items()}
    has_pipe = any(v > 0 for v in pipe_origins.values())
    has_structural = any(v > 0 for v in structural.values())
    has_anchored = any(v > 0 for v in anchored.values())

    if has_anchored:
        most_common = max(
            col_data.keys(), key=lambda k: (anchored[k], latest_anchored[k], pipe_origins[k], structural[k], len(col_data[k]), -earliest[k])
        )
    elif has_pipe:
        most_common = max(
            col_data.keys(), key=lambda k: (pipe_origins[k], structural[k], len(col_data[k]), -earliest[k])
        )
    elif has_structural:
        most_common = max(col_data.keys(), key=lambda k: (structural[k], len(col_data[k]), -earliest[k]))
    else:
        most_common = max(col_data.keys(), key=lambda k: len(col_data[k]))
    minority = len(rail) - len(col_data[most_common])
    if not has_structural and not has_pipe and minority * 3 > len(rail):
        return None, col_data

    return most_common, col_data


def _rail_errors(rail, group=None, already_flagged=None):
    errors = []
    if not rail:
        return errors
    most_common, col_data = _resolve_rail(rail, group)
    if most_common is None:
        return errors

    for col, entries in col_data.items():
        if col != most_common:
            for li, _ in entries:
                if already_flagged and (li, col) in already_flagged:
                    continue
                errors.append(f"L{li + 1} box char at col {col}, expected col {most_common}")
    return errors


def _check_rails_by_column(group, already_flagged):
    errors = []
    for rail in _identify_rails(group):
        errors.extend(_rail_errors(rail, group, already_flagged))
    return errors


CONNECTOR_DRIFT = 5


def _is_anchored_connector(raw, col, outer_cols):
    if col >= len(raw) or raw[col] not in ("┬", "┴"):
        return False
    found_opener = False
    for j in range(col - 1, -1, -1):
        c = raw[j]
        if c == "─" or c in ("┬", "┴", "┼"):
            continue
        found_opener = c in BOX_OPENERS and j not in outer_cols
        break
    if not found_opener:
        return False
    for j in range(col + 1, len(raw)):
        c = raw[j]
        if c == "─" or c in ("┬", "┴", "┼"):
            continue
        return c in BOX_CLOSERS and j not in outer_cols
    return False


def _detect_outer_columns(group):
    col_count = {}
    for _, raw in group:
        for j, c in enumerate(raw):
            if c in BOX_CHARS:
                col_count[j] = col_count.get(j, 0) + 1
    threshold = len(group) * 0.8
    return {col for col, count in col_count.items() if count >= threshold}


def _local_support(group, col, gi, exclude_gi, window=2):
    count = 0
    for dgi in range(-window, window + 1):
        check_gi = gi + dgi
        if check_gi == gi or check_gi == exclude_gi:
            continue
        if 0 <= check_gi < len(group):
            _, raw = group[check_gi]
            if col < len(raw) and raw[col] in BOX_CHARS:
                count += 1
    return count


def _find_connector_drifts(group, already_flagged=None):
    outer = _detect_outer_columns(group)
    inner = {}
    for gi, (line_idx, raw) in enumerate(group):
        chars = {j: c for j, c in enumerate(raw) if c in BOX_CHARS and j not in outer}
        if chars:
            inner[gi] = (line_idx, chars)

    drifts = []
    flagged = set() if already_flagged is None else set(already_flagged)
    for gi_a in sorted(inner):
        gi_b = gi_a + 1
        if gi_b not in inner:
            continue
        li_a, chars_a = inner[gi_a]
        li_b, chars_b = inner[gi_b]
        raw_a = group[gi_a][1]
        raw_b = group[gi_b][1]
        anchored_a = {col for col in chars_a if _is_anchored_connector(raw_a, col, outer)}
        sorted_cols = sorted(anchored_a) + sorted(set(chars_a) - anchored_a)

        for col_a in sorted_cols:
            if col_a in chars_b:
                continue
            candidates = [(abs(col_b - col_a), col_b) for col_b in chars_b if 0 < abs(col_b - col_a) <= CONNECTOR_DRIFT]
            if not candidates:
                continue
            _, col_b = min(candidates)
            if col_b in chars_a:
                continue
            is_anchor_a = col_a in anchored_a
            is_anchor_b = _is_anchored_connector(raw_b, col_b, outer)
            if is_anchor_a and not is_anchor_b:
                if (li_b, col_b) not in flagged:
                    drifts.append((li_b, col_b, col_a))
                    flagged.add((li_b, col_b))
            elif is_anchor_b and not is_anchor_a:
                if (li_a, col_a) not in flagged:
                    drifts.append((li_a, col_a, col_b))
                    flagged.add((li_a, col_a))
            else:
                support_a = _local_support(group, col_a, gi_a, gi_b)
                support_b = _local_support(group, col_b, gi_b, gi_a)
                if support_a < support_b and (li_a, col_a) not in flagged:
                    drifts.append((li_a, col_a, col_b))
                    flagged.add((li_a, col_a))
                elif support_b < support_a and (li_b, col_b) not in flagged:
                    drifts.append((li_b, col_b, col_a))
                    flagged.add((li_b, col_b))
    return drifts


def _check_rails(code_lines):
    errors = []
    if _is_tree_block(code_lines):
        return errors

    for group in group_box_lines(code_lines):
        index_errors, already_flagged = _check_rails_by_index(group)
        errors.extend(index_errors)
        errors.extend(_check_rails_by_column(group, already_flagged))
        for line_idx, col, expected in _find_connector_drifts(group, already_flagged):
            errors.append(f"L{line_idx + 1} box char at col {col}, expected col {expected}")

    return errors


def _build_corrections(rails, group=None):
    corrections = {}
    for rail in rails:
        most_common, col_data = _resolve_rail(rail, group)
        if most_common is None:
            continue
        for col, entries in col_data.items():
            if col != most_common:
                for li, _ in entries:
                    corrections[(li, col)] = most_common
    return corrections


def _apply_corrections(group, all_lines, corrections):
    failed = {}
    for i, raw in group:
        actual = [j for j, c in enumerate(raw) if c in BOX_CHARS]
        expected = [corrections.get((i, j), j) for j in actual]
        if actual == expected:
            continue
        fixed = _realign_box_chars(raw, actual, expected)
        if fixed != raw:
            all_lines[i] = fixed + "\n"
        else:
            for a, e in zip(actual, expected):
                if a != e:
                    failed[(i, a)] = e

    if not failed:
        return

    group_now = [(i, all_lines[i].rstrip("\n")) for i, _ in group]

    reverse = {}
    for (failed_line, failed_col), target_col in failed.items():
        for i, raw in group_now:
            if i == failed_line:
                continue
            box_positions = [j for j, c in enumerate(raw) if c in BOX_CHARS]
            if target_col in box_positions:
                reverse[(i, target_col)] = failed_col

    if not reverse:
        return

    for i, raw in group_now:
        actual = [j for j, c in enumerate(raw) if c in BOX_CHARS]
        expected = [reverse.get((i, j), j) for j in actual]
        if actual == expected:
            continue
        fixed = _realign_box_chars(raw, actual, expected)
        if fixed != raw:
            all_lines[i] = fixed + "\n"


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
    corrections = _build_corrections(_identify_rails(group), group)
    _apply_corrections(group, all_lines, corrections)


def _fix_connector_drifts(group, all_lines):
    drifts = _find_connector_drifts(group)
    if not drifts:
        return
    corrections = {(li, col): expected for li, col, expected in drifts}
    _apply_corrections(group, all_lines, corrections)


def _fix_rails_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]

    if _is_tree_block(code_lines):
        return

    for group in group_box_lines(code_lines):
        _fix_rails_by_index(group, all_lines)
        group = [(i, all_lines[i].rstrip("\n")) for i, _ in group]
        _fix_rails_by_column(group, all_lines)
        group = [(i, all_lines[i].rstrip("\n")) for i, _ in group]
        _fix_connector_drifts(group, all_lines)
