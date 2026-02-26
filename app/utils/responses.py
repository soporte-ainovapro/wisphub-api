from app.schemas.responses.response_types import ResponseType
from app.schemas.responses.response_actions import ResponseAction, ClientAction
from app.schemas.responses.backend_response import BackendResponse


def build_client_response(client):
    if not client:
        return BackendResponse.info(
            action=ClientAction.NOT_FOUND
        )

    return BackendResponse.success(
        action=ClientAction.FOUND,
        data=client
    )
