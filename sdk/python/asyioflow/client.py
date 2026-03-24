from __future__ import annotations

import asyncio
import time
from typing import Optional

from .exceptions import WorkflowStepFailedError, WorkflowTimeoutError
from ._http import AsyncHttpClient, HttpClient
from .models import Job, JobStatus, SubmitJobRequest, Workflow

_JOBS_URL = "/api/v1/jobs"
_JOB_URL = "/api/v1/jobs/{id}"
_POLL_INTERVAL = 2.0
_TERMINAL: frozenset[JobStatus] = frozenset({JobStatus.FAILED, JobStatus.DEAD})
_DEFAULT_WORKFLOW_TIMEOUT = 600.0  # 10 minutes


def _validate_dag(workflow: "Workflow") -> None:
    """Raise ValueError for duplicate step names, dangling deps, or cycles."""
    names = [s.name for s in workflow.steps]
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise ValueError(f"Duplicate workflow step name: {name!r}")
        seen.add(name)

    name_set = set(names)
    for step in workflow.steps:
        for dep in step.depends_on:
            if dep not in name_set:
                raise ValueError(
                    f"Step {step.name!r} depends on unknown step {dep!r}"
                )

    # DFS cycle detection
    visiting: set[str] = set()
    visited: set[str] = set()
    deps = {s.name: s.depends_on for s in workflow.steps}

    def dfs(node: str) -> None:
        if node in visiting:
            raise ValueError(f"Cycle detected in workflow at step {node!r}")
        if node in visited:
            return
        visiting.add(node)
        for dep in deps[node]:
            dfs(dep)
        visiting.discard(node)
        visited.add(node)

    for name in names:
        dfs(name)


class AysioFlow:
    """Synchronous AysioFlow client."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        api_key: Optional[str] = None,
        workflow_timeout: float = _DEFAULT_WORKFLOW_TIMEOUT,
    ) -> None:
        self._http = HttpClient(base_url=base_url, timeout=timeout, api_key=api_key)
        self._workflow_timeout = workflow_timeout

    def submit(self, req: SubmitJobRequest) -> Job:
        """Submit a job. Returns the created Job with server-populated fields."""
        data = self._http.post(_JOBS_URL, json=req.model_dump(exclude_none=True))
        return Job.model_validate(data)

    def get(self, job_id: str) -> Job:
        """Get current job state by ID."""
        data = self._http.get(_JOB_URL.format(id=job_id))
        return Job.model_validate(data)

    def cancel(self, job_id: str) -> None:
        """Cancel a job. Raises JobNotFoundError if the job does not exist."""
        self._http.delete(_JOB_URL.format(id=job_id))

    def submit_workflow(self, workflow: "Workflow") -> "dict[str, Job]":
        """Execute a workflow DAG. Returns completed step name → Job mapping.

        Steps are executed in dependency order. Polling is fixed at 2 seconds.
        Raises WorkflowStepFailedError if any step fails (includes partial results).
        Raises WorkflowTimeoutError if the total workflow execution exceeds workflow_timeout seconds.
        """
        _validate_dag(workflow)
        completed: dict[str, Job] = {}
        pending = {step.name: step for step in workflow.steps}
        deadline = time.monotonic() + self._workflow_timeout

        while pending:
            ready = [
                step
                for step in pending.values()
                if all(dep in completed for dep in step.depends_on)
            ]
            for step in ready:
                job = self.submit(SubmitJobRequest(type=step.job_type, payload=step.payload))
                while True:
                    job = self.get(job.id)
                    if job.status == JobStatus.COMPLETED:
                        completed[step.name] = job
                        del pending[step.name]
                        break
                    if job.status in _TERMINAL:
                        raise WorkflowStepFailedError(step.name, job.id, dict(completed))
                    if time.monotonic() > deadline:
                        raise WorkflowTimeoutError(step.name)
                    time.sleep(_POLL_INTERVAL)

        return completed

    def close(self) -> None:
        self._http.close()


class AsyncAysioFlow:
    """Asynchronous AysioFlow client, usable as async context manager."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        api_key: Optional[str] = None,
        workflow_timeout: float = _DEFAULT_WORKFLOW_TIMEOUT,
    ) -> None:
        self._http = AsyncHttpClient(base_url=base_url, timeout=timeout, api_key=api_key)
        self._workflow_timeout = workflow_timeout

    async def submit(self, req: SubmitJobRequest) -> Job:
        """Submit a job. Returns the created Job with server-populated fields."""
        data = await self._http.post(_JOBS_URL, json=req.model_dump(exclude_none=True))
        return Job.model_validate(data)

    async def get(self, job_id: str) -> Job:
        """Get current job state by ID."""
        data = await self._http.get(_JOB_URL.format(id=job_id))
        return Job.model_validate(data)

    async def cancel(self, job_id: str) -> None:
        """Cancel a job. Raises JobNotFoundError if the job does not exist."""
        await self._http.delete(_JOB_URL.format(id=job_id))

    async def submit_workflow(self, workflow: "Workflow") -> "dict[str, Job]":
        """Execute a workflow DAG asynchronously. Returns step name → Job mapping.

        Steps are executed in dependency order. Polling uses asyncio.sleep (2 seconds).
        Raises WorkflowStepFailedError if any step fails.
        Raises WorkflowTimeoutError if total workflow execution exceeds workflow_timeout seconds.
        """
        _validate_dag(workflow)
        completed: dict[str, Job] = {}
        pending = {step.name: step for step in workflow.steps}
        deadline = asyncio.get_running_loop().time() + self._workflow_timeout

        while pending:
            ready = [
                step
                for step in pending.values()
                if all(dep in completed for dep in step.depends_on)
            ]
            for step in ready:
                job = await self.submit(SubmitJobRequest(type=step.job_type, payload=step.payload))
                while True:
                    if asyncio.get_running_loop().time() > deadline:
                        raise WorkflowTimeoutError(step.name)
                    job = await self.get(job.id)
                    if job.status == JobStatus.COMPLETED:
                        completed[step.name] = job
                        del pending[step.name]
                        break
                    if job.status in _TERMINAL:
                        raise WorkflowStepFailedError(step.name, job.id, dict(completed))
                    await asyncio.sleep(_POLL_INTERVAL)

        return completed

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncAysioFlow:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
