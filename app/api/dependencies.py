from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token

# Points to the token endpoint so FastAPI's OpenAPI UI can auto-authenticate.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    FastAPI dependency that extracts and validates the Bearer token from the
    Authorization header. Returns the authenticated username on success.
    Raises HTTP 401 if the token is missing, invalid, or expired.
    """
    return decode_access_token(token)
