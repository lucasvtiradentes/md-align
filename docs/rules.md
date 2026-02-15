# Rules

Design principles, conventions, and anti-patterns for mdalign.

## Design principles

- Modular check/fix: each alignment concern lives in its own module (tables, box_widths, box_padding, box_spacing, horiz_arrows, rails, arrows, pipes, box_walls, list_descs, def_lists)
- Common interface: every module exports `check(lines) -> list[str]` and `fix(lines) -> list[str]`
- Iterative convergence: fixes that interact (box_walls, rails, pipes) run in a loop up to 3 times, stopping early if output stabilizes
- Idempotent output: applying fix to already-fixed content produces identical output
- Scope isolation: box-related checks operate inside fenced code blocks; list_descs operates on regular markdown lines (skipping code blocks)
- Tree exclusion: tree-like structures (with branch chars but no box borders) are skipped to avoid false positives

## Module interface convention

```
┌─────────────────────────────────┐
│         Module Contract         │
│                                 │
│  check(lines) -> errors[]       │
│    - lines: list of strings     │
│    - returns: list of error     │
│      strings like               │
│      "L{n} {issue} (context)"   │
│    - never modifies input       │
│                                 │
│  fix(lines) -> fixed_lines[]    │
│    - lines: list of strings     │
│    - returns: new list with     │
│      corrections applied        │
│    - never modifies input list  │
│    - safe to chain              │
└─────────────────────────────────┘
```

## Error message format

All check errors follow the pattern:

```
L{line_number} {description} ({context})
```

Examples:
- `L5 table col0: width=3 expected=5 (separator at L3)`
- `L12 box char at col 15, expected col 17`
- `L8 arrow 'v' at col 4, expected col 6`

## Fix pipeline ordering

The fix order matters:

1. tables.fix - standalone, no dependencies
2. box_widths.fix - must run before rail/wall fixes (sets line lengths)
3. box_padding.fix - normalizes left-padding inside boxes
4. horiz_arrows.fix - closes gaps between arrow tips and box walls
5. Convergence loop (max 3x):
   - box_spacing.fix - ensures right-side spacing
   - box_widths.fix  - re-normalizes widths after spacing changes
   - box_walls.fix   - adjusts corner and wall positions
   - rails.fix       - aligns vertical box char columns
   - pipes.fix       - realigns drifted connector pipes
6. arrows.fix - depends on final box char positions
7. list_descs.fix - independent of box fixes
8. def_lists.fix - independent of box fixes

## Coding conventions

- No runtime dependencies (stdlib only)
- Functions prefixed with `_` are module-internal
- Shared utilities live in utils.py, shared parsers in parser.py
- Constants defined at module level in utils.py with uppercase names
- Lines are always processed as strings with trailing `\n`
- Fixes operate by index into the all_lines list, modifying in-place

## Anti-patterns

- Avoid modifying lines without validating width impact: changing a box char position affects all lines in the same box group
- Do not apply fixes without detecting issues first: the fix pipeline only triggers when run_checks finds errors
- Do not skip the convergence loop: box_walls, rails, and pipes interact; a single pass may leave drift
- Do not process content outside code fences for box-related checks: list_descs is the only module that operates on regular markdown
- Do not treat tree blocks as box diagrams: branch characters overlap with box chars but have different semantics

---

related docs:
- docs/architecture.md - fix pipeline flow and ordering
- docs/concepts.md     - domain terminology referenced here

related sources:
- src/mdalign/cli.py    - pipeline orchestration, check/fix dispatch
- src/mdalign/utils.py  - shared constants and helpers
- src/mdalign/parser.py - code block detection shared by most modules
