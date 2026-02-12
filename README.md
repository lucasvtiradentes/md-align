# mdalign

Auto-fix alignment issues in markdown documentation files containing box-drawing diagrams, tables, and list descriptions.

## What it fixes

1. Tables          - pads cells so every column matches the separator row width
2. Box widths      - ensures all lines in a box group have the same total length
3. Rail alignment  - aligns vertically adjacent box chars to the same column
4. Arrow alignment - aligns standalone `v`/`^` arrows with the nearest box char above/below
5. Pipe continuity - traces from T-junctions to detect drifted connector pipes
6. Box walls       - verifies nested box right walls match their opening/closing borders
7. List descs      - aligns the separator dash in list item descriptions

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
# check-only (default) - detect issues, no writes
mdalign <path>

# auto-fix files in place
mdalign --fix <path>

# show unified diff of what would change
mdalign --diff <path>
```

Paths can be files, directories, or glob patterns (e.g. `"docs/**/*.md"`).

## Exit codes

- 0 - all docs aligned (or all issues auto-fixed)
- 1 - errors found (check mode), unfixable issues remain (fix mode), or diff non-empty (diff mode)

## Tests

```bash
pytest -v
pytest -k "tables"       # run only table fixtures
pytest -k "box-walls"    # run only box-walls fixtures
```

## Project structure

```
src/
├── cli.py          main entrypoint, arg parsing, orchestration
├── parser.py       shared helpers: iter_code_blocks, group_box_lines
├── utils.py        constants and shared utility functions
└── checks/
    ├── tables.py       table column alignment
    ├── box_widths.py   box line width normalization
    ├── rails.py        vertical box char alignment
    ├── arrows.py       arrow-to-box alignment
    ├── pipes.py        pipe continuity from T-junctions
    ├── box_walls.py    nested box wall alignment
    └── list_descs.py   list description separator alignment
```

Each module exports `check(lines) -> list[str]` and `fix(lines) -> list[str]`.
