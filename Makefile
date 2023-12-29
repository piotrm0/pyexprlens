dist: LICENSE Makefile README.md pyproject.toml src tests
	python3 -m build

upload: dist
	python3 -m twine upload --repository testpypi dist/* --config-file=~/.pypirc
