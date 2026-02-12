# Repository

## Stack

- Python 3.9+ (no runtime dependencies)
- Dev dependencies: pytest >= 7, ruff >= 0.9
- Build system: hatchling
- Package version: 0.1.0

## Folder structure

```
align-md-docs/
├── src/mdalign/
│   ├── __init__.py        re-exports run_checks, run_fixes
│   ├── cli.py             main entrypoint, arg parsing, orchestration
│   ├── parser.py          iter_code_blocks, group_box_lines
│   ├── utils.py           constants (BOX_CHARS, thresholds), shared helpers
│   └── checks/
│       ├── tables.py      table column alignment check/fix
│       ├── box_widths.py  box line width normalization check/fix
│       ├── box_walls.py   nested box wall alignment check/fix
│       ├── rails.py       vertical rail alignment check/fix
│       ├── arrows.py      arrow-to-box alignment check/fix
│       ├── pipes.py       pipe continuity check/fix
│       └── list_descs.py  list description separator alignment check/fix
├── tests/
│   ├── test_align.py      parametrized test suite
│   └── fixtures/
│       ├── checks/        per-module fixtures (arrows, box-walls, etc.)
│       └── general/       integration fixtures (deploy, mixed, nested, etc.)
├── .github/workflows/
│   ├── callable-ci.yml    reusable CI workflow (check + test)
│   ├── prs.yml            PR trigger → callable-ci
│   └── push-to-main.yml   push trigger → callable-ci + deploy stub
├── pyproject.toml          package config, scripts, tool settings
├── Makefile                install, test, check targets
└── README.md               project docs
```

## Tooling

| Tool     | Purpose               | Config location     |
|----------|-----------------------|---------------------|
| pytest   | Test runner           | pyproject.toml      |
| ruff     | Linting + formatting  | pyproject.toml      |
| hatchling| Build backend         | pyproject.toml      |
| make     | Task runner           | Makefile            |

## Scripts

| Command      | What it does                          |
|--------------|---------------------------------------|
| make install | Creates venv, installs package in dev |
| make test    | Runs pytest -v                        |
| make check   | Runs ruff check + ruff format --check |

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make test
```

## Configuration

- ruff line-length: 120
- ruff lint rules: E, F, I (errors, pyflakes, isort)
- pytest testpaths: tests/
- No environment variables required

---

related docs:
- docs/cicd.md                    - CI pipeline that runs these tools
- docs/guides/testing-strategy.md - how fixtures and tests work

related sources:
- pyproject.toml - package metadata, tool configs
- Makefile       - task runner targets
- src/mdalign/   - source modules
- tests/         - test suite and fixtures
