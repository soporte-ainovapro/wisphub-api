from fastapi import APIRouter, Body, Depends, Path, HTTPException
from app.services.network_service import ping, get_task__id
from app.domain.models.responses.response_actions import ResponseAction, NetworkAction
from app.domain.models.responses.response_types import ResponseType
from app.domain.models.connection_status import ConnectionStatus
from app.domain.models.ping_request import PingRequest
from app.api.dependencies import verify_api_key
from typing import Dict, Any

router = APIRouter(tags=["network"])

@router.post("/api/{service_id}/ping/", response_model=Dict[str, Any])
async def create_ping(
    service_id: int = Path(..., description="ID del servicio que posee la IP o equipo asignado"),
    body: PingRequest = Body(...),
    _: str = Depends(verify_api_key)
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
        raise HTTPException(
            status_code=400,
            detail=NetworkAction.PING_FAILED.value if hasattr(NetworkAction.PING_FAILED, 'value') else "Ping failed"
        )

    return {"task_id": task_id}


@router.get("/api/ping/{task_id}/", response_model=Any)
async def get_ping_result(task_id: str = Path(..., description="ID de la tarea generada en la creación del Ping"), _: str = Depends(verify_api_key)):
    """
    Obtiene el resultado resolutivo de una tarea de PING previamente inicializada.
    Interpreta el nivel de pérdida de paquetes de los resultados devueltos por WispHub 
    (ej. paquetes enviados vs recibidos) para determinar si la conexión es Estable, 
    Intermitente, o si no hay servicio de internet en el extremo del cliente.
    """
    result = await ping(task_id)

    if result == ConnectionStatus.error:
        raise HTTPException(status_code=400, detail="Ping failed")

    if result == ConnectionStatus.no_internet:
        raise HTTPException(status_code=400, detail="No internet")

    if result == ConnectionStatus.intermittent:
        raise HTTPException(status_code=400, detail="Intermittent connection")

    if result == ConnectionStatus.stable:
        return {"result": "stable"}
