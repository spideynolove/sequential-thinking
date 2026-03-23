---
name: xia-philogicae-left-to-be-done
source: https://github.com/philogicae/sequential-thinking-mcp
extracted: 2026-03-23
---

# left_to_be_done — Xỉa from philogicae/sequential-thinking-mcp

**Source**: https://github.com/philogicae/sequential-thinking-mcp
**Extracted**: 2026-03-23
**Gap filled**: A had total_thoughts (count) and next_thought_needed (done/not done) but no narrative of what work remains at each step

## What this is

A free-text string field on each thought that declares what still needs to happen after this step. More expressive than a count (`total_thoughts`) and more flexible than a rigid list (`remaining_steps`) — it captures the *narrative* of remaining work in natural language.

## Why it fills A's gap

A's progress-signaling (from Xia #1) tells you how many steps are planned and when the chain ends. It doesn't say *what* those steps will address. `left_to_be_done` makes the remaining work visible at every thought, enabling the caller to course-correct mid-chain without waiting for the end.

## The pattern

```python
left_to_be_done: str = ""
```

Serialized only when non-empty:
```
**Left to do:** check parser edge cases, write tests, update XIALOGUE
```

## How to apply here

Applied as optional field on `Thought` (`models.py`), passed through `add_thought` in `session_manager.py` and `mcp_tools.py`, parsed in `_parse_session_markdown` via `r"\*\*Left to do:\*\* ([^\n]+)"`.

Usage:
```python
h.add_thought("analyzed the storage layer",
    stage="analysis",
    thought_number=2, total_thoughts=4,
    left_to_be_done="check parser edge cases, write tests, update XIALOGUE")
```

## Original context

D (`philogicae/sequential-thinking-mcp`) uses `left_to_be_done` as a required param on its single `think` tool, alongside `tool_recommendation`. The agent updates it at each step to track remaining work. A uses it as optional — no breaking changes.
