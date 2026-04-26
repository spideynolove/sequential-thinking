# DECISIONS

## Interface Shape

The primary interface should be an MCP tool surface called by an LLM agent.

That fits the project better than making the CLI or REST API the main product surface, because the current design is centered on structured reasoning operations:
- start a session
- add a thought
- branch
- revise
- verify assumptions
- analyze session state

These are agent-friendly primitives.

### Recommended interface priority

1. **Primary:** MCP server used by an LLM agent
2. **Secondary:** optional CLI for debugging, local inspection, and tests
3. **Later, only if needed:** REST API

### Why this is the right shape

- The project is already implemented as an MCP server.
- The natural caller is an agent that reasons step by step.
- The tool semantics are richer than a simple human CLI flow.
- A CLI is still useful, but mainly as an operator and validation surface.
- A REST API is possible later, but it should not define the product unless there is a real external integration need.

### Acceptance-criteria implication

If MCP is the primary interface, then acceptance criteria should be phrased as:
- calling tool `X` with input `Y` returns structured result `Z`
- session state after operation `X` contains expected changes
- follow-up tool calls reflect the updated reasoning state

For deterministic testing, a thin CLI wrapper can still be useful so shell tests can express:
- "Running command X produces JSON Y"

But that CLI should be treated as a test and operator layer over the MCP core, not the product center.

## Contradiction Detection Trigger

Contradiction detection should be primarily **on demand**, not a hard automatic invariant on every new thought.

### Recommended model

1. **On demand is primary**
   Add an explicit operation such as `check_contradictions` or extend `analyze_session` to surface contradictions.

2. **Automatic lightweight hints are optional**
   When a new thought is added, the system may attach soft warnings if a simple contradiction is obvious.

3. **Do not make full contradiction detection a required side effect of `add_thought`**
   That would make `add_thought` too semantically heavy, harder to test, and harder to evolve.

### Why this is the better choice

- Contradiction detection is inherently heuristic unless the reasoning graph becomes much more formal.
- Automatic hard detection on every thought would create noisy or unstable behavior.
- An explicit operation is easier to define, easier to test, and easier to trust.
- This also separates storage from analysis cleanly.

### Product meaning

The system should help the user detect contradictions, but it should not pretend every contradiction can be caught automatically at write time.

So the right contract is:
- `add_thought` stores structured reasoning
- contradiction analysis is an explicit capability
- optional warnings can exist, but they should be advisory rather than authoritative

### Testing implication

If contradiction detection is on demand, shell-testable acceptance criteria become much cleaner:

- create session
- add thought A
- add thought B
- run contradiction check
- assert that contradiction result includes the expected conflict

That is more deterministic than expecting every `add_thought` call to produce stable automatic judgments.

## Final Position

The sharper product shape is:
- an MCP-first reasoning tool for an LLM agent
- with optional CLI support for humans and tests
- where contradiction detection is an explicit analysis operation
- and where automatic detection, if added, is a lightweight warning layer rather than a strict invariant

This keeps the system honest, testable, and aligned with its current architecture.