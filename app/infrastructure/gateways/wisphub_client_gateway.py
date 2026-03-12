import httpx
from typing import List, Optional, Dict
from async_lru import alru_cache

from app.core.config import settings
from app.domain.interfaces.client_gateway import IClientGateway
from app.domain.models.clients import ClientResponse


def _parse_client(c: dict) -> ClientResponse:
    zone = c.get("zona")
    technician = c.get("tecnico")
    internet_plan = c.get("plan_internet")

    raw_price = c.get("precio_plan")
    try:
        resolved_price = float(raw_price) if raw_price not in (None, "", "0", "0.00") else None
    except (ValueError, TypeError):
        resolved_price = None

    return ClientResponse(
        service_id=c.get("id_servicio"),
        name=c.get("nombre"),
        document=c.get("cedula"),
        phone=c.get("telefono"),
        address=c.get("direccion"),
        city=c.get("ciudad"),
        locality=c.get("localidad"),
        payment_status=c.get("estado"),
        zone_id=zone.get("id") if isinstance(zone, dict) else None,
        antenna_ip=c.get("ip"),
        cut_off_date=c.get("fecha_corte"),
        outstanding_balance=c.get("saldo"),
        lan_interface=c.get("interfaz_lan"),
        internet_plan_name=(
            internet_plan.get("nombre")
            if isinstance(internet_plan, dict)
            else None
        ),
        internet_plan_price=resolved_price,
        technician_id=(
            technician.get("id")
            if isinstance(technician, dict)
            else None
        ),
    )


class WispHubClientGateway(IClientGateway):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Api-Key {api_key}"}

    async def fetch_client(self, params: Dict[str, str]) -> Optional[ClientResponse]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/api/clientes/",
                headers=self.headers,
                params=params,
            )

        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except ValueError:
            return None

        results = data.get("results")
        if not isinstance(results, list) or not results:
            return None

        return _parse_client(results[0])

    async def fetch_clients_by_query(self, query: str) -> List[ClientResponse]:
        all_clients = await self.get_clients()
        if not all_clients:
            return []

        q = query.strip().lower()
        matches: List[ClientResponse] = []
        for c in all_clients:
            searchable = " ".join(filter(None, [
                c.name,
                c.address,
                c.document,
                c.phone,
            ])).lower()
            if q in searchable:
                matches.append(c)

        return matches

    async def get_client_by_document(self, document: str) -> Optional[ClientResponse]:
        return await self.fetch_client({"cedula": document})

    async def get_client_by_phone(self, phone: str) -> Optional[ClientResponse]:
        phone = phone.replace("+", "").strip()
        return await self.fetch_client({"telefono": phone})

    async def get_client_by_service_id(self, service_id: str) -> Optional[ClientResponse]:
        return await self.fetch_client({"id_servicio": service_id})

    @alru_cache(maxsize=1, ttl=300)
    async def get_clients(self) -> List[ClientResponse]:
        """
        Carga TODOS los clientes de WispHub siguiendo la paginación.
        Los resultados se cachean por 5 minutos.
        """
        all_results: List[ClientResponse] = []
        next_url: Optional[str] = f"{self.base_url}/api/clientes/"

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            while next_url:
                response = await client.get(next_url, headers=self.headers)
                if response.status_code != 200:
                    break
                try:
                    data = response.json()
                except Exception:
                    break
                results = data.get("results")
                if not isinstance(results, list):
                    break
                all_results.extend(_parse_client(c) for c in results)
                next_url = data.get("next")

        return all_results

    async def update_client_profile(self, service_id: int, request_data: dict) -> bool:
        url = f"{self.base_url}/api/clientes/{service_id}/perfil/"
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.put(
                    url,
                    headers=self.headers,
                    json=request_data
                )
                return response.status_code in [200, 204]
            except httpx.RequestError:
                return False
