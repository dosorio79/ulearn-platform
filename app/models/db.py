"""MongoDB telemetry models and validation wrappers."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel


# -----------------------------
# Validation model (boundary)
# -----------------------------

class LessonRunModel(BaseModel):
    """Pydantic validation model for telemetry records."""
    run_id: str
    session_id: str
    topic: str
    level: Literal["beginner", "intermediate"]
    created_at: datetime
    attempt_count: int
    total_minutes: int
    objective: str
    section_ids: List[str]
    hint_summary: Optional[dict[str, Any]] = None
    rule_hints: Optional[List[dict[str, Any]]] = None
    runtime_hints: Optional[List[dict[str, Any]]] = None
    mcp_hints: Optional[List[dict[str, Any]]] = None
    mcp_summary: Optional[dict[str, Any]] = None
    rule_summary: Optional[dict[str, Any]] = None
    system_observations: Optional[dict[str, Any]] = None


class LessonFailureModel(BaseModel):
    """Pydantic validation model for failure records."""
    run_id: str
    session_id: str
    topic: str
    level: Literal["beginner", "intermediate"]
    created_at: datetime
    attempt_count: Optional[int] = None
    error_type: str
    error_message: str
    error_details: Optional[List[dict[str, Any]]] = None


# -----------------------------
# Internal telemetry model
# -----------------------------

@dataclass(frozen=True)
class LessonRun:
    """Validated telemetry record for a lesson generation run."""
    run_id: str
    session_id: str
    topic: str
    level: Literal["beginner", "intermediate"]
    created_at: datetime
    attempt_count: int
    total_minutes: int
    objective: str
    section_ids: List[str]
    hint_summary: Optional[dict[str, Any]] = None
    rule_hints: Optional[List[dict[str, Any]]] = None
    runtime_hints: Optional[List[dict[str, Any]]] = None
    mcp_hints: Optional[List[dict[str, Any]]] = None
    mcp_summary: Optional[dict[str, Any]] = None
    rule_summary: Optional[dict[str, Any]] = None
    system_observations: Optional[dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Validate fields once at construction time."""
        # Validate once at construction time
        LessonRunModel(
            run_id=self.run_id,
            session_id=self.session_id,
            topic=self.topic,
            level=self.level,
            created_at=self.created_at,
            attempt_count=self.attempt_count,
            total_minutes=self.total_minutes,
            objective=self.objective,
            section_ids=self.section_ids,
            hint_summary=self.hint_summary,
            rule_hints=self.rule_hints,
            runtime_hints=self.runtime_hints,
            mcp_hints=self.mcp_hints,
            mcp_summary=self.mcp_summary,
            rule_summary=self.rule_summary,
            system_observations=self.system_observations,
        )

    def to_mongo(self) -> dict:
        """Convert the telemetry record to a MongoDB-ready document."""
        doc = {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "topic": self.topic,
            "level": self.level,
            "created_at": self.created_at,
            "attempt_count": self.attempt_count,
            "total_minutes": self.total_minutes,
            "objective": self.objective,
            "section_ids": self.section_ids,
        }
        if self.hint_summary is not None:
            doc["hint_summary"] = self.hint_summary
        if self.rule_hints is not None:
            doc["rule_hints"] = self.rule_hints
        if self.runtime_hints is not None:
            doc["runtime_hints"] = self.runtime_hints
        if self.mcp_hints is not None:
            doc["mcp_hints"] = self.mcp_hints
        if self.mcp_summary is not None:
            doc["mcp_summary"] = self.mcp_summary
        if self.rule_summary is not None:
            doc["rule_summary"] = self.rule_summary
        if self.system_observations is not None:
            doc["system_observations"] = self.system_observations
        return doc


@dataclass(frozen=True)
class LessonFailure:
    """Validated telemetry record for a lesson generation failure."""
    run_id: str
    session_id: str
    topic: str
    level: Literal["beginner", "intermediate"]
    created_at: datetime
    error_type: str
    error_message: str
    error_details: Optional[List[dict[str, Any]]] = None
    attempt_count: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate fields once at construction time."""
        LessonFailureModel(
            run_id=self.run_id,
            session_id=self.session_id,
            topic=self.topic,
            level=self.level,
            created_at=self.created_at,
            attempt_count=self.attempt_count,
            error_type=self.error_type,
            error_message=self.error_message,
            error_details=self.error_details,
        )

    def to_mongo(self) -> dict:
        """Convert the failure record to a MongoDB-ready document."""
        return {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "topic": self.topic,
            "level": self.level,
            "created_at": self.created_at,
            "attempt_count": self.attempt_count,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_details": self.error_details,
        }
