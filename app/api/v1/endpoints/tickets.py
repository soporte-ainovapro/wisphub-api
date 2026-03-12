from fastapi import APIRouter, Depends, Path, Body, HTTPException
from typing import Any

from app.infrastructure.gateways.wisphub_ticket_gateway import WispHubTicketGateway
from app.core.config import settings
from app.domain.models.tickets import TicketCreate, TicketResponse, TicketCreateRequest
from app.utils.ticket_rules import priorities
from app.api.dependencies import verify_api_key

router = APIRouter(tags=["tickets"])


def get_ticket_gateway() -> WispHubTicketGateway:
    return WispHubTicketGateway(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
    )


@router.post("/api/tickets", response_model=TicketResponse | dict)
async def create_ticket_endpoint(
    request: TicketCreateRequest = Body(...),
    gateway: WispHubTicketGateway = Depends(get_ticket_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Abre un nuevo Ticket de Soporte Técnico en WispHub. Verifica límites de zona.
    """
    import logging
    zone_blocked = await gateway.zone_has_three_open_tickets(request.zone_id)
    logging.getLogger(__name__).info(f"Zona {request.zone_id} bloqueada: {zone_blocked}")

    if zone_blocked:
        raise HTTPException(
            status_code=400,
            detail=f"Zona límite alcanzado. Máximo {settings.MAX_ACTIVE_TICKETS_PER_ZONE} tickets.",
        )

    ticket_create = TicketCreate(
        service_id=request.service_id,
        subject=request.subject,
        technician_id=request.technician_id,
        description=request.description,
    )

    ticket = await gateway.create_ticket(ticket_create)

    if not ticket:
        raise HTTPException(status_code=400, detail="Error creando ticket.")

    return ticket


@router.get("/api/tickets/subjects", response_model=dict)
async def get_ticket_subjects(_: str = Depends(verify_api_key)):
    """
    Devuelve todos los asuntos válidos para la creación de tickets, agrupados por prioridad.
    """
    all_subjects = [s for subjects in priorities.values() for s in subjects]
    return {
        "by_priority": {
            "low": priorities[1],
            "normal": priorities[2],
            "high": priorities[3],
            "very_high": priorities[4],
        },
        "all": all_subjects,
    }


@router.get("/api/tickets/zone-blocked/{zone_id}", response_model=dict)
async def check_zone_blocked_endpoint(
    zone_id: int = Path(..., description="ID de la zona del cliente"),
    gateway: WispHubTicketGateway = Depends(get_ticket_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Verifica si una zona ha excedido el límite máximo de tickets abiertos.
    """
    zone_blocked = await gateway.zone_has_three_open_tickets(zone_id)
    return {"is_blocked": zone_blocked, "max_tickets": settings.MAX_ACTIVE_TICKETS_PER_ZONE}


@router.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket_endpoint(
    ticket_id: int = Path(..., description="Identificador único del ticket"),
    gateway: WispHubTicketGateway = Depends(get_ticket_gateway),
    _: str = Depends(verify_api_key),
):
    """
    Recupera la información completa de un ticket por su ID.
    """
    ticket = await gateway.get_ticket(ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado.")

    return ticket
