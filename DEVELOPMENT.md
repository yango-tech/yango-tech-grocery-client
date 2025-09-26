# Development Guide

This document contains instructions for developers who want to contribute to or build the Yango Tech Grocery API Client package.

## Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)

## Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yango-tech/yango-tech-grocery-client.git
   cd yango-tech-grocery-client
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

## Building the Package

### Using Poetry (Recommended)

1. **Build the package:**
   ```bash
   poetry build
   ```

   This will create both wheel (`.whl`) and source distribution (`.tar.gz`) files in the `dist/` directory.

2. **Install the built package locally:**
   ```bash
   pip install dist/yango_tech_grocery_client-*.whl
   ```

## Development Workflow

2. **Run type checking:**
   ```bash
   poetry run mypy yango_tech_grocery_client/
   ```

3. **Lint and Format code:**
   ```bash
   poetry run black .
   poetry run isort .
   poetry run flake8
   ```

## Version Management

The package version is managed in `pyproject.toml`. To update the version:

1. **Update version in pyproject.toml:**
   ```toml
   version = "0.1.3"  # or your new version
   ```

2. **Build and publish:**
   Package build and uploading to PyPi is performed in github actions by package maintainer

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Project Structure

```
yango-tech-grocery-client/
├── yango_tech_grocery_client/     # Main package directory
│   ├── __init__.py               # Package initialization
│   ├── base_client.py            # Base client functionality
│   ├── client.py                 # Main client implementation
│   ├── constants.py              # Constants and enums
│   ├── endpoints.py              # API endpoint definitions
│   ├── exceptions.py             # Custom exceptions
│   ├── prices.py                 # Price-related functionality
│   ├── schema.py                 # Data models and schemas
│   ├── utils.py                  # Utility functions
│   └── py.typed                  # Type checking support
├── tests/                        # Test files
├── pyproject.toml                # Project configuration
├── poetry.lock                   # Dependency lock file
├── README.md                     # User documentation
├── EXAMPLES.md                   # Usage examples
├── DEVELOPMENT.md                # This file
└── LICENSE                       # License file
```
