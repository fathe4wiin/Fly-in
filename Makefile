.PHONY: help install run run-visual debug clean lint lint-strict

DEFAULT_MAP := maps/easy/01_linear_path.txt
PYTHON := python3
PIP := $(PYTHON) -m pip
MAP ?= $(DEFAULT_MAP)

help:
	@echo "Available targets:"
	@echo "  make install           Install dependencies"
	@echo "  make run               Run simulation (default map)"
	@echo "  make run MAP=<path>    Run with a specific map"
	@echo "  make run-visual        Run with pygame visualization"
	@echo "  make debug             Run under pdb"
	@echo "  make lint              Run flake8 and mypy"
	@echo "  make lint-strict       Run flake8 and mypy --strict"
	@echo "  make clean             Remove Python cache files"

install:
	$(PIP) install -r requirements.txt

run: install
	$(PYTHON) main.py $(MAP)

run-visual: install
	$(PYTHON) main.py $(MAP)

debug: install
	$(PYTHON) -m pdb main.py $(MAP)

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

.DEFAULT_GOAL := help
