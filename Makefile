dist: LICENSE Makefile README.md pyproject.toml src
	poetry build

build:
	poetry build

env:
	poetry install

dev-env:
	poetry install --with dev

test-env:
	poetry install --with tests

doc-env:
	poetry install --with docs

# Run the ruff linter.
lint:
	poetry run ruff check --fix

lock:
	poetry lock

README.md: docs/README.ipynb
	poetry run jupyter nbconvert --to markdown docs/README.ipynb --output ../README.md

# Documentation
docs: doc-env
	poetry run mkdocs build

docs-serve: doc-env
	poetry run mkdocs serve

# Test
test: test-env
	poetry run python -m pytest tests/*.py

# Run the ruff formatter.
format: dev-env
	poetry run ruff format

precommit-hooks:
	poetry run pre-commit install

run-precommit:
	poetry run pre-commit run --all-files --show-diff-on-failure

clean:
	git clean --dry-run -fxd

# Setup with ~/.pypirc
upload: dist
	poetry run twine upload -r pypi --skip-existing -u __token__ dist/*
