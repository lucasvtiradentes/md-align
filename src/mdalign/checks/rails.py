from mdalign.parser import group_box_lines, iter_code_blocks
from mdalign.utils import (
    BOX_CHARS,
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


def _rail_errors(rail, already_flagged=None):
    errors = []
    col_data = {}
    for line_idx, col, char in rail:
        col_data.setdefault(col, []).append((line_idx, char))

    if len(col_data) <= 1:
        return errors

    pipe_origins = {col: sum(1 for _, c in entries if c in ("┬", "┴")) for col, entries in col_data.items()}
    structural = {col: sum(1 for _, c in entries if c not in ("│", "┼")) for col, entries in col_data.items()}
    earliest = {col: min(li for li, _ in entries) for col, entries in col_data.items()}
    has_pipe = any(v > 0 for v in pipe_origins.values())
    has_structural = any(v > 0 for v in structural.values())
    if has_pipe:
        most_common = max(
            col_data.keys(), key=lambda k: (pipe_origins[k], structural[k], len(col_data[k]), -earliest[k])
        )
    elif has_structural:
        most_common = max(col_data.keys(), key=lambda k: (structural[k], len(col_data[k]), -earliest[k]))
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
                errors.append(f"L{li + 1} box char at col {col}, expected col {most_common}")
    return errors


def _check_rails_by_column(group, already_flagged):
    errors = []
    for rail in _identify_rails(group):
        errors.extend(_rail_errors(rail, already_flagged))
    return errors


def _check_rails(code_lines):
    errors = []
    if _is_tree_block(code_lines):
        return errors

    for group in group_box_lines(code_lines):
        index_errors, already_flagged = _check_rails_by_index(group)
        errors.extend(index_errors)
        errors.extend(_check_rails_by_column(group, already_flagged))

    return errors


def _build_corrections(rails):
    corrections = {}
    for rail in rails:
        col_data = {}
        for line_idx, col, char in rail:
            col_data.setdefault(col, []).append((line_idx, char))
        if len(col_data) <= 1:
            continue
        pipe_origins = {col: sum(1 for _, c in entries if c in ("┬", "┴")) for col, entries in col_data.items()}
        structural = {col: sum(1 for _, c in entries if c not in ("│", "┼")) for col, entries in col_data.items()}
        earliest = {col: min(li for li, _ in entries) for col, entries in col_data.items()}
        has_pipe = any(v > 0 for v in pipe_origins.values())
        has_structural = any(v > 0 for v in structural.values())
        if has_pipe:
            most_common = max(
                col_data.keys(), key=lambda k: (pipe_origins[k], structural[k], len(col_data[k]), -earliest[k])
            )
        elif has_structural:
            most_common = max(col_data.keys(), key=lambda k: (structural[k], len(col_data[k]), -earliest[k]))
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
    corrections = _build_corrections(_identify_rails(group))
    _apply_corrections(group, all_lines, corrections)


def _fix_rails_in_block(code_indices, all_lines):
    code_lines = [(i, all_lines[i].rstrip("\n")) for i in code_indices]

    if _is_tree_block(code_lines):
        return

    for group in group_box_lines(code_lines):
        _fix_rails_by_index(group, all_lines)
        group = [(i, all_lines[i].rstrip("\n")) for i, _ in group]
        _fix_rails_by_column(group, all_lines)
