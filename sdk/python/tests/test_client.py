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


from asyioflow.models import Workflow, WorkflowStep
from asyioflow.exceptions import WorkflowStepFailedError, WorkflowTimeoutError


class TestValidateDag:
    def test_duplicate_step_name_raises_value_error(self):
        from asyioflow.client import _validate_dag
        from asyioflow.models import Workflow, WorkflowStep
        wf = Workflow(name="bad", steps=[
            WorkflowStep(name="fetch", job_type="fetch-data"),
            WorkflowStep(name="fetch", job_type="fetch-data-2"),
        ])
        with pytest.raises(ValueError, match="Duplicate"):
            _validate_dag(wf)

    def test_dangling_dependency_raises_value_error(self):
        from asyioflow.client import _validate_dag
        from asyioflow.models import Workflow, WorkflowStep
        wf = Workflow(name="bad", steps=[
            WorkflowStep(name="transform", job_type="transform-data", depends_on=["nonexistent"]),
        ])
        with pytest.raises(ValueError, match="unknown step"):
            _validate_dag(wf)

    def test_cycle_raises_value_error(self):
        from asyioflow.client import _validate_dag
        from asyioflow.models import Workflow, WorkflowStep
        wf = Workflow(name="bad", steps=[
            WorkflowStep(name="a", job_type="job-a", depends_on=["b"]),
            WorkflowStep(name="b", job_type="job-b", depends_on=["a"]),
        ])
        with pytest.raises(ValueError, match="[Cc]ycle"):
            _validate_dag(wf)


class TestAysioFlowWorkflow:
    def _completed_job(self, job_id: str, job_type: str) -> dict:
        now = "2026-01-01T00:00:00Z"
        return {
            "id": job_id,
            "type": job_type,
            "payload": {},
            "status": "completed",
            "priority": 5,
            "max_retries": 3,
            "attempts": 1,
            "error": None,
            "run_at": None,
            "created_at": now,
            "updated_at": now,
        }

    def _failed_job(self, job_id: str, job_type: str) -> dict:
        j = self._completed_job(job_id, job_type)
        j["status"] = "failed"
        j["error"] = "worker crashed"
        return j

    def test_single_step_workflow(self):
        wf = Workflow(name="simple", steps=[
            WorkflowStep(name="fetch", job_type="fetch-data"),
        ])
        fetch_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/api/v1/jobs").respond(201, json=self._completed_job(fetch_id, "fetch-data"))
            mock.get(f"/api/v1/jobs/{fetch_id}").respond(200, json=self._completed_job(fetch_id, "fetch-data"))

            client = AysioFlow(base_url=BASE_URL)
            results = client.submit_workflow(wf)

        assert "fetch" in results
        assert results["fetch"].id == fetch_id

    def test_sequential_workflow(self):
        """fetch → transform: transform is submitted only after fetch completes."""
        wf = Workflow(name="pipeline", steps=[
            WorkflowStep(name="fetch", job_type="fetch-data"),
            WorkflowStep(name="transform", job_type="transform-data", depends_on=["fetch"]),
        ])
        fetch_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
        transform_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"

        with respx.mock(base_url=BASE_URL) as mock:
            # First POST → fetch job, second POST → transform job
            mock.post("/api/v1/jobs").side_effect = [
                respx.MockResponse(201, json=self._completed_job(fetch_id, "fetch-data")),
                respx.MockResponse(201, json=self._completed_job(transform_id, "transform-data")),
            ]
            mock.get(f"/api/v1/jobs/{fetch_id}").respond(200, json=self._completed_job(fetch_id, "fetch-data"))
            mock.get(f"/api/v1/jobs/{transform_id}").respond(200, json=self._completed_job(transform_id, "transform-data"))

            client = AysioFlow(base_url=BASE_URL)
            results = client.submit_workflow(wf)

        assert set(results.keys()) == {"fetch", "transform"}

    def test_failed_step_raises_workflow_step_failed_error(self):
        wf = Workflow(name="pipeline", steps=[
            WorkflowStep(name="fetch", job_type="fetch-data"),
        ])
        fetch_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"

        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/api/v1/jobs").respond(201, json=self._failed_job(fetch_id, "fetch-data"))
            mock.get(f"/api/v1/jobs/{fetch_id}").respond(200, json=self._failed_job(fetch_id, "fetch-data"))

            client = AysioFlow(base_url=BASE_URL)
            with pytest.raises(WorkflowStepFailedError) as exc_info:
                client.submit_workflow(wf)

        err = exc_info.value
        assert err.step_name == "fetch"
        assert err.job_id == fetch_id
        assert err.completed_steps == {}

    def test_failed_step_includes_partial_results(self):
        """When transform fails, fetch results are in completed_steps."""
        wf = Workflow(name="pipeline", steps=[
            WorkflowStep(name="fetch", job_type="fetch-data"),
            WorkflowStep(name="transform", job_type="transform-data", depends_on=["fetch"]),
        ])
        fetch_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
        transform_id = "00000000-0000-0000-0000-000000000000"

        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/api/v1/jobs").side_effect = [
                respx.MockResponse(201, json=self._completed_job(fetch_id, "fetch-data")),
                respx.MockResponse(201, json=self._failed_job(transform_id, "transform-data")),
            ]
            mock.get(f"/api/v1/jobs/{fetch_id}").respond(200, json=self._completed_job(fetch_id, "fetch-data"))
            mock.get(f"/api/v1/jobs/{transform_id}").respond(200, json=self._failed_job(transform_id, "transform-data"))

            client = AysioFlow(base_url=BASE_URL)
            with pytest.raises(WorkflowStepFailedError) as exc_info:
                client.submit_workflow(wf)

        assert "fetch" in exc_info.value.completed_steps

    def test_workflow_timeout_raises_timeout_error(self):
        """With a very short timeout, polling should raise WorkflowTimeoutError."""
        wf = Workflow(name="simple", steps=[
            WorkflowStep(name="fetch", job_type="fetch-data"),
        ])
        fetch_id = "11111111-2222-3333-4444-555555555555"

        # Job stays in "running" state forever
        running_job = {
            **_job_json(id=fetch_id, status="running"),
            "type": "fetch-data",
        }

        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/api/v1/jobs").respond(201, json=running_job)
            mock.get(f"/api/v1/jobs/{fetch_id}").respond(200, json=running_job)

            client = AysioFlow(base_url=BASE_URL, workflow_timeout=0.0)  # immediate timeout
            with pytest.raises(WorkflowTimeoutError) as exc_info:
                client.submit_workflow(wf)

        assert exc_info.value.step_name == "fetch"
