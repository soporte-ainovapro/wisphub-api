from fastapi import APIRouter, Depends, Path, Body
from app.services.tickets_service import zone_has_three_open_tickets, create_ticket, get_ticket
from app.schemas.responses.response_actions import ResponseAction, TicketAction
from app.schemas.responses.response_types import ResponseType
from app.schemas.responses.backend_response import BackendResponse
from app.core.config import settings
from app.schemas.tickets import TicketCreate, TicketResponse, TicketCreateRequest
from app.utils.ticket_rules import priorities
from app.api.dependencies import get_current_user

router = APIRouter(tags=["tickets"])


@router.post(
    "/api/v1/tickets",
    response_model=BackendResponse[TicketResponse | dict]
)
async def create_ticket_endpoint(
    request: TicketCreateRequest = Body(...),
    _: str = Depends(get_current_user)
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
        return BackendResponse.info(
            action=TicketAction.ZONE_LIMIT_REACHED,
            data={"max_tickets": settings.MAX_ACTIVE_TICKETS_PER_ZONE}
        )

    ticket_create = TicketCreate(
        service_id=request.service_id,
        subject=request.subject,
        technician_id=request.technician_id,
        description=request.description,
    )

    ticket = await create_ticket(ticket_create)

    if not ticket:
        return BackendResponse.error(
            action=TicketAction.CREATION_FAILED
        )

    return BackendResponse.success(
        action=TicketAction.CREATED,
        data=ticket
    )


@router.get("/api/v1/tickets/subjects", response_model=BackendResponse[dict])
async def get_ticket_subjects(_: str = Depends(get_current_user)):
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
    return BackendResponse.success(action=TicketAction.SUBJECTS_LISTED, data=data)


@router.get("/api/v1/tickets/zone-blocked/{zone_id}", response_model=BackendResponse[dict])
async def check_zone_blocked_endpoint(zone_id: int = Path(..., description="ID de la zona del cliente"), _: str = Depends(get_current_user)):
    """
    Verifica rápidamente si una zona específica ha excedido el límite máximo
    de tickets abiertos en WispHub. 
    Retorna verdadero o falso y el límite configurado actualmente.
    """
    zone_blocked = await zone_has_three_open_tickets(zone_id)

    return BackendResponse.success(
        action=TicketAction.FOUND,
        data={
            "is_blocked": zone_blocked,
            "max_tickets": settings.MAX_ACTIVE_TICKETS_PER_ZONE
        }
    )


@router.get("/api/v1/tickets/{ticket_id}", response_model=BackendResponse[TicketResponse])
async def get_ticket_endpoint(ticket_id: int = Path(..., description="El identificador único del ticket"), _: str = Depends(get_current_user)):
    """
    Recupera la información completa de un soporte técnico mediante su ID único.
    Extrae elementos esenciales como la fecha de apertura, la prioridad asignada 
    y verifica el historial para traer la última respuesta o estado actual 
    resolutivo anotado en el sistema externo.
    """
    ticket = await get_ticket(ticket_id)

    if not ticket:
        return BackendResponse.info(
            action=TicketAction.NOT_FOUND
        )

    return BackendResponse.success(
        action=TicketAction.FOUND,
        data=ticket
    )
