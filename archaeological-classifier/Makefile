.PHONY: help install dev test clean build publish run-api run-mcp format lint

help:
	@echo "Archaeological Classifier System - Make Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install     - Install package"
	@echo "  make dev         - Install with dev dependencies"
	@echo "  make test        - Run tests"
	@echo "  make format      - Format code with black"
	@echo "  make lint        - Run type checking"
	@echo ""
	@echo "Running:"
	@echo "  make run-api     - Start Flask API server"
	@echo "  make run-mcp     - Start MCP server"
	@echo ""
	@echo "Building:"
	@echo "  make build       - Build distribution packages"
	@echo "  make clean       - Clean build artifacts"
	@echo ""
	@echo "Publishing:"
	@echo "  make publish-test - Publish to Test PyPI"
	@echo "  make publish      - Publish to PyPI"
	@echo ""
	@echo "Setup:"
	@echo "  make setup-claude - Show Claude Desktop config instructions"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=acs --cov-report=html

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

format:
	black acs/ tests/ examples/

lint:
	mypy acs/

run-api:
	python -m acs.api.app

run-mcp:
	python -m acs.mcp.server

publish-test: build
	twine upload --repository testpypi dist/*

publish: build
	twine upload dist/*

setup-claude:
	@echo "Claude Desktop MCP Configuration"
	@echo "================================="
	@echo ""
	@echo "1. Find your configuration file:"
	@echo "   macOS:   ~/Library/Application Support/Claude/claude_desktop_config.json"
	@echo "   Windows: %APPDATA%\\Claude\\claude_desktop_config.json"
	@echo "   Linux:   ~/.config/Claude/claude_desktop_config.json"
	@echo ""
	@echo "2. Add this configuration:"
	@echo ""
	@cat claude_desktop_config.json
	@echo ""
	@echo "3. Restart Claude Desktop"
	@echo ""
	@echo "For detailed instructions, see INSTALL.md"
