---
name: xia-sequentialthinking-revisable-thought-chain
source: https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking
extracted: 2026-03-23
type: learned
---

# Numbered Revisable Thought Chain — Xỉa from modelcontextprotocol/servers

**Source**: https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking
**Extracted**: 2026-03-23
**Focus**: ThoughtData interface — thought numbering, revision, and completion signaling
**Gap filled**: A's thoughts were append-only and immutable with no progress awareness or termination signal

## What this is

Five optional fields added to `add_thought` that let the calling LLM declare how many thoughts it plans, mark a thought as a correction of an earlier one, and signal when the chain is complete. Borrowed from B's `ThoughtData` interface, adapted to A's UUID-based identity model (B uses integer indices; A uses UUIDs for `revises_thought_id`).

## Why it's valuable

Without these fields, thought chains in A had no declared scope (you couldn't say "step 3 of 7"), no way to correct an earlier mistake without appending contradictory content, and no explicit termination — the chain just stopped. These five fields make thought chains self-documenting and revisable.

## The pattern

```python
thought_number: Optional[int] = None      # "I am on step K"
total_thoughts: Optional[int] = None      # "I plan N steps total"
is_revision: bool = False                 # "this corrects an earlier thought"
revises_thought_id: str = ""              # which thought (UUID) is being revised
next_thought_needed: bool = True          # False = chain is complete
```

Serialized into markdown as optional metadata lines between `Confidence:` and `Created:`:
```
**Thought:** 2/5
**Revision of:** <uuid>
**Next Needed:** False
```

Only written when non-default — keeps backward compat with old sessions.

## How to apply here

Applied to `Thought` dataclass (`models.py:66`), `add_thought` in `session_manager.py:200` and `mcp_tools.py:47`, and the markdown parser at `session_manager.py:686`. All fields are optional — zero breaking changes to existing callers.

Usage example:
```python
# Step 1 of 5
h.add_thought("initial analysis", thought_number=1, total_thoughts=5)

# Realize step 1 was wrong — revise it
h.add_thought("corrected analysis", thought_number=2, total_thoughts=5,
              is_revision=True, revises_thought_id="<t1-uuid>")

# Final step — signal done
h.add_thought("conclusion", thought_number=5, total_thoughts=5,
              next_thought_needed=False)
```

## Original context

B exposes a single `sequential_thinking` MCP tool. All state is in-memory and stateless — the LLM holds state across calls. B uses `revisesThought: number` (integer index); A adapted this to `revises_thought_id: str` (UUID) to match A's existing identity model.
