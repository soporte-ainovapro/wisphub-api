from fastapi import APIRouter, Body, Depends, Path, HTTPException
from typing import Dict, Any

from app.services.interfaces import NetworkService
from app.api.deps import get_network_service
from app.schemas.connection_status import ConnectionStatus
from app.schemas.ping_request import PingRequest
from app.api.deps import verify_api_key

router = APIRouter(tags=["network"])


@router.post("/api/{service_id}/ping/", response_model=Dict[str, Any])
async def create_ping(
    service_id: int = Path(
        ..., description="ID del servicio que posee la IP o equipo asignado"
    ),
    body: PingRequest = Body(...),
    service: NetworkService = Depends(get_network_service),
    _: str = Depends(verify_api_key),
):
    """
    Inicia una tarea asíncrona de diagnóstico de red (ICMP PING) dirigida a un equipo cliente.
    """
    task_id = await service.start_ping(service_id=service_id, pings=body.pings)

    if not task_id:
        raise HTTPException(
            status_code=400, detail="Ping failed. No se pudo obtener el task_id."
        )

    return {"task_id": task_id}


@router.get("/api/ping/{task_id}/", response_model=Any)
async def get_ping_result(
    task_id: str = Path(
        ..., description="ID de la tarea generada en la creación del Ping"
    ),
    service: NetworkService = Depends(get_network_service),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene el resultado de una tarea de PING previamente inicializada.
    """
    result = await service.get_ping_result(task_id)

    if result == ConnectionStatus.error:
        raise HTTPException(status_code=400, detail="Ping failed")

    return {"result": result.value}
