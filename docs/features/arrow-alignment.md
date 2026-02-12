# Arrow Alignment

Module: `align_md_docs/arrows.py`

## What it does

Aligns standalone `v` and `^` arrow characters with the nearest box-drawing character in the line above (for `v`) or below (for `^`). Arrows embedded in text are ignored.

## Detection

For each character in a code block line:
1. Check if it is `v` or `^`
2. Check if it is standalone (spaces or line boundary on both sides)
3. Search the adjacent line (above for `v`, below for `^`) for a box char within 2 columns
4. If found at a different column, report as misaligned

```
┌────────────────────────────────────┐
│  For each line in code block:      │
│  find standalone v/^ chars         │
│         │                          │
│         v                          │
│  _find_arrow_target():             │
│  search adjacent line at offsets   │
│  [0, -1, +1, -2, +2]               │
│         │                          │
│    ┌────┴────┐                     │
│    │ offset  │                     │
│    │ = 0?    │                     │
│    └────┬────┘                     │
│   yes   │   no                     │
│ already │  report                  │
│ aligned │  expected col            │
└─────────┴──────────────────────────┘
```

## Check output

Format: `L{line} arrow '{char}' at col {actual}, expected col {target}`

## Fix algorithm

1. For each line, collect all arrow corrections
2. Apply corrections right-to-left:
   - Shift right: insert spaces before arrow, remove spaces after
   - Shift left: remove spaces before arrow, insert spaces after
3. Only shift if sufficient spaces exist (no overwriting content)

## Standalone check

An arrow is standalone when:
- Left neighbor is space or it is at position 0
- Right neighbor is space or it is at end of line

This prevents matching `v` in words like "value" or `^` in expressions.

## Scope

- Operates only within fenced code blocks
- No tree block exclusion needed (arrows are not tree chars)
- Runs last in the fix pipeline, after all box-related fixes have stabilized positions

---

related docs:
- docs/concepts.md     - arrow alignment concept
- docs/architecture.md - runs last in fix pipeline

related sources:
- align_md_docs/arrows.py - check and fix implementation
- align_md_docs/utils.py  - ARROW_CHARS, _is_standalone_arrow
