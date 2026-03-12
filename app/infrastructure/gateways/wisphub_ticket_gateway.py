import httpx
from datetime import datetime
from typing import List, Optional

from app.core.config import settings
from app.domain.interfaces.ticket_gateway import ITicketGateway
from app.domain.models.tickets import TicketCreate, TicketResponse
from app.utils.ticket_rules import get_priority
from app.utils.dates import add_business_days


class WispHubTicketGateway(ITicketGateway):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Api-Key {api_key}"}

    async def create_ticket(self, ticket: TicketCreate) -> Optional[TicketResponse]:
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
            payload_filtered = {k: v for k, v in payload.items() if v not in (None, "")}
            response = await client.post(
                f"{self.base_url}/api/tickets/",
                headers=self.headers,
                files={k: (None, str(v)) for k, v in payload_filtered.items()},
            )

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
            answer_text=None,
        )

    async def get_client_tickets(self, service_id: int) -> List[TicketResponse]:
        url = f"{self.base_url}/api/tickets/"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                url,
                headers=self.headers,
                params={"servicio": service_id},
            )

        if response.status_code != 200:
            return []

        data = response.json()
        results = data.get("results", [])

        tickets = []
        for t in results:
            answer = t.get("respuestas")
            tickets.append(TicketResponse(
                ticket_id=t.get("id_ticket"),
                subject=t.get("asunto"),
                created_at=t.get("fecha_estimada_inicio"),
                end_date=t.get("fecha_estimada_fin"),
                status_ticket=t.get("estado"),
                priority=t.get("prioridad"),
                answer_text=(answer.get("respuesta") if isinstance(answer, dict) else None),
            ))
        return tickets

    async def has_recent_ticket(self, service_id: int, hours: int = 24) -> bool:
        tickets = await self.get_client_tickets(service_id)
        return bool(tickets)

    async def get_ticket(self, ticket_id: int) -> Optional[TicketResponse]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/api/tickets/{ticket_id}/",
                headers=self.headers,
            )

        if response.status_code != 200:
            return None

        t = response.json()
        if not isinstance(t, dict) or not t:
            return None

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

    async def zone_has_three_open_tickets(self, zone_id: int) -> bool:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/api/tickets/",
                headers=self.headers,
                params={"estado": settings.ACTIVE_TICKET_STATES},
            )
            if response.status_code != 200:
                return False

            data = response.json()
            tickets = data.get("results", [])

            zone_count = 0
            for ticket in tickets:
                service = ticket.get("servicio", {})
                zone = service.get("zona")
                if zone and zone.get("id") == zone_id:
                    zone_count += 1
                    if zone_count >= settings.MAX_ACTIVE_TICKETS_PER_ZONE:
                        return True

            return False
