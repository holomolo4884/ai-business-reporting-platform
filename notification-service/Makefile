.PHONY: lint format check

lint:
	ruff check .
	mypy .

format:
	ruff check --fix .
	ruff format .

check: lint
