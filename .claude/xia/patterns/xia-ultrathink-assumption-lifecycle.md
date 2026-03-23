---
name: xia-ultrathink-assumption-lifecycle
source: https://github.com/husniadil/ultrathink
extracted: 2026-03-24
---

# Assumption Lifecycle System — Xỉa from ultrathink

**Source**: [husniadil/ultrathink](https://github.com/husniadil/ultrathink)
**Extracted**: 2026-03-24
**Gap filled**: A had unstructured `assumptions_challenged` and `axioms_used` strings — no way to query which critical assumptions are unverified or track reasoning dependencies

## What this is

A full assumption lifecycle model with structured tracking:

**Assumption dataclass:**
- `id`, `session_id`, `text`, `confidence` (0-1)
- `critical`: bool — if false and assumption fails, reasoning collapses
- `verifiable`: bool — can this be checked?
- `evidence`: str — supporting/contradicting data
- `verification_status`: "verified" | "falsified" | ""
- Properties: `is_verified`, `is_falsified`, `is_risky` (critical + low confidence + unverified)

**Thought fields:**
- `assumptions: List[str]` — IDs of new assumptions created with this thought
- `depends_on_assumptions: List[str]` — IDs of assumptions this reasoning builds on
- `invalidates_assumptions: List[str]` — IDs of assumptions marked false

**Session-level operations:**
- `verify_assumption(assumption_id, is_true)` — marks as verified/falsified
- `get_session_assumptions()` — returns all assumptions + risky/falsified lists

## Why it fills A's gap

A's existing `assumptions_challenged` and `axioms_used` are unstructured narration — you can't query "which critical assumptions are unverified?" or "what thoughts depend on assumption A3?". Ultrathink's structured model enables:
- Risk detection: surface `risky_assumptions` in responses
- Dependency tracking: `depends_on_assumptions` links thoughts to assumptions
- Invalidation propagation: `invalidates_assumptions` auto-marks assumptions as falsified

## The pattern

```python
@dataclass
class Assumption:
    id: str
    session_id: str
    text: str
    confidence: float
    critical: bool = False
    verifiable: bool = False
    evidence: str = ""
    verification_status: str = ""

    @property
    def is_risky(self) -> bool:
        return self.critical and self.confidence < 0.7 and not self.is_verified
```

DB table `assumptions` stores per-session assumptions. `add_thought` accepts comma-separated `assumptions` (new assumption texts), creates Assumption objects, stores IDs in thought. `verify_assumption` updates verification_status.

## How to apply here

**models.py:**
- Added `Assumption` dataclass
- Added `assumptions`, `depends_on_assumptions`, `invalidates_assumptions` to Thought

**session_manager.py:**
- Created `assumptions` table
- Added `_insert_assumption`, `_row_to_assumption`
- Updated `add_thought` to parse `assumptions` param, create Assumption objects, handle invalidation
- Added `verify_assumption(assumption_id, is_true)` method
- Added `get_session_assumptions()` returning assumptions + risky/falsified lists
- Updated `load_session` to populate `_assumptions` dict on session

**mcp_tools.py:**
- Added `assumptions`, `depends_on_assumptions`, `invalidates_assumptions` params to `add_thought`
- Added `verify_assumption(assumption_id, is_true)` method
- Added `get_assumptions()` method

**main.py:**
- Updated `add_thought` tool schema with new fields
- Added `verify_assumption` and `get_assumptions` tools

All fields optional, fully backward compatible.

## Original context

ultrathink uses FastMCP + Pydantic. The `Assumption` model includes validation, scoping (cross-session refs like `session-id:A1`), and rich formatting. A's implementation drops cross-session refs (incompatible with single-active-session model) and uses dataclasses instead of Pydantic.
