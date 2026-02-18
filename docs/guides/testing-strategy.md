# Testing Strategy

## Framework

- pytest with parametrized test functions
- Each fixture is a directory containing `input.md` (broken) and `expected.md` (correct)
- Fixtures discovered automatically via `FIXTURES.rglob("input.md")`

## Test functions

Three test functions run for every fixture directory:

| Test                       | What it verifies                                            |
|----------------------------|-------------------------------------------------------------|
| test_check_detects_issues  | run_checks returns errors when input differs from expected  |
| test_fix_produces_expected | run_fixes(input) produces output matching expected.md       |
| test_fix_is_idempotent     | run_fixes(expected) returns expected unchanged              |

## Fixture categories

Fixtures are organized into two groups:

checks/ - per-module fixtures (1:1 with src/docalign/checks/):

| Category     | Count | Tests                                                              |
|--------------|-------|--------------------------------------------------------------------|
| tables       | 3     | col-mismatch, fp-aligned-table, fp-pipe-in-text                    |
| box-widths   | 6     | trailing-space, border-vs-content, fp-consistent-width, + 3 more   |
| box-padding  | 6     | inconsistent-pad, fp-consistent, nested-boxes, + 3 more            |
| box-spacing  | 2     | content-touching-wall, fp-padded                                   |
| box-walls    | 7     | short-wall, inner-displaced, nested-cascade, + 4 more              |
| horiz-arrows | 7     | right-gap, left-gap, fp-touching, both-directions, + 3 more        |
| rails        | 3     | column-drift, fp-aligned-rails, multi-box-arrows                   |
| arrows       | 7     | v-arrow-shift, fp-arrow-in-text, fp-already-aligned, + 4 more      |
| pipes        | 2     | pipe-drift, fp-aligned-pipes                                       |
| list-descs   | 5     | basic, fp-single-item, fp-hyphenated, fp-non-consec, fp-code-block |
| def-lists    | 6     | basic, fp-single-item, fp-url-in-value, + 3 more                   |
| wide-chars   | 3     | wide-chars-in-diagram, fp-no-wide-chars, fp-safe-box-chars         |

all-checks/ - single combined fixture covering all 12 checks.

general/ - integration and edge case fixtures:

| Category     | Count | Tests                                                     |
|--------------|-------|-----------------------------------------------------------|
| trees        | 2     | Schema tree, flow tree (should be skipped)                |
| mixed        | 1     | Multiple issue types in one file                          |
| nested       | 2     | Deep nested boxes, tree inside box                        |
| multi-column | 2     | Sequence diagram, branching flow                          |
| deploy       | 1     | Pipeline with merge diagram                               |
| edge-cases   | 5     | Empty file, no code blocks, unclosed, unicode, empty block|

Total: 71 fixture directories, 213 test cases (3 tests x 71 fixtures).

## Test flow

```
tests/fixtures/
  input.md + expected.md
        │
        v
┌──────────────────────────────────┐
│   test_check_detects_issues      │
│   input != expected ? errors > 0 │
│   input == expected ? errors = 0 │
├──────────────────────────────────┤
│   test_fix_produces_expected     │
│   fix(input) == expected         │
├──────────────────────────────────┤
│   test_fix_is_idempotent         │
│   fix(expected) == expected      │
└──────────────────────────────────┘
```

## CI integration

- CI runs `pytest -v` on Python 3.9 + 3.12 matrix (ubuntu-latest)
- ruff validates lint + format in a separate CI job
- Makefile targets mirror CI: `make test` and `make check`

## Adding new fixtures

1. Create a new directory under tests/fixtures/checks/{module}/{nn-name}/ or tests/fixtures/general/{category}/{nn-name}/
2. Add input.md with the broken alignment
3. Add expected.md with the correct alignment
4. For unfixable issues (check-only, no auto-fix): set input.md == expected.md and add an empty `check_only` marker file
5. Tests auto-discover the new fixture on next pytest run

---

related docs:
- docs/cicd.md - CI pipeline that runs these tests
- docs/repo.md - project tooling and Makefile targets

related sources:
- tests/test_align.py - test function definitions
- tests/fixtures/     - all fixture directories
