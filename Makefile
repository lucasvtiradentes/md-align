install:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

check:
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

test:
	.venv/bin/pytest -v

practical-test:
	.venv/bin/mdalign $(ARGS) docs/
