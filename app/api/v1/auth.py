from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.schemas.auth import Token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/token",
    response_model=Token,
    summary="Obtain a JWT access token",
    description=(
        "Authenticate with API credentials (`username` and `password`) to receive a "
        "Bearer JWT token. Include this token in the `Authorization` header of all "
        "subsequent protected requests: `Authorization: Bearer <token>`."
    ),
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    Login endpoint. Validates credentials against the configured API user and
    returns a signed JWT token on success.
    """
    is_valid_user = form_data.username == settings.API_USERNAME
    is_valid_password = verify_password(form_data.password, settings.API_PASSWORD_HASH)

    if not is_valid_user or not is_valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": form_data.username})
    return Token(access_token=token, token_type="bearer")
