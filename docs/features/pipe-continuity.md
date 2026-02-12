# Pipe Continuity

Module: `src/mdalign/checks/pipes.py`

## What it does

Traces connector pipes (`│`) from T-junctions (`┬` downward, `┴` upward) and detects pipes that have drifted from their expected column. Drifted pipes are realigned to match the junction column.

## Detection

For each T-junction found in a code block:
1. Trace in the junction's direction (down for `┬`, up for `┴`)
2. At each subsequent line, check if a box char exists at the expected column
3. If the expected column has a `│`, continue tracing
4. If the expected column has another box char, stop (junction endpoint)
5. If no box char at expected column, search nearby (up to PIPE_DRIFT_MAX = 5 columns)
6. If a drifted isolated pipe is found, report it as an error

```
┌────────────────────────────────┐
│  Find all T-junctions          │
│         │                      │
│         v                      │
│  For each junction:            │
│  trace pipe in direction       │
│         │                      │
│         v                      │
│  At expected col:              │
│  - pipe found? continue        │
│  - other box char? stop        │
│  - nothing? search nearby      │
│         │                      │
│         v                      │
│  Search +/- 5 cols for pipe    │
│  Report drifted pipe           │
└────────────────────────────────┘
```

## Check output

Format: `L{line} pipe '│' at col {actual}, expected col {junction_col}`

## Fix algorithm

1. Collect all corrections: `(line_idx, current_col) -> expected_col`
2. Group corrections by line
3. For each line, apply corrections in right-to-left order using `_shift_pipe()`:
   - Positive shift: move pipe right by inserting spaces before, removing after
   - Negative shift: move pipe left by removing spaces before, inserting after

## Isolation check

A pipe is considered "isolated" (eligible for correction) only if both adjacent characters are spaces (or it sits at a line boundary). This prevents modifying pipes that are part of box structures.

## Scope

- Operates only within fenced code blocks
- Skips tree blocks
- Runs inside the convergence loop (up to 3 iterations)

---

related docs:
- docs/concepts.md     - pipe continuity concept and PIPE_DRIFT_MAX constant
- docs/architecture.md - position in convergence loop

related sources:
- src/mdalign/checks/pipes.py - check and fix implementation
- src/mdalign/utils.py - PIPE_DRIFT_MAX, _find_nearby_isolated_pipe, _shift_pipe
