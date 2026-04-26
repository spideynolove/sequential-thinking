# IDEAs

## Review Verdict

This project is already good enough as a thoughtful experimental MCP server. It is not yet done as a durable reasoning primitive.

Its strongest part is the model:
- revisable thoughts
- stages
- assumptions
- uncertainty notes
- outcomes

These form a coherent system.

Its weaker part is operational semantics:
- branch lifecycle is too loose
- session-mode truthfulness is inconsistent
- package discovery is shallow
- persistence confidence is unclear because code, tests, and README do not fully align

If development stopped now, the project would still have value. If it continues, the best returns are no longer in adding more borrowed fields. The best returns are in making the current features more truthful, more connected, and more useful.

## Highest-Value Ideas

### 1. Replace weak branch merge with semantic branch resolution

Current `merge_branch` behavior is mostly a string append to a target thought. That is too weak for a system centered on structured reasoning.

Better direction:
- add `resolve_branch`
- allow statuses such as `accepted`, `rejected`, `superseded`, `merged`
- record resolution rationale
- optionally record which thoughts or conclusions were adopted
- keep branch history visible after resolution

This would turn branching from a cosmetic feature into a real reasoning tool.

### 2. Add a real session summary / state-of-thinking tool

The current metadata is good, but it is not yet converted into a strong operator view.

A useful summary tool should answer:
- what stage the session is currently in
- what assumptions are still open
- which branches remain unresolved
- what the confidence trend looks like
- what is left to do across recent thoughts
- whether the chain appears complete

This would make the existing structure materially more useful to clients.

### 3. Add explicit evidence links between objects

Right now thoughts, memories, decisions, and assumptions coexist, but the reasoning graph is still loose.

Useful additions:
- `supports_thought_ids`
- `memory_ids`
- `decision_ids`
- `assumption_ids`

This would let the project move from structured notes to traceable reasoning.

### 4. Add contradiction / revision assistance

The project already supports revisions and falsified assumptions, but it does not actively help the caller detect conflicts.

Potential improvements:
- flag a thought that depends on a falsified assumption
- detect when a new outcome conflicts with an earlier conclusion
- suggest revision when confidence drops or logic diverges

This would make the tool more than storage. It would become an active reasoning aid.

### 5. Add branch comparison, not just branching

A good reasoning system should help compare alternatives, not just create them.

Useful output:
- competing conclusions
- differing assumptions
- differing evidence
- confidence comparison
- recommended next step

This would make branches actionable.

### 6. Add cross-session synthesis

The project can already store memories and decisions, but it does not yet extract reusable patterns across sessions.

Promising direction:
- summarize recurring assumptions
- identify repeated decisions
- surface reusable patterns from prior sessions
- build a lightweight "what this project tends to learn" layer

This is one of the best ways to make the system feel cumulative rather than session-bound.

## Issues That Matter Now

### Contract drift on session types

The public tool schema exposes `memory`, but the implementation only has `general` and `coding`, and non-`coding` values are effectively coerced to `general`.

That should be fixed one of two ways:
- implement a real `memory` mode
- or remove it from the public schema

### Branch referential integrity is too weak

`create_branch` validates that `from_thought` is non-empty, but not that it actually exists in the current session.

That means the reasoning graph can become inconsistent.

### Package exploration is currently low-trust

It only searches installed packages and uses weak relevance scoring. It also appears easy to duplicate package records across repeated exploration.

This feature should either be:
- upgraded substantially
- or reduced in scope / importance

### Persistence confidence needs tightening

The README still says session reload is the main known issue, while the code looks substantially implemented. That mismatch makes it unclear whether:
- the bug is stale
- the README is stale
- or edge cases are still broken

This is mainly a trust issue and should be resolved directly.

## Strict Roadmap

### Must Fix

These are not optional if the goal is a trustworthy tool.

1. Fix session-type truthfulness.
   Either implement `memory` properly or remove it from the public contract.

2. Enforce branch integrity.
   `from_thought` should reference a real thought in the active session.

3. Clarify persistence reality.
   Align README, tests, and implementation so session reload status is unambiguous.

4. Define branch lifecycle explicitly.
   A branch should have meaningful states and a real resolution path.

### Worth Building

These are the best product improvements after correctness/truthfulness is fixed.

1. Add `resolve_branch` with structured outcomes and rationale.
2. Add a session summary / analysis tool that surfaces open assumptions, unresolved branches, progress, and confidence shape.
3. Add explicit links between thoughts, memories, decisions, and assumptions.
4. Add contradiction detection and revision guidance.
5. Add branch comparison output.
6. Add cross-session synthesis for memories and decisions.

### Nice to Have

These are useful, but they should not come before the items above.

1. Better export formats and richer session reports.
2. More polished query/filter tools for thoughts and assumptions.
3. Improved tags, grouping, and summarization views.
4. Better package exploration only if it becomes genuinely reliable.

### Stop Here Option

If the goal is to keep this project small and useful, there is a reasonable stopping point:

- fix contract drift
- fix branch integrity
- verify and document persistence behavior
- leave the rest as a compact structured-thinking MCP server

That version would already be coherent and defensible.

## Recommendation

Do not keep expanding the schema just because more ideas exist in other codebases.

The next high-value move is to strengthen semantics:
- make branches real
- make summaries useful
- make links explicit
- make contradictions visible

That is the path from "interesting structured note system" to "credible reasoning tool."
