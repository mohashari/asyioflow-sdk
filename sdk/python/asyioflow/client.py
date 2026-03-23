from __future__ import annotations

from typing import Optional

from .exceptions import WorkflowStepFailedError, WorkflowTimeoutError
from ._http import AsyncHttpClient, HttpClient
from .models import Job, SubmitJobRequest, Workflow

_JOBS_URL = "/api/v1/jobs"
_JOB_URL = "/api/v1/jobs/{id}"
_POLL_INTERVAL = 2.0
_TERMINAL = frozenset({"completed", "failed", "dead"})
_DEFAULT_WORKFLOW_TIMEOUT = 600.0  # 10 minutes


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

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncAysioFlow:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
