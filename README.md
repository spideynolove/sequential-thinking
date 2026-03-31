# sequential-thinking

## Summary

Sequential Thinking is a Python MCP server for structured problem solving. It manages sessions, thoughts, branches, memories, assumptions, architecture decisions, and lightweight package discovery through a single SQLite-backed workflow.

The server entrypoint is `main.py`. Core behavior lives in `session_manager.py` and `mcp_tools.py`. Data models are defined in `models.py`, and tests live under `tests/`.

## Project Layout

This repository uses a flat structure.

- `main.py` exposes the MCP server and tool registry
- `session_manager.py` handles persistence, session lifecycle, and analysis
- `mcp_tools.py` adapts internal behavior to MCP tool responses
- `models.py` defines the main domain objects
- `errors.py` defines custom exceptions
- `tests/` covers unit and integration behavior

## Current Status

The codebase is small, readable, and mostly covered by tests. The main known issue is session reload from persisted thoughts, which currently breaks several persistence-related tests. The public tool schema also advertises a `memory` session type, while the internal enum currently supports only `general` and `coding`.

## Maintenance Notes

This is a single-maintainer project. Keep changes small, direct, and easy to validate. Treat the test suite as the primary source of expected behavior until the higher-level documentation is expanded.
