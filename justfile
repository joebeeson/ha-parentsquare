set shell := ["pwsh", "-NoLogo", "-NoProfile", "-Command"]

default: check

install:
    uv sync --extra dev

test:
    uv run python -c "from pathlib import Path; Path('artifacts').mkdir(exist_ok=True)"
    uv run pytest --junitxml=artifacts/junit.xml --cov=custom_components.parentsquare --cov-report=term-missing --cov-report=xml:artifacts/coverage.xml

lint:
    uv run ruff check custom_components tests

format:
    uv run ruff format --check custom_components tests

typecheck:
    uv run pyrefly check

prek:
    uvx prek run --all-files

check: lint format typecheck test
