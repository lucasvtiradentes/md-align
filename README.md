# mdalign

CLI utility that auto-fixes alignment issues in markdown documentation files - tables, box-drawing diagrams, list descriptions, and more.

## Motivation

In the era of agentic engineering, documentation is the most critical artifact in any codebase. It guides both humans and AI agents. 
When docs are visually harmonious - with aligned columns, consistent box widths, and straight connector lines - they become easier to read, parse, and maintain by everyone.

## Features

- 3 modes        - check (default), auto-fix in place, or unified diff
- flexible paths - files, directories, or glob patterns (e.g. `"docs/**/*.md"`)
- CI-friendly    - exit code 0 when aligned, 1 when issues found
- 11 alignment checks:
  - [Table columns](tests/fixtures/checks/tables)          - pads cells so every column matches the separator row width
  - [Box widths](tests/fixtures/checks/box-widths)          - ensures all lines in a box group have the same total length
  - [Box padding](tests/fixtures/checks/box-padding)        - normalizes left-padding of content lines inside boxes
  - [Horizontal arrows](tests/fixtures/checks/horiz-arrows) - closes gaps between `─>` / `<─` arrow tips and box walls
  - [Rail alignment](tests/fixtures/checks/rails)           - aligns vertically adjacent box chars to the same column
  - [Arrow alignment](tests/fixtures/checks/arrows)         - aligns standalone `v`/`^` arrows with the nearest box char above/below
  - [Pipe continuity](tests/fixtures/checks/pipes)          - traces from T-junctions to detect drifted connector pipes
  - [Box spacing](tests/fixtures/checks/box-spacing)         - ensures minimum right-side spacing between content and box wall
  - [Box walls](tests/fixtures/checks/box-walls)             - verifies nested box right walls match their opening/closing borders
  - [List descriptions](tests/fixtures/checks/list-descs)    - aligns the separator dash in list item descriptions
  - [Definition lists](tests/fixtures/checks/def-lists)     - aligns the `:` separator in `key: value` list items

## Example

```
┌────────────────────────┐       ┌────────────────────────┐
│  ┌────┐   ┌────┐      │        │  ┌────┐   ┌────┐       │
│  │ A  │   │ B  │      │        │  │ A  │   │ B  │       │
│  └──┬─┘   └──┬─┘      │        │  └──┬─┘   └──┬─┘       │
│     │         │        │       │     │        │         │
│     └────┬───┘         │  -->  │     └────┬───┘         │
│           v            │       │          v             │
│     ┌──────┐           │       │     ┌──────┐           │
│     │  C   │           │       │     │  C   │           │
│     └──────┘           │       │     └──────┘           │
└────────────────────────┘       └────────────────────────┘
```

<details>
<summary>More examples</summary>

### [Tables](tests/fixtures/checks/tables)

```
| Service        | Usage                         |             | Service        | Usage                         |
|----------------|-------------------------------|             |----------------|-------------------------------|
| Linear API     | Status transitions, comments|        -->    | Linear API     | Status transitions, comments  |
| GitHub API| Repo clone, PR creation       |                  | GitHub API     | Repo clone, PR creation       |
```

### [List descriptions](tests/fixtures/checks/list-descs)

```
- docs/repo.md - mirrors CI steps                       - docs/repo.md                    - mirrors CI steps
- docs/guides/testing-strategy.md - test suite  -->     - docs/guides/testing-strategy.md - test suite
```

### [Box widths](tests/fixtures/checks/box-widths)

```
┌──────────────┐       ┌──────────────┐
│  Linear UI  │   -->  │  Linear UI   │
│  (userscript)│       │  (userscript)│
└──────────────┘       └──────────────┘
```

### [Rail alignment](tests/fixtures/checks/rails)

```
┌──────┬──────┐       ┌──────┬──────┐
│      │      │       │      │      │
│       │     │  -->  │      │      │
│      │      │       │      │      │
└──────┴──────┘       └──────┴──────┘
```

### [Arrow alignment](tests/fixtures/checks/arrows)

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

```
┌──────┬──────┐              ┌──────┬──────┐
│ src  │ dest │              │ src  │ dest │
└──────┴──┬───┘              └──────┴──┬───┘
          │        -->                 │
            │                          │
          │                            │
┌─────────┴───┐              ┌─────────┴───┐
│   output    │              │   output    │
└─────────────┘              └─────────────┘
```

### [Box spacing](tests/fixtures/checks/box-spacing)

```
┌───────────┐       ┌────────────┐
│  errors[] │       │  errors[]  │
│  (strings)│  -->  │  (strings) │
└───────────┘       └────────────┘
```

### [Box walls](tests/fixtures/checks/box-walls)

```
┌──────────────────┐       ┌──────────────────┐
│  content here    │       │  content here    │
│  more text       │  -->  │  more text       │
└────────────────┘         └──────────────────┘
```

</details>

## Usage

```bash
mdalign <path>         # check-only (default) - detect issues, no writes
mdalign --fix <path>   # auto-fix files in place
mdalign --diff <path>  # show unified diff of what would change
```

### Install

```bash
pipx install mdalign
```

or inside a virtual environment:

```bash
pip install mdalign
```

### Update

```bash
pipx upgrade mdalign
```

or:

```bash
pip install --upgrade mdalign
```

### Uninstall

```bash
pipx uninstall mdalign
```

or:

```bash
pip uninstall mdalign
```

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```
