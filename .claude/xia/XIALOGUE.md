# XIALOGUE — sequential-thinking (v3)

## Current evolved state of A

sequential-thinking v3 started as a direct copy of v2 (the original sequential-thinking MCP server). It provides 14 MCP tools for session-based thought management, persistent markdown storage, memory/query, branching, architecture decision recording, package exploration, and assumption lifecycle tracking.

From Xỉa #1 (modelcontextprotocol/servers reference implementation), v3 gained **numbered revisable thought chains**: `add_thought` accepts `thought_number`, `total_thoughts`, `is_revision`, `revises_thought_id`, and `next_thought_needed` — enabling progress-aware, revisable, self-terminating thought chains.

From Xỉa #2 (arben-adm/mcp-sequential-thinking), v3 gained **staged + tagged + epistemic thoughts**: `add_thought` now also accepts `stage` (one of `problem_definition`, `research`, `analysis`, `synthesis`, `conclusion`), `tags` (comma-separated, per-thought), `axioms_used`, and `assumptions_challenged`. All are optional, backward compatible, and round-trip through markdown storage. This lays the groundwork for a future `ThoughtAnalyzer` borrow (generate_summary by stage + tag frequency).

From Xỉa #3 (philogicae/sequential-thinking-mcp), v3 gained **`left_to_be_done`**: a free-text string field on each thought that narrates remaining work. Completes the progress-signaling picture alongside `total_thoughts` (count) and `next_thought_needed` (done signal).

From Xỉa #4 (FradSer/mcp-server-mas-sequential-thinking), v3 gained three defensive additions: **input sanitization** (`_sanitize_input` — rejects control characters, injection patterns, and over-length content on thought `content`), **DoS protection limits** (`MAX_THOUGHTS_PER_SESSION=500`, `MAX_BRANCHES_PER_SESSION=50`, `MAX_THOUGHTS_PER_BRANCH=100`), and **`ThoughtType` enum** (`STANDARD`, `REVISION`, `BRANCH` — auto-derived from existing fields, exposed in `add_thought` response). HTML escaping and Shannon entropy from F's original were dropped as incompatible with A's code-containing markdown storage.

From Xỉa #5 (husniadil/ultrathink), v3 gained **uncertainty narration + outcome capture**: `add_thought` accepts `uncertainty_notes` (explains why confidence is what it is) and `outcome` (what this step concluded). Together with `left_to_be_done`, this completes the per-thought narrative arc.

From Xỉa #5 (husniadil/ultrathink), v3 also gained a **structured assumption lifecycle system**: `Assumption` dataclass with `id`, `text`, `confidence`, `critical`, `verifiable`, `evidence`, `verification_status` (properties: `is_verified`, `is_falsified`, `is_risky`). Thoughts can declare new assumptions (`assumptions` param — comma-separated texts), depend on existing ones (`depends_on_assumptions` — comma-separated IDs), and invalidate them (`invalidates_assumptions` — comma-separated IDs). New tools: `verify_assumption(assumption_id, is_true)` and `get_assumptions()` return all assumptions + risky/falsified lists. Stored in dedicated `assumptions` table, round-trips through `load_session`. This replaces A's unstructured `assumptions_challenged`/`axioms_used` strings with queryable, verifiable assumption tracking.

---

## Borrow history

| Date | Source repo | Pattern | Gap filled | Saved to |
|------|-------------|---------|------------|----------|
| 2026-03-23 | modelcontextprotocol/servers/src/sequentialthinking | Numbered revisable thought chain (thought_number, total_thoughts, is_revision, revises_thought_id, next_thought_needed) | Thoughts were append-only with no progress awareness, no revision, no completion signal | .claude/xia/patterns/xia-sequentialthinking-revisable-thought-chain.md |
| 2026-03-23 | arben-adm/mcp-sequential-thinking | ThoughtStage enum + tags on thoughts + axioms_used + assumptions_challenged | Thoughts were undifferentiated — no reasoning phase, no topic tags, no epistemic metadata | .claude/xia/patterns/xia-arben-thought-stage-tags-axioms.md |
| 2026-03-23 | spences10/mcp-sequentialthinking-tools | studied, skipped — tool-advisor architecture (ToolRecommendation/StepRecommendation) is out of scope; A already has thought_number/revision from Xia #1; MAX_HISTORY_SIZE conflicts with A's persistence design | — | — |
| 2026-03-23 | recallnet/sequential-thinking-recall | studied, skipped — blockchain adapter | — | — |
| 2026-03-23 | philogicae/sequential-thinking-mcp | left_to_be_done — free-text remaining work narrative per thought | A had count (total_thoughts) and done-signal (next_thought_needed) but no narrative of what remains | .claude/xia/patterns/xia-philogicae-left-to-be-done.md |
| 2026-03-23 | FradSer/mcp-server-mas-sequential-thinking | Input sanitization + DoS limits + ThoughtType enum | A had no input validation, no session growth limits, no thought type classification | .claude/xia/patterns/xia-fradser-sanitization-dos-thoughttype.md |
| 2026-03-24 | husniadil/ultrathink | uncertainty_notes + outcome fields on Thought | A had confidence scoring but no narrative explaining uncertainty or capturing conclusions | .claude/xia/patterns/xia-ultrathink-uncertainty-outcome.md |
| 2026-03-24 | husniadil/ultrathink | Assumption lifecycle system (Assumption model, depends_on/invalidates, verify_assumption, get_assumptions tools) | A had unstructured assumptions_challenged/axioms_used strings — no way to query critical unverified assumptions or track reasoning dependencies | .claude/xia/patterns/xia-ultrathink-assumption-lifecycle.md |
