install:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

test:
	.venv/bin/pytest -v

check:
	@find tests/fixtures -name 'expected.md' -exec .venv/bin/align-md-docs --check {} +
