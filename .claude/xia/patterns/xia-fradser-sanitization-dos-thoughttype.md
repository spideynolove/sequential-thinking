---
name: xia-fradser-sanitization-dos-thoughttype
source: https://github.com/FradSer/mcp-server-mas-sequential-thinking
extracted: 2026-03-23
---

# Input Sanitization + DoS Limits + ThoughtType — Xỉa from FradSer

**Source**: https://github.com/FradSer/mcp-server-mas-sequential-thinking
**Extracted**: 2026-03-23
**Gap filled**: A had no input validation on thought content, no session growth limits, and no thought classification concept

## What this is

Three defensive additions adapted from F's production-grade MCP server:
1. `_sanitize_input` — rejects control characters, injection patterns, and over-length content
2. Session/branch/thought count limits — prevents unbounded growth
3. `ThoughtType` enum — classifies thoughts as STANDARD, REVISION, or BRANCH from existing fields

## Why it fills A's gap

A stored arbitrary user text verbatim with no validation. Sessions could grow without bound. Thoughts had no type classification in responses — callers had to infer from `is_revision`/`branch_id`.

## The pattern

```python
# models.py — ThoughtType enum + derived property
class ThoughtType(Enum):
    STANDARD = "standard"
    REVISION = "revision"
    BRANCH = "branch"

# On Thought dataclass:
@property
def thought_type(self) -> "ThoughtType":
    if self.is_revision:
        return ThoughtType.REVISION
    if self.branch_id:
        return ThoughtType.BRANCH
    return ThoughtType.STANDARD
```

```python
# session_manager.py — module-level
MAX_THOUGHTS_PER_SESSION = 500
MAX_BRANCHES_PER_SESSION = 50
MAX_THOUGHTS_PER_BRANCH = 100
MAX_THOUGHT_CONTENT_LENGTH = 10_000

_INJECTION_PATTERNS = [
    re.compile(r"(?i)\b(ignore|forget|disregard)\s+(previous|prior|above)\s+(instructions?|commands?|directives?)"),
    re.compile(r"(?i)\b(you\s+are\s+now|act\s+as|pretend\s+(you\s+are|to\s+be))\b"),
]

def _sanitize_input(text: str, max_length: int, field_name: str) -> str:
    text = text.strip()
    control_chars = sum(1 for c in text if ord(c) < 32 and c not in "\n\r\t")
    if control_chars > 0:
        raise ValidationError(f"{field_name} contains invalid control characters")
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            raise ValidationError(f"{field_name} contains disallowed content")
    if len(text) > max_length:
        raise ValidationError(f"{field_name} exceeds {max_length} character limit")
    return text
```

```python
# session_manager.py — in add_thought, before Thought construction
content = _sanitize_input(content, MAX_THOUGHT_CONTENT_LENGTH, "content")
if len(self.current_session.thoughts) >= MAX_THOUGHTS_PER_SESSION:
    raise ValidationError(f"Session thought limit ({MAX_THOUGHTS_PER_SESSION}) reached")
if branch_id:
    branch_thoughts = sum(1 for t in self.current_session.thoughts if t.branch_id == branch_id)
    if branch_thoughts >= MAX_THOUGHTS_PER_BRANCH:
        raise ValidationError(f"Branch thought limit ({MAX_THOUGHTS_PER_BRANCH}) reached")

# in create_branch, before Branch construction
if len(self.current_session.branches) >= MAX_BRANCHES_PER_SESSION:
    raise ValidationError(f"Session branch limit ({MAX_BRANCHES_PER_SESSION}) reached")
```

```python
# mcp_tools.py — in add_thought response
if is_revision:
    thought_type = ThoughtType.REVISION.value
elif branch_id:
    thought_type = ThoughtType.BRANCH.value
else:
    thought_type = ThoughtType.STANDARD.value
result["thought_type"] = thought_type
```

## How to apply here

Applied to: `models.py`, `session_manager.py`, `mcp_tools.py`
Seam: `add_thought` and `create_branch` in `UnifiedSessionManager`

## Adaptation notes

- F uses `markupsafe.escape` for HTML sanitization — dropped (A is not a web app; HTML escaping mangles code content in markdown storage)
- F uses Shannon entropy checks — dropped (too aggressive for code-containing thoughts)
- F's injection patterns are extensive (15+ patterns) — kept only the 2 most critical
- F's limits come from a deeply nested `ValidationLimits` class — flattened to module-level constants in A

## Original context

F is a MAS (Multi-Agent System) server built on Agno with LLM-powered agents. Its sanitization protects prompts sent to LLMs. A adapts it for thought content validation without the LLM-call context.
