from fastapi import APIRouter, Depends, Path, Body, HTTPException

from app.services.interfaces import TicketService
from app.api.deps import get_ticket_service
from app.schemas.tickets import TicketResponse, TicketCreateRequest
from app.utils.ticket_rules import priorities
from app.api.deps import verify_api_key
from app.core.config import settings

router = APIRouter(tags=["tickets"])


@router.post("/api/tickets", response_model=TicketResponse | dict)
async def create_ticket_endpoint(
    request: TicketCreateRequest = Body(...),
    service: TicketService = Depends(get_ticket_service),
    _: str = Depends(verify_api_key),
):
    """
    Abre un nuevo Ticket de Soporte Técnico en WispHub. Verifica límites de zona.
    """
    return await service.create(request)


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
    service: TicketService = Depends(get_ticket_service),
    _: str = Depends(verify_api_key),
):
    """
    Verifica si una zona ha excedido el límite máximo de tickets abiertos.
    """
    zone_blocked = await service.zone_is_blocked(zone_id)
    return {
        "is_blocked": zone_blocked,
        "max_tickets": settings.MAX_ACTIVE_TICKETS_PER_ZONE,
    }


@router.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket_endpoint(
    ticket_id: int = Path(..., description="Identificador único del ticket"),
    service: TicketService = Depends(get_ticket_service),
    _: str = Depends(verify_api_key),
):
    """
    Recupera la información completa de un ticket por su ID.
    """
    ticket = await service.get(ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado.")

    return ticket
