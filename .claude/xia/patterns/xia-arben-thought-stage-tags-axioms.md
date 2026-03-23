---
name: xia-arben-thought-stage-tags-axioms
source: https://github.com/arben-adm/mcp-sequential-thinking
extracted: 2026-03-23
---

# Thought Stage + Tags + Epistemic Metadata — Xỉa from arben-adm/mcp-sequential-thinking

**Source**: https://github.com/arben-adm/mcp-sequential-thinking
**Extracted**: 2026-03-23
**Gap filled**: A's thoughts were undifferentiated — no reasoning phase, no topic tags, no declaration of assumptions or axioms

## What this is

Three optional enrichments added to `add_thought`, borrowed as a single coherent unit from B's `ThoughtData` model: a `ThoughtStage` enum that forces thoughts into explicit reasoning phases, `tags` for topic labeling on thoughts (distinct from Memory tags), and `axioms_used` + `assumptions_challenged` for epistemic transparency.

## Why it fills A's gap

B's `ThoughtStage` enum (PROBLEM_DEFINITION → RESEARCH → ANALYSIS → SYNTHESIS → CONCLUSION) gives thought chains an explicit progression structure. Without stages, all of A's thoughts were a flat undifferentiated list — no way to know where in the reasoning process you were. Tags on thoughts (separate from Memory tags) enable cross-thought retrieval and grouping by topic. Axioms/assumptions surface the epistemics of each step.

## The pattern

```python
class ThoughtStage(Enum):
    PROBLEM_DEFINITION = "problem_definition"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    CONCLUSION = "conclusion"

    @classmethod
    def from_string(cls, value: str) -> Optional["ThoughtStage"]:
        if not value:
            return None
        normalized = value.lower().strip()
        for member in cls:
            if member.value == normalized or member.name.lower() == normalized:
                return member
        return None
```

On `Thought` dataclass:
```python
stage: Optional[ThoughtStage] = None
tags: List[str] = field(default_factory=list)
axioms_used: str = ""
assumptions_challenged: str = ""
```

Serialized as optional markdown lines (only written when non-empty):
```
**Stage:** analysis
**Tags:** scope, requirements
**Axioms:** user needs structured reasoning
**Assumptions:** one tool per concept is sufficient
```

## How to apply here

Applied to `Thought` (`models.py`), `add_thought` in `session_manager.py` and `mcp_tools.py`, and the markdown parser in `_parse_session_markdown`. All fields optional — zero breaking changes.

Usage:
```python
h.add_thought("define what we need to solve",
    stage="problem_definition",
    tags="scope,requirements",
    axioms_used="users want structured cognition",
    assumptions_challenged="one session per problem is enough")
```

`stage` accepts both `"problem_definition"` and `"PROBLEM_DEFINITION"` (case-insensitive via `from_string`).

## Original context

B uses these as required/optional fields on a single `process_thought` MCP tool. B's `ThoughtAnalyzer` then groups thoughts by stage and aggregates tags to generate summaries — A will borrow `ThoughtAnalyzer` in a future Xỉa session.
