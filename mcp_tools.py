import json
import logging
from typing import Dict, Any, List, Optional
from session_manager import UnifiedSessionManager
from models import ThoughtType
from errors import (
    NoActiveSessionError,
    ValidationError,
    ExportError,
    make_error,
    validate_id_format,
)


class MCPToolsHandler:
    def __init__(self, session_manager: UnifiedSessionManager):
        self.session_manager = session_manager
        self.logger = logging.getLogger(__name__)

    def start_session(
        self,
        problem: str,
        success_criteria: str,
        constraints: str = "",
        session_type: str = "general",
        codebase_context: str = "",
        package_exploration_required: bool = True,
    ) -> Dict[str, Any]:
        try:
            session_id = self.session_manager.start_session(
                problem,
                success_criteria,
                constraints,
                session_type,
                codebase_context,
                package_exploration_required,
            )
            return {
                "session_id": session_id,
                "session_type": session_type,
                "problem": problem,
                "success_criteria": success_criteria,
                "constraints": constraints,
                "codebase_context": codebase_context,
                "package_exploration_required": package_exploration_required,
            }
        except Exception as e:
            return {"error": str(e)}

    def add_thought(
        self,
        content: Optional[str] = None,
        branch_id: str = "",
        confidence: float = 0.8,
        dependencies: str = "",
        explore_packages: bool = False,
        thought_number: Optional[int] = None,
        total_thoughts: Optional[int] = None,
        is_revision: bool = False,
        revises_thought_id: str = "",
        next_thought_needed: bool = True,
        stage: str = "",
        tags: str = "",
        axioms_used: str = "",
        assumptions_challenged: str = "",
        left_to_be_done: str = "",
        uncertainty_notes: str = "",
        outcome: str = "",
        assumptions: str = "",
        depends_on_assumptions: str = "",
        invalidates_assumptions: str = "",
    ) -> Dict[str, Any]:
        if content is None:
            return make_error("validation_error", "Missing required field: content", {"field": "content"})
        if not self.session_manager.current_session:
            return make_error("no_active_session", "No active session. Call start_session first.", {})
        try:
            thought_id = self.session_manager.add_thought(
                content, branch_id, confidence, dependencies, explore_packages,
                thought_number, total_thoughts, is_revision, revises_thought_id, next_thought_needed,
                stage, tags, axioms_used, assumptions_challenged, left_to_be_done,
                uncertainty_notes, outcome, assumptions, depends_on_assumptions, invalidates_assumptions,
            )
            if is_revision:
                thought_type = ThoughtType.REVISION.value
            elif branch_id:
                thought_type = ThoughtType.BRANCH.value
            else:
                thought_type = ThoughtType.STANDARD.value
            result: Dict[str, Any] = {
                "thought_id": thought_id,
                "thought_type": thought_type,
                "content": content,
                "confidence": confidence,
                "branch_id": branch_id,
                "next_thought_needed": next_thought_needed,
            }
            if thought_number is not None:
                result["thought_number"] = thought_number
                result["total_thoughts"] = total_thoughts
            if is_revision:
                result["is_revision"] = True
                result["revises_thought_id"] = revises_thought_id
            if stage:
                result["stage"] = stage
            if tags:
                result["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
            if axioms_used:
                result["axioms_used"] = axioms_used
            if assumptions_challenged:
                result["assumptions_challenged"] = assumptions_challenged
            if left_to_be_done:
                result["left_to_be_done"] = left_to_be_done
            if uncertainty_notes:
                result["uncertainty_notes"] = uncertainty_notes
            if outcome:
                result["outcome"] = outcome
            if assumptions:
                result["assumptions"] = [a.strip() for a in assumptions.split(",") if a.strip()]
            if depends_on_assumptions:
                result["depends_on_assumptions"] = [d.strip() for d in depends_on_assumptions.split(",") if d.strip()]
            if invalidates_assumptions:
                result["invalidates_assumptions"] = [i.strip() for i in invalidates_assumptions.split(",") if i.strip()]
            return result
        except Exception as e:
            return {"error": str(e)}

    def create_branch(
        self, name: str, from_thought: str, purpose: str
    ) -> Dict[str, Any]:
        try:
            branch_id = self.session_manager.create_branch(name, from_thought, purpose)
            return {
                "branch_id": branch_id,
                "name": name,
                "from_thought": from_thought,
                "purpose": purpose,
            }
        except Exception as e:
            return {"error": str(e)}

    def merge_branch(self, branch_id: str, target_thought: str = "") -> Dict[str, Any]:
        try:
            result = self.session_manager.merge_branch(branch_id, target_thought)
            return {
                "branch_id": result,
                "target_thought": target_thought,
                "status": "merged",
            }
        except Exception as e:
            return {"error": str(e)}

    def revise_thought(self, thought_id: str, content: str) -> Dict[str, Any]:
        err = validate_id_format(thought_id, "thought")
        if err:
            return err
        try:
            found = self.session_manager.revise_thought(thought_id, content)
            if not found:
                return make_error("thought_not_found", f"Thought '{thought_id}' not found", {"thought_id": thought_id})
            return {"success": True, "thought_id": thought_id}
        except Exception as e:
            return {"error": str(e)}

    def get_thought(self, thought_id: str) -> Dict[str, Any]:
        err = validate_id_format(thought_id, "thought")
        if err:
            return err
        try:
            result = self.session_manager.get_thought(thought_id)
            if result is None:
                return make_error("thought_not_found", f"Thought '{thought_id}' not found", {"thought_id": thought_id})
            return result
        except Exception as e:
            return {"error": str(e)}

    def check_contradictions(self, session_id: str) -> Dict[str, Any]:
        err = validate_id_format(session_id, "session")
        if err:
            return err
        try:
            return self.session_manager.check_contradictions(session_id)
        except Exception as e:
            return {"error": str(e)}

    def get_session(self, session_id: str) -> Dict[str, Any]:
        err = validate_id_format(session_id, "session")
        if err:
            return err
        try:
            result = self.session_manager.get_full_session(session_id)
            if result is None:
                return make_error("session_not_found", f"Session '{session_id}' not found", {"session_id": session_id})
            return result
        except Exception as e:
            return {"error": str(e)}

    def tag_thought(self, thought_id: str, tag: Dict[str, Any]) -> Dict[str, Any]:
        err = validate_id_format(thought_id, "thought")
        if err:
            return err
        try:
            uncertainty = tag.get("uncertainty", "") if isinstance(tag, dict) else ""
            assumptions = tag.get("assumptions", []) if isinstance(tag, dict) else []
            found = self.session_manager.tag_thought(thought_id, uncertainty, assumptions)
            if not found:
                return make_error("thought_not_found", f"Thought '{thought_id}' not found", {"thought_id": thought_id})
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    def find_memories(self, tag: str = "") -> Dict[str, Any]:
        try:
            memories = self.session_manager.find_memories_by_tag(tag)
            return {"memories": memories, "count": len(memories)}
        except Exception as e:
            return {"error": str(e)}

    def resolve_branch(self, session_id: str, branch_id: str) -> Dict[str, Any]:
        err = validate_id_format(branch_id, "branch")
        if err:
            return err
        try:
            found = self.session_manager.resolve_branch(session_id, branch_id)
            if not found:
                return make_error("branch_not_found", f"Branch '{branch_id}' not found", {"branch_id": branch_id})
            return {"success": True, "status": "resolved"}
        except Exception as e:
            return {"error": str(e)}

    def store_memory(
        self,
        content: str,
        confidence: float = 0.8,
        code_snippet: str = "",
        language: str = "",
        tags: str = "",
    ) -> Dict[str, Any]:
        try:
            memory_id = self.session_manager.store_memory(
                content, confidence, code_snippet, language, tags
            )
            return {
                "memory_id": memory_id,
                "content": content,
                "confidence": confidence,
                "tags": tags.split(",") if tags else [],
            }
        except Exception as e:
            return {"error": str(e)}

    def query_memories(
        self, tags: str = "", content_contains: str = ""
    ) -> Dict[str, Any]:
        try:
            memories = self.session_manager.query_memories(tags, content_contains)
            result = {
                "memories": memories,
                "count": len(memories),
                "query": {"tags": tags, "content": content_contains},
            }
            if not memories:
                result["search_tips"] = [
                    "Try using broader tag terms",
                    "For tag OR searches, use comma or | (tag1,tag2 or tag1|tag2)",
                    "For tag AND searches, use & (tag1&tag2)",
                    "For regex content search, use /pattern/",
                ]
            return result
        except Exception as e:
            return {"error": str(e)}

    def record_decision(
        self,
        decision_title: str,
        context: str,
        options_considered: str,
        chosen_option: str,
        rationale: str,
        consequences: str,
        package_dependencies: str = "",
    ) -> Dict[str, Any]:
        try:
            decision_id = self.session_manager.record_decision(
                decision_title,
                context,
                options_considered,
                chosen_option,
                rationale,
                consequences,
                package_dependencies,
            )
            return {
                "decision_id": decision_id,
                "decision_title": decision_title,
                "chosen_option": chosen_option,
            }
        except Exception as e:
            return {"error": str(e)}

    def explore_packages(
        self, task_description: str, language: str = "python"
    ) -> Dict[str, Any]:
        try:
            packages = self.session_manager.explore_packages(task_description, language)
            return {"packages": packages, "count": len(packages), "language": language}
        except Exception as e:
            return {"error": str(e)}

    def export_session(
        self,
        filename: str,
        format: str = "markdown",
        export_type: str = "session",
        tags: str = "",
    ) -> Dict[str, Any]:
        try:
            if not filename or not filename.strip():
                raise ValidationError("Export filename cannot be empty")

            if format not in ["markdown", "json"]:
                raise ValidationError("Export format must be 'markdown' or 'json'")

            if export_type not in ["session", "memories"]:
                raise ValidationError("Export type must be 'session' or 'memories'")

            if not self.session_manager.current_session:
                raise NoActiveSessionError("Cannot export without an active session")

            output_path = self.session_manager.memory_bank_path / filename.strip()

            if export_type == "session":
                content = self._export_session_content(format)
            else:
                memories = self.session_manager.query_memories(tags, "")
                content = self._export_memories_content(memories, format)

            with open(output_path, "w") as f:
                f.write(content)

            return {
                "filename": str(output_path),
                "format": format,
                "export_type": export_type,
                "status": "exported",
            }

        except (ValidationError, NoActiveSessionError, ExportError) as e:
            return {"error": str(e)}
        except Exception as e:
            self.logger.error(f"Failed to export session: {e}")
            return {"error": f"Export failed: {str(e)}"}

    def list_sessions(self) -> Dict[str, Any]:
        try:
            sessions = self.session_manager.list_sessions()
            return {"sessions": sessions, "count": len(sessions)}
        except Exception as e:
            return {"error": str(e)}

    def load_session(self, session_id: str) -> Dict[str, Any]:
        try:
            result = self.session_manager.load_session(session_id)
            return result
        except Exception as e:
            return {"error": str(e)}

    def analyze_session(self) -> Dict[str, Any]:
        try:
            analysis = self.session_manager.analyze_session()
            return analysis
        except Exception as e:
            return {"error": str(e)}

    def verify_assumption(self, assumption_id: str, is_true: bool) -> Dict[str, Any]:
        err = validate_id_format(assumption_id, "assumption")
        if err:
            return err
        try:
            result = self.session_manager.verify_assumption(assumption_id, is_true)
            if result is None:
                return make_error("assumption_not_found", f"Assumption '{assumption_id}' not found", {"assumption_id": assumption_id})
            return {
                "assumption_id": result,
                "verification_status": "verified" if is_true else "falsified",
            }
        except Exception as e:
            return {"error": str(e)}

    def get_assumptions(self) -> Dict[str, Any]:
        try:
            return self.session_manager.get_session_assumptions()
        except Exception as e:
            return {"error": str(e)}

    def _export_session_content(self, format: str) -> str:
        session = self.session_manager.current_session
        if not session:
            return "No active session"
        if format == "json":
            return json.dumps(
                {
                    "session_id": session.id,
                    "problem": session.problem,
                    "success_criteria": session.success_criteria,
                    "thoughts": [
                        {"id": t.id, "content": t.content, "confidence": t.confidence}
                        for t in session.thoughts
                    ],
                    "memories": [
                        {"id": m.id, "content": m.content, "tags": m.tags}
                        for m in session.memories
                    ],
                },
                indent=2,
            )
        else:
            return f"""# {session.problem}

**Session ID:** {session.id}
**Type:** {session.session_type.value}

## Success Criteria
{session.success_criteria}

## Thoughts ({len(session.thoughts)})
{chr(10).join([f"- {t.content}" for t in session.thoughts])}

## Memories ({len(session.memories)})
{chr(10).join([f"- {m.content}" for m in session.memories])}

## Architecture Decisions ({len(session.architecture_decisions)})
{chr(10).join([f"- {d.decision_title}: {d.chosen_option}" for d in session.architecture_decisions])}
"""

    def _export_memories_content(self, memories: List[Dict], format: str) -> str:
        if format == "json":
            return json.dumps(memories, indent=2)
        else:
            content = "# Exported Memories\n\n"
            for memory in memories:
                content += f"## {memory.get('content', '')[:50]}...\n"
                content += f"**Tags:** {', '.join(memory.get('tags', []))}\n"
                content += f"**Confidence:** {memory.get('confidence', 0.8)}\n\n"
                content += f"{memory.get('content', '')}\n\n"
                if memory.get("code_snippet"):
                    content += f"```{memory.get('language', '')}\n{memory.get('code_snippet')}\n```\n\n"
                content += "---\n\n"
            return content
