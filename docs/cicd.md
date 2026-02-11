# CI/CD

## Pipeline architecture

```
┌──────────────────────────────────────────────┐
│              callable-ci.yml                 │
│          (reusable workflow)                 │
│                                              │
│  ┌─────────────┐    ┌─────────────────┐      │
│  │    check    │    │       test      │      │
│  │  ruff check │    │    pytest -v    │      │
│  │  ruff format│    │                 │      │
│  └─────────────┘    └─────────────────┘      │
└──────────────────────────────────────────────┘
         ^                     ^
         │                     │
    ┌────┴─────┐         ┌─────┴─────┐
    │ prs.yml  │         │push-to-   │
    │ (on PR)  │         │main.yml   │
    └──────────┘         └─────┬─────┘
                               │
                               v
                        ┌────────────┐
                        │   deploy   │
                        │  (stub)    │
                        └────────────┘
```

## Workflows

### callable-ci.yml

Reusable workflow triggered via `workflow_call`. Contains two parallel jobs:

| Job   | Steps                                                                |
|-------|----------------------------------------------------------------------|
| check | checkout, setup Python 3.12, install, ruff check, ruff format --check|
| test  | checkout, setup Python 3.12, install, pytest -v                      |

### prs.yml

Triggers on `pull_request` events. Calls callable-ci.yml.

### push-to-main.yml

Triggers on `push` to `main` branch. Two jobs:
- ci: calls callable-ci.yml
- deploy: runs after ci passes (currently a stub that echoes "deploy")

## Branch strategy

```
feature branch ──── PR ──── prs.yml (CI)
                     │
                     v
                   main ──── push-to-main.yml (CI + deploy)
```

- PRs trigger full CI via workflow_call
- Push to main triggers CI + deploy stub
- No secrets configured
- Python 3.12 used in all CI jobs

## Environment

- Runner: ubuntu-latest
- Python: 3.12
- Install: pip install -e ".[dev]"
- No secrets or environment variables required

---

related docs:
- docs/repo.md - local tooling that mirrors CI steps
- docs/guides/testing-strategy.md - test suite run by CI

related sources:
- .github/workflows/callable-ci.yml - reusable CI workflow definition
- .github/workflows/prs.yml - PR trigger workflow
- .github/workflows/push-to-main.yml - main branch trigger workflow
