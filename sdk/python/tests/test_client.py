import pytest
import respx
import httpx
from asyioflow.client import AysioFlow
from asyioflow.models import SubmitJobRequest, Job, Priority, JobStatus
from asyioflow.exceptions import JobNotFoundError, ValidationError, AysioFlowError

BASE_URL = "http://test-engine:8080"


# Minimal valid Job JSON the engine would return
def _job_json(**overrides):
    now = "2026-01-01T00:00:00Z"
    base = {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "type": "send-email",
        "payload": {"to": "x@y.com"},
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


class TestAysioFlowSubmit:
    def test_submit_returns_job(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/api/v1/jobs").respond(201, json=_job_json())
            client = AysioFlow(base_url=BASE_URL)
            job = client.submit(SubmitJobRequest(type="send-email", payload={"to": "x@y.com"}))
            assert isinstance(job, Job)
            assert job.id == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
            assert job.status == JobStatus.PENDING

    def test_submit_400_raises_validation_error(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/api/v1/jobs").respond(400, text="type required")
            client = AysioFlow(base_url=BASE_URL)
            with pytest.raises(ValidationError):
                client.submit(SubmitJobRequest(type="send-email"))

    def test_submit_network_error_raises_asyioflow_error(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/api/v1/jobs").mock(side_effect=httpx.ConnectError("refused"))
            client = AysioFlow(base_url=BASE_URL)
            with pytest.raises(AysioFlowError):
                client.submit(SubmitJobRequest(type="send-email"))


class TestAysioFlowGet:
    def test_get_returns_job(self):
        job_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get(f"/api/v1/jobs/{job_id}").respond(200, json=_job_json(id=job_id, status="completed"))
            client = AysioFlow(base_url=BASE_URL)
            job = client.get(job_id)
            assert job.id == job_id
            assert job.status == JobStatus.COMPLETED

    def test_get_404_raises_job_not_found(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/api/v1/jobs/missing").respond(404, text="not found")
            client = AysioFlow(base_url=BASE_URL)
            with pytest.raises(JobNotFoundError):
                client.get("missing")


class TestAysioFlowCancel:
    def test_cancel_success(self):
        job_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        with respx.mock(base_url=BASE_URL) as mock:
            mock.delete(f"/api/v1/jobs/{job_id}").respond(204)
            client = AysioFlow(base_url=BASE_URL)
            client.cancel(job_id)  # no exception

    def test_cancel_404_raises_job_not_found(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.delete("/api/v1/jobs/missing").respond(404, text="not found")
            client = AysioFlow(base_url=BASE_URL)
            with pytest.raises(JobNotFoundError):
                client.cancel("missing")
