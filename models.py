import uuid
from typing import List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from errors import ValidationError


class SessionType(Enum):
    GENERAL = "general"
    CODING = "coding"


class ThoughtType(Enum):
    STANDARD = "standard"
    REVISION = "revision"
    BRANCH = "branch"


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


@dataclass
class Assumption:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    text: str = ""
    confidence: float = 0.8
    critical: bool = False
    verifiable: bool = False
    evidence: str = ""
    verification_status: str = ""

    def __post_init__(self):
        if not self.text or not self.text.strip():
            raise ValidationError("Assumption text cannot be empty")
        if self.confidence < 0 or self.confidence > 1:
            raise ValidationError("Assumption confidence must be between 0 and 1")

    @property
    def is_verified(self) -> bool:
        return self.verification_status == "verified"

    @property
    def is_falsified(self) -> bool:
        return self.verification_status == "falsified"

    @property
    def is_risky(self) -> bool:
        return self.critical and self.confidence < 0.7 and not self.is_verified


@dataclass
class UnifiedSession:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    problem: str = ""
    success_criteria: str = ""
    constraints: str = ""
    session_type: SessionType = SessionType.GENERAL
    codebase_context: str = ""
    package_exploration_required: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    memories: List["Memory"] = field(default_factory=list)
    thoughts: List["Thought"] = field(default_factory=list)
    branches: List["Branch"] = field(default_factory=list)
    architecture_decisions: List["ArchitectureDecision"] = field(default_factory=list)
    discovered_packages: List["PackageInfo"] = field(default_factory=list)


@dataclass
class Memory:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    content: str = ""
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.8
    importance: float = 0.5
    dependencies: List[str] = field(default_factory=list)
    code_snippet: str = ""
    language: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.content or not self.content.strip():
            raise ValidationError("Memory content cannot be empty")

        if self.confidence < 0 or self.confidence > 1:
            raise ValidationError("Memory confidence must be between 0 and 1")

        if self.importance < 0 or self.importance > 1:
            raise ValidationError("Memory importance must be between 0 and 1")

        if isinstance(self.tags, str):
            if self.tags.strip():
                self.tags = [tag.strip() for tag in self.tags.split(",") if tag.strip()]
            else:
                self.tags = []


@dataclass
class Thought:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    branch_id: str = ""
    content: str = ""
    confidence: float = 0.8
    dependencies: List[str] = field(default_factory=list)
    explore_packages: bool = False
    suggested_packages: List[str] = field(default_factory=list)
    thought_number: Optional[int] = None
    total_thoughts: Optional[int] = None
    is_revision: bool = False
    revises_thought_id: str = ""
    next_thought_needed: bool = True
    stage: Optional["ThoughtStage"] = None
    tags: List[str] = field(default_factory=list)
    axioms_used: str = ""
    assumptions_challenged: str = ""
    left_to_be_done: str = ""
    uncertainty_notes: str = ""
    outcome: str = ""
    assumptions: List[str] = field(default_factory=list)
    depends_on_assumptions: List[str] = field(default_factory=list)
    invalidates_assumptions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def thought_type(self) -> "ThoughtType":
        if self.is_revision:
            return ThoughtType.REVISION
        if self.branch_id:
            return ThoughtType.BRANCH
        return ThoughtType.STANDARD

    def __post_init__(self):
        if not self.content or not self.content.strip():
            raise ValidationError("Thought content cannot be empty")

        if self.confidence < 0 or self.confidence > 1:
            raise ValidationError("Thought confidence must be between 0 and 1")

        if isinstance(self.dependencies, str):
            self.dependencies = [d.strip() for d in self.dependencies.split(",") if d.strip()] if self.dependencies.strip() else []

        if isinstance(self.tags, str):
            self.tags = [t.strip() for t in self.tags.split(",") if t.strip()] if self.tags.strip() else []


@dataclass
class Branch:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    purpose: str = ""
    session_id: str = ""
    from_thought_id: str = ""
    thoughts: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ArchitectureDecision:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    decision_title: str = ""
    context: str = ""
    options_considered: str = ""
    chosen_option: str = ""
    rationale: str = ""
    consequences: str = ""
    package_dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PackageInfo:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version: str = ""
    description: str = ""
    api_signatures: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    installation_status: str = ""
    session_id: str = ""
    discovered_at: datetime = field(default_factory=datetime.now)
