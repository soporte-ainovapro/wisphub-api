from fastapi import HTTPException
from app.schemas.clients import ClientAction


def build_client_response(client):
    if not client:
        raise HTTPException(
            status_code=404,
            detail=ClientAction.NOT_FOUND.value
            if hasattr(ClientAction.NOT_FOUND, "value")
            else "Client not found",
        )
    return client
