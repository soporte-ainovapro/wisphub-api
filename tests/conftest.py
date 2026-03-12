import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the whole test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

def _get_auth_headers() -> dict:
    """Generate a valid API Key Header for testing authenticated routes."""
    return {"X-API-Key": settings.WISPHUB_INTERNAL_API_KEY}


@pytest_asyncio.fixture
async def async_client():
    """Unauthenticated client — for testing public endpoints and 401 scenarios."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def auth_client():
    """Authenticated client — pre-configured with a valid Bearer token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers=_get_auth_headers()
    ) as client:
        yield client
