# Contributing to SDTS

Thank you for your interest in contributing to SDTS! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/sdts.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Install development dependencies: `pip install -e ".[dev]"`

## Development Workflow

1. Make your changes
2. Run tests: `pytest`
3. Format code: `black . && isort .`
4. Run linter: `flake8`
5. Run type checker: `mypy .`
6. Commit your changes with a descriptive message
7. Push to your fork
8. Create a pull request

## Code Style

We use the following tools to maintain code quality:

- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Please ensure your code passes all these checks before submitting a pull request.

## Testing

- Write tests for new features
- Ensure all tests pass before submitting
- Follow the existing test patterns
- Use pytest fixtures where appropriate

## Documentation

- Update documentation for new features
- Add docstrings to new functions and classes
- Keep the README.md up to date
- Document any breaking changes

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the CHANGELOG.md with a summary of changes
3. The PR must pass all CI checks
4. At least one maintainer must review and approve the PR
5. Once approved, a maintainer will merge the PR

## Questions?

Feel free to open an issue if you have any questions about contributing to SDTS. 