dist: LICENSE Makefile README.md pyproject.toml src tests
	poetry build

# Run the ruff linter.
lint:
	poetry run ruff check --fix

lock:
	poetry lock

# Run the ruff formatter.
format:
	poetry run ruff format

precommit-hooks:
	poetry run pre-commit install

run-precommit:
	poetry run pre-commit run --all-files --show-diff-on-failure

clean:
	git clean --dry-run -fxd

# Usage: TOKEN=... make upload
upload: build
	poetry run twine upload -r testpypi --skip-existing -u __token__ -p $(TOKEN) dist/*
