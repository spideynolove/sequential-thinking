---
name: xia-ultrathink-uncertainty-outcome
source: https://github.com/husniadil/ultrathink
extracted: 2026-03-24
---

# uncertainty_notes + outcome — Xỉa from ultrathink

**Source**: [husniadil/ultrathink](https://github.com/husniadil/ultrathink)
**Extracted**: 2026-03-24
**Gap filled**: Thoughts had confidence scoring but no narrative explaining uncertainty or capturing conclusions

## What this is

Two optional `str` fields on the `Thought` dataclass:
- `uncertainty_notes`: explains *why* confidence is what it is (e.g., "I haven't seen the actual API schema")
- `outcome`: captures what this step *concluded* (distinct from `left_to_be_done` which captures what remains)

## Why it fills A's gap

A already had `confidence: float` but no way to narrate the reasoning behind that score. Clients had to infer *why* a thought was only 60% confident. Similarly, A had `left_to_be_done` for remaining work but nothing for completed conclusions. These two fields complete the per-thought narrative: uncertainty explains the past/present confidence, outcome explains the conclusion reached.

## The pattern

```python
@dataclass
class Thought:
    # ... existing fields ...
    uncertainty_notes: str = ""
    outcome: str = ""
```

Stored in DB as `TEXT NOT NULL DEFAULT ''`, round-trips through `_insert_thought` and `_row_to_thought`.

## How to apply here

- `models.py`: Added `uncertainty_notes` and `outcome` to Thought dataclass
- `session_manager.py`: Added columns to thoughts table, updated `_insert_thought` and `_row_to_thought`
- `mcp_tools.py`: Added to `add_thought` signature, passes to session_manager, surfaces in response
- `main.py`: Added to add_thought tool schema

Both fields are optional, empty string by default — fully backward compatible.

## Original context

ultrathink uses these fields in its `Thought` model (Pydantic-based) to surface uncertainty rationale and step conclusions in formatted console output. The fields are optional and default to empty strings.
