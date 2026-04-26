## Invalid ID Behavior

Invalid or non-existent IDs must produce explicit, stable, structured errors.

This behavior should be required for all tools that accept identifiers such as:
- `session_id`
- `thought_id`
- `branch_id`
- `assumption_id`
- and any future object reference IDs

Without this, behavior is undefined and reliable shell testing becomes impossible.

### Required rule

Every tool that accepts an ID must distinguish between:
- malformed ID
- well-formed but non-existent ID
- well-formed ID that exists but is outside the active session or otherwise not visible to the caller

These should not silently pass, coerce, or degrade into generic failures.

### Recommended error contract

Return a structured error object with at least:
- `error.code`
- `error.message`
- `error.details`

Recommended codes:
- `invalid_id_format`
- `session_not_found`
- `thought_not_found`
- `branch_not_found`
- `assumption_not_found`
- `cross_session_reference`
- `no_active_session`
- `validation_error`

### Recommended semantics

1. **Malformed ID**
   Return `invalid_id_format`.
   Meaning: the ID is syntactically invalid for the expected identifier type.

2. **Non-existent ID**
   Return `<object>_not_found`.
   Example: `session_not_found` or `thought_not_found`.

3. **Existing ID from the wrong session**
   Return `cross_session_reference`.
   Meaning: the object exists, but it is not valid in the current session context.

4. **Missing active context**
   Return `no_active_session`.
   Meaning: the operation depends on an active session, but none is loaded.

5. **Other validation failures**
   Return `validation_error`.
   Meaning: the request shape is wrong even if the ID itself is fine.

### Why this should be mandatory across all tools

- It makes failures predictable.
- It prevents accidental silent corruption of the reasoning graph.
- It improves UX for both LLM callers and human operators.
- It makes shell tests deterministic.
- It creates a reusable contract for future tools.

### Testing implication

This should be directly testable in shell-style acceptance criteria.

Examples:
- calling `load_session` with a non-existent `session_id` returns `session_not_found`
- calling `create_branch` with a `from_thought` from another session returns `cross_session_reference`
- calling `verify_assumption` with a malformed ID returns `invalid_id_format`

### Final position

Yes, the system should return specific error codes and messages for invalid or non-existent IDs.

Yes, this behavior should be required across all tools that accept object references.

This is a core contract decision, not an implementation detail.
