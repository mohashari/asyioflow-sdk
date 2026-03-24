import pytest
import respx
import httpx
from asyioflow.client import AsyncAysioFlow
from asyioflow.models import SubmitJobRequest, Job, Workflow, WorkflowStep, JobStatus
from asyioflow.exceptions import JobNotFoundError, WorkflowStepFailedError

BASE_URL = "http://test-engine:8080"


def _job_json(**overrides):
    now = "2026-01-01T00:00:00Z"
    base = {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "type": "send-email",
        "payload": {},
        "status": "pending",
        "priority": 5,
        "max_retries": 3,
        "attempts": 0,
        "error": None,
        "run_at": None,
        "created_at": now,
        "updated_at": now,
    }
    base.update(overrides)
    return base


class TestAsyncAysioFlowSubmit:
    async def test_submit_returns_job(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/api/v1/jobs").respond(201, json=_job_json())
            async with AsyncAysioFlow(base_url=BASE_URL) as client:
                job = await client.submit(SubmitJobRequest(type="send-email"))
            assert isinstance(job, Job)
            assert job.status == JobStatus.PENDING

    async def test_get_returns_job(self):
        job_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get(f"/api/v1/jobs/{job_id}").respond(200, json=_job_json(id=job_id, status="completed"))
            async with AsyncAysioFlow(base_url=BASE_URL) as client:
                job = await client.get(job_id)
            assert job.status == JobStatus.COMPLETED

    async def test_cancel_success(self):
        job_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        with respx.mock(base_url=BASE_URL) as mock:
            mock.delete(f"/api/v1/jobs/{job_id}").respond(204)
            async with AsyncAysioFlow(base_url=BASE_URL) as client:
                await client.cancel(job_id)  # no exception

    async def test_cancel_404_raises_job_not_found(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.delete("/api/v1/jobs/missing").respond(404, text="not found")
            async with AsyncAysioFlow(base_url=BASE_URL) as client:
                with pytest.raises(JobNotFoundError):
                    await client.cancel("missing")


class TestAsyncAysioFlowWorkflow:
    async def test_submit_workflow(self):
        wf = Workflow(name="pipe", steps=[
            WorkflowStep(name="fetch", job_type="fetch-data"),
        ])
        fetch_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        done = _job_json(id=fetch_id, type="fetch-data", status="completed")

        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/api/v1/jobs").respond(201, json=done)
            mock.get(f"/api/v1/jobs/{fetch_id}").respond(200, json=done)
            async with AsyncAysioFlow(base_url=BASE_URL) as client:
                results = await client.submit_workflow(wf)

        assert "fetch" in results

    async def test_submit_workflow_failed_step(self):
        wf = Workflow(name="pipe", steps=[
            WorkflowStep(name="fetch", job_type="fetch-data"),
        ])
        fetch_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
        failed = _job_json(id=fetch_id, type="fetch-data", status="failed", error="crash")

        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/api/v1/jobs").respond(201, json=failed)
            mock.get(f"/api/v1/jobs/{fetch_id}").respond(200, json=failed)
            async with AsyncAysioFlow(base_url=BASE_URL) as client:
                with pytest.raises(WorkflowStepFailedError) as exc_info:
                    await client.submit_workflow(wf)

        assert exc_info.value.step_name == "fetch"
