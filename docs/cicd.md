# CI/CD

## Pipeline architecture

```
┌──────────────────────────────────────────────────────────┐
│                    callable-ci.yml                       │
│                 (reusable workflow)                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │  check       │  │ practical-test   │  │    test     │ │
│  │  ruff check  │  │ docalign --check │  │   pytest -v │ │
│  │  ruff format │  │ docs/            │  │ (3.9, 3.12) │ │
│  └──────────────┘  └──────────────────┘  └─────────────┘ │
└──────────────────────────────────────────────────────────┘
              ^                      ^
              │                      │
         ┌────┴─────┐         ┌──────┴─────┐
         │ prs.yml  │         │ push-to-   │
         │ (on PR)  │         │ main.yml   │
         └──────────┘         └────────────┘
```

## Workflows

### callable-ci.yml

Reusable workflow triggered via `workflow_call`. Contains three parallel jobs:

| Job            | Steps                                                                 |
|----------------|-----------------------------------------------------------------------|
| check          | checkout, setup Python 3.12, install, ruff check, ruff format --check |
| practical-test | checkout, setup Python 3.12, install, docalign --check docs/          |
| test           | checkout, setup Python 3.9 + 3.12 (matrix), install, pytest -v        |

### prs.yml

Triggers on `pull_request` events. Calls callable-ci.yml.

### push-to-main.yml

Triggers on `push` to `main` branch. Calls callable-ci.yml.

### release.yml

Manual workflow (`workflow_dispatch`) for publishing releases. Bumps version, builds changelog, commits, tags, builds, and publishes to PyPI via trusted publishing.

## Branch strategy

```
feature branch ──── PR ──── prs.yml (CI)
                     │
                     v
                   main ──── push-to-main.yml (CI + deploy)
```

- PRs trigger full CI via workflow_call
- Push to main triggers CI
- Release is manual via workflow_dispatch
- Python 3.9 + 3.12 matrix for tests, 3.12 for check/practical-test

## Environment

- Runner:  ubuntu-latest
- Python:  3.12
- Install: pip install -e ".[dev]"
- No secrets or environment variables required

---

related docs:
- docs/repo.md                    - local tooling that mirrors CI steps
- docs/guides/testing-strategy.md - test suite run by CI

related sources:
- .github/workflows/callable-ci.yml  - reusable CI workflow definition
- .github/workflows/prs.yml          - PR trigger workflow
- .github/workflows/push-to-main.yml - main branch trigger workflow
- .github/workflows/release.yml      - manual release workflow
