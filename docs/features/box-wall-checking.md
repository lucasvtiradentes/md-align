# Box Wall Checking

Module: `align_md_docs/box_walls.py`

## What it does

Validates that nested box right walls (`┐`/`┘`) and interior pipe walls (`│`) align with their parent box corners. Detects and corrects drift in right-side walls of box structures.

## Detection

For each `┌` found in a code block:

1. Find matching `┐` on the same line using depth-counting
2. Find the `└` at the same left column in a subsequent line
3. Find matching `┘` on the closing line
4. Compute expected right column as max(open_right, close_right)
5. Check all interior lines for wall alignment at expected_right and col_left

```
┌───────────────────────────────────────────┐
│  Find corner at col_left                  │
│         │                                 │
│         v                                 │
│  _find_box_closer(open, close) for top    │
│         │                                 │
│         v                                 │
│  Scan down for bottom-left at col_left    │
│         │                                 │
│         v                                 │
│  _find_box_closer(open, close) for bottom │
│         │                                 │
│         v                                 │
│  expected_right = max(open, close)        │
│         │                                 │
│         v                                 │
│  Check corners and interior wall positions│
│  against expected_right                   │
└───────────────────────────────────────────┘
```

## Tolerances

| Parameter     | Value | Purpose                                      |
|---------------|-------|----------------------------------------------|
| BOX_WALL_DRIFT| 8     | Max distance between open/close right corners|
| Min box size  | 4     | Minimum columns between ┌ and ┐              |
| Min height    | 3     | Minimum lines between ┌ and └ rows           |

If the distance between `col_right_open` and `col_right_close` exceeds BOX_WALL_DRIFT, the box is skipped.

## Check output

Formats:
- `L{line} box ┐ at col {actual}, expected col {target}`
- `L{line} box ┘ at col {actual}, expected col {target}`
- `L{line} box wall │ at col {actual}, expected col {target} (box ┌ at L{open_line} col {col_left})`

## Fix algorithm

1. For opening/closing corners: `_fix_closer()` adjusts the dash run before the corner character
2. For interior walls: `_find_nearby_wall()` locates drifted pipes, `_shift_wall()` moves them
3. After any correction, code_lines are re-read from all_lines to reflect changes for subsequent boxes

The fix cascades through nested boxes. Correcting an outer box may shift inner box positions, which is why box_walls runs in the convergence loop (up to 3 iterations with rails and pipes).

## Nested box handling

```
┌──────────────────────────────────┐
│ Outer box                        │
│  ┌────────────────────────────┐  │
│  │ Inner box                  │  │
│  │  ┌──────────────────────┐  │  │
│  │  │ Innermost box        │  │  │
│  │  └──────────────────────┘  │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

Each `┌` is processed left-to-right, top-to-bottom. After fixing a box, the code_lines are refreshed so subsequent box checks see the corrected state.

## Scope

- Operates only within fenced code blocks
- Skips tree blocks
- Runs inside the convergence loop (up to 3 iterations)

---

related docs:
- docs/concepts.md - box walls concept and BOX_WALL_DRIFT constant
- docs/architecture.md - position in convergence loop

related sources:
- align_md_docs/box_walls.py - check and fix implementation
- align_md_docs/utils.py - BOX_WALL_DRIFT, _find_box_closer, _find_nearby_wall, _shift_wall, _fix_closer
