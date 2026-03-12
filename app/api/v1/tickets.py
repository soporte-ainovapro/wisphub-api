from fastapi import APIRouter, Depends, Path, Body, HTTPException
from app.services.tickets_service import zone_has_three_open_tickets, create_ticket, get_ticket
from app.domain.models.responses.response_actions import ResponseAction, TicketAction
from app.domain.models.responses.response_types import ResponseType
from app.core.config import settings
from app.domain.models.tickets import TicketCreate, TicketResponse, TicketCreateRequest
from app.utils.ticket_rules import priorities
from app.api.dependencies import verify_api_key

router = APIRouter(tags=["tickets"])


@router.post(
    "/api/tickets",
    response_model=TicketResponse | dict
)
async def create_ticket_endpoint(
    request: TicketCreateRequest = Body(...),
    _: str = Depends(verify_api_key)
):
    """
    Abre e instancia un nuevo Ticket de Soporte Técnico en WispHub.
    Verifica de manera preventiva que la zona no exceda el umbral permitido de tickets 
    abiertos para evitar saturación de visitas. Además, calcula automáticamente la fecha de 
    resolución aproximada en base a los días hábiles dictados por la configuración del núcleo.
    """
    zone_blocked = await zone_has_three_open_tickets(request.zone_id)
    import logging
    logging.getLogger(__name__).info(f"Zona {request.zone_id} bloqueada: {zone_blocked}")

    if zone_blocked:
        raise HTTPException(
            status_code=400,
            detail=f"Zona límite alcanzado. Máximo {settings.MAX_ACTIVE_TICKETS_PER_ZONE} tickets."
        )

    ticket_create = TicketCreate(
        service_id=request.service_id,
        subject=request.subject,
        technician_id=request.technician_id,
        description=request.description,
    )

    ticket = await create_ticket(ticket_create)

    if not ticket:
        raise HTTPException(
            status_code=400,
            detail=TicketAction.CREATION_FAILED.value if hasattr(TicketAction.CREATION_FAILED, 'value') else "Error creando ticket"
        )

    return ticket


@router.get("/api/tickets/subjects", response_model=dict)
async def get_ticket_subjects(_: str = Depends(verify_api_key)):
    """
    Devuelve todos los asuntos válidos para la creación de tickets en WispHub,
    agrupados por nivel de prioridad. Útil para bots y clientes externos que
    necesitan seleccionar un asunto válido antes de abrir un soporte.
    """
    all_subjects = [s for subjects in priorities.values() for s in subjects]
    data = {
        "by_priority": {
            "low": priorities[1],
            "normal": priorities[2],
            "high": priorities[3],
            "very_high": priorities[4],
        },
        "all": all_subjects
    }
    return data


@router.get("/api/tickets/zone-blocked/{zone_id}", response_model=dict)
async def check_zone_blocked_endpoint(zone_id: int = Path(..., description="ID de la zona del cliente"), _: str = Depends(verify_api_key)):
    """
    Verifica rápidamente si una zona específica ha excedido el límite máximo
    de tickets abiertos en WispHub. 
    Retorna verdadero o falso y el límite configurado actualmente.
    """
    zone_blocked = await zone_has_three_open_tickets(zone_id)

    return {
        "is_blocked": zone_blocked,
        "max_tickets": settings.MAX_ACTIVE_TICKETS_PER_ZONE
    }


@router.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket_endpoint(ticket_id: int = Path(..., description="El identificador único del ticket"), _: str = Depends(verify_api_key)):
    """
    Recupera la información completa de un soporte técnico mediante su ID único.
    Extrae elementos esenciales como la fecha de apertura, la prioridad asignada 
    y verifica el historial para traer la última respuesta o estado actual 
    resolutivo anotado en el sistema externo.
    """
    ticket = await get_ticket(ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail=TicketAction.NOT_FOUND.value if hasattr(TicketAction.NOT_FOUND, 'value') else "No encontrado"
        )

    return ticket
