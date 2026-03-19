"""
Único punto de inyección de dependencias (Factory/DI).

Los routers importan solo las funciones get_*_service() de este módulo.
Las clases concretas se instancian como singletons al arrancar la app para que
los cachés internos (alru_cache) persistan entre requests.
Añadir soporte para un nuevo proveedor ISP solo requiere cambios en este archivo.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.services.interfaces import (
    ClientService,
    InternetPlanService,
    NetworkService,
    TicketService,
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key != settings.WISPHUB_INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key inválida o ausente.",
        )
    return api_key


def _build_services() -> tuple:
    """Instancia los servicios una sola vez al importar el módulo."""
    if settings.ISP_PROVIDER == "wisphub":
        from app.services.providers.wisphub.wisphub_client_service import (
            WispHubClientService,
        )
        from app.services.providers.wisphub.wisphub_internet_plan_service import (
            WispHubInternetPlanService,
        )
        from app.services.providers.wisphub.wisphub_network_service import (
            WispHubNetworkService,
        )
        from app.services.providers.wisphub.wisphub_ticket_service import (
            WispHubTicketService,
        )

        kwargs = {"base_url": settings.WISPHUB_NET_HOST, "api_key": settings.WISPHUB_NET_KEY}
        return (
            WispHubClientService(**kwargs),
            WispHubTicketService(**kwargs),
            WispHubInternetPlanService(**kwargs),
            WispHubNetworkService(**kwargs),
        )

    raise ValueError(
        f"ISP_PROVIDER no soportado: '{settings.ISP_PROVIDER}'. "
        "Valores válidos: 'wisphub'"
    )


_client_service, _ticket_service, _internet_plan_service, _network_service = _build_services()


def get_client_service() -> ClientService:
    return _client_service


def get_ticket_service() -> TicketService:
    return _ticket_service


def get_internet_plan_service() -> InternetPlanService:
    return _internet_plan_service


def get_network_service() -> NetworkService:
    return _network_service
