from abc import ABC, abstractmethod

class INetworkGateway(ABC):
    @abstractmethod
    async def reboot_antenna(self, service_id: int) -> bool:
        pass

    @abstractmethod
    async def check_connection(self, antenna_ip: str, router_ip: str) -> bool:
        pass
