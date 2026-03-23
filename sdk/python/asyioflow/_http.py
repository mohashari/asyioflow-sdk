from __future__ import annotations

from typing import Any

import httpx

from .exceptions import AysioFlowError, JobNotFoundError, ServerError, ValidationError

_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def _raise_for_status(response: httpx.Response) -> None:
    """Map HTTP status codes to typed exceptions."""
    if response.status_code == 400:
        raise ValidationError(response.text)
    if response.status_code == 404:
        raise JobNotFoundError(response.text)
    if response.status_code >= 500:
        raise ServerError(response.text)
    if not response.is_success:
        raise AysioFlowError(
            f"Unexpected status {response.status_code}: {response.text}"
        )


class HttpClient:
    """Synchronous httpx transport."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        api_key: str | None = None,
    ) -> None:
        headers = dict(_HEADERS)
        if api_key:
            headers["X-Api-Key"] = api_key
        self._client = httpx.Client(
            base_url=base_url, headers=headers, timeout=timeout
        )

    def get(self, path: str) -> dict[str, Any]:
        try:
            resp = self._client.get(path)
            _raise_for_status(resp)
            return resp.json()  # type: ignore[no-any-return]
        except httpx.RequestError as exc:
            raise AysioFlowError(str(exc)) from exc

    def post(self, path: str, json: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = self._client.post(path, json=json)
            _raise_for_status(resp)
            return resp.json()  # type: ignore[no-any-return]
        except httpx.RequestError as exc:
            raise AysioFlowError(str(exc)) from exc

    def delete(self, path: str) -> None:
        try:
            resp = self._client.delete(path)
            _raise_for_status(resp)
        except httpx.RequestError as exc:
            raise AysioFlowError(str(exc)) from exc

    def close(self) -> None:
        self._client.close()


class AsyncHttpClient:
    """Asynchronous httpx transport, usable as async context manager."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        api_key: str | None = None,
    ) -> None:
        headers = dict(_HEADERS)
        if api_key:
            headers["X-Api-Key"] = api_key
        self._client = httpx.AsyncClient(
            base_url=base_url, headers=headers, timeout=timeout
        )

    async def get(self, path: str) -> dict[str, Any]:
        try:
            resp = await self._client.get(path)
            _raise_for_status(resp)
            return resp.json()  # type: ignore[no-any-return]
        except httpx.RequestError as exc:
            raise AysioFlowError(str(exc)) from exc

    async def post(self, path: str, json: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = await self._client.post(path, json=json)
            _raise_for_status(resp)
            return resp.json()  # type: ignore[no-any-return]
        except httpx.RequestError as exc:
            raise AysioFlowError(str(exc)) from exc

    async def delete(self, path: str) -> None:
        try:
            resp = await self._client.delete(path)
            _raise_for_status(resp)
        except httpx.RequestError as exc:
            raise AysioFlowError(str(exc)) from exc

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHttpClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
