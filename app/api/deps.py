"""
Único punto de inyección de dependencias (Factory/DI).

Los routers importan solo las funciones get_*_service() de este módulo.
Las clases concretas se instancian aquí según el valor de settings.ISP_PROVIDER.
Añadir soporte para un nuevo proveedor ISP solo requiere cambios en este archivo.
"""

from fastapi import Depends, HTTPException, Security, status
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


def get_client_service() -> ClientService:
    if settings.ISP_PROVIDER == "wisphub":
        from app.services.providers.wisphub.wisphub_client_service import (
            WispHubClientService,
        )

        return WispHubClientService(
            base_url=settings.WISPHUB_NET_HOST,
            api_key=settings.WISPHUB_NET_KEY,
        )

    raise ValueError(
        f"ISP_PROVIDER no soportado: '{settings.ISP_PROVIDER}'. "
        "Valores válidos: 'wisphub'"
    )


def get_ticket_service() -> TicketService:
    if settings.ISP_PROVIDER == "wisphub":
        from app.services.providers.wisphub.wisphub_ticket_service import (
            WispHubTicketService,
        )

        return WispHubTicketService(
            base_url=settings.WISPHUB_NET_HOST,
            api_key=settings.WISPHUB_NET_KEY,
        )

    raise ValueError(f"ISP_PROVIDER no soportado: '{settings.ISP_PROVIDER}'")


def get_internet_plan_service() -> InternetPlanService:
    if settings.ISP_PROVIDER == "wisphub":
        from app.services.providers.wisphub.wisphub_internet_plan_service import (
            WispHubInternetPlanService,
        )

        return WispHubInternetPlanService(
            base_url=settings.WISPHUB_NET_HOST,
            api_key=settings.WISPHUB_NET_KEY,
        )

    raise ValueError(f"ISP_PROVIDER no soportado: '{settings.ISP_PROVIDER}'")


def get_network_service() -> NetworkService:
    if settings.ISP_PROVIDER == "wisphub":
        from app.services.providers.wisphub.wisphub_network_service import (
            WispHubNetworkService,
        )

        return WispHubNetworkService(
            base_url=settings.WISPHUB_NET_HOST,
            api_key=settings.WISPHUB_NET_KEY,
        )

    raise ValueError(f"ISP_PROVIDER no soportado: '{settings.ISP_PROVIDER}'")
