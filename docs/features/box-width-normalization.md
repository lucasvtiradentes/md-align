# Box Width Normalization

Module: `src/mdalign/checks/box_widths.py`

## What it does

Ensures all lines in a box group that share the same first and last box-character columns have equal total length. Mismatched widths cause ragged right edges in diagrams.

## Detection

Within each code block, lines are grouped by consecutive box-char presence. For each group, lines are further sub-grouped by their first and last box-char column positions (the "extent"). Lines sharing the same extent should have the same total length.

```
┌─────────────────────────────────────────┐
│  iter_code_blocks(lines)                │
│         │                               │
│         v                               │
│  group_box_lines(code_lines)            │
│         │                               │
│         v                               │
│  Sub-group by (first_col, last_col)     │
│         │                               │
│         v                               │
│  Count line lengths per sub-group       │
│         │                               │
│         v                               │
│  Most-common length = target            │
│  Report outliers as errors              │
└─────────────────────────────────────────┘
```

## Check output

Format: `L{line} width={actual}, expected={target} (box group at cols {first}-{last})`

## Fix algorithm

1. Identify the most-common length in each sub-group
2. For lines that differ from the target:
   - Border lines (opener + closer): adjust trailing dash run before the closing corner
   - Content lines (with `│` walls): insert or remove spaces before the closing `│`
3. Skip tree blocks (├── patterns without box borders)

```
Before:                  After:
┌──────────┐             ┌──────────┐
│ content  │             │ content  │
└──────────┘             └──────────┘
(11 chars)               (12 chars, matching others)
```

## Width adjustment strategies

| Line type    | How width is adjusted                              |
|--------------|----------------------------------------------------|
| Border line  | Add/remove `─` chars before the closing corner     |
| Content line | Add/remove spaces before the closing `│`           |

## Scope

- Operates only within fenced code blocks
- Skips tree blocks
- Runs second in the fix pipeline, after tables and before the convergence loop

---

related docs:
- docs/concepts.md     - box width normalization concept
- docs/architecture.md - position in fix pipeline

related sources:
- src/mdalign/checks/box_widths.py - check and fix implementation
- src/mdalign/parser.py     - code block and box group detection
- src/mdalign/utils.py      - BOX_CHARS, BOX_OPENERS, BOX_CLOSERS constants
