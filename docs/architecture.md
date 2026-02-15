# Architecture

mdalign is a pure Python CLI utility with a modular fix pipeline. Each alignment concern is isolated in its own module, all sharing a common check/fix interface.

## Entry point

cli.main() handles argument parsing and orchestration:

```
cli.main()
  ├── parse args (--check, --help, --version)
  ├── _collect_files(path) → list of .md files
  └── for each file:
      ├── run_checks(lines) → error list
      └── run_fixes(lines) → fixed lines → write back
```

## Fix pipeline

Fixes run in a specific order. Tables, box widths, box padding, and horiz arrows run once. Box spacing, box widths, box walls, rails, and pipes run in a 3-iteration convergence loop. Arrows, list descriptions, and definition lists run last.

```
┌──────────────────────────────────────────────────────────────┐
│                        Fix Pipeline                          │
│                                                              │
│  lines[] ── tables ── box_widths ── box_padding ──┐          │
│                                                   │          │
│         ┌─────────────────────────────────────────┘          │
│         │                                                    │
│         └── horiz_arrows ──┐                                 │
│                          │                                   │
│         ┌──────────────────┘                                 │
│         │                                                    │
│         │   ┌──────────────────────────────────────────┐     │
│         └──>│  Convergence Loop (max 3x)               │     │
│             │                                          │     │
│             │  box_spacing ── box_widths ── box_walls  │     │
│             │       │                         │        │     │
│             │       └── rails ── pipes ───────┘        │     │
│             │                                          │     │
│             │  break if output == previous             │     │
│             └──────────────────────────────────────────┘     │
│                          │                                   │
│                          v                                   │
│                    arrows.fix                                │
│                          │                                   │
│                          v                                   │
│                   list_descs.fix                             │
│                          │                                   │
│                          v                                   │
│                   def_lists.fix                              │
│                          │                                   │
│                          v                                   │
│                    fixed lines[]                             │
└──────────────────────────────────────────────────────────────┘
```

## Module dependency graph

Most fix modules depend on parser.py and utils.py. No fix module depends on another fix module. list_descs.py and def_lists.py are standalone (no shared imports).

```
┌──────────────────┐
│     cli.py       │
│    (main)        │
└────────┬─────────┘
         │ imports all check modules
         v
┌──────────────┐  ┌────────────────┐  ┌──────────────┐
│  tables.py   │  │ box_widths.py  │  │ box_walls.py │
└──────────────┘  └──────┬─────────┘  └──────┬───────┘
                         │                   │
┌──────────────┐  ┌──────┴─────────┐  ┌──────┴───────┐
│  arrows.py   │  │  rails.py      │  │  pipes.py    │
└──────┬───────┘  └──────┬─────────┘  └─────┬────────┘
       │                 │                  │
┌──────┴────────┐  ┌─────┴──────────┐       │
│box_padding.py │  │box_spacing.py  │       │
└──────┬────────┘  └─────┬──────────┘       │
       │                 │                  │
┌──────┴───────┐         │                  │
│horiz_arrows  │         │                  │
└──────┬───────┘         │                  │
       │                 │                  │
       └────────┬────────┴────────┬─────────┘
                v                 v
         ┌────────────┐    ┌───────────┐
         │ parser.py  │    │  utils.py │
         └────────────┘    └───────────┘

┌───────────────┐  ┌───────────────┐
│ list_descs.py │  │ def_lists.py  │  (standalone, no shared deps)
└───────────────┘  └───────────────┘
```

## Code block detection flow

The parser identifies code blocks (``` fences) and groups consecutive lines containing box-drawing characters. Most fix modules operate only within these detected groups. The list_descs module operates on regular markdown lines outside code blocks.

```
┌───────────────────────────────────────┐
│          Markdown File                │
│                                       │
│  text...                              │
│  ``` ◄─── fence start                 │
│  ┌─────┐                              │
│  │ box │  ◄─── box group detected     │
│  └─────┘                              │
│  ``` ◄─── fence end                   │
│  text...                              │
└───────────────────────────────────────┘
         │
         v
┌───────────────────────────────────────┐
│    iter_code_blocks(lines)            │
│    yields (indices, code_lines)       │
│              │                        │
│              v                        │
│    group_box_lines(code_lines)        │
│    returns groups of consecutive      │
│    lines with BOX_CHARS               │
└───────────────────────────────────────┘
```

## Data flow

Each module follows the same pattern:

```
┌──────────┐    check(lines)     ┌────────────┐
│  lines[] │ ──────────────────> │  errors[]  │
│          │                     │  (strings) │
└──────────┘                     └────────────┘

┌──────────┐    fix(lines)       ┌───────────┐
│  lines[] │ ──────────────────> │  lines[]  │
│ (input)  │                     │ (fixed)   │
└──────────┘                     └───────────┘
```

Internally, fix modules:
1. Call iter_code_blocks() to find code fences
2. Call group_box_lines() to cluster box-char lines
3. Analyze group geometry (positions, widths, columns)
4. Compute corrections (target columns, target widths)
5. Apply corrections by rewriting line content in-place

## Check mode vs fix mode

```
┌──────────────────┐
│   Input .md file │
│   read lines     │
└────────┬─────────┘
         │
    ┌────┴────┐
    │ --check │
    │  flag?  │
    └────┬────┘
    yes  │  no
         │
   run_checks      run_fixes
   print errors    write file
   exit 1          recheck + report
```

## Tree block exclusion

Tree structures (containing branch chars like `├──` and `└──` without box borders) are excluded from box-related checks. This prevents false positives on directory listings and tree diagrams.

Detection logic: has_branches AND NOT has_box_borders

---

related docs:
- docs/concepts.md                         - domain terminology used in pipeline stages
- docs/features/table-alignment.md         - tables.fix stage details
- docs/features/box-width-normalization.md - box_widths.fix stage details
- docs/features/rail-alignment.md          - rails.fix stage details
- docs/features/pipe-continuity.md         - pipes.fix stage details
- docs/features/arrow-alignment.md         - arrows.fix stage details
- docs/features/box-wall-checking.md       - box_walls.fix stage details

related sources:
- src/mdalign/cli.py    - entry point, pipeline orchestration
- src/mdalign/parser.py - code block iteration, box line grouping
- src/mdalign/utils.py  - constants, shared utility functions
- src/mdalign/checks/   - all check/fix modules
