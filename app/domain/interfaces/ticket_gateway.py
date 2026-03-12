from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.tickets import TicketResponse, TicketCreate

class ITicketGateway(ABC):
    @abstractmethod
    async def create_ticket(self, ticket_data: TicketCreate) -> Optional[TicketResponse]:
        pass

    @abstractmethod
    async def get_client_tickets(self, service_id: int) -> List[TicketResponse]:
        pass

    @abstractmethod
    async def has_recent_ticket(self, service_id: int, hours: int = 24) -> bool:
        pass

    @abstractmethod
    async def get_ticket(self, ticket_id: int) -> Optional[TicketResponse]:
        pass
