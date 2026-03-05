import httpx
from datetime import datetime
from typing import Optional
from app.core.config import settings
from app.utils.ticket_rules import get_priority
from app.utils.dates import add_business_days
from app.schemas.tickets import TicketCreate, TicketResponse

url = settings.TICKETS_URL
HEADERS = {"Authorization": f"Api-Key {settings.WISPHUB_NET_KEY}"}


async def zone_has_three_open_tickets(zone_id: int) -> bool:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            url, headers=HEADERS, params={"estado": settings.ACTIVE_TICKET_STATES}
        )
        if response.status_code != 200:
            return False

        data = response.json()
        tickets = data.get("results", [])
        
        zone_count = 0

        for ticket in tickets:
            service = ticket.get("servicio", [])
            zone = service.get("zona")
            if zone and zone.get("id") == zone_id:
                zone_count += 1
                if zone_count >= settings.MAX_ACTIVE_TICKETS_PER_ZONE:
                    return True

        return False


async def create_ticket(
    ticket: TicketCreate
)-> Optional[TicketResponse]:
    department = "Soporte Técnico"
    priority = get_priority(ticket.subject) or 2

    start_date = datetime.now()
    end_date = add_business_days(start_date, settings.MAX_TICKET_RESOLUTION_DAYS)
    
    payload = {
        "servicio": ticket.service_id,
        "asunto": ticket.subject,
        "asuntos_default": ticket.subject,
        "tecnico": ticket.technician_id,
        "descripcion": ticket.description,
        "estado": settings.DEFAULT_TICKET_STATUS,
        "prioridad": priority,
        "fecha_inicio": start_date.strftime("%d/%m/%Y %H:%M"),
        "fecha_final": end_date.strftime("%d/%m/%Y %H:%M"),
        "departamento": department,
        "departamentos_default": department,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        # Solo enviar campos que tengan valor
        payload_filtered = {k: v for k, v in payload.items() if v not in (None, "")}
        response = await client.post(
            url,
            headers=HEADERS,
            files={k: (None, str(v)) for k, v in payload_filtered.items()},
        )

    print(f"Respuesta de creación de ticket: {response.status_code} - {response.text}")
    if response.status_code != 201:
        return None

    data = response.json()

    if not isinstance(data, dict) or not data:
        return None

    t = data

    return TicketResponse(
        ticket_id=t.get("id_ticket"),
        subject=t.get("asunto"),
        created_at=t.get("fecha_estimada_inicio"),
        end_date=t.get("fecha_estimada_fin"),
        status_ticket=t.get("estado"),
        priority=t.get("prioridad"),
        answer_text=None
    )


async def get_ticket(ticket_id: int) -> Optional[TicketResponse]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{settings.TICKETS_URL}{ticket_id}/",
            headers=HEADERS,
        )
        
        if response.status_code != 200:
            return None

        ticket = response.json()
        
        
        if not isinstance(ticket, dict) or not ticket:
            return None

        t = ticket
        answer = t.get("respuestas")
        
        return TicketResponse(
            ticket_id=t.get("id_ticket"),
            subject=t.get("asunto"),
            created_at=t.get("fecha_estimada_inicio"),
            end_date=t.get("fecha_estimada_fin"),
            status_ticket=t.get("estado"),
            priority=t.get("prioridad"),
            answer_text=(answer.get("respuesta") if isinstance(answer, dict) else None),
        )

