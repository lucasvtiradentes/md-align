# Overview

CLI utility that auto-fixes alignment issues in markdown documentation files - tables, box-drawing diagrams, list descriptions, and more.

```
┌───────────────────┐       ┌───────────────────┐
│  ┌────┐   ┌────┐ │        │  ┌────┐   ┌────┐  │
│  │ A  │   │ B  │ │        │  │ A  │   │ B  │  │
│  └──┬─┘   └──┬─┘ │        │  └──┬─┘   └──┬─┘  │
│     │         │   │       │     │        │    │
│     └────┬───┘    │  -->  │     └────┬───┘    │
│           v       │       │          v        │
│     ┌──────┐      │       │     ┌──────┐      │
 │     │  C   │      │      │     │  C   │      │
│     └──────┘      │       │     └──────┘      │
└───────────────────┘       └───────────────────┘
```

<div align="center">

<details>
<summary>See all 12 checks</summary>

<div align="left">

### [Tables](tests/fixtures/checks/tables)
Aligns columns and ensures `| content |` spacing in cells.

```
| Service        | Usage                         |             | Service    | Usage                        |
|----------------|-------------------------------|             |------------|------------------------------|
| Linear API     | Status transitions, comments|        -->    | Linear API | Status transitions, comments |
| GitHub API| Repo clone, PR creation       |                  | GitHub API | Repo clone, PR creation      |
```

### [List descriptions](tests/fixtures/checks/list-descs)
Aligns the separator dash in list item descriptions.

```
- docs/repo.md - mirrors CI steps                       - docs/repo.md                    - mirrors CI steps
- docs/guides/testing-strategy.md - test suite  -->     - docs/guides/testing-strategy.md - test suite
```

### [Definition lists](tests/fixtures/checks/def-lists)
Aligns the `:` separator in key-value list items.

```
- timeout: 30s                    - timeout:         30s
- retries: 3               -->    - retries:         3
- max-connections: 100            - max-connections: 100
```

### [Box widths](tests/fixtures/checks/box-widths)
Ensures all lines in a box group have the same total length.

```
┌──────────────┐       ┌───────────────┐
│  Linear UI  │   -->  │  Linear UI    │
│  (userscript)│       │  (userscript) │
└──────────────┘       └───────────────┘
```

### [Rail alignment](tests/fixtures/checks/rails)
Aligns vertically adjacent box chars to the same column.

```
┌──────┬──────┐       ┌──────┬──────┐
│      │      │       │      │      │
│       │     │  -->  │      │      │
│      │      │       │      │      │
└──────┴──────┘       └──────┴──────┘
```

### [Arrow alignment](tests/fixtures/checks/arrows)
Aligns standalone `v`/`^` arrows with their source pipes.

```
┌──────┐                     ┌──────┐
│ step │                     │ step │
└──┬───┘                     └──┬───┘
   │           -->              │
     v                          v
┌──────┐                     ┌──────┐
│ next │                     │ next │
└──────┘                     └──────┘
```

### [Pipe continuity](tests/fixtures/checks/pipes)
Traces from T-junctions to detect drifted connector pipes.

```
┌──────┬──────┐              ┌──────┬──────┐
│ src  │ dest │              │ src  │ dest │
└──────┴──┬───┘              └──────┬──────┘
       │           -->              │
       │                            │
          │                         │
┌──────┴──────┐              ┌──────┴──────┐
│   output    │              │   output    │
└─────────────┘              └─────────────┘
```

### [Box spacing](tests/fixtures/checks/box-spacing)
Ensures minimum right-side spacing between content and box wall.

```
┌───────────┐       ┌────────────┐
│  errors[] │       │  errors[]  │
│  (strings)│  -->  │  (strings) │
└───────────┘       └────────────┘
```

### [Box walls](tests/fixtures/checks/box-walls)
Verifies nested box right walls match their opening/closing borders.

```
┌──────────────────┐       ┌──────────────────┐
│  content here    │       │  content here    │
│  more text       │  -->  │  more text       │
└────────────────┘         └──────────────────┘
```

### [Box padding](tests/fixtures/checks/box-padding)
Normalizes left-padding of content lines inside boxes.

```
┌──────────────┐       ┌──────────────┐
│ validateAuth │       │ validateAuth │
│ compare with │  -->  │ compare with │
└──────────────┘       └──────────────┘
```

### [Horizontal arrows](tests/fixtures/checks/horiz-arrows)
Closes gaps between arrow tips and box walls.

```
┌──────┐          ┌──────┐       ┌──────┐          ┌──────┐
│ Src  │─────────>│ Dest │  -->  │ Src  │─────────>│ Dest │
└──────┘          └──────┘       └──────┘          └──────┘
```

### [Wide chars](tests/fixtures/checks/wide-chars)
Detects ambiguous/double-width Unicode chars in code blocks.

```
┌──────────┐
│ ▶ start  │  -->  warning: wide char '▶' (U+25B6) at col 2
│ ● status │
└──────────┘
```

</div>

</details>

</div>

## Motivation

In the era of agentic engineering, documentation is the most critical artifact in any codebase. It guides both humans and AI agents. When docs are visually harmonious - with aligned columns, consistent box widths, and straight connector lines - they become easier to read, parse, and maintain by everyone.

## Features

- 3 modes        - check (default), auto-fix in place, or unified diff
- flexible paths - files, directories, or glob patterns (e.g. `"docs/**/*.md"`)
- CI-friendly    - exit code 0 when aligned, 1 when issues found
- 12 checks      - tables, boxes, arrows, pipes, lists (see examples above)

## Commands

```bash
docalign <path>                        # check-only (default) - detect issues, no writes
docalign --check <path>                # explicit check-only (same as default)
docalign --fix <path>                  # auto-fix files in place
docalign --diff <path>                 # show unified diff of what would change
docalign --verbose <path>              # show actionable hints with each error
docalign --ignore tables,pipes <path>  # skip specific checks
docalign --help                        # show help
docalign --version                     # show version
```

Paths can be files, directories, or glob patterns (e.g. `"docs/**/*.md"`).

Check names for `--ignore`: tables, box-widths, box-padding, box-spacing, horiz-arrows, box-walls, rails, arrows, pipes, list-descs, def-lists, wide-chars.

Exit codes: 0 = all aligned, 1 = issues found.

### Install

```bash
pipx install docalign
# pip install docalign
```

### Update

```bash
pipx upgrade docalign
# pip install --upgrade docalign
```

### Uninstall

```bash
pipx uninstall docalign
# pip uninstall docalign
```

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

```bash
# dev alias (mdalign)
ln -s $(pwd)/.venv/bin/docalign ~/.local/bin/docalignd   # install
rm ~/.local/bin/docalignd                                # remove
```
