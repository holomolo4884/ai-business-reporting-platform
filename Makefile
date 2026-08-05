.PHONY: help install run test lint format lint-all docker-build docker-up docker-down

help:
	@echo "install      - install backend dependencies"
	@echo "run          - run Django dev server"
	@echo "test         - run backend tests"
	@echo "lint         - run ruff and black check"
	@echo "format       - run ruff fix and black"
	@echo "lint-all     - run pre-commit hooks"
	@echo "docker-build - build docker images"
	@echo "docker-up    - start docker compose"
	@echo "docker-down  - stop docker compose"

install:
	@test -d backend/.venv || python3 -m venv backend/.venv
	backend/.venv/bin/python -m pip install --upgrade pip
	backend/.venv/bin/python -m pip install -r backend/requirements/dev.txt

run:
	backend/.venv/bin/python backend/manage.py runserver

test:
	cd backend && .venv/bin/python -m pytest

lint:
	backend/.venv/bin/ruff check --config backend/pyproject.toml .
	backend/.venv/bin/black --check --config backend/pyproject.toml .

format:
	backend/.venv/bin/ruff check --fix --config backend/pyproject.toml .
	backend/.venv/bin/black --config backend/pyproject.toml .

lint-all:
	pre-commit run --all-files

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down
