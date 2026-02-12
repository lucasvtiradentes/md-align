# Overview

mdalign is a Python CLI tool that auto-fixes alignment issues in markdown documentation files containing box-drawing diagrams, tables, and list descriptions. It detects and corrects seven categories of alignment problems.

Repository: github.com/lucasvtiradentes/align-md-docs

## What it does

- Scans .md files for alignment issues in tables and box-drawing diagrams
- Operates in two modes: auto-fix (writes corrected output) and check-only (reports issues)
- Runs as a CLI tool installed via pip, usable locally or in CI pipelines
- Zero runtime dependencies - pure Python 3.9+

## Fix categories

| Category           | Description                                              |
|--------------------|----------------------------------------------------------|
| Table alignment    | Pads table cells to match separator row column widths    |
| Box widths         | Normalizes all lines in a box group to equal length      |
| Rail alignment     | Aligns vertically adjacent box chars to the same column  |
| Arrow alignment    | Aligns standalone v/^ arrows with nearest box char       |
| Pipe continuity    | Traces T-junctions to detect drifted connector pipes     |
| Box walls          | Matches nested box right walls to opening/closing borders|
| List descriptions  | Aligns separator dash in list item descriptions           |

## Doc index

| File                                    | Description                                        |
|-----------------------------------------|----------------------------------------------------|
| docs/overview.md                        | Project summary and documentation index            |
| docs/architecture.md                    | System architecture, fix pipeline, module graph    |
| docs/repo.md                            | Stack, folder structure, tooling, setup            |
| docs/concepts.md                        | Domain concepts and alignment terminology          |
| docs/cicd.md                            | CI/CD pipelines and branch strategy                |
| docs/rules.md                           | Design principles, conventions, anti-patterns      |
| docs/guides/cli-usage.md                | Installation, CLI usage, exit codes                |
| docs/guides/testing-strategy.md         | Test framework, fixtures, CI validation            |
| docs/features/table-alignment.md        | Table column alignment module                      |
| docs/features/box-width-normalization.md| Box width normalization module                     |
| docs/features/rail-alignment.md         | Vertical rail alignment module                     |
| docs/features/pipe-continuity.md        | Pipe continuity from T-junctions module            |
| docs/features/arrow-alignment.md        | Arrow-to-box alignment module                      |
| docs/features/box-wall-checking.md      | Nested box wall validation module                  |
| docs/features/list-desc-alignment.md    | List description alignment module                  |

---

related sources:
- README.md      - project description and usage instructions
- pyproject.toml - package metadata, dependencies, scripts
- src/mdalign/   - all source modules
- tests/         - test suite and fixture data
