import pytest
from datetime import datetime, timezone
from asyioflow.models import (
    Priority,
    JobStatus,
    SubmitJobRequest,
    Job,
    WorkflowStep,
    Workflow,
)


class TestPriority:
    def test_values(self):
        assert Priority.LOW == 1
        assert Priority.NORMAL == 5
        assert Priority.HIGH == 10

    def test_is_int(self):
        assert isinstance(Priority.HIGH, int)


class TestJobStatus:
    def test_values(self):
        assert JobStatus.PENDING == "pending"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.DEAD == "dead"


class TestSubmitJobRequest:
    def test_minimal(self):
        req = SubmitJobRequest(type="send-email")
        assert req.type == "send-email"
        assert req.payload == {}
        assert req.priority == Priority.NORMAL
        assert req.max_retries == 3

    def test_full(self):
        req = SubmitJobRequest(
            type="send-email",
            payload={"to": "x@y.com"},
            priority=Priority.HIGH,
            max_retries=5,
        )
        assert req.payload == {"to": "x@y.com"}
        assert req.priority == Priority.HIGH

    def test_type_required(self):
        with pytest.raises(Exception):
            SubmitJobRequest()  # type: ignore


class TestJob:
    def _make_job_dict(self, **overrides):
        now = "2026-01-01T00:00:00Z"
        base = {
            "id": "11111111-1111-1111-1111-111111111111",
            "type": "send-email",
            "payload": {"to": "x@y.com"},
            "status": "completed",
            "priority": 5,
            "max_retries": 3,
            "attempts": 1,
            "error": None,
            "run_at": None,
            "created_at": now,
            "updated_at": now,
        }
        base.update(overrides)
        return base

    def test_parse_from_dict(self):
        job = Job.model_validate(self._make_job_dict())
        assert job.id == "11111111-1111-1111-1111-111111111111"
        assert job.status == JobStatus.COMPLETED
        assert job.priority == Priority.NORMAL

    def test_error_field_optional(self):
        # Server may omit error field entirely (not just send null)
        d = self._make_job_dict()
        del d["error"]
        job = Job.model_validate(d)
        assert job.error is None

    def test_run_at_optional(self):
        d = self._make_job_dict()
        del d["run_at"]
        job = Job.model_validate(d)
        assert job.run_at is None


class TestWorkflowStep:
    def test_minimal(self):
        step = WorkflowStep(name="fetch", job_type="fetch-data")
        assert step.name == "fetch"
        assert step.job_type == "fetch-data"
        assert step.payload == {}
        assert step.depends_on == []

    def test_with_deps(self):
        step = WorkflowStep(name="transform", job_type="transform-data", depends_on=["fetch"])
        assert step.depends_on == ["fetch"]


class TestWorkflow:
    def test_create(self):
        wf = Workflow(
            name="pipeline",
            steps=[
                WorkflowStep(name="fetch", job_type="fetch-data"),
                WorkflowStep(name="transform", job_type="transform-data", depends_on=["fetch"]),
            ],
        )
        assert wf.name == "pipeline"
        assert len(wf.steps) == 2


class TestPublicExports:
    def test_client_exports(self):
        from asyioflow import AysioFlow, AsyncAysioFlow
        assert AysioFlow is not None
        assert AsyncAysioFlow is not None

    def test_model_exports(self):
        from asyioflow import SubmitJobRequest, Job, Workflow, WorkflowStep, Priority, JobStatus
        assert SubmitJobRequest is not None

    def test_exception_exports(self):
        from asyioflow import AysioFlowError, JobNotFoundError, ValidationError, ServerError
        from asyioflow import WorkflowStepFailedError, WorkflowTimeoutError
        assert AysioFlowError is not None
