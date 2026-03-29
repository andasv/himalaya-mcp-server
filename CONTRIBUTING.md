# Contributing to himalaya-mcp-server

Thank you for your interest in contributing! This document covers everything you need to get started.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- [himalaya](https://github.com/pimalaya/himalaya) CLI (for integration testing)

## Development Setup

```bash
git clone https://github.com/andasv/himalaya-mcp-server.git
cd himalaya-mcp-server
uv sync
```

This installs all dependencies including dev tools (pytest, ruff, mypy).

## Running Checks

All three checks must pass before submitting a PR:

```bash
# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format --check src/ tests/

# Type check
uv run mypy src/

# Tests
uv run pytest tests/ -v
```

## Auto-formatting

```bash
uv run ruff format src/ tests/
```

## Code Style

- **Formatting:** enforced by ruff (line length 100)
- **Linting:** ruff with pycodestyle, pyflakes, isort, bugbear, bandit, and more
- **Types:** strict mypy — all public functions must have type annotations
- **Security:** no `shell=True` in subprocess calls; all user inputs validated before passing to CLI

## Project Structure

```
src/himalaya_mcp/
  server.py       # MCP server entry point, mode logic, tool registration
  cli.py          # Safe subprocess wrapper for himalaya CLI
  validation.py   # Input validation for all tool parameters
  types.py        # Shared types and constants (Mode enum, danger prefixes)
  tools/          # One module per himalaya command group
    account.py
    folder.py
    envelope.py
    message.py
    flag.py
    attachment.py
    template.py
tests/
  test_cli.py         # CLI wrapper unit tests
  test_validation.py   # Input validation tests
  test_tools.py        # Tool function tests (mocked subprocess)
  test_server.py       # Server mode/registration tests
  test_error_handling.py  # Error scenario tests
```

## Adding a New Tool

1. Add the tool function in the appropriate `tools/*.py` module
2. Add input validation in `validation.py` if needed
3. Register the tool in `server.py` — under read-only or write section
4. If it's a write tool, add a `[DANGER: WRITE]` or `[DANGER: DESTRUCTIVE]` description prefix
5. Add tests in `test_tools.py` and validation tests in `test_validation.py`
6. Update README.md tool table

## Pull Requests

- Keep PRs focused — one feature or fix per PR
- All checks must pass (lint, format, types, tests)
- Include tests for new functionality
- Update documentation if adding/changing tools

## Reporting Issues

Please open an issue on GitHub with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your himalaya version (`himalaya --version`)
