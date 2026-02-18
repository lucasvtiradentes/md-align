# CLI Usage

## Installation

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The `docalign` command becomes available after installation via the entry point defined in pyproject.toml.

## Commands

### Check-only mode (default)

```
docalign <file_or_folder>
```

- Detects alignment issues without writing any changes
- Prints errors grouped by file with format: `L{line} {issue} (context)`
- Returns non-zero exit code if issues found
- `--check` flag also works as explicit alias

### Auto-fix mode

```
docalign --fix <file_or_folder>
```

- Reads each .md file, detects alignment issues, writes corrected output in-place
- Reports number of issues fixed per file
- Reports unfixable issues if any remain after correction

### Diff mode

```
docalign --diff <file_or_folder>
```

- Shows unified diff of what would change, without writing
- Returns exit code 1 if diff is non-empty

### Ignoring checks

```
docalign --ignore tables,pipes <file_or_folder>
```

- Skips specific checks by name (comma-separated)
- Valid names: tables, box-widths, box-padding, box-spacing, horiz-arrows, box-walls, rails, arrows, pipes, list-descs, def-lists

### Help and version

```
docalign --help
docalign --version
```

## Exit codes

| Code | Meaning                                                 |
|------|---------------------------------------------------------|
| 0    | All docs aligned (no errors found or all auto-fixed)    |
| 1    | Issues found (check mode) or unfixable issues (fix mode)|

## Execution flow

```
┌────────────────────────────────────┐
│  docalign <path>                    │
└────────────┬───────────────────────┘
             │
             v
┌────────────────────────────────────┐
│  _collect_files(path)              │
│  - glob pattern: expand matches    │
│  - single file: return [path]      │
│  - directory: os.walk for .md      │
└────────────┬───────────────────────┘
             │
             v
┌────────────────────────────────────┐
│  For each .md file:                │
│  1. Read lines                     │
│  2. run_checks(lines)              │
│  3. If errors:                     │
│     --diff: show unified diff      │
│     --fix:  fix + write + recheck  │
│     else:   print errors (default) │
└────────────────────────────────────┘
```

## Error output format

Check mode output:

```
path/to/file.md:
  L5 table col0: width=3 expected=5 (separator at L3)
  L12 box char at col 15, expected col 17

2 error(s) found
```

Fix mode output:

```
path/to/file.md: fixed 3 issue(s)

path/to/other.md: 1 unfixable issue(s):
  L8 box char at col 20, expected col 22

3 issue(s) auto-fixed
1 issue(s) could not be auto-fixed
```

## Recursive scanning

When given a directory, docalign walks all subdirectories and collects every `.md` file. Files are processed in sorted order. The path passed to _collect_files is converted to absolute via os.path.abspath.

---

related docs:
- docs/architecture.md - fix pipeline details
- docs/rules.md        - module interface conventions

related sources:
- src/docalign/cli.py - CLI implementation, argument parsing, file collection
