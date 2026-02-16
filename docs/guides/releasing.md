# Releasing

## Adding changelog entries

Every PR that changes user-facing behavior should include a changelog fragment in `.changelog/`.

Fragment naming: `<descriptive-name>.<type>` where type is one of:

| Type    | When to use          |
|---------|----------------------|
| feature | new functionality    |
| bugfix  | bug fix              |
| misc    | docs, refactor, etc. |

Example:

```bash
echo "Added --verbose flag for detailed output" > .changelog/add-verbose-flag.feature
```

Preview the changelog without writing it:

```bash
make changelog-draft
```

## Publishing a new version

1. Go to GitHub Actions > "Release" workflow
2. Click "Run workflow"
3. Select bump type:
   - patch (0.1.0 -> 0.1.1) - bug fixes
   - minor (0.1.0 -> 0.2.0) - new features
   - major (0.1.0 -> 1.0.0) - breaking changes
4. The workflow will:
   - Bump the version in pyproject.toml
   - Compile all `.changelog/` fragments into CHANGELOG.md
   - Commit, tag, and push
   - Build and publish to PyPI

## First time only

Before the first release, configure PyPI trusted publishing:

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new pending publisher:
   - Package name:     `mdalign`
   - Owner:            `lucasvtiradentes`
   - Repository:       `md-align`
   - Workflow name:    `release.yml`
   - Environment name: `pypi`
3. On the GitHub repo, go to Settings > Environments
4. Create an environment named `pypi`
