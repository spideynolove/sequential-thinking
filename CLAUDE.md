# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python MCP (Model Context Protocol) server providing structured sequential reasoning. Sessions, thoughts, branches, memories, assumptions, and architecture decisions are persisted in SQLite. Uses stdio transport.

## Commands

```bash
source /home/hung/env/.venv/bin/activate

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_models.py -v

# Run a specific test
pytest tests/test_session_manager.py::test_add_thought -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing

# Lint
ruff check .
```

## Architecture

Flat layout — four modules at root:

- **main.py** — MCP server entry point. Registers 14 tools, wires `UnifiedSessionManager` → `MCPToolsHandler` → MCP protocol over stdio.
- **session_manager.py** — Core persistence layer. SQLite-backed CRUD for sessions, thoughts, branches, memories, decisions, assumptions, packages. Input sanitization, DoS limits (500 thoughts/session, 50 branches/session, 10k char content cap).
- **mcp_tools.py** — Thin adapter wrapping session_manager into MCP tool responses. All exceptions caught and returned as `{"error": str(e)}`.
- **models.py** — Dataclasses (`UnifiedSession`, `Thought`, `Branch`, `Memory`, `Assumption`, `ArchitectureDecision`, `PackageInfo`) and enums (`SessionType`, `ThoughtType`, `ThoughtStage`).

**Data flow:** MCP client → main.py (tool dispatch) → mcp_tools.py (validation/adaptation) → session_manager.py (business logic + SQLite) → models.py (data structures).

**SQLite schema** lives in `session_manager.py` — seven tables: sessions, thoughts, branches, memories, architecture_decisions, discovered_packages, assumptions.

## Key Patterns

- Single active session per `UnifiedSessionManager` instance
- All new fields on models are optional with defaults (backward compat)
- `_conn()` context manager handles transactional DB access
- `_sanitize_input()` rejects SQL injection and script patterns before any DB writes
- Tests use `tempfile.mkdtemp()` for isolated SQLite instances

## Known Issues

- Session reload from persisted thoughts breaks some persistence tests
- Tool schema advertises "memory" session type but `SessionType` enum only has GENERAL and CODING

## Maintenance Notes

Single-maintainer project. Keep changes small and direct. Treat the test suite as the primary source of expected behavior.
