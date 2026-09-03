from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    reviewed = "reviewed"
    revision = "revision_requested"


class ConstraintSet(BaseModel):
    audience: str = "general"
    language: str = "English"
    tone: str = "clear and helpful"
    length: str = "medium"
    output_format: str = "structured response"


class Ambiguity(BaseModel):
    term: str
    possible_meanings: list[str] = Field(default_factory=list)
    question: str


class LanguageAnalysis(BaseModel):
    original_text: str
    normalized_text: str
    intent: str
    entities: list[str] = Field(default_factory=list)
    key_phrases: list[str] = Field(default_factory=list)
    constraints: ConstraintSet = Field(default_factory=ConstraintSet)
    ambiguities: list[Ambiguity] = Field(default_factory=list)
    semantic_frame: dict[str, Any] = Field(default_factory=dict)
    confidence_note: str = "Heuristic estimate; not a calibrated probability."


class TaskNode(BaseModel):
    id: str
    title: str
    objective: str
    parent_id: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    assigned_role: str = "Worker Agent"
    expected_output: str = "concise findings"
    status: TaskStatus = TaskStatus.pending


class TaskPlan(BaseModel):
    goal: str
    tasks: list[TaskNode]
    planning_notes: list[str] = Field(default_factory=list)


class AgentMessage(BaseModel):
    sequence: int
    sender: str
    receiver: str
    message_type: str
    task_id: str | None = None
    human_summary: str
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkerResult(BaseModel):
    task_id: str
    title: str
    content: str
    key_points: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)


class ReviewResult(BaseModel):
    approved: bool
    score: int = Field(ge=1, le=10)
    strengths: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    revision_instruction: str = ""


class RunResult(BaseModel):
    analysis: LanguageAnalysis
    plan: TaskPlan
    worker_results: list[WorkerResult]
    review: ReviewResult
    final_answer: str
    messages: list[AgentMessage]


class CompactRunResult(BaseModel):
    """Quota-efficient Gemini response; communication messages are built locally."""

    analysis: LanguageAnalysis
    plan: TaskPlan
    worker_results: list[WorkerResult]
    review: ReviewResult
    final_answer: str
