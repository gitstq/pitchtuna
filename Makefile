# PitchTuna Makefile — convenience targets (Linux / macOS).
PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip

.PHONY: help install install-all run test smoke tones clean dial

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install core package + runtime dependency
	$(PIP) install -e .

install-all: ## Install with mic + graphical dial extras
	$(PIP) install -e ".[all]"

run: ## Launch the interactive tuner
	$(PYTHON) -m pitchtuna

dial: ## Launch the optional graphical dial
	$(PYTHON) -m pitchtuna --dial

test: ## Run the full unit-test suite
	$(PYTHON) -m unittest discover -s tests -v

smoke: ## Headless smoke test (renders frames, drives engine, exits 0)
	$(PYTHON) -m pitchtuna --smoke-test

tones: ## Generate example reference tones into examples/
	$(PYTHON) -m pitchtuna --make-tones examples

clean: ## Remove build artifacts and caches
	rm -rf build dist *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
