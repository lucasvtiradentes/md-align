# Rules

Design principles, conventions, and anti-patterns for align-md-docs.

## Design principles

- Modular check/fix: each alignment concern lives in its own module (tables, box_widths, rails, arrows, pipes, box_walls)
- Common interface: every module exports `check(lines) -> list[str]` and `fix(lines) -> list[str]`
- Iterative convergence: fixes that interact (box_walls, rails, pipes) run in a loop up to 3 times, stopping early if output stabilizes
- Idempotent output: applying fix to already-fixed content produces identical output
- Scope isolation: only content inside fenced code blocks is analyzed; outside text is never modified
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
3. Convergence loop (max 3x):
   - box_walls.fix - adjusts corner and wall positions
   - rails.fix - aligns vertical box char columns
   - pipes.fix - realigns drifted connector pipes
4. arrows.fix - runs last, depends on final box char positions

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
- Do not process content outside code fences: text, headings, and inline code are never alignment targets
- Do not treat tree blocks as box diagrams: branch characters overlap with box chars but have different semantics

---

related docs:
- docs/architecture.md - fix pipeline flow and ordering
- docs/concepts.md - domain terminology referenced here

related sources:
- align_md_docs/cli.py - pipeline orchestration, check/fix dispatch
- align_md_docs/utils.py - shared constants and helpers
- align_md_docs/parser.py - code block detection shared by all modules
