BOX_CHARS = set("│┌└├┐┘┤┬┴┼")
BOX_CLOSERS = {"┐", "┘", "┤"}
BOX_OPENERS = {"┌", "└", "├"}
ARROW_CHARS = {"v", "^"}

RAIL_THRESHOLD = 1
RAIL_MAX_GAP = 1
CLUSTER_THRESHOLD = 3
BOX_WALL_DRIFT = 8
PIPE_DRIFT_MAX = 5


def _is_tree_block(code_lines):
    has_branches = any("├──" in raw or "└──" in raw for _, raw in code_lines)
    has_box_borders = any("┌" in raw or "┐" in raw for _, raw in code_lines)
    return has_branches and not has_box_borders


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
            if 0 <= nc < len(raw) and raw[nc] == "│":
                left_ok = nc == 0 or raw[nc - 1] == " "
                right_ok = nc == len(raw) - 1 or raw[nc + 1] == " "
                if left_ok and right_ok:
                    return nc
    return None


def _find_nearby_isolated_pipe(raw, expected_col, max_drift):
    for dc in range(1, max_drift + 1):
        for sign in [-1, 1]:
            nc = expected_col + sign * dc
            if 0 <= nc < len(raw) and raw[nc] == "│":
                left_ok = nc == 0 or raw[nc - 1] == " "
                right_ok = nc == len(raw) - 1 or raw[nc + 1] == " "
                if left_ok and right_ok:
                    return nc
    return None


def _shift_wall(raw, current_col, expected_col):
    if current_col >= len(raw) or raw[current_col] != "│":
        return raw
    delta = expected_col - current_col
    if delta == 0:
        return raw
    if delta > 0:
        spaces_after = 0
        for k in range(current_col + 1, len(raw)):
            if raw[k] == " ":
                spaces_after += 1
            else:
                break
        if spaces_after >= delta:
            return raw[:current_col] + " " * delta + "│" + raw[current_col + 1 + delta :]
        elif current_col >= len(raw) - 1:
            return raw[:current_col] + " " * delta + "│"
    else:
        remove = abs(delta)
        spaces_before = 0
        for k in range(current_col - 1, -1, -1):
            if raw[k] == " ":
                spaces_before += 1
            else:
                break
        if spaces_before >= remove:
            return raw[: current_col - remove] + "│" + " " * remove + raw[current_col + 1 :]
    return raw


def _shift_pipe(raw, current_col, expected_col):
    if current_col >= len(raw) or raw[current_col] != "│":
        return raw
    delta = expected_col - current_col
    if delta == 0:
        return raw
    if delta > 0:
        spaces_after = 0
        for k in range(current_col + 1, len(raw)):
            if raw[k] == " ":
                spaces_after += 1
            else:
                break
        if spaces_after >= delta:
            return raw[:current_col] + " " * delta + "│" + raw[current_col + 1 + delta :]
    else:
        remove = abs(delta)
        spaces_before = 0
        for k in range(current_col - 1, -1, -1):
            if raw[k] == " ":
                spaces_before += 1
            else:
                break
        if spaces_before >= remove:
            result = raw[: current_col - remove] + "│" + " " * remove + raw[current_col + 1 :]
            return result.rstrip(" ")
    return raw


def _fix_closer(raw, current_col, expected_col, closer_char):
    if current_col >= len(raw) or raw[current_col] != closer_char:
        return raw
    delta = expected_col - current_col
    if delta == 0:
        return raw

    run_end = current_col
    run_start = run_end - 1
    while run_start >= 0 and raw[run_start] == "─":
        run_start -= 1
    run_start += 1
    run_length = run_end - run_start
    if run_length == 0:
        return raw

    new_run_length = run_length + delta
    if new_run_length < 1:
        return raw

    before = raw[:run_start]
    after = raw[current_col + 1 :]

    if delta > 0:
        space_count = 0
        for ch in after:
            if ch == " ":
                space_count += 1
            else:
                break
        if space_count >= delta:
            return before + "─" * new_run_length + closer_char + after[delta:]
    else:
        return before + "─" * new_run_length + closer_char + " " * abs(delta) + after

    return raw


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
            if seg and all(c == "─" for c in seg):
                new_segments.append(seg + "─" * delta)
            else:
                new_segments.append(seg + " " * delta)
        else:
            delta = cur_w - exp_w
            trailing_spaces = len(seg) - len(seg.rstrip(" "))
            if trailing_spaces >= delta:
                new_segments.append(seg[: cur_w - delta])
            else:
                trailing_dashes = len(seg) - len(seg.rstrip("─"))
                if trailing_dashes >= delta:
                    new_segments.append(seg[: cur_w - delta])
                else:
                    return raw

    result = []
    for i, seg in enumerate(new_segments):
        result.append(seg)
        if i < len(chars):
            result.append(chars[i])

    return "".join(result)


def _is_standalone_arrow(raw, j):
    return (j == 0 or raw[j - 1] == " ") and (j == len(raw) - 1 or raw[j + 1] == " ")
