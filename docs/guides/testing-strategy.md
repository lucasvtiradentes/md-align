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

| Category     | Count | Tests                                         |
|--------------|-------|-----------------------------------------------|
| tables       | 1     | Column width mismatches                       |
| box-widths   | 2     | Trailing space, border vs content length      |
| box-walls    | 3     | Short wall, inner displaced, nested cascade   |
| rails        | 1     | Column drift in vertical alignment            |
| arrows       | 1     | v-arrow shift alignment                       |
| pipes        | 1     | Pipe drift from T-junction                    |
| trees        | 2     | Schema tree, flow tree (should be skipped)    |
| mixed        | 1     | Multiple issue types in one file              |
| nested       | 2     | Deep nested boxes, tree inside box            |
| multi-column | 2     | Sequence diagram, branching flow              |
| deploy       | 1     | Pipeline with merge diagram                   |

Total: 17 fixture directories, 51 test cases (3 tests x 17 fixtures).

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

- CI runs `pytest -v` on Python 3.12 (ubuntu-latest)
- ruff validates lint + format in a separate CI job
- Makefile targets mirror CI: `make test` and `make check`

## Adding new fixtures

1. Create a new directory under tests/fixtures/{category}/{nn-name}/
2. Add input.md with the broken alignment
3. Add expected.md with the correct alignment
4. Tests auto-discover the new fixture on next pytest run

---

related docs:
- docs/cicd.md - CI pipeline that runs these tests
- docs/repo.md - project tooling and Makefile targets

related sources:
- tests/test_align.py - test function definitions
- tests/fixtures/ - all fixture directories
