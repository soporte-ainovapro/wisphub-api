from fastapi import APIRouter, Body, Path
from app.services.network_service import ping, get_task__id
from app.schemas.responses.backend_response import BackendResponse
from app.schemas.responses.response_actions import ResponseAction, NetworkAction
from app.schemas.responses.response_types import ResponseType
from app.schemas.connection_status import ConnectionStatus
from app.schemas.ping_request import PingRequest
from typing import Dict, Any

router = APIRouter(tags=["network"])

@router.post("/api/v1/{service_id}/ping/", response_model=BackendResponse[Dict[str, Any]])
async def create_ping(
    service_id: int = Path(..., description="ID del servicio que posee la IP o equipo asignado"),
    body: PingRequest = Body(...)
):
    """
    Inicia una tarea asíncrona de diagnóstico de red (ICMP PING) dirigida a un equipo cliente.
    Acepta el número de pings a enviar. Como las pruebas de latencia demoran, esta ruta
    crea un trabajo de red en WispHub (Devuelve HTTP 202 Interno) y retorna un `task_id` 
    para poder sondear los resultados posteriormente.
    """
    task_id = await get_task__id(
        pings=body.pings,
        service_id=service_id
    )

    if not task_id:
        return BackendResponse.error(
            action=NetworkAction.PING_FAILED
        )

    return BackendResponse.success(
        action=NetworkAction.PING_CREATED,
        data={"task_id": task_id}
    )


@router.get("/api/v1/ping/{task_id}/", response_model=BackendResponse[None])
async def get_ping_result(task_id: str = Path(..., description="ID de la tarea generada en la creación del Ping")):
    """
    Obtiene el resultado resolutivo de una tarea de PING previamente inicializada.
    Interpreta el nivel de pérdida de paquetes de los resultados devueltos por WispHub 
    (ej. paquetes enviados vs recibidos) para determinar si la conexión es Estable, 
    Intermitente, o si no hay servicio de internet en el extremo del cliente.
    """
    result = await ping(task_id)

    if result == ConnectionStatus.error:
        return BackendResponse.error(
            action=NetworkAction.PING_FAILED
        )

    if result == ConnectionStatus.no_internet:
        return BackendResponse.info(
            action=NetworkAction.NO_INTERNET
        )

    if result == ConnectionStatus.intermittent:
        return BackendResponse.info(
            action=NetworkAction.INTERMITTENT
        )

    if result == ConnectionStatus.stable:
        return BackendResponse.success(
            action=NetworkAction.STABLE
        )
