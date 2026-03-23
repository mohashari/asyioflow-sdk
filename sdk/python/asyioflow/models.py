from __future__ import annotations

from datetime import datetime
from enum import IntEnum, Enum
from typing import Any, Optional

from pydantic import BaseModel


class Priority(IntEnum):
    LOW = 1
    NORMAL = 5
    HIGH = 10


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"


class SubmitJobRequest(BaseModel):
    type: str
    payload: dict[str, Any] = {}
    priority: Priority = Priority.NORMAL
    max_retries: int = 3


class Job(BaseModel):
    """Server response — all required fields are always populated by the engine."""

    id: str
    type: str
    payload: dict[str, Any] = {}
    status: JobStatus
    priority: Priority
    max_retries: int
    attempts: int
    error: Optional[str] = None
    run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class WorkflowStep(BaseModel):
    name: str
    job_type: str
    payload: dict[str, Any] = {}
    depends_on: list[str] = []


class Workflow(BaseModel):
    name: str
    steps: list[WorkflowStep] = []
