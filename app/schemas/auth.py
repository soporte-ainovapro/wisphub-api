from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """Response model returned by the /auth/token endpoint."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Internal model used to carry decoded token claims."""
    username: Optional[str] = None
