import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import create_access_token


def _get_auth_headers() -> dict:
    """Generate a valid Bearer token for tests using a known test secret."""
    token = create_access_token(data={"sub": "admin"})
    return {"Authorization": f"Bearer {token}"}


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
