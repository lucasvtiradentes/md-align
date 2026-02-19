def split_table_row(raw):
    cells = []
    current = ""
    in_backtick = False
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "`":
            in_backtick = not in_backtick
            current += ch
        elif ch == "|" and not in_backtick:
            cells.append(current)
            current = ""
        else:
            current += ch
        i += 1
    cells.append(current)
    return cells


def check(lines):
    errors = []
    sep_widths = None
    sep_line = None
    for i, line in enumerate(lines):
        raw = line.rstrip("\n")
        if raw.startswith("|") and raw.endswith("|") and len(raw) > 2:
            cells = split_table_row(raw)
            inner_cells = cells[1:-1]
            widths = [len(c) for c in inner_cells]
            is_sep = widths and all(c.strip().replace("-", "") == "" for c in inner_cells)
            if is_sep:
                sep_widths = widths
                sep_line = i + 1
            elif sep_widths:
                for ci, (w, ew) in enumerate(zip(widths, sep_widths)):
                    if w != ew:
                        errors.append(f"L{i + 1} table col{ci}: width={w} expected={ew} (separator at L{sep_line})")
            if not is_sep:
                for ci, cell in enumerate(inner_cells):
                    if cell and not cell.startswith(" "):
                        errors.append(f"L{i + 1} table col{ci}: missing space after |")
                    if cell and not cell.endswith(" "):
                        errors.append(f"L{i + 1} table col{ci}: missing space before |")
        else:
            sep_widths = None
    return errors


def fix(lines):
    result = list(lines)
    i = 0
    while i < len(result):
        raw = result[i].rstrip("\n")
        if raw.startswith("|") and raw.endswith("|") and len(raw) > 2:
            table_rows = []
            while i < len(result):
                raw = result[i].rstrip("\n")
                if raw.startswith("|") and raw.endswith("|") and len(raw) > 2:
                    table_rows.append(i)
                    i += 1
                else:
                    break

            all_cells = []
            sep_idx = None
            for ri, row_idx in enumerate(table_rows):
                raw = result[row_idx].rstrip("\n")
                cells = split_table_row(raw)[1:-1]
                all_cells.append(cells)
                if cells and all(c.strip().replace("-", "") == "" for c in cells):
                    sep_idx = ri

            if sep_idx is None:
                continue

            num_cols = max(len(c) for c in all_cells)
            max_widths = [0] * num_cols
            for ri, cells in enumerate(all_cells):
                if ri == sep_idx:
                    continue
                for ci, cell in enumerate(cells):
                    w = len(cell.strip())
                    if w > max_widths[ci]:
                        max_widths[ci] = w

            for ri, row_idx in enumerate(table_rows):
                cells = all_cells[ri]
                is_sep = ri == sep_idx
                new_cells = []
                for ci, cell in enumerate(cells):
                    target = max_widths[ci]
                    if is_sep:
                        new_cells.append("-" * (target + 2))
                    else:
                        content = cell.strip()
                        new_cells.append(" " + content + " " * (target - len(content)) + " ")
                result[row_idx] = "|" + "|".join(new_cells) + "|\n"
        else:
            i += 1
    return result
