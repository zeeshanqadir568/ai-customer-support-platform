# Convenience targets for Linux / macOS. Windows users: run .\start.ps1 instead.
.PHONY: help setup env run dev test clean

PY ?= python3
VENV := .venv
BIN := $(VENV)/bin

help:
	@echo "make setup   - create .venv and install the project + dev tools"
	@echo "make run     - start the server at http://localhost:8000"
	@echo "make dev     - start the server with auto-reload"
	@echo "make test    - run the test suite"
	@echo "make clean   - remove .venv, caches and the local SQLite file"

$(BIN)/python:
	$(PY) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip

setup: $(BIN)/python
	$(BIN)/python -m pip install -e ".[dev]"

env:
	@test -f .env || (cp .env.example .env && echo "Created .env - add ANTHROPIC_API_KEY to enable /chat")

run: setup env
	$(BIN)/python -m app

dev: setup env
	RELOAD=1 $(BIN)/python -m app

test: setup
	$(BIN)/python -m pytest -q

clean:
	rm -rf $(VENV) .pytest_cache **/__pycache__ support.db
