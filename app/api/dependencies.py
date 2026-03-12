from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    FastAPI dependency that extracts and validates the API Key from the
    X-API-Key header. Returns the key on success.
    Raises HTTP 403 if the token is missing or invalid.
    """
    if api_key != settings.WISPHUB_INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid API Key",
        )
    return api_key
