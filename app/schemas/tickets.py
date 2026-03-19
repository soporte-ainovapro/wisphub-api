from pydantic import BaseModel


class TicketCreate(BaseModel):
    service_id: int
    subject: str
    description: str
    technician_id: int | None


class TicketCreateRequest(TicketCreate):
    zone_id: int


class TicketResponse(BaseModel):
    ticket_id: int
    subject: str
    created_at: str
    end_date: str | None
    status_ticket: str
    priority: str
    answer_text: str | None
