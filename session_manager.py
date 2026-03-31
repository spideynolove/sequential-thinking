import sqlite3
import json
import importlib.metadata
import re
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from models import (
    UnifiedSession, Memory, Thought, Branch,
    ArchitectureDecision, PackageInfo, Assumption, SessionType, ThoughtStage, ThoughtType,
)
from errors import (
    SessionError, NoActiveSessionError, SessionNotFoundError,
    ValidationError, StorageError, BranchError,
)

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


class UnifiedSessionManager:
    def __init__(self, memory_bank_path: str = "memory-bank"):
        self.logger = logging.getLogger(__name__)
        self.memory_bank_path = Path(memory_bank_path)
        self.db_path = self.memory_bank_path / "sessions.db"
        self.current_session: Optional[UnifiedSession] = None
        try:
            self._init_db()
            self._load_last_active_session()
        except Exception as e:
            self.logger.error(f"Failed to initialize session manager: {e}")
            raise StorageError(f"Could not initialize memory bank at {memory_bank_path}: {e}")

    def _init_db(self) -> None:
        self.memory_bank_path.mkdir(exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    problem TEXT NOT NULL,
                    success_criteria TEXT NOT NULL,
                    constraints TEXT NOT NULL DEFAULT '',
                    session_type TEXT NOT NULL DEFAULT 'general',
                    codebase_context TEXT NOT NULL DEFAULT '',
                    package_exploration_required INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS thoughts (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(id),
                    branch_id TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.8,
                    dependencies TEXT NOT NULL DEFAULT '',
                    explore_packages INTEGER NOT NULL DEFAULT 0,
                    suggested_packages TEXT NOT NULL DEFAULT '',
                    thought_number INTEGER,
                    total_thoughts INTEGER,
                    is_revision INTEGER NOT NULL DEFAULT 0,
                    revises_thought_id TEXT NOT NULL DEFAULT '',
                    next_thought_needed INTEGER NOT NULL DEFAULT 1,
                    stage TEXT,
                    tags TEXT NOT NULL DEFAULT '',
                    axioms_used TEXT NOT NULL DEFAULT '',
                    assumptions_challenged TEXT NOT NULL DEFAULT '',
                    left_to_be_done TEXT NOT NULL DEFAULT '',
                    uncertainty_notes TEXT NOT NULL DEFAULT '',
                    outcome TEXT NOT NULL DEFAULT '',
                    assumptions TEXT NOT NULL DEFAULT '',
                    depends_on_assumptions TEXT NOT NULL DEFAULT '',
                    invalidates_assumptions TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS branches (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(id),
                    name TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    from_thought_id TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(id),
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '',
                    confidence REAL NOT NULL DEFAULT 0.8,
                    importance REAL NOT NULL DEFAULT 0.5,
                    dependencies TEXT NOT NULL DEFAULT '',
                    code_snippet TEXT NOT NULL DEFAULT '',
                    language TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS architecture_decisions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(id),
                    decision_title TEXT NOT NULL,
                    context TEXT NOT NULL,
                    options_considered TEXT NOT NULL,
                    chosen_option TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    consequences TEXT NOT NULL,
                    package_dependencies TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS discovered_packages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(id),
                    name TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT '',
                    description TEXT NOT NULL DEFAULT '',
                    api_signatures TEXT NOT NULL DEFAULT '[]',
                    relevance_score REAL NOT NULL DEFAULT 0.0,
                    installation_status TEXT NOT NULL DEFAULT '',
                    discovered_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS assumptions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(id),
                    text TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.8,
                    critical INTEGER NOT NULL DEFAULT 0,
                    verifiable INTEGER NOT NULL DEFAULT 0,
                    evidence TEXT NOT NULL DEFAULT '',
                    verification_status TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
            for col, defn in [
                ("uncertainty_notes", "TEXT NOT NULL DEFAULT ''"),
                ("outcome", "TEXT NOT NULL DEFAULT ''"),
                ("assumptions", "TEXT NOT NULL DEFAULT ''"),
                ("depends_on_assumptions", "TEXT NOT NULL DEFAULT ''"),
                ("invalidates_assumptions", "TEXT NOT NULL DEFAULT ''"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE thoughts ADD COLUMN {col} {defn}")
                except Exception:
                    pass
            conn.commit()
        finally:
            conn.close()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _upsert_session(self, session: UnifiedSession) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO sessions
                   (id, problem, success_criteria, constraints, session_type,
                    codebase_context, package_exploration_required, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session.id, session.problem, session.success_criteria, session.constraints,
                 session.session_type.value, session.codebase_context,
                 int(session.package_exploration_required),
                 session.created_at.isoformat(), session.updated_at.isoformat()),
            )

    def _touch_session(self, session_id: str) -> None:
        now = datetime.now()
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now.isoformat(), session_id),
            )
        if self.current_session and self.current_session.id == session_id:
            self.current_session.updated_at = now

    def _insert_thought(self, thought: Thought) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO thoughts
                   (id, session_id, branch_id, content, confidence, dependencies,
                    explore_packages, suggested_packages, thought_number, total_thoughts,
                    is_revision, revises_thought_id, next_thought_needed, stage, tags,
                    axioms_used, assumptions_challenged, left_to_be_done, uncertainty_notes,
                    outcome, assumptions, depends_on_assumptions, invalidates_assumptions, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (thought.id, thought.session_id, thought.branch_id, thought.content,
                 thought.confidence, ",".join(thought.dependencies),
                 int(thought.explore_packages), ",".join(thought.suggested_packages),
                 thought.thought_number, thought.total_thoughts,
                 int(thought.is_revision), thought.revises_thought_id,
                 int(thought.next_thought_needed),
                 thought.stage.value if thought.stage else None,
                 ",".join(thought.tags), thought.axioms_used, thought.assumptions_challenged,
                 thought.left_to_be_done, thought.uncertainty_notes, thought.outcome,
                 ",".join(thought.assumptions), ",".join(thought.depends_on_assumptions),
                 ",".join(thought.invalidates_assumptions),
                 thought.created_at.isoformat(), thought.updated_at.isoformat()),
            )

    def _insert_branch(self, branch: Branch) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO branches (id, session_id, name, purpose, from_thought_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (branch.id, branch.session_id, branch.name, branch.purpose,
                 branch.from_thought_id, branch.created_at.isoformat()),
            )

    def _insert_memory(self, memory: Memory) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO memories
                   (id, session_id, content, tags, confidence, importance, dependencies,
                    code_snippet, language, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (memory.id, memory.session_id, memory.content, ",".join(memory.tags),
                 memory.confidence, memory.importance, ",".join(memory.dependencies),
                 memory.code_snippet, memory.language,
                 memory.created_at.isoformat(), memory.updated_at.isoformat()),
            )

    def _insert_decision(self, decision: ArchitectureDecision) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO architecture_decisions
                   (id, session_id, decision_title, context, options_considered, chosen_option,
                    rationale, consequences, package_dependencies, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (decision.id, decision.session_id, decision.decision_title, decision.context,
                 decision.options_considered, decision.chosen_option, decision.rationale,
                 decision.consequences, ",".join(decision.package_dependencies),
                 decision.created_at.isoformat()),
            )

    def _insert_package(self, package: PackageInfo) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO discovered_packages
                   (id, session_id, name, version, description, api_signatures,
                    relevance_score, installation_status, discovered_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (package.id, package.session_id, package.name, package.version,
                 package.description, json.dumps(package.api_signatures),
                 package.relevance_score, package.installation_status,
                 package.discovered_at.isoformat()),
            )

    def _insert_assumption(self, assumption: Assumption) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO assumptions
                   (id, session_id, text, confidence, critical, verifiable, evidence, verification_status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (assumption.id, assumption.session_id, assumption.text,
                 assumption.confidence, int(assumption.critical), int(assumption.verifiable),
                 assumption.evidence, assumption.verification_status, datetime.now().isoformat()),
            )

    def _row_to_thought(self, row) -> Thought:
        return Thought(
            id=row["id"],
            session_id=row["session_id"],
            branch_id=row["branch_id"] or "",
            content=row["content"],
            confidence=row["confidence"],
            dependencies=[d for d in (row["dependencies"] or "").split(",") if d],
            explore_packages=bool(row["explore_packages"]),
            suggested_packages=[p for p in (row["suggested_packages"] or "").split(",") if p],
            thought_number=row["thought_number"],
            total_thoughts=row["total_thoughts"],
            is_revision=bool(row["is_revision"]),
            revises_thought_id=row["revises_thought_id"] or "",
            next_thought_needed=bool(row["next_thought_needed"]),
            stage=ThoughtStage.from_string(row["stage"]) if row["stage"] else None,
            tags=[t for t in (row["tags"] or "").split(",") if t],
            axioms_used=row["axioms_used"] or "",
            assumptions_challenged=row["assumptions_challenged"] or "",
            left_to_be_done=row["left_to_be_done"] or "",
            uncertainty_notes=row["uncertainty_notes"] or "",
            outcome=row["outcome"] or "",
            assumptions=[a for a in (row["assumptions"] or "").split(",") if a],
            depends_on_assumptions=[a for a in (row["depends_on_assumptions"] or "").split(",") if a],
            invalidates_assumptions=[a for a in (row["invalidates_assumptions"] or "").split(",") if a],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_memory(self, row) -> Memory:
        return Memory(
            id=row["id"],
            session_id=row["session_id"],
            content=row["content"],
            tags=[t for t in (row["tags"] or "").split(",") if t],
            confidence=row["confidence"],
            importance=row["importance"],
            dependencies=[d for d in (row["dependencies"] or "").split(",") if d],
            code_snippet=row["code_snippet"] or "",
            language=row["language"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_branch(self, row) -> Branch:
        return Branch(
            id=row["id"],
            name=row["name"],
            purpose=row["purpose"],
            session_id=row["session_id"],
            from_thought_id=row["from_thought_id"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def _row_to_decision(self, row) -> ArchitectureDecision:
        return ArchitectureDecision(
            id=row["id"],
            session_id=row["session_id"],
            decision_title=row["decision_title"],
            context=row["context"],
            options_considered=row["options_considered"],
            chosen_option=row["chosen_option"],
            rationale=row["rationale"],
            consequences=row["consequences"],
            package_dependencies=[p for p in (row["package_dependencies"] or "").split(",") if p],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def _row_to_package(self, row) -> PackageInfo:
        return PackageInfo(
            id=row["id"],
            name=row["name"],
            version=row["version"] or "",
            description=row["description"] or "",
            api_signatures=json.loads(row["api_signatures"] or "[]"),
            relevance_score=row["relevance_score"],
            installation_status=row["installation_status"] or "",
            session_id=row["session_id"],
            discovered_at=datetime.fromisoformat(row["discovered_at"]),
        )

    def _row_to_assumption(self, row) -> Assumption:
        return Assumption(
            id=row["id"],
            session_id=row["session_id"],
            text=row["text"],
            confidence=row["confidence"],
            critical=bool(row["critical"]),
            verifiable=bool(row["verifiable"]),
            evidence=row["evidence"] or "",
            verification_status=row["verification_status"] or "",
        )

    def start_session(
        self,
        problem: str,
        success_criteria: str,
        constraints: str = "",
        session_type: str = "general",
        codebase_context: str = "",
        package_exploration_required: bool = True,
    ) -> str:
        session_type_enum = SessionType.CODING if session_type == "coding" else SessionType.GENERAL
        session = UnifiedSession(
            problem=problem,
            success_criteria=success_criteria,
            constraints=constraints,
            session_type=session_type_enum,
            codebase_context=codebase_context,
            package_exploration_required=package_exploration_required,
        )
        self._upsert_session(session)
        self.current_session = session
        if package_exploration_required and session_type == "coding":
            self.explore_packages(problem)
        return session.id

    def add_thought(
        self,
        content: str,
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
    ) -> str:
        if not self.current_session:
            raise NoActiveSessionError("Cannot add thought without an active session")
        try:
            if not (0 <= confidence <= 1):
                raise ValidationError("Thought confidence must be between 0 and 1")
            content = _sanitize_input(content, MAX_THOUGHT_CONTENT_LENGTH, "content")
            if len(self.current_session.thoughts) >= MAX_THOUGHTS_PER_SESSION:
                raise ValidationError(f"Session thought limit ({MAX_THOUGHTS_PER_SESSION}) reached")
            if branch_id:
                branch_thoughts = sum(1 for t in self.current_session.thoughts if t.branch_id == branch_id)
                if branch_thoughts >= MAX_THOUGHTS_PER_BRANCH:
                    raise ValidationError(f"Branch thought limit ({MAX_THOUGHTS_PER_BRANCH}) reached")

            assumption_ids: List[str] = []
            if assumptions:
                for assumption_text in [a.strip() for a in assumptions.split(",") if a.strip()]:
                    assumption = Assumption(
                        session_id=self.current_session.id,
                        text=assumption_text,
                        confidence=confidence,
                    )
                    self._insert_assumption(assumption)
                    assumption_ids.append(assumption.id)

            if invalidates_assumptions:
                for invalid_id in [i.strip() for i in invalidates_assumptions.split(",") if i.strip()]:
                    self.verify_assumption(invalid_id, False)

            thought = Thought(
                session_id=self.current_session.id,
                branch_id=branch_id,
                content=content,
                confidence=confidence,
                dependencies=dependencies,
                explore_packages=explore_packages,
                thought_number=thought_number,
                total_thoughts=total_thoughts,
                is_revision=is_revision,
                revises_thought_id=revises_thought_id,
                next_thought_needed=next_thought_needed,
                stage=ThoughtStage.from_string(stage),
                tags=tags,
                axioms_used=axioms_used,
                assumptions_challenged=assumptions_challenged,
                left_to_be_done=left_to_be_done,
                uncertainty_notes=uncertainty_notes,
                outcome=outcome,
                assumptions=assumption_ids,
                depends_on_assumptions=[d.strip() for d in depends_on_assumptions.split(",") if d.strip()],
                invalidates_assumptions=[i.strip() for i in invalidates_assumptions.split(",") if i.strip()],
            )
            if explore_packages and self.current_session.session_type == SessionType.CODING:
                try:
                    thought.suggested_packages = self._suggest_packages(content)
                except Exception as e:
                    self.logger.warning(f"Package exploration failed: {e}")
                    thought.suggested_packages = []
            self.current_session.thoughts.append(thought)
            self._insert_thought(thought)
            self._touch_session(self.current_session.id)
            return thought.id
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to add thought: {e}")
            raise SessionError(f"Could not add thought: {e}")

    def create_branch(self, name: str, from_thought: str, purpose: str) -> str:
        if not self.current_session:
            raise NoActiveSessionError("Cannot create branch without an active session")
        try:
            if not name or not name.strip():
                raise ValidationError("Branch name cannot be empty")
            if not purpose or not purpose.strip():
                raise ValidationError("Branch purpose cannot be empty")
            if not from_thought or not from_thought.strip():
                raise ValidationError("Branch must reference a valid thought ID")
            if len(self.current_session.branches) >= MAX_BRANCHES_PER_SESSION:
                raise ValidationError(f"Session branch limit ({MAX_BRANCHES_PER_SESSION}) reached")
            branch = Branch(
                name=name.strip(),
                purpose=purpose.strip(),
                session_id=self.current_session.id,
                from_thought_id=from_thought.strip(),
            )
            self.current_session.branches.append(branch)
            self._insert_branch(branch)
            self._touch_session(self.current_session.id)
            return branch.id
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create branch: {e}")
            raise BranchError(f"Could not create branch '{name}': {e}")

    def merge_branch(self, branch_id: str, target_thought: str = "") -> str:
        if not self.current_session:
            raise NoActiveSessionError("Cannot merge branch without an active session")
        try:
            if not branch_id or not branch_id.strip():
                raise ValidationError("Branch ID cannot be empty")
            branch_found = False
            for branch in self.current_session.branches:
                if branch.id == branch_id:
                    branch_found = True
                    if target_thought:
                        thought_found = False
                        for thought in self.current_session.thoughts:
                            if thought.id == target_thought:
                                thought.content += f"\n[Merged from {branch.name}]"
                                thought_found = True
                                with self._conn() as conn:
                                    conn.execute(
                                        "UPDATE thoughts SET content = ?, updated_at = ? WHERE id = ?",
                                        (thought.content, datetime.now().isoformat(), thought.id),
                                    )
                                break
                        if not thought_found:
                            raise ValidationError(f"Target thought '{target_thought}' not found")
                    self._touch_session(self.current_session.id)
                    return branch_id
            if not branch_found:
                raise BranchError(f"Branch '{branch_id}' not found")
        except (ValidationError, BranchError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to merge branch: {e}")
            raise BranchError(f"Could not merge branch '{branch_id}': {e}")

    def store_memory(
        self,
        content: str,
        confidence: float = 0.8,
        code_snippet: str = "",
        language: str = "",
        tags: str = "",
    ) -> str:
        if not self.current_session:
            raise ValueError("No active session")
        memory = Memory(
            session_id=self.current_session.id,
            content=content,
            confidence=confidence,
            code_snippet=code_snippet,
            language=language,
            tags=tags.split(",") if tags else [],
        )
        self.current_session.memories.append(memory)
        self._insert_memory(memory)
        self._touch_session(self.current_session.id)
        return memory.id

    def query_memories(
        self, tags: str = "", content_contains: str = ""
    ) -> List[Dict[str, Any]]:
        if not self.current_session:
            return []
        tag_filter_type = "any"
        if tags and ("&" in tags or "|" in tags):
            if "&" in tags:
                tag_list = [t.strip() for t in tags.split("&")]
                tag_filter_type = "all"
            else:
                tag_list = [t.strip() for t in tags.split("|")]
        elif tags:
            tag_list = [t.strip() for t in tags.split(",")]
        else:
            tag_list = []
        use_regex = False
        if (
            content_contains
            and content_contains.startswith("/")
            and content_contains.endswith("/")
            and len(content_contains) > 2
        ):
            use_regex = True
            regex_pattern = content_contains[1:-1]
            try:
                content_regex = re.compile(regex_pattern, re.IGNORECASE)
            except re.error:
                use_regex = False
        filtered_memories = []
        for memory in self.current_session.memories:
            if tag_list:
                if tag_filter_type == "all":
                    if not all(
                        any(tag.lower() in t.lower() for t in memory.tags)
                        for tag in tag_list
                    ):
                        continue
                elif not any(
                    any(tag.lower() in t.lower() for t in memory.tags)
                    for tag in tag_list
                ):
                    continue
            if content_contains:
                if use_regex:
                    if not content_regex.search(memory.content):
                        continue
                elif content_contains.lower() not in memory.content.lower():
                    continue
            memory_data = {
                "id": memory.id,
                "content": memory.content,
                "tags": memory.tags,
                "confidence": memory.confidence,
                "language": memory.language if memory.language else "",
                "has_code": bool(memory.code_snippet),
                "created_at": memory.created_at.isoformat(),
                "session_id": memory.session_id,
            }
            if len(memory.content) > 100:
                if content_contains and not use_regex:
                    pos = memory.content.lower().find(content_contains.lower())
                    if pos >= 0:
                        start = max(0, pos - 40)
                        end = min(len(memory.content), pos + len(content_contains) + 40)
                        excerpt = memory.content[start:end]
                        if start > 0:
                            excerpt = "..." + excerpt
                        if end < len(memory.content):
                            excerpt = excerpt + "..."
                        memory_data["excerpt"] = excerpt
                else:
                    memory_data["excerpt"] = memory.content[:100] + "..."
            filtered_memories.append(memory_data)
        return sorted(filtered_memories, key=lambda x: x["confidence"], reverse=True)

    def explore_packages(
        self, task_description: str, language: str = "python"
    ) -> List[str]:
        if not self.current_session:
            raise ValueError("No active session")
        installed_packages = []
        try:
            for dist in importlib.metadata.distributions():
                package_name = dist.metadata["name"]
                relevance_score = self._calculate_relevance(package_name, task_description)
                if relevance_score > 0.3:
                    package = PackageInfo(
                        name=package_name,
                        version=dist.version,
                        description=f"Installed package: {package_name}",
                        relevance_score=relevance_score,
                        installation_status="installed",
                        session_id=self.current_session.id,
                    )
                    self.current_session.discovered_packages.append(package)
                    self._insert_package(package)
                    installed_packages.append(package_name)
        except Exception:
            pass
        self._touch_session(self.current_session.id)
        return installed_packages

    def record_decision(
        self,
        decision_title: str,
        context: str,
        options_considered: str,
        chosen_option: str,
        rationale: str,
        consequences: str,
        package_dependencies: str = "",
    ) -> str:
        if not self.current_session:
            raise ValueError("No active session")
        decision = ArchitectureDecision(
            session_id=self.current_session.id,
            decision_title=decision_title,
            context=context,
            options_considered=options_considered,
            chosen_option=chosen_option,
            rationale=rationale,
            consequences=consequences,
            package_dependencies=(
                package_dependencies.split(",") if package_dependencies else []
            ),
        )
        self.current_session.architecture_decisions.append(decision)
        self._insert_decision(decision)
        self._touch_session(self.current_session.id)
        return decision.id

    def analyze_session(self) -> Dict[str, Any]:
        if not self.current_session:
            return {"error": "No active session"}
        return {
            "session_id": self.current_session.id,
            "session_type": self.current_session.session_type.value,
            "total_thoughts": len(self.current_session.thoughts),
            "total_memories": len(self.current_session.memories),
            "total_branches": len(self.current_session.branches),
            "architecture_decisions": len(self.current_session.architecture_decisions),
            "discovered_packages": len(self.current_session.discovered_packages),
            "created_at": self.current_session.created_at.isoformat(),
            "updated_at": self.current_session.updated_at.isoformat(),
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        try:
            with self._conn() as conn:
                rows = conn.execute(
                    "SELECT id, problem, session_type, created_at FROM sessions ORDER BY updated_at DESC"
                ).fetchall()
            return [
                {"id": r["id"], "problem": r["problem"], "type": r["session_type"], "created": r["created_at"]}
                for r in rows
            ]
        except Exception:
            return []

    def load_session(self, session_id: str) -> Dict[str, Any]:
        try:
            if not session_id or not session_id.strip():
                raise ValidationError("Session ID cannot be empty")
            with self._conn() as conn:
                row = conn.execute(
                    "SELECT * FROM sessions WHERE id = ?", (session_id,)
                ).fetchone()
                if not row:
                    raise SessionNotFoundError(f"Session {session_id} not found")
                session = UnifiedSession(
                    id=row["id"],
                    problem=row["problem"],
                    success_criteria=row["success_criteria"],
                    constraints=row["constraints"] or "",
                    session_type=SessionType.CODING if row["session_type"] == "coding" else SessionType.GENERAL,
                    codebase_context=row["codebase_context"] or "",
                    package_exploration_required=bool(row["package_exploration_required"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
                thought_rows = conn.execute(
                    "SELECT * FROM thoughts WHERE session_id = ? ORDER BY created_at", (session_id,)
                ).fetchall()
                session.thoughts = [self._row_to_thought(r) for r in thought_rows]
                branch_rows = conn.execute(
                    "SELECT * FROM branches WHERE session_id = ? ORDER BY created_at", (session_id,)
                ).fetchall()
                session.branches = [self._row_to_branch(r) for r in branch_rows]
                memory_rows = conn.execute(
                    "SELECT * FROM memories WHERE session_id = ? ORDER BY created_at", (session_id,)
                ).fetchall()
                session.memories = [self._row_to_memory(r) for r in memory_rows]
                decision_rows = conn.execute(
                    "SELECT * FROM architecture_decisions WHERE session_id = ? ORDER BY created_at", (session_id,)
                ).fetchall()
                session.architecture_decisions = [self._row_to_decision(r) for r in decision_rows]
                package_rows = conn.execute(
                    "SELECT * FROM discovered_packages WHERE session_id = ? ORDER BY discovered_at", (session_id,)
                ).fetchall()
                session.discovered_packages = [self._row_to_package(r) for r in package_rows]
                assumption_rows = conn.execute(
                    "SELECT * FROM assumptions WHERE session_id = ?", (session_id,)
                ).fetchall()
                for ar in assumption_rows:
                    assumption = self._row_to_assumption(ar)
                    if not hasattr(session, "_assumptions"):
                        session._assumptions = {}
                    session._assumptions[assumption.id] = assumption
            self.current_session = session
            return {
                "session_id": session_id,
                "status": "loaded",
                "thoughts_count": len(session.thoughts),
                "memories_count": len(session.memories),
            }
        except (ValidationError, SessionNotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to load session {session_id}: {e}")
            raise SessionError(f"Could not load session {session_id}: {e}")

    def _suggest_packages(self, content: str) -> List[str]:
        suggestions = []
        keywords = {
            "http": ["requests", "httpx", "urllib3"],
            "web": ["flask", "django", "fastapi"],
            "data": ["pandas", "numpy", "sqlite3"],
            "test": ["pytest", "unittest", "mock"],
            "json": ["json", "jsonschema", "pydantic"],
            "async": ["asyncio", "aiohttp", "tornado"],
        }
        content_lower = content.lower()
        for keyword, packages in keywords.items():
            if keyword in content_lower:
                suggestions.extend(packages)
        return list(set(suggestions))

    def _calculate_relevance(self, package_name: str, task_description: str) -> float:
        task_lower = task_description.lower()
        package_lower = package_name.lower()
        if package_lower in task_lower:
            return 0.8
        common_words = set(task_lower.split()) & set(package_lower.split())
        if common_words:
            return 0.5
        return 0.1

    def _load_last_active_session(self) -> None:
        try:
            sessions = self.list_sessions()
            if sessions:
                self.load_session(sessions[0]["id"])
        except Exception:
            pass

    def verify_assumption(self, assumption_id: str, is_true: bool) -> Optional[str]:
        if not self.current_session:
            raise NoActiveSessionError("Cannot verify assumption without an active session")
        try:
            with self._conn() as conn:
                row = conn.execute(
                    "SELECT * FROM assumptions WHERE id = ? AND session_id = ?",
                    (assumption_id, self.current_session.id),
                ).fetchone()
                if not row:
                    return None
                status = "verified" if is_true else "falsified"
                conn.execute(
                    "UPDATE assumptions SET verification_status = ? WHERE id = ?",
                    (status, assumption_id),
                )
            return assumption_id
        except Exception as e:
            self.logger.error(f"Failed to verify assumption: {e}")
            raise SessionError(f"Could not verify assumption: {e}")

    def get_session_assumptions(self) -> Dict[str, Any]:
        if not self.current_session:
            return {"error": "No active session"}
        try:
            with self._conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM assumptions WHERE session_id = ?",
                    (self.current_session.id,),
                ).fetchall()
            assumptions = [self._row_to_assumption(r) for r in rows]
            risky = [a.id for a in assumptions if a.is_risky]
            falsified = [a.id for a in assumptions if a.is_falsified]
            return {
                "assumptions": [
                    {
                        "id": a.id,
                        "text": a.text,
                        "confidence": a.confidence,
                        "critical": a.critical,
                        "verifiable": a.verifiable,
                        "verification_status": a.verification_status,
                        "is_risky": a.is_risky,
                    }
                    for a in assumptions
                ],
                "risky_assumptions": risky,
                "falsified_assumptions": falsified,
                "count": len(assumptions),
            }
        except Exception as e:
            self.logger.error(f"Failed to get assumptions: {e}")
            return {"error": str(e)}
