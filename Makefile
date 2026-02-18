install:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

check:
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

test:
	.venv/bin/pytest -v

test-all-checks:
	.venv/bin/pytest -v -k "all-checks"

practical-test:
	.venv/bin/docalign docs/ --fix

changelog:
	.venv/bin/towncrier build --yes --version $(shell python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")

changelog-draft:
	.venv/bin/towncrier build --draft --version $(shell python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
