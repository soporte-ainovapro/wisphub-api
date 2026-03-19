from typing import Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Clave API para autenticarse con WispHub Net
    WISPHUB_NET_KEY: str

    # URL base de WispHub Net (ejemplo: "https://tuservidor.wisphub.net")
    WISPHUB_NET_HOST: str

    # Límite de tickets activos por zona
    MAX_ACTIVE_TICKETS_PER_ZONE: int = 3

    # Solo consideramos como "activos" los tickets que están en estos estados (pueden ser "Abierto", "En Progreso", etc. dependiendo de la configuración de WispHub)
    ACTIVE_TICKET_STATES: Tuple[int, ...] = (1,)

    # El estado por defecto para nuevos tickets (puede ser "Abierto", "En Progreso", etc. dependiendo de la configuración de WispHub)
    DEFAULT_TICKET_STATUS: int = 1

    # Días hábiles para la resolución de un ticket
    MAX_TICKET_RESOLUTION_DAYS: int = 3

    # Clave interna estática para autenticarse contra WispHub API (Frontend -> Middleware)
    WISPHUB_INTERNAL_API_KEY: str

    # Proveedor ISP activo — determina qué implementación concreta se inyecta en deps.py
    ISP_PROVIDER: str = "wisphub"


settings = Settings()
