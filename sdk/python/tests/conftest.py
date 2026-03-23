import pytest
import respx
from asyioflow.client import AysioFlow, AsyncAysioFlow

BASE_URL = "http://test-engine:8080"


@pytest.fixture
def client():
    return AysioFlow(base_url=BASE_URL)


@pytest.fixture
async def async_client():
    async with AsyncAysioFlow(base_url=BASE_URL) as c:
        yield c


@pytest.fixture
def mock_http():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as mock:
        yield mock
