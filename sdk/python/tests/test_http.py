import pytest
import httpx
import respx
from asyioflow._http import HttpClient, AsyncHttpClient, _raise_for_status
from asyioflow.exceptions import (
    AysioFlowError,
    JobNotFoundError,
    ValidationError,
    ServerError,
)

BASE_URL = "http://test-engine:8080"


class TestRaiseForStatus:
    def _make_response(self, status_code: int, text: str = "msg") -> httpx.Response:
        return httpx.Response(status_code, text=text)

    def test_200_ok(self):
        resp = self._make_response(200)
        _raise_for_status(resp)  # no exception

    def test_201_created(self):
        resp = self._make_response(201)
        _raise_for_status(resp)  # no exception

    def test_204_no_content(self):
        resp = self._make_response(204)
        _raise_for_status(resp)  # no exception

    def test_400_raises_validation_error(self):
        resp = self._make_response(400, "bad request")
        with pytest.raises(ValidationError, match="bad request"):
            _raise_for_status(resp)

    def test_404_raises_job_not_found(self):
        resp = self._make_response(404, "not found")
        with pytest.raises(JobNotFoundError, match="not found"):
            _raise_for_status(resp)

    def test_500_raises_server_error(self):
        resp = self._make_response(500, "internal error")
        with pytest.raises(ServerError, match="internal error"):
            _raise_for_status(resp)

    def test_503_raises_server_error(self):
        resp = self._make_response(503)
        with pytest.raises(ServerError):
            _raise_for_status(resp)


class TestHttpClient:
    def test_get_success(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/api/v1/jobs/abc").respond(200, json={"id": "abc"})
            c = HttpClient(base_url=BASE_URL)
            result = c.get("/api/v1/jobs/abc")
            assert result == {"id": "abc"}

    def test_post_success(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/api/v1/jobs").respond(201, json={"id": "xyz"})
            c = HttpClient(base_url=BASE_URL)
            result = c.post("/api/v1/jobs", json={"type": "t"})
            assert result == {"id": "xyz"}

    def test_delete_success(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.delete("/api/v1/jobs/abc").respond(204)
            c = HttpClient(base_url=BASE_URL)
            c.delete("/api/v1/jobs/abc")  # no exception

    def test_network_error_raises_asyioflow_error(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/api/v1/jobs/abc").mock(side_effect=httpx.ConnectError("refused"))
            c = HttpClient(base_url=BASE_URL)
            with pytest.raises(AysioFlowError):
                c.get("/api/v1/jobs/abc")

    def test_404_raises_job_not_found(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/api/v1/jobs/missing").respond(404, text="not found")
            c = HttpClient(base_url=BASE_URL)
            with pytest.raises(JobNotFoundError):
                c.get("/api/v1/jobs/missing")


class TestAsyncHttpClient:
    async def test_get_success(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/api/v1/jobs/abc").respond(200, json={"id": "abc"})
            async with AsyncHttpClient(base_url=BASE_URL) as c:
                result = await c.get("/api/v1/jobs/abc")
            assert result == {"id": "abc"}

    async def test_network_error_raises_asyioflow_error(self):
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/api/v1/jobs/abc").mock(side_effect=httpx.ConnectError("refused"))
            async with AsyncHttpClient(base_url=BASE_URL) as c:
                with pytest.raises(AysioFlowError):
                    await c.get("/api/v1/jobs/abc")
