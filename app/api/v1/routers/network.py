from fastapi import APIRouter, Body, Depends, Path, HTTPException
from typing import Dict, Any

from app.infrastructure.gateways.wisphub_network_gateway import WispHubNetworkGateway
from app.domain.models.connection_status import ConnectionStatus
from app.domain.models.ping_request import PingRequest
from app.api.dependencies import verify_api_key
from app.core.config import settings

router = APIRouter(tags=["network"])


def get_network_gateway() -> WispHubNetworkGateway:
    return WispHubNetworkGateway(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
    )


@router.post("/api/{service_id}/ping/", response_model=Dict[str, Any])
async def create_ping(
    service_id: int = Path(..., description="ID del servicio que posee la IP o equipo asignado"),
    body: PingRequest = Body(...),
    gateway: WispHubNetworkGateway = Depends(get_network_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Inicia una tarea asíncrona de diagnóstico de red (ICMP PING) dirigida a un equipo cliente.
    """
    task_id = await gateway._get_task_id(pings=body.pings, service_id=service_id)

    if not task_id:
        raise HTTPException(status_code=400, detail="Ping failed. No se pudo obtener el task_id.")

    return {"task_id": task_id}


@router.get("/api/ping/{task_id}/", response_model=Any)
async def get_ping_result(
    task_id: str = Path(..., description="ID de la tarea generada en la creación del Ping"),
    gateway: WispHubNetworkGateway = Depends(get_network_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Obtiene el resultado de una tarea de PING previamente inicializada.
    """
    result = await gateway._poll_ping(task_id)

    if result == ConnectionStatus.error:
        raise HTTPException(status_code=400, detail="Ping failed")
    if result == ConnectionStatus.no_internet:
        raise HTTPException(status_code=400, detail="No internet")
    if result == ConnectionStatus.intermittent:
        raise HTTPException(status_code=400, detail="Intermittent connection")
    if result == ConnectionStatus.stable:
        return {"result": "stable"}
    if result == ConnectionStatus.pending:
        return {"result": "pending"}
