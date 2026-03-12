from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from app.domain.models.clients import ClientResponse, ClientUpdateRequest, ClientVerifyRequest, ClientResolveRequest

class IClientGateway(ABC):
    @abstractmethod
    async def fetch_client(self, params: Dict[str, str]) -> Optional[ClientResponse]:
        pass

    @abstractmethod
    async def fetch_clients_by_query(self, query: str) -> List[ClientResponse]:
        pass

    @abstractmethod
    async def get_client_by_document(self, document: str) -> Optional[ClientResponse]:
        pass

    @abstractmethod
    async def get_client_by_phone(self, phone: str) -> Optional[ClientResponse]:
        pass

    @abstractmethod
    async def get_client_by_service_id(self, service_id: str) -> Optional[ClientResponse]:
        pass

    @abstractmethod
    async def get_clients(self) -> List[ClientResponse]:
        pass

    @abstractmethod
    async def update_client_profile(self, service_id: int, request_data: dict) -> bool:
        pass
