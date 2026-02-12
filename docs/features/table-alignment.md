# Table Alignment

Module: `align_md_docs/tables.py`

## What it does

Detects markdown tables where data row cell widths do not match the separator row column widths, then pads all cells to uniform width.

## Detection

A table is identified by consecutive lines starting and ending with `|`. The separator row contains only dashes and pipes (e.g., `|---|---|`). Column widths are derived from the separator row cell lengths.

```
┌─────────────────────────────────────┐
│  Scan lines for |...|...|           │
│           │                         │
│           v                         │
│  Find separator row (all dashes)    │
│           │                         │
│           v                         │
│  Compare each data row cell width   │
│  against separator widths           │
│           │                         │
│           v                         │
│  Report mismatches as errors        │
└─────────────────────────────────────┘
```

## Check output

Format: `L{line} table col{n}: width={actual} expected={sep_width} (separator at L{sep_line})`

## Fix algorithm

1. Collect all consecutive table rows (lines matching `|...|`)
2. Find the separator row index
3. Calculate max width per column across all rows (using content width, ignoring trailing spaces)
4. Rewrite each row:
   - Separator cells: fill with dashes to target width
   - Data cells: right-pad content with spaces to target width

```
Input:                   Fixed:
|Name |Age||Name |Age|
|-----|---||-----|---|
|Alice|30 ||Alice|30 |
|Bob  |7  ||Bob  |7  |
```

## Scope

- Only processes lines matching the `|...|` pattern
- Does not require code block fences (operates on raw lines)
- Runs first in the fix pipeline, before box-related fixes

---

related docs:
- docs/concepts.md     - table column alignment concept
- docs/architecture.md - position in fix pipeline

related sources:
- align_md_docs/tables.py - check and fix implementation
