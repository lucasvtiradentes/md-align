# align-md-docs

Auto-fix alignment issues in markdown documentation files containing box-drawing diagrams and tables.

## What it fixes

1. Tables - pads cells so every column matches the separator row width
2. Box widths - ensures all lines in a box group have the same total length
3. Rail alignment - aligns vertically adjacent box chars to the same column
4. Arrow alignment - aligns standalone `v`/`^` arrows with the nearest box char above/below
5. Pipe continuity - traces from T-junctions to detect drifted connector pipes
6. Box walls - verifies nested box right walls match their opening/closing borders

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
# auto-fix file or all .md files in folder
align-md-docs <file_or_folder>

# detect-only mode (no writes)
align-md-docs --check <file_or_folder>
```

## Exit codes

- 0 - all docs aligned (or all issues auto-fixed)
- 1 - unfixable issues remain (fix mode) or errors found (check mode)

## Tests

```bash
pytest -v
pytest -k "tables"       # run only table fixtures
pytest -k "box-walls"    # run only box-walls fixtures
```

## Project structure

```
align_md_docs/
├── cli.py          main entrypoint, arg parsing, orchestration
├── parser.py       shared helpers: iter_code_blocks, group_box_lines
├── utils.py        constants and shared utility functions
├── tables.py       table column alignment
├── box_widths.py   box line width normalization
├── rails.py        vertical box char alignment
├── arrows.py       arrow-to-box alignment
├── pipes.py        pipe continuity from T-junctions
└── box_walls.py    nested box wall alignment
```

Each module exports `check(lines) -> list[str]` and `fix(lines) -> list[str]`.
