from abc import ABC, abstractmethod
from typing import Optional
from app.domain.models.tickets import TicketResponse, TicketCreate

class ITicketGateway(ABC):
    @abstractmethod
    async def create_ticket(self, ticket_data: TicketCreate) -> Optional[TicketResponse]:
        pass

    @abstractmethod
    async def get_ticket(self, ticket_id: int) -> Optional[TicketResponse]:
        pass

    @abstractmethod
    async def zone_has_three_open_tickets(self, zone_id: int) -> bool:
        return False
