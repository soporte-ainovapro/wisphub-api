"""
Servicio WispHub para tickets de soporte.

Combina acceso HTTP a la API de WispHub con la lógica de negocio:
validación de límite de zona y creación de tickets con prioridad y fechas.
"""

from datetime import date as date_type, datetime
from typing import Optional

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.tickets import TicketCreate, TicketCreateRequest, TicketResponse
from app.utils.dates import add_business_days, get_colombian_holidays
from app.utils.ticket_rules import get_priority


class WispHubTicketService:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.headers = {"Authorization": f"Api-Key {api_key}"}

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def create_ticket(self, ticket: TicketCreate) -> Optional[TicketResponse]:
        department = "Soporte Técnico"
        priority = get_priority(ticket.subject) or 2

        start_date = datetime.now()
        holidays = get_colombian_holidays(start_date.year) | frozenset(
            date_type.fromisoformat(d) for d in settings.EXTRA_HOLIDAYS
        )
        end_date = add_business_days(start_date, settings.MAX_TICKET_RESOLUTION_DAYS, holidays)

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

    # ------------------------------------------------------------------
    # Business logic
    # ------------------------------------------------------------------

    async def create(self, request: TicketCreateRequest) -> TicketResponse:
        if await self.zone_has_three_open_tickets(request.zone_id):
            raise HTTPException(
                status_code=400,
                detail=f"Zona límite alcanzado. Máximo {settings.MAX_ACTIVE_TICKETS_PER_ZONE} tickets.",
            )

        ticket_data = TicketCreate(
            service_id=request.service_id,
            subject=request.subject,
            technician_id=request.technician_id,
            description=request.description,
        )

        ticket = await self.create_ticket(ticket_data)
        if not ticket:
            raise HTTPException(status_code=400, detail="Error creando ticket.")

        return ticket

    async def get(self, ticket_id: int) -> Optional[TicketResponse]:
        return await self.get_ticket(ticket_id)

    async def zone_is_blocked(self, zone_id: int) -> bool:
        return await self.zone_has_three_open_tickets(zone_id)
