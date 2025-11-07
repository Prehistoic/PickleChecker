.PHONY: install test lint format clean run

install:
    poetry install

test:
    poetry run pytest

lint:
    poetry run ruff check picklechecker tests
    poetry run mypy picklechecker

format:
    poetry run black picklechecker tests
    poetry run ruff check --fix picklechecker tests

clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    rm -rf .pytest_cache .coverage htmlcov dist build

run:
    poetry run picklechecker