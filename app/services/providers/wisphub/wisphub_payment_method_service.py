"""
Servicio WispHub para formas de pago.

Obtiene el catálogo de formas de pago disponibles en WispHub.
Resultado cacheado 15 minutos (es data de referencia que cambia raramente).
"""

from typing import List, Optional

import httpx
from async_lru import alru_cache

from app.schemas.payment_methods import PaymentMethodResponse


class WispHubPaymentMethodService:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.headers = {"Authorization": f"Api-Key {api_key}"}

    @alru_cache(ttl=900)
    async def list_payment_methods(self) -> Optional[List[PaymentMethodResponse]]:
        """Lista todas las formas de pago. Resultado cacheado 15 min."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/api/formas-de-pago/",
                headers=self.headers,
            )

        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except ValueError:
            return None

        results = data.get("results")
        if not isinstance(results, list):
            return None

        return [
            PaymentMethodResponse(id=p.get("id"), name=p.get("nombre"))
            for p in results
        ]
