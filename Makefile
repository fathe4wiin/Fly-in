.PHONY: help run install clean

DEFAULT_MAP := maps/easy/01_linear_path.txt
PYTHON := ./venv/bin/python
PIP := ./venv/bin/pip
MAP ?= $(DEFAULT_MAP)

help:
	@echo "Available targets:"
	@echo "  make run               Run the simulation with the default map"
	@echo "  make run MAP=<path>    Run the simulation with a specific map file"
	@echo "  make install           Install dependencies"
	@echo "  make clean             Remove Python cache files"

venv:
	python -m venv venv

install: venv
	$(PIP) install -r requirements.txt

run: install
	$(PYTHON) main.py $(MAP)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

.DEFAULT_GOAL := help
